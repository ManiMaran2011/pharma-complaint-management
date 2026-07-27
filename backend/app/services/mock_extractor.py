"""
Lightweight regex/keyword fallback so the app is runnable end-to-end without
a live Groq key (e.g. for quick local demo/testing). The real path is the
Groq gemma2-9b-it / llama-3.3-70b-versatile calls in agents/graph.py — this
module is only used when groq_client.is_live() is False.
"""
import re


def mock_extract(text: str) -> dict:
    t = text
    out = {}

    m = re.search(r"([A-Z][\w&.\- ]{2,40}?)\s+reported", t)
    if m:
        out["complaint_source"] = m.group(1).strip()

    m = re.search(r"batch(?:\s*/?\s*lot)?\s*(?:number|no\.?)?\s*(?:is|was|:)?\s*([A-Z0-9\-]{5,20})", t, re.I)
    if m:
        out["batch_lot_number"] = m.group(1).upper()

    m = re.search(r"(\d+(?:\.\d+)?)\s*(kg|capsules|tablets|units|vials|bottles|drums?)\b", t, re.I)
    if m:
        out["quantity_affected"] = f"{m.group(1)} {m.group(2).lower()}"

    m = re.search(r"\b(\w+)\s+capsules?\s*(\d+\s*mg)?", t, re.I)
    if m:
        out["product_name"] = f"{m.group(1).title()} Capsules".strip()
        if m.group(2):
            out["product_strength_grade"] = m.group(2)

    m = re.search(r"(discolo(?:u)?red|contaminat\w+|damaged|leak\w*|broken|cracked|moldy|foreign particles?)", t, re.I)
    if m:
        out["complaint_type"] = m.group(1).title()
        out["detailed_description"] = t.strip()[:400]

    m = re.search(r"manufactur\w*\s*(?:date)?\s*(?:is|was|:)?\s*(\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4})", t, re.I)
    if m:
        out["manufacturing_date"] = m.group(1)

    m = re.search(r"expir\w*\s*(?:date)?\s*(?:is|was|:)?\s*(\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4})", t, re.I)
    if m:
        out["expiry_date"] = m.group(1)

    return out


def mock_risk(merged: dict) -> dict:
    desc = (merged.get("detailed_description") or "") + " " + (merged.get("complaint_type") or "")
    desc = desc.lower()
    critical_terms = ["contaminat", "wrong label", "potency", "efficacy", "sterility", "mislabel"]
    major_terms = ["discolo", "damage", "seal", "leak", "broken", "crack"]

    if any(term in desc for term in critical_terms):
        severity, priority = "Critical", "Urgent"
    elif any(term in desc for term in major_terms):
        severity, priority = "Major", "High"
    else:
        severity, priority = "Minor", "Medium"

    return {
        "ai_severity_classification": severity,
        "priority": priority,
        "ai_recommended_action": "Route to QA investigation and issue replacement" if severity != "Minor"
            else "Log for trend monitoring; notify batch owner",
        "ai_root_cause_hypothesis": "Potential deviation during manufacturing, packaging, or storage/transit "
            "affecting the reported batch — pending QA investigation for confirmation.",
        "ai_capa_recommendation": "Initiate batch quarantine and review, verify against retained samples, "
            "and assess CAPA on the relevant manufacturing/packaging line if root cause is confirmed.",
        "ai_risk_summary": f"Complaint concerns {merged.get('product_name', 'the product')} "
            f"(batch {merged.get('batch_lot_number', 'unspecified')}) — classified {severity} based on "
            f"the nature of the reported defect and potential patient impact.",
        "ai_completeness_notes": "Complaint record is complete." if merged.get("batch_lot_number")
            and merged.get("quantity_affected") else "Batch/lot number and affected quantity are still needed for full triage.",
        "ai_duplicate_flag": "No similar complaints detected in this session.",
    }
