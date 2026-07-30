from __future__ import annotations

import argparse
import os

from .config import load_dotenv
from .http import fetch_json


def find_chat_ids(bot_token: str) -> list[dict]:
    if not bot_token:
        raise RuntimeError("Provide a bot token argument or set TELEGRAM_BOT_TOKEN")
    data = fetch_json(f"https://api.telegram.org/bot{bot_token}/getUpdates")
    chats: dict[str, dict] = {}
    for update in data.get("result", []):
        message = update.get("message") or update.get("edited_message") or update.get("channel_post") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            continue
        chats[str(chat_id)] = {
            "chat_id": chat_id,
            "type": chat.get("type", ""),
            "title": chat.get("title") or chat.get("username") or chat.get("first_name") or "",
        }
    return list(chats.values())


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Find Telegram chat IDs for Opportunity Scout")
    parser.add_argument("bot_token", nargs="?", default=os.getenv("TELEGRAM_BOT_TOKEN", ""))
    args = parser.parse_args()
    chats = find_chat_ids(args.bot_token)
    if not chats:
        print("No chats found. Send a message to your bot in Telegram, then run this command again.")
        return 1
    for chat in chats:
        print(f"TELEGRAM_CHAT_ID={chat['chat_id']}  type={chat['type']}  title={chat['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
