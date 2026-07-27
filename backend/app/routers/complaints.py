from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.complaint import Complaint
from app.schemas.complaint import ComplaintOut

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintOut)
def create_complaint(db: Session = Depends(get_db)):
    c = Complaint()
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    c = db.get(Complaint, complaint_id)
    if not c:
        raise HTTPException(404, "Complaint not found")
    return c


@router.get("", response_model=list[ComplaintOut])
def list_complaints(db: Session = Depends(get_db)):
    return db.query(Complaint).order_by(Complaint.created_at.desc()).all()


@router.post("/{complaint_id}/reset", response_model=ComplaintOut)
def reset_complaint(complaint_id: str, db: Session = Depends(get_db)):
    c = db.get(Complaint, complaint_id)
    if not c:
        raise HTTPException(404, "Complaint not found")
    for col in c.__table__.columns.keys():
        if col not in ("id", "created_at"):
            setattr(c, col, None)
    c.status = "Pending Triage"
    db.commit()
    db.refresh(c)
    return c
