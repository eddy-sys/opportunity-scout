from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Lead


def find_keywords(text: str, keywords: list[str]) -> list[str]:
    normalized = text.casefold()
    return [keyword for keyword in keywords if keyword.casefold() in normalized]


def is_recent(lead: Lead, lookback_hours: int, now: datetime | None = None) -> bool:
    if lead.created_at is None:
        return True
    now = now or datetime.now(timezone.utc)
    created_at = lead.created_at.astimezone(timezone.utc)
    return created_at >= now - timedelta(hours=lookback_hours)


def apply_basic_filters(
    leads: list[Lead],
    *,
    include_keywords: list[str],
    exclude_keywords: list[str],
    lookback_hours: int,
    now: datetime | None = None,
) -> list[Lead]:
    filtered: list[Lead] = []
    for lead in leads:
        if not is_recent(lead, lookback_hours, now=now):
            continue
        text = lead.text_for_filtering
        if find_keywords(text, exclude_keywords):
            continue
        matches = find_keywords(text, include_keywords)
        if not matches:
            continue
        lead.matched_keywords = matches
        filtered.append(lead)
    return filtered


def select_digest_leads(
    leads: list[Lead],
    *,
    strong_threshold: int,
    limit: int,
    include_score_3_if_few_strong: bool,
) -> list[Lead]:
    scored = [lead for lead in leads if lead.fit_score is not None]
    strong = [lead for lead in scored if lead.fit_score >= strong_threshold]
    maybes = [lead for lead in scored if lead.fit_score == 3]
    selected = strong
    if include_score_3_if_few_strong and len(strong) < 3:
        selected = strong + maybes[: max(0, 3 - len(strong))]
    return sorted(selected, key=lambda lead: lead.fit_score or 0, reverse=True)[:limit]
