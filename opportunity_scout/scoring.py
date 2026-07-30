from __future__ import annotations

import json
import time
from typing import Any

from .http import fetch_json, post_json
from .models import Lead

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


SYSTEM_PROMPT = """You score public posts for a cash-strapped product designer seeking paid SaaS/product design work.

Return only valid JSON with this shape:
{"fit_score": 1, "summary": "", "signal_notes": "", "draft_opener": ""}

Fit score rubric:
5 = clear paid or high-intent SaaS/product design need, recent, strong founder/client signal, obvious reply angle.
4 = strong product/design need relevant to the designer, but budget or urgency is unclear.
3 = possibly relevant, but vague, weak buying signal, or lower-value scope.
2 = mostly irrelevant, weak fit, too broad, or unlikely to become paid work.
1 = not a lead, spam, stale, unpaid, full-time-only, or outside product design/SaaS skills.

The draft_opener must be one short, specific first line that references the post. It must not sound generic or salesy.
"""


def lead_prompt(lead: Lead) -> str:
    return f"""Source: {lead.source}
Title: {lead.title}
Author: {lead.author}
URL: {lead.url}
Matched keywords: {', '.join(lead.matched_keywords)}
Post text:
{lead.raw_text[:4000]}
"""


def parse_scoring_response(data: dict[str, Any]) -> dict[str, Any]:
    # Gemini response shape: {candidates: [{content: {parts: [{text: "..."}]}}]}
    candidates = data.get("candidates", [{}])
    parts = candidates[0].get("content", {}).get("parts", [{}])
    raw_text = parts[0].get("text", "")
    # Strip markdown code fences if Gemini wraps the JSON
    stripped = raw_text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    parsed = json.loads(stripped)
    fit_score = int(parsed.get("fit_score", 1))
    return {
        "fit_score": max(1, min(5, fit_score)),
        "summary": str(parsed.get("summary", "")).strip(),
        "signal_notes": str(parsed.get("signal_notes", "")).strip(),
        "draft_opener": str(parsed.get("draft_opener", "")).strip(),
    }


def score_lead(lead: Lead, *, api_key: str, model: str) -> Lead:
    # Gemini generateContent REST endpoint (no SDK required)
    url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": SYSTEM_PROMPT + "\n\n" + lead_prompt(lead)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    data = post_json(
        url,
        payload,
        headers={"Content-Type": "application/json"},
        timeout=45,
    )
    parsed = parse_scoring_response(data)
    lead.fit_score = parsed["fit_score"]
    lead.summary = parsed["summary"]
    lead.signal_notes = parsed["signal_notes"]
    lead.draft_opener = parsed["draft_opener"]
    return lead


def score_leads(leads: list[Lead], *, api_key: str, model: str) -> tuple[list[Lead], list[str]]:
    scored: list[Lead] = []
    errors: list[str] = []
    if not api_key:
        return scored, ["GEMINI_API_KEY is missing"]
    for index, lead in enumerate(leads):
        if index > 0:
            time.sleep(4)  # free-tier rate limit: ~15 RPM
        try:
            scored.append(score_lead(lead, api_key=api_key, model=model))
        except Exception as exc:
            errors.append(f"{lead.url or lead.title}: {exc}")
    return scored, errors


GOOD_SIGNAL_TERMS = [
    "budget",
    "paid",
    "contract",
    "funded",
    "mvp",
    "saas",
    "onboarding",
    "dashboard",
    "landing page",
    "conversion",
    "ux",
    "designer",
]


def mock_score_lead(lead: Lead) -> Lead:
    text = lead.text_for_filtering.casefold()
    hits = [term for term in GOOD_SIGNAL_TERMS if term in text]
    if any(term in text for term in ["unpaid", "equity only", "full-time only", "logo only"]):
        score = 1
    elif len(hits) >= 5:
        score = 5
    elif len(hits) >= 3:
        score = 4
    elif len(hits) >= 1:
        score = 3
    else:
        score = 2
    lead.fit_score = score
    lead.summary = f"Mock-scored lead with {len(hits)} relevant signal(s): {', '.join(hits[:5]) or 'none'}."
    lead.signal_notes = "Offline mock scoring; use real OpenAI scoring before replying."
    lead.draft_opener = f"Saw your post about {lead.title[:80].rstrip()} - I may be able to help with the product/UX side."
    return lead


def mock_score_leads(leads: list[Lead]) -> tuple[list[Lead], list[str]]:
    return [mock_score_lead(lead) for lead in leads], []
