import unittest

from opportunity_scout.digest import format_digest
from opportunity_scout.models import Lead


def make_lead(index, score=5):
    return Lead(
        source="reddit/r/SaaS",
        source_id=str(index),
        url=f"https://example.com/{index}",
        title=f"Need UX help {index}",
        author="alice",
        created_at=None,
        raw_text="SaaS onboarding problem",
        fit_score=score,
        summary="Founder needs onboarding UX help.",
        signal_notes="SaaS, urgent product pain, budget unclear.",
        draft_opener="Saw your note about onboarding drop-off.",
    )


class DigestTests(unittest.TestCase):
    def test_format_digest_handles_no_leads(self):
        message = format_digest([], fetched_count=3, filtered_count=0, scored_count=0)

        self.assertIn("No leads today", message)
        self.assertIn("System is alive", message)

    def test_format_digest_handles_one_lead(self):
        message = format_digest([make_lead(1)], fetched_count=3, filtered_count=1, scored_count=1)

        self.assertIn("[5/5] Need UX help 1", message)
        self.assertIn("Opener:", message)

    def test_format_digest_handles_ten_leads(self):
        leads = [make_lead(index) for index in range(10)]
        message = format_digest(leads, fetched_count=20, filtered_count=10, scored_count=10)

        self.assertIn("10. [5/5] Need UX help 9", message)


if __name__ == "__main__":
    unittest.main()
