from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


DEFAULT_INCLUDE_KEYWORDS = [
    "designer",
    "ux help",
    "product designer",
    "design partner",
    "mvp",
    "saas",
    "landing page",
    "dashboard",
    "onboarding",
    "product ui",
    "redesign",
    "conversion",
    "user flow",
    "founder",
    "bootstrapped",
    "contract",
    "paid help",
]

DEFAULT_EXCLUDE_KEYWORDS = [
    "hiring full-time",
    "full-time only",
    "unpaid",
    "equity only",
    "students only",
    "logo only",
    "free work",
    "internship",
    "volunteer",
]


def load_dotenv(path: Path = ROOT_DIR / ".env") -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True, slots=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    telegram_bot_token: str
    telegram_chat_id: str
    reddit_subreddits: list[str]
    rss_feeds: list[str]
    include_keywords: list[str]
    exclude_keywords: list[str]
    max_llm_candidates: int
    digest_limit: int
    strong_score_threshold: int
    include_score_3_if_few_strong: bool
    lookback_hours: int
    seen_path: Path
    run_log_path: Path


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        reddit_subreddits=env_list(
            "REDDIT_SUBREDDITS",
            ["SaaS", "startups", "Entrepreneur", "forhire", "designjobs"],
        ),
        rss_feeds=env_list("RSS_FEEDS", ["https://www.producthunt.com/feed"]),
        include_keywords=env_list("INCLUDE_KEYWORDS", DEFAULT_INCLUDE_KEYWORDS),
        exclude_keywords=env_list("EXCLUDE_KEYWORDS", DEFAULT_EXCLUDE_KEYWORDS),
        max_llm_candidates=env_int("MAX_LLM_CANDIDATES", 25),
        digest_limit=env_int("DIGEST_LIMIT", 10),
        strong_score_threshold=env_int("STRONG_SCORE_THRESHOLD", 4),
        include_score_3_if_few_strong=env_bool("INCLUDE_SCORE_3_IF_FEW_STRONG", True),
        lookback_hours=env_int("LOOKBACK_HOURS", 48),
        seen_path=DATA_DIR / "seen.json",
        run_log_path=DATA_DIR / "run-log.jsonl",
    )
