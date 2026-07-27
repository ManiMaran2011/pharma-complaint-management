from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.complaint import Complaint, ChatMessage
from app.schemas.complaint import ChatRequest, ChatResponse, ComplaintOut
from app.agents.graph import run_complaint_agent, FORM_KEYS, RISK_KEYS
from app.services.document_parser import extract_text

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _complaint_to_dict(c: Complaint) -> dict:
    return {k: getattr(c, k) for k in FORM_KEYS + RISK_KEYS}


def _apply_result(c: Complaint, result: dict) -> None:
    for k in FORM_KEYS:
        if result["merged"].get(k) is not None:
            setattr(c, k, result["merged"][k])
    for k in RISK_KEYS:
        if result.get("risk", {}).get(k) is not None:
            setattr(c, k, result["risk"][k])
    if result.get("updated_fields"):
        c.status = "Triaged" if result.get("risk") else "Pending Triage"


def _get_or_create(db: Session, complaint_id: str | None) -> Complaint:
    if complaint_id:
        c = db.get(Complaint, complaint_id)
        if c:
            return c
    c = Complaint()
    db.add(c)
    db.flush()
    return c


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """Log Complaint tool + Edit Complaint tool — natural-language prompt in, form state out."""
    c = _get_or_create(db, req.complaint_id)
    db.add(ChatMessage(complaint_id=c.id, role="user", content=req.message))

    result = run_complaint_agent(req.message, _complaint_to_dict(c))
    _apply_result(c, result)

    db.add(ChatMessage(complaint_id=c.id, role="assistant", content=result["assistant_message"]))
    db.commit()
    db.refresh(c)

    return ChatResponse(
        complaint=ComplaintOut.model_validate(c),
        assistant_message=result["assistant_message"],
        updated_fields=result["updated_fields"],
    )


@router.post("/extract-document", response_model=ChatResponse)
async def extract_document(
    complaint_id: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Document Extraction tool — PDF/DOCX/TXT/EML complaint upload -> form + risk assessment."""
    content = await file.read()
    try:
        text = extract_text(file.filename, content)
    except Exception as e:
        raise HTTPException(400, f"Could not parse document: {e}")

    if not text.strip():
        raise HTTPException(400, "No extractable text found in the uploaded document.")

    c = _get_or_create(db, complaint_id)
    db.add(ChatMessage(complaint_id=c.id, role="user", content=f"[Uploaded document: {file.filename}]"))

    result = run_complaint_agent(f"Uploaded complaint document: {file.filename}", _complaint_to_dict(c), source_text=text)
    _apply_result(c, result)

    db.add(ChatMessage(complaint_id=c.id, role="assistant", content=result["assistant_message"]))
    db.commit()
    db.refresh(c)

    return ChatResponse(
        complaint=ComplaintOut.model_validate(c),
        assistant_message=result["assistant_message"],
        updated_fields=result["updated_fields"],
    )
