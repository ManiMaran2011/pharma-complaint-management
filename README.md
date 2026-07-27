# AI-Powered Customer Complaint Management System

A pharmaceutical (API & FDF) Quality Assurance complaint intake system. The left panel is a
**Log Customer Complaint** form; the right panel is an **AI Complaint Intake Assistant**. The form is
never filled manually — every field is populated by the AI agent from a chat prompt, a pasted
email/letter, or an uploaded complaint document.

## Stack

| Layer            | Technology |
|-------------------|------------|
| Frontend          | React + Redux Toolkit (Vite) |
| Backend           | Python, FastAPI |
| AI agent workflow | LangGraph |
| LLMs              | Groq — `gemma2-9b-it` (extraction), `llama-3.3-70b-versatile` (risk reasoning) |
| Database          | SQLAlchemy — SQLite by default, drop-in Postgres/MySQL via `DATABASE_URL` |
| Font              | Google Inter (+ JetBrains Mono for batch/lot/quantity fields) |

## Why a LangGraph agent (not one prompt)

The assistant runs as a 5-node graph (`backend/app/agents/graph.py`):

```
classify_intent → extract_fields → merge_fields → risk_assessment → compose_response
```

- **classify_intent** — decides log vs. edit vs. document-extraction vs. general question.
- **extract_fields** — Groq `gemma2-9b-it` structured JSON extraction. Only fields present in
  the input are returned (nulls elsewhere), so a short correction like *"the batch number is
  X"* doesn't overwrite unrelated fields.
- **merge_fields** — non-null extracted fields overwrite the existing complaint; everything else
  is preserved. This is what makes the **edit complaint** tool safe to call repeatedly.
- **risk_assessment** — Groq `llama-3.3-70b-versatile` reasons over the *merged* record (as a QA
  officer would) to produce severity, priority, recommended action, root cause hypothesis, CAPA
  recommendation, a summary, a completeness check, and a duplicate-complaint flag.
- **compose_response** — turns the diff into the short natural-language message shown in chat.

Splitting extraction (fast, cheap, structured) from risk reasoning (slower, more deliberate) onto
two different Groq models is deliberate — it mirrors how a real QA intake process separates data
capture from clinical/quality judgment.

## Implemented AI tools (per assignment spec)

1. **Log Complaint tool** — free-text prompt → populates the whole form + risk assessment.
2. **Edit Complaint tool** — a correction/follow-up prompt → updates only the mentioned fields,
   preserves the rest, and re-runs risk assessment on the updated record.
3. **Document Extraction tool** — upload a PDF / DOCX / TXT / EML complaint letter or email →
   same extraction + risk-assessment pipeline, further editable by chat afterwards.

### Bonus features implemented

- **AI Risk Classification** — severity (Critical/Major/Minor) + priority, shown as a dedicated
  AI Co-pilot Risk Assessment card.
- **Root Cause Recommendation** — plausible root-cause hypothesis per complaint.
- **CAPA Recommendation** — suggested corrective/preventive action.
- **Complaint Completeness Checker** — flags missing fields still needed for full triage.
- **Complaint Summary** — 2–3 sentence AI-written summary of the record.
- **Duplicate Complaint Detection** — placeholder flag in the risk card (no historical-complaint
  index is wired up yet; the extension point is `node_risk_assessment` in `graph.py`, querying
  past `Complaint` rows before the LLM call).

## Project layout

```
backend/
  app/
    agents/graph.py          # LangGraph workflow (see above)
    services/groq_client.py  # Groq API wrapper (JSON-mode + text) with offline mock fallback
    services/document_parser.py  # PDF/DOCX/EML/TXT text extraction
    services/mock_extractor.py   # regex fallback used only when GROQ_API_KEY is unset
    models/complaint.py       # SQLAlchemy models (Complaint, ChatMessage)
    schemas/complaint.py      # Pydantic request/response schemas
    routers/complaints.py     # CRUD
    routers/ai.py             # /api/ai/chat, /api/ai/extract-document
    main.py
frontend/
  src/
    store/complaintSlice.js   # Redux Toolkit slice + async thunks
    api/client.js             # axios client
    components/ComplaintForm.jsx  # left panel (AI-populated, read-only)
    components/AiCopilot.jsx      # right panel (upload/paste/chat/risk card)
    App.jsx, app.css, index.css
sample-documents/
  generate_sample_pdf.py      # regenerates the demo complaint PDF
  sample_complaint_metformin_api.pdf   # sample Metformin HCl API complaint for the extraction demo
```

## Running it locally

### 1. Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then paste your Groq API key into .env
uvicorn app.main:app --reload --port 8000
```

Without a `GROQ_API_KEY`, the backend still runs end-to-end using a small regex-based fallback
extractor (`app/services/mock_extractor.py`) so the app is demoable offline — but the real
Groq calls are what the assignment is graded on, so set the key for the actual demo/video.

`GET /api/health` returns `{"groq_live": true}` once the key is picked up.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env        # points at the backend, default http://localhost:8000
npm run dev
```

Open the printed local URL. A new complaint record is created automatically on load.

### 3. Try the three tools

- **Log**: type `Apollo Pharmacy reported discolored capsules in amoxicillin capsules 500 mg.`
- **Edit**: follow up with `Sorry, the batch number is BMX24602 and the affected quantity is 48 capsules.`
- **Extract**: drag `sample-documents/sample_complaint_metformin_api.pdf` onto the upload zone.

## Database

Defaults to local SQLite (zero setup, `backend/complaints.db`). To use Postgres or MySQL instead,
set `DATABASE_URL` in `backend/.env`, e.g.:

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/complaints
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/complaints
```

The SQLAlchemy models are DB-agnostic; no code changes are needed beyond the connection string
(and installing the matching driver — `psycopg2-binary` is already in `requirements.txt`, add
`pymysql` for MySQL).

## Notes on the QMS context

This models the **Customer Complaint** sub-process of a pharmaceutical Quality Management System:
a customer/distributor-reported product issue is logged, triaged for severity/priority, routed for
QA investigation, and tracked toward CAPA — the same lifecycle a complaint record follows in
systems like TrackWise or MasterControl, simplified here to the intake + AI-assisted triage step.
