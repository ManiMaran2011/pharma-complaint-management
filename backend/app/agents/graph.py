"""
LangGraph workflow powering the AI Complaint Intake Assistant.

Graph:
    classify_intent -> extract_fields -> merge_fields -> risk_assessment -> compose_response

- classify_intent: decides whether the user is logging a new complaint,
  editing an existing one, extracting from an uploaded document, or asking
  a general question (bonus "ask about this complaint" tool).
- extract_fields: Groq gemma2-9b-it structured JSON extraction of only the
  Log Customer Complaint fields present in the input (chat text and/or a
  parsed document). Existing form state is passed in as context so partial
  follow-ups ("batch number is X, qty is 40") only return the changed keys.
- merge_fields: non-null extracted fields overwrite the existing complaint,
  everything else is preserved (required by the edit-complaint tool spec).
- risk_assessment: Groq llama-3.3-70b-versatile reasons over the *merged*
  complaint to populate the AI Co-pilot Risk Assessment panel (severity,
  next action, root cause hypothesis, CAPA suggestion, completeness check,
  duplicate-complaint flag).
- compose_response: short natural-language summary of what changed, shown
  in the assistant chat panel.
"""
from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END

from app.services import groq_client
from app.services.mock_extractor import mock_extract, mock_risk

EXTRACTION_SYSTEM_PROMPT = """You are a data-extraction engine for a pharmaceutical Quality Management \
System's Customer Complaint intake form. Given a user's chat message and/or the text of an uploaded \
complaint document (email/PDF/letter), extract ONLY the fields that are explicitly stated or can be \
directly, unambiguously inferred from the text.

Return a single flat JSON object with exactly these keys (use null for any field not present in the input, \
never invent values):
{
  "complaint_source": string|null,        // who/where the complaint came from, e.g. "Apollo Pharmacy" or "Customer Email"
  "customer_name": string|null,
  "product_name": string|null,             // e.g. "Amoxicillin Capsules"
  "product_strength_grade": string|null,   // e.g. "500mg" or "IP/BP" for API grade
  "batch_lot_number": string|null,
  "manufacturing_date": string|null,       // YYYY-MM-DD if determinable
  "expiry_date": string|null,              // YYYY-MM-DD if determinable
  "quantity_affected": string|null,        // include units, e.g. "48 capsules" or "50 kg (2 HDPE drums)"
  "complaint_type": string|null,           // e.g. "Physical Defect", "Discoloration", "Packaging Damage", "Efficacy Issue"
  "complaint_date": string|null,
  "detailed_description": string|null      // 1-2 sentence factual description of the defect/issue
}

Rules:
- If the message is only a small correction (e.g. "the batch number is X and quantity is Y"), return ONLY those keys as non-null, all others null.
- Never overwrite information with a guess. If unsure, use null.
- Output raw JSON only, no markdown, no commentary."""

RISK_SYSTEM_PROMPT = """You are the AI reasoning engine of a pharmaceutical QA Customer Complaint Co-pilot. \
Given the current state of a logged complaint (product, batch, defect description, quantity affected, \
complaint type), perform a risk assessment as an experienced Quality Assurance officer would.

Return a single flat JSON object with exactly these keys:
{
  "ai_severity_classification": string,   // one of "Critical", "Major", "Minor"
  "priority": string,                     // one of "Urgent", "High", "Medium", "Low"
  "ai_recommended_action": string,        // short next-step, e.g. "Route to QA investigation and issue replacement"
  "ai_root_cause_hypothesis": string,     // 1-2 sentence plausible root cause given the defect described
  "ai_capa_recommendation": string,       // 1-2 sentence corrective/preventive action suggestion
  "ai_risk_summary": string,              // 2-3 sentence summary of the complaint and why it was classified this way
  "ai_completeness_notes": string,        // note any fields still missing/needed for full triage, or "Complaint record is complete." if none
  "ai_duplicate_flag": string             // "No similar complaints detected in this session." (placeholder — no historical DB search wired up yet)
}

Base the classification on pharma QA norms: patient-safety-impacting defects (contamination, wrong labeling, \
efficacy/potency failure) are Critical; visible physical defects (discoloration, damage, seal issues) affecting \
a batch are typically Major; minor packaging/cosmetic issues with no safety impact are Minor.
Output raw JSON only, no markdown, no commentary."""


class GraphState(TypedDict, total=False):
    user_input: str
    source_text: str
    existing: dict[str, Any]
    intent: str
    extracted: dict[str, Any]
    merged: dict[str, Any]
    risk: dict[str, Any]
    assistant_message: str
    updated_fields: list[str]


FORM_KEYS = [
    "complaint_source", "customer_name", "product_name", "product_strength_grade",
    "batch_lot_number", "manufacturing_date", "expiry_date", "quantity_affected",
    "complaint_type", "complaint_date", "detailed_description",
]
RISK_KEYS = [
    "ai_severity_classification", "priority", "ai_recommended_action",
    "ai_root_cause_hypothesis", "ai_capa_recommendation", "ai_risk_summary",
    "ai_completeness_notes", "ai_duplicate_flag",
]


