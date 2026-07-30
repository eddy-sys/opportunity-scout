import unittest

from opportunity_scout.dedupe import mark_seen, unseen_leads
from opportunity_scout.models import Lead


def make_lead(source_id, url):
    return Lead(
        source="test",
        source_id=source_id,
        url=url,
        title="Need UX help",
        author="alice",
        created_at=None,
        raw_text="SaaS onboarding problem",
    )


class DedupeTests(unittest.TestCase):
    def test_unseen_leads_skips_seen_id_and_url(self):
        leads = [
            make_lead("id-1", "https://example.com/1"),
            make_lead("id-2", "https://example.com/2"),
        ]

        result = unseen_leads(leads, {"id-1", "https://example.com/2"})

        self.assertEqual(result, [])

    def test_mark_seen_stores_id_and_url(self):
        seen = mark_seen(set(), [make_lead("id-1", "https://example.com/1")])

        self.assertIn("id-1", seen)
        self.assertIn("https://example.com/1", seen)


if __name__ == "__main__":
    unittest.main()
