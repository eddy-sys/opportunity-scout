from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Lead:
    source: str
    source_id: str
    url: str
    title: str
    author: str
    created_at: datetime | None
    raw_text: str
    matched_keywords: list[str] = field(default_factory=list)
    fit_score: int | None = None
    summary: str = ""
    signal_notes: str = ""
    draft_opener: str = ""

    @property
    def dedupe_key(self) -> str:
        return self.source_id or self.url

    @property
    def text_for_filtering(self) -> str:
        return f"{self.title}\n{self.raw_text}".strip()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = (
            self.created_at.astimezone(timezone.utc).isoformat()
            if self.created_at
            else None
        )
        return data
