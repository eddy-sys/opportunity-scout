import unittest
from datetime import datetime, timedelta, timezone

from opportunity_scout.filtering import apply_basic_filters, select_digest_leads
from opportunity_scout.models import Lead


def make_lead(title, raw_text="", hours_old=1, score=None):
    return Lead(
        source="test",
        source_id=title,
        url=f"https://example.com/{title}",
        title=title,
        author="alice",
        created_at=datetime.now(timezone.utc) - timedelta(hours=hours_old),
        raw_text=raw_text,
        fit_score=score,
    )


class FilteringTests(unittest.TestCase):
    def test_keyword_include_and_exclude_matching(self):
        leads = [
            make_lead("Need UX help for SaaS onboarding"),
            make_lead("Hiring full-time product designer for SaaS"),
            make_lead("Need a backend engineer"),
        ]

        filtered = apply_basic_filters(
            leads,
            include_keywords=["ux help", "saas", "product designer"],
            exclude_keywords=["hiring full-time"],
            lookback_hours=48,
        )

        self.assertEqual([lead.title for lead in filtered], ["Need UX help for SaaS onboarding"])
        self.assertEqual(filtered[0].matched_keywords, ["ux help", "saas"])

    def test_old_posts_are_rejected_when_timestamp_exists(self):
        leads = [make_lead("Need UX help", hours_old=72)]

        filtered = apply_basic_filters(
            leads,
            include_keywords=["ux help"],
            exclude_keywords=[],
            lookback_hours=48,
        )

        self.assertEqual(filtered, [])

    def test_score_thresholding_and_digest_limit(self):
        leads = [
            make_lead("a", score=5),
            make_lead("b", score=4),
            make_lead("c", score=3),
            make_lead("d", score=2),
        ]

        selected = select_digest_leads(
            leads,
            strong_threshold=4,
            limit=10,
            include_score_3_if_few_strong=True,
        )

        self.assertEqual([lead.title for lead in selected], ["a", "b", "c"])

    def test_digest_limit_is_enforced(self):
        leads = [make_lead(str(index), score=5) for index in range(11)]

        selected = select_digest_leads(
            leads,
            strong_threshold=4,
            limit=10,
            include_score_3_if_few_strong=True,
        )

        self.assertEqual(len(selected), 10)


if __name__ == "__main__":
    unittest.main()
