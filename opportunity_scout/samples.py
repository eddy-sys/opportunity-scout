from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Lead


def sample_leads() -> list[Lead]:
    now = datetime.now(timezone.utc)
    return [
        Lead(
            source="sample/reddit/r/SaaS",
            source_id="sample-1",
            url="https://example.com/sample-1",
            title="Need UX help improving SaaS onboarding drop-off",
            author="founder_a",
            created_at=now - timedelta(hours=3),
            raw_text="We launched our MVP and users keep dropping off during onboarding. We have a small paid contract budget for a designer who understands SaaS dashboards and activation flows.",
        ),
        Lead(
            source="sample/reddit/r/startups",
            source_id="sample-2",
            url="https://example.com/sample-2",
            title="Looking for a logo only for my student project",
            author="student_b",
            created_at=now - timedelta(hours=5),
            raw_text="This is unpaid and only for a simple logo. Students only please.",
        ),
        Lead(
            source="sample/rss/producthunt",
            source_id="sample-3",
            url="https://example.com/sample-3",
            title="Bootstrapped founder needs landing page conversion advice",
            author="founder_c",
            created_at=now - timedelta(hours=8),
            raw_text="I am building a bootstrapped SaaS MVP. The landing page is getting traffic but conversion is weak, and I need a design partner or paid help to improve the flow.",
        ),
    ]
