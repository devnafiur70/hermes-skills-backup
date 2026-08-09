---
name: generate-xauusd-daily-briefing
description: "Generate XAUUSD daily briefing Markdown from Notion."
version: 1.0.0
author: hermes
license: MIT
tags: [notion, forex, xauusd, gold, briefing, telegram, automation]
---

# Generate XAUUSD Daily Briefing

Reads a day's USD events from the Notion "Forex News Pipeline" DB, classifies
High/Medium impact, builds caution windows (+-30 min around High events), and
emits a mobile-friendly Markdown Telegram message (<400 words).

## Engine
`/opt/xauusd-news-automation/generate_briefing.py`
(Windows: `C:\opt\xauusd-news-automation\generate_briefing.py`)
Run: `python generate_briefing.py [YYYY-MM-DD]`  (default = today, Asia/Dhaka)
Outputs the Markdown message + meta line (events/high/med/caution/words).
Caches to `cache/briefing_<date>.json`.

## What it does
1. Read day's events (00:00–23:59 Asia/Dhaka) from Notion DB
   `b8b1052b-...` (data_source `6a9bfc75-...`). Dates stored as `+06:00` with
   `.000` ms — parse with `datetime.fromisoformat(...).astimezone(DHAKA)`.
2. Classify: keep `Currency == USD`. High → High-Impact section; Medium →
   Medium-Impact section.
3. Caution windows: for each High event, +-30 min block (configurable
   `CAUTION_MIN`). Marked ⚠️.
4. Emit Markdown:
   - Header: `#XAUUSD  Gold News Briefing` + `📅 <weekday>, <dd Mon yyyy> (Asia/Dhaka)`
   - 🔴 High-Impact (time, title ⭐ if key event, `F x | P y`)
   - 🟠 Medium-Impact
   - ⚠️ High Volatility / Risk Windows (time ranges)
   - 🧠 USD → XAUUSD Read (analysis)
5. Constraints: <400 words (busy day ~170), clean emoji markers
   (🔴 High, 🟠 Medium, ⚠️ Caution), mobile-readable (short lines, 2-space indent).

## Key-event detection
`HIGH_KEYWORDS = [CPI, NFP, NON-FARM, FOMC, PPI, RETAIL SALES, UNEMPLOYMENT, PAYROLL]`
Key events get ⭐ and drive the "Focus:" line.

## Gotchas / fixes baked in
- **Duplicate high-impact rows**: FF/sample data may list the same release under
  two titles (e.g. "Non-Farm Payrolls" + "US Non-Farm Payrolls (NFP)"). Collapse
  by keyword group (NFP/FOMC/CPI/PPI/RETAIL/UNEMP) in `classify()` so it shows once.
- **No events today**: prints "None scheduled" sections + a calm analysis line
  ("trade on technicals"). Handles gracefully.
- **Analysis is rule-based, zero-LLM** (per user's zero-token preference). It
  reports focus + general caution guidance, NOT a fake directional forecast —
  avoids wrong hawk/dove calls (e.g. lower unemployment is hawkish, not dovish).

## Notion read pattern (2025-09-03)
Query `POST /v1/data_sources/{data_source_id}/query`; iterate `has_more` with
`start_cursor`. Title = `Name` property; date = `Date & Time.date.start`.

## Downstream
Pair with `fetch-forex-factory-feed` (populate DB) and a Telegram sender (deliver
message to `telegramChatId` from config/settings.ts). Schedule via cron at
`briefingTime` ("07:30" Asia/Dhaka).
