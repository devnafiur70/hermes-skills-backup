---
name: xauusd-high-impact-alert-runner
description: "Run XAUUSD high-impact pre-news Telegram alerts from Notion."
version: 1.0.0
author: hermes
license: MIT
tags: [notion, forex, xauusd, gold, alert, telegram, automation]
---

# XAUUSD High-Impact Alert Runner

Queries Notion "Forex News Pipeline" for High-Impact USD events that are Upcoming
and fire within the next 30 minutes (Asia/Dhaka). Sends an urgent Telegram alert,
flips Status to "Alert Sent" (dedup), and logs to /logs/alerts.log.

## Engine
`/opt/xauusd-news-automation/alert_runner.py`
(Windows: `C:\opt\xauusd-news-automation\alert_runner.py`)
Run: `python alert_runner.py [--dry-run]`   (dry-run = no Telegram send)
Designed for cron every 5 min.

## Query (Notion 2025-09-03)
`POST /v1/data_sources/{data_source_id}/query` with filter:
```json
{"filter":{"and":[
  {"property":"Impact","select":{"equals":"High"}},
  {"property":"Currency","select":{"equals":"USD"}},
  {"property":"Status","select":{"equals":"Upcoming"}}
]}}
```
Then keep rows where `Date & Time.date.start` (parse with
`datetime.fromisoformat(...).astimezone(DHAKA)`) is between `now` and `now+30min`.

## Alert message (exact format)
```
🚨 HIGH IMPACT NEWS ALERT (XAUUSD)
Event: <title>
Time: <HH:MM> BD (In <N> mins)
Forecast: <fc> | Previous: <pv>
⚠️ Caution: Spreads may widen. Consider pausing EAs or locking positions.
```

## Status update (dedup)
`PATCH /v1/pages/{page_id}` with `{"properties":{"Status":{"select":{"name":"Alert Sent"}}}}`.
Prevents re-alerting on next cron tick. (DELETE is 400 on this API; use PATCH.
Archive = PATCH `{"archived":true}`.)

## Telegram send
Reads `TELEGRAM_BOT_TOKEN` env + `telegramChatId` (from config/settings.ts).
If token/chat missing or `--dry-run`, it SKIPS send but still updates Notion +
logs (so the pipeline is testable without a bot). Use Markdown parse_mode.
Logs every execution to `logs/alerts.log`:
`YYYY-MM-DD HH:MM:SS | ALERT | <title> | <datetime> BD | sent=<bool> | <detail>`

## Gotchas
- DB id `b8b1052b-...`, data_source `6a9bfc75-...`. Notion `/v1/databases` shows
  empty `properties` (schema lives on data_source) but query filters still work.
- Date stored as `+06:00` with `.000` ms — always `astimezone(DHAKA)` for compare.
- "All"-country High events (e.g. FOMC) are tagged USD in the synced DB, so they
  match the Currency=USD filter.

## Pipeline
`fetch_forex_factory.py` (populate) → `alert_runner.py` (30-min pre-alerts) →
`generate_briefing.py` (07:30 Dhaka briefing) → Telegram.
