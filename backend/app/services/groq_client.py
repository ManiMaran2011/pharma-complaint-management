"""
Thin wrapper around the Groq chat-completions API.

Two models are used per the assignment spec:
  - EXTRACTION_MODEL (gemma2-9b-it)      -> fast structured field extraction
  - REASONING_MODEL  (llama-3.3-70b-versatile) -> QA risk-assessment reasoning

If no GROQ_API_KEY is configured, calls fall back to a small rule-based mock
so the app is still runnable/demoable without a live key. Replace the key in
backend/.env to use real Groq inference end-to-end.
"""
import json
import re
from typing import Any

from groq import Groq

from app.config import settings

_client: Groq | None = None
if settings.groq_api_key:
    _client = Groq(api_key=settings.groq_api_key)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def call_json(system_prompt: str, user_prompt: str, model: str) -> dict[str, Any]:
    """Call Groq and force/parse a JSON object response."""
    if _client is None:
        return {"_mock": True}

    resp = _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return json.loads(_strip_code_fence(content))
    except json.JSONDecodeError:
        return {}


def call_text(system_prompt: str, user_prompt: str, model: str) -> str:
    if _client is None:
        return ""
    resp = _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content or ""


def is_live() -> bool:
    return _client is not None
