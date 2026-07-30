from __future__ import annotations

from .http import post_form


TELEGRAM_LIMIT = 4096


def chunk_message(message: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    if len(message) <= limit:
        return [message]
    chunks: list[str] = []
    remaining = message
    while remaining:
        chunk = remaining[:limit]
        split_at = chunk.rfind("\n\n")
        if split_at > 1000:
            chunk = chunk[:split_at]
        chunks.append(chunk)
        remaining = remaining[len(chunk):].lstrip()
    return chunks


def send_telegram_message(*, bot_token: str, chat_id: str, message: str) -> None:
    if not bot_token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for chunk in chunk_message(message):
        post_form(
            url,
            {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": "true",
            },
        )
