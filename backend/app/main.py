from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import complaint  # noqa: F401 - register models
from app.routers import complaints, ai
from app.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pharma Customer Complaint Management API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints.router)
app.include_router(ai.router)


@app.get("/api/health")
def health():
    from app.services.groq_client import is_live
    return {"status": "ok", "groq_live": is_live()}
