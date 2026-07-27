from typing import Optional
from pydantic import BaseModel


class ComplaintFields(BaseModel):
    """All fields the AI is allowed to read/write on the Log Customer Complaint form."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength_grade: Optional[str] = None
    batch_lot_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    detailed_description: Optional[str] = None
    initial_severity: Optional[str] = None
    priority: Optional[str] = None


class RiskAssessment(BaseModel):
    ai_severity_classification: Optional[str] = None
    ai_recommended_action: Optional[str] = None
    ai_root_cause_hypothesis: Optional[str] = None
    ai_capa_recommendation: Optional[str] = None
    ai_risk_summary: Optional[str] = None
    ai_completeness_notes: Optional[str] = None
    ai_duplicate_flag: Optional[str] = None


class ComplaintOut(ComplaintFields, RiskAssessment):
    id: str
    status: str

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    complaint_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    complaint: ComplaintOut
    assistant_message: str
    updated_fields: list[str] = []
