# Opportunity Scout

Opportunity Scout is a local lead-finding agent for product design / SaaS work. It fetches public Reddit/RSS posts, filters likely opportunities, scores them with Google Gemini, and sends a Telegram digest.

## Your Only Setup Work

You need two things:

1. A Gemini API key — get one free at [Google AI Studio](https://aistudio.google.com/apikey) (no billing required).
2. A Telegram bot token from `@BotFather`.

Your API keys can live in `.env`. If they are already saved, the setup wizard reuses them automatically. After creating the Telegram bot, send any message to that bot once. This lets the setup wizard discover your chat ID automatically.

## One-Time Setup

Double-click:

```text
SETUP_ONCE.bat
```

It reuses saved keys, asks only for anything missing, discovers your Telegram chat ID, saves `.env`, and sends a Telegram test message.

## Run The Scout

Double-click:

```text
RUN_SCOUT.bat
```

That runs the real daily scout: live sources, OpenAI scoring, Telegram delivery, and dedupe.

## Optional Safe Test

Before adding APIs, you can double-click:

```text
TEST_WITHOUT_APIS.bat
```

This uses sample leads and mock scoring only. It does not call OpenAI, Telegram, Reddit, or RSS.

## Runtime Files

- `.env`: your local secrets, ignored by git.
- `data/seen.json`: dedupe store, ignored by git.
- `data/run-log.jsonl`: run history, ignored by git.

## Notes

- Dry runs do not update `data/seen.json`, so testing will not burn leads.
- The live scout only marks leads as seen after they are actually scored.
- If one source fails, the other sources still run.
