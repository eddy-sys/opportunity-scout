from __future__ import annotations

import getpass
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import ROOT_DIR, load_dotenv
from .http import fetch_json, post_form, post_json


ENV_PATH = ROOT_DIR / ".env"


def prompt_secret(label: str, current: str = "") -> str:
    if current:
        print(f"{label}: already saved")
        return current
    return getpass.getpass(f"{label}: ").strip()


def prompt_text(label: str, current: str = "") -> str:
    if current:
        print(f"{label}: {current}")
        return current
    return input(f"{label}: ").strip()


def write_env(values: dict[str, str]) -> None:
    lines = [
        "# Opportunity Scout local secrets/config",
        f"GEMINI_API_KEY={values['GEMINI_API_KEY']}",
        f"GEMINI_MODEL={values.get('GEMINI_MODEL') or 'gemini-2.0-flash'}",
        "",
        f"TELEGRAM_BOT_TOKEN={values['TELEGRAM_BOT_TOKEN']}",
        f"TELEGRAM_CHAT_ID={values['TELEGRAM_CHAT_ID']}",
        "",
        "MAX_LLM_CANDIDATES=25",
        "DIGEST_LIMIT=10",
        "STRONG_SCORE_THRESHOLD=4",
        "INCLUDE_SCORE_3_IF_FEW_STRONG=true",
        "LOOKBACK_HOURS=48",
        "",
        "REDDIT_SUBREDDITS=SaaS,startups,Entrepreneur,forhire,designjobs",
        "RSS_FEEDS=https://www.producthunt.com/feed",
        "",
    ]
    ENV_PATH.write_text("\n".join(lines), encoding="utf-8")


def discover_chat_id(bot_token: str) -> str:
    while True:
        print("\nLooking for Telegram chats...")
        data = fetch_json(f"https://api.telegram.org/bot{bot_token}/getUpdates")
        chats: list[tuple[str, str]] = []
        for update in data.get("result", []):
            message = update.get("message") or update.get("edited_message") or update.get("channel_post") or {}
            chat = message.get("chat") or {}
            chat_id = chat.get("id")
            if chat_id is None:
                continue
            title = chat.get("title") or chat.get("username") or chat.get("first_name") or "private chat"
            item = (str(chat_id), str(title))
            if item not in chats:
                chats.append(item)
        if len(chats) == 1:
            print(f"Found Telegram chat: {chats[0][1]} ({chats[0][0]})")
            return chats[0][0]
        if len(chats) > 1:
            for index, (chat_id, title) in enumerate(chats, 1):
                print(f"{index}. {title} ({chat_id})")
            choice = input("Choose chat number: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(chats):
                return chats[int(choice) - 1][0]
        print("No chat found yet. Open Telegram, send any message to your bot, then press Enter here.")
        input()


def validate_gemini(api_key: str, model: str) -> bool:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        post_json(
            url,
            {
                "contents": [{"role": "user", "parts": [{"text": "Reply with OK."}]}],
                "generationConfig": {"maxOutputTokens": 5, "temperature": 0},
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        print("Gemini check passed.")
        return True
    except Exception as exc:
        print(f"Gemini check failed: {exc}")
        return False


def validate_telegram(bot_token: str, chat_id: str) -> bool:
    try:
        post_form(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            {
                "chat_id": chat_id,
                "text": "Opportunity Scout setup check passed. Tomorrow we hunt.",
                "disable_web_page_preview": "true",
            },
        )
        print("Telegram check passed. You should see a setup message in Telegram.")
        return True
    except Exception as exc:
        print(f"Telegram check failed: {exc}")
        return False


def main() -> int:
    load_dotenv()
    print("Opportunity Scout setup")
    print("Saved keys are reused automatically. Missing values will be requested.")
    print("If you have not messaged your Telegram bot yet, do that before chat ID discovery.\n")

    values = {
        "GEMINI_API_KEY": prompt_secret("Gemini API key", os.getenv("GEMINI_API_KEY", "")),
        "GEMINI_MODEL": prompt_text("Gemini model", os.getenv("GEMINI_MODEL", "gemini-2.0-flash")),
        "TELEGRAM_BOT_TOKEN": prompt_secret("Telegram bot token", os.getenv("TELEGRAM_BOT_TOKEN", "")),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
    }

    if not values["GEMINI_API_KEY"] or not values["TELEGRAM_BOT_TOKEN"]:
        print("Setup stopped: Gemini API key and Telegram bot token are required.")
        return 1

    if not values["TELEGRAM_CHAT_ID"]:
        values["TELEGRAM_CHAT_ID"] = discover_chat_id(values["TELEGRAM_BOT_TOKEN"])
    else:
        keep = prompt_text("Telegram chat ID", values["TELEGRAM_CHAT_ID"])
        values["TELEGRAM_CHAT_ID"] = keep

    write_env(values)
    print(f"\nSaved config to {ENV_PATH}")

    gemini_ok = validate_gemini(values["GEMINI_API_KEY"], values["GEMINI_MODEL"])
    telegram_ok = validate_telegram(values["TELEGRAM_BOT_TOKEN"], values["TELEGRAM_CHAT_ID"])

    if gemini_ok and telegram_ok:
        print("\nSetup complete. Use RUN_SCOUT.bat whenever you want to run the scout.")
        return 0
    print("\nSetup saved, but one validation failed. Check the message above, fix .env, then run SETUP_ONCE.bat again.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
