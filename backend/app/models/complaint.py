import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from app.database import Base


def gen_id():
    return uuid.uuid4().hex[:12]


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(20), primary_key=True, default=gen_id)
    status = Column(String(30), default="Pending Triage")

    # 1. Origin & customer details
    complaint_source = Column(String(255))
    customer_name = Column(String(255))

    # 2. Product & batch identification
    product_name = Column(String(255))
    product_strength_grade = Column(String(120))
    batch_lot_number = Column(String(120))
    manufacturing_date = Column(String(30))
    expiry_date = Column(String(30))
    quantity_affected = Column(String(60))

    # 3. Complaint details
    complaint_type = Column(String(120))
    complaint_date = Column(String(30))
    detailed_description = Column(Text)

    # 4. Initial assessment & priority (human-editable, AI-suggested)
    initial_severity = Column(String(30))
    priority = Column(String(30))

    # AI Co-pilot risk assessment (AI-only reasoning panel)
    ai_severity_classification = Column(String(30))
    ai_recommended_action = Column(Text)
    ai_root_cause_hypothesis = Column(Text)
    ai_capa_recommendation = Column(Text)
    ai_risk_summary = Column(Text)
    ai_completeness_notes = Column(Text)
    ai_duplicate_flag = Column(Text)

    # bookkeeping
    raw_fields = Column(JSON, default=dict)  # last full AI field-extraction payload
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(20), index=True)
    role = Column(String(20))  # user | assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