def node_classify_intent(state: GraphState) -> GraphState:
    if state.get("source_text"):
        state["intent"] = "document_extraction"
    else:
        text = state["user_input"].lower()
        has_existing = any(state.get("existing", {}).values())
        if has_existing and any(k in text for k in ["update", "correct", "actually", "change", "sorry"]):
            state["intent"] = "edit_complaint"
        elif has_existing:
            state["intent"] = "edit_complaint"
        else:
            state["intent"] = "log_complaint"
    return state


def node_extract_fields(state: GraphState) -> GraphState:
    combined_input = state["user_input"]
    if state.get("source_text"):
        combined_input += f"\n\n--- Uploaded document text ---\n{state['source_text']}"

    user_prompt = (
        f"Existing complaint state (for context only, do not repeat unchanged values): "
        f"{ {k: v for k, v in state.get('existing', {}).items() if v} }\n\n"
        f"New input to extract from:\n{combined_input}"
    )

    if groq_client.is_live():
        result = groq_client.call_json(
            EXTRACTION_SYSTEM_PROMPT, user_prompt, model=__import__("app.config", fromlist=["settings"]).settings.groq_extraction_model
        )
    else:
        result = {}

    if not result or result.get("_mock"):
        result = mock_extract(combined_input)

    state["extracted"] = {k: v for k, v in result.items() if k in FORM_KEYS and v not in (None, "", "null")}
    return state


def node_merge_fields(state: GraphState) -> GraphState:
    merged = dict(state.get("existing", {}))
    updated_fields = []
    for k, v in state["extracted"].items():
        if v and v != merged.get(k):
            merged[k] = v
            updated_fields.append(k)
    state["merged"] = merged
    state["updated_fields"] = updated_fields
    return state


def node_risk_assessment(state: GraphState) -> GraphState:
    merged = state["merged"]
    if not any(merged.get(k) for k in ["product_name", "detailed_description", "complaint_type"]):
        state["risk"] = {}
        return state

    user_prompt = f"Current complaint record:\n{merged}"

    from app.config import settings
    if groq_client.is_live():
        result = groq_client.call_json(RISK_SYSTEM_PROMPT, user_prompt, model=settings.groq_reasoning_model)
    else:
        result = {}

    if not result or result.get("_mock"):
        result = mock_risk(merged)

    state["risk"] = {k: v for k, v in result.items() if v}
    if "priority" in state["risk"]:
        state["updated_fields"].append("priority")
    return state


def node_compose_response(state: GraphState) -> GraphState:
    fields = state["updated_fields"]
    risk = state.get("risk", {})
    intent = state["intent"]

    if not fields:
        state["assistant_message"] = (
            "I couldn't find any new complaint details in that message. Try describing the product, "
            "batch, or issue, or upload a complaint document/email."
        )
        return state

    pretty = {
        "complaint_source": "complaint source", "customer_name": "customer name",
        "product_name": "product name", "product_strength_grade": "strength/grade",
        "batch_lot_number": "batch/lot number", "manufacturing_date": "manufacturing date",
        "expiry_date": "expiry date", "quantity_affected": "quantity affected",
        "complaint_type": "complaint type", "complaint_date": "complaint date",
        "detailed_description": "complaint description", "priority": "priority",
    }
    field_list = ", ".join(pretty.get(f, f) for f in fields if f in pretty)

    if intent == "document_extraction":
        prefix = "Extracted the complaint from the uploaded document and populated"
    elif intent == "edit_complaint":
        prefix = "Updated"
    else:
        prefix = "Logged the complaint and populated"

    msg = f"{prefix} {field_list}."
    if risk.get("ai_severity_classification"):
        msg += (
            f" Based on the details, I classified this as **{risk['ai_severity_classification']}** severity "
            f"with **{risk.get('priority', 'Medium')}** priority — recommended action: {risk.get('ai_recommended_action', '')}"
        )
    state["assistant_message"] = msg
    return state


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("classify_intent", node_classify_intent)
    graph.add_node("extract_fields", node_extract_fields)
    graph.add_node("merge_fields", node_merge_fields)
    graph.add_node("risk_assessment", node_risk_assessment)
    graph.add_node("compose_response", node_compose_response)

    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent", "extract_fields")
    graph.add_edge("extract_fields", "merge_fields")
    graph.add_edge("merge_fields", "risk_assessment")
    graph.add_edge("risk_assessment", "compose_response")
    graph.add_edge("compose_response", END)
    return graph.compile()


complaint_graph = build_graph()


def run_complaint_agent(user_input: str, existing: dict[str, Any], source_text: str = "") -> GraphState:
    initial: GraphState = {
        "user_input": user_input,
        "source_text": source_text,
        "existing": existing,
    }
    return complaint_graph.invoke(initial)
