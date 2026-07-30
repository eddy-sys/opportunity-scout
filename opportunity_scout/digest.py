from __future__ import annotations

from .models import Lead


def truncate(value: str, limit: int = 700) -> str:
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def format_lead(lead: Lead, index: int) -> str:
    parts = [
        f"{index}. [{lead.fit_score}/5] {lead.title}",
        f"Source: {lead.source}",
        f"URL: {lead.url}",
    ]
    if lead.summary:
        parts.append(f"Summary: {truncate(lead.summary, 360)}")
    if lead.signal_notes:
        parts.append(f"Signals: {truncate(lead.signal_notes, 360)}")
    if lead.draft_opener:
        parts.append(f"Opener: {truncate(lead.draft_opener, 360)}")
    return "\n".join(parts)


def format_digest(
    leads: list[Lead],
    *,
    fetched_count: int,
    filtered_count: int,
    scored_count: int,
    errors: list[str] | None = None,
) -> str:
    errors = errors or []
    header = "Opportunity Scout daily digest"
    stats = f"Fetched: {fetched_count} | Filtered: {filtered_count} | Scored: {scored_count} | Delivered: {len(leads)}"
    if not leads:
        message = f"{header}\n{stats}\n\nNo leads today. System is alive."
    else:
        body = "\n\n".join(format_lead(lead, index) for index, lead in enumerate(leads, 1))
        message = f"{header}\n{stats}\n\n{body}"
    if errors:
        short_errors = "\n".join(f"- {truncate(error, 220)}" for error in errors[:5])
        message += f"\n\nWarnings:\n{short_errors}"
    return message
