from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from .config import load_settings
from .dedupe import load_seen, mark_seen, save_seen, unseen_leads
from .digest import format_digest
from .fetchers import fetch_reddit, fetch_rss
from .filtering import apply_basic_filters, select_digest_leads
from .samples import sample_leads
from .scoring import mock_score_leads, score_leads
from .telegram import send_telegram_message


def log_run(path, summary: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary, default=str) + "\n")


def run(*, dry_run: bool = False, sample: bool = False, mock_scoring: bool = False) -> int:
    settings = load_settings()
    errors: list[str] = []

    if sample:
        fetched = sample_leads()
    else:
        reddit_leads, reddit_errors = fetch_reddit(settings.reddit_subreddits)
        rss_leads, rss_errors = fetch_rss(settings.rss_feeds)
        errors.extend(reddit_errors)
        errors.extend(rss_errors)
        fetched = reddit_leads + rss_leads
    seen = load_seen(settings.seen_path)
    new_leads = unseen_leads(fetched, seen)
    filtered = apply_basic_filters(
        new_leads,
        include_keywords=settings.include_keywords,
        exclude_keywords=settings.exclude_keywords,
        lookback_hours=settings.lookback_hours,
    )
    candidates = filtered[: settings.max_llm_candidates]

    if mock_scoring:
        scored, scoring_errors = mock_score_leads(candidates)
    else:
        scored, scoring_errors = score_leads(
            candidates,
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        )
    errors.extend(scoring_errors)

    digest_leads = select_digest_leads(
        scored,
        strong_threshold=settings.strong_score_threshold,
        limit=settings.digest_limit,
        include_score_3_if_few_strong=settings.include_score_3_if_few_strong,
    )

    if not fetched:
        errors.append("All configured sources returned zero leads or failed")

    message = format_digest(
        digest_leads,
        fetched_count=len(fetched),
        filtered_count=len(filtered),
        scored_count=len(scored),
        errors=errors,
    )

    if dry_run:
        print(message)
    else:
        try:
            send_telegram_message(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
                message=message,
            )
        except Exception as exc:
            errors.append(f"telegram: {exc}")
            print(message)
            print(f"\nTelegram delivery failed: {exc}")
            return_code = 1
        else:
            return_code = 0

    if not dry_run:
        updated_seen = mark_seen(seen, scored)
        save_seen(settings.seen_path, updated_seen)

    summary = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "sample": sample,
        "mock_scoring": mock_scoring,
        "fetched": len(fetched),
        "new": len(new_leads),
        "filtered": len(filtered),
        "scored": len(scored),
        "delivered": len(digest_leads),
        "errors": errors,
    }
    log_run(settings.run_log_path, summary)
    return locals().get("return_code", 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Opportunity Scout")
    parser.add_argument("--dry-run", action="store_true", help="Print digest instead of sending Telegram and do not update seen.json")
    parser.add_argument("--sample", action="store_true", help="Use built-in sample leads instead of live network sources")
    parser.add_argument("--mock-scoring", action="store_true", help="Use offline heuristic scoring instead of OpenAI")
    args = parser.parse_args()
    return run(dry_run=args.dry_run, sample=args.sample, mock_scoring=args.mock_scoring)


if __name__ == "__main__":
    raise SystemExit(main())
