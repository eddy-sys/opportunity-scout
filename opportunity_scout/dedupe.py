from __future__ import annotations

import json
from pathlib import Path

from .models import Lead


def load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    if isinstance(data, list):
        return {str(item) for item in data}
    if isinstance(data, dict):
        return {str(item) for item in data.get("seen", [])}
    return set()


def save_seen(path: Path, seen: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"seen": sorted(seen)}, indent=2),
        encoding="utf-8",
    )


def unseen_leads(leads: list[Lead], seen: set[str]) -> list[Lead]:
    return [lead for lead in leads if lead.dedupe_key not in seen and lead.url not in seen]


def mark_seen(seen: set[str], leads: list[Lead]) -> set[str]:
    updated = set(seen)
    for lead in leads:
        if lead.dedupe_key:
            updated.add(lead.dedupe_key)
        if lead.url:
            updated.add(lead.url)
    return updated
