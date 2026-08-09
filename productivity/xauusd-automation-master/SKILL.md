---
name: xauusd-automation-master
description: "Master cron for XAUUSD news briefing + alerts."
version: 1.0.0
author: hermes
license: MIT
tags: [notion, forex, xauusd, gold, cron, automation, telegram, news]
---

# XAUUSD Automation Master (cron orchestration)

Wires the full XAUUSD news pipeline into scheduled cron jobs with error
handling + offline fallbacks.

## Machine timezone = Asia/Dhaka
CONFIRMED: this box's `datetime.now()` already returns Dhaka local time, so cron
times are set directly in BD without offset math.
- Morning briefing: `30 7 * * *`  (07:30 BD)
- Alert monitor:    `*/5 12-23 * * *`  (every 5 min, 12:00–23:00 BD = London+NY)

## Files (in /opt/xauusd-news-automation, Windows C:\opt\...)
- `fetch_forex_factory.py` — fetch FF → filter USD/High+Med → Dhaka → sync Notion.
  Writes `cache/today-news.json` for offline fallback. Endpoints tried in order:
  nls (dead) → nfs json (live) → nfs csv → cache/ff_thisweek.json.
- `generate_briefing.py [YYYY-MM-DD]` — classify + caution windows + Markdown
  (<400 words). Falls back to `cache/today-news.json` if Notion down.
- `alert_runner.py [--dry-run]` — High/USD/Upcoming due in 30 min → TG alert →
  Status "Alert Sent" (dedup) → `logs/alerts.log`.
- `common.py` — shared `send_telegram()`, `log_error()`, `critical_notify()`.
- `run_briefing.py [YYYY-MM-DD]` — orchestrator: fetch → generate → send.
- `run_alerts.py` — alert orchestrator (self-guards 12–23 BD).

## Cron setup (create via cronjob tool)
1. Name "XAUUSD Morning Briefing", schedule `30 7 * * *`, deliver telegram,
   skills [fetch-forex-factory-feed, generate-xauusd-daily-briefing],
   prompt: run `cd C:/opt/xauusd-news-automation && python run_briefing.py`.
2. Name "XAUUSD Alert Monitor", schedule `*/5 12-23 * * *`, deliver telegram,
   skills [xauusd-high-impact-alert-runner],
   prompt: run `cd C:/opt/xauusd-news-automation && python run_alerts.py`.

## Error handling / fallbacks (baked into scripts)
- FF JSON endpoint fails → CSV fallback → local cache.
- Notion API unreachable → briefing reads `cache/today-news.json`.
- All errors → `logs/errors.log`; critical failure → Telegram notify.

## Verification (manual test run)
1. `python fetch_forex_factory.py --use-cache` (or live) → status JSON.
2. `python run_briefing.py [YYYY-MM-DD]` → prints briefing + tg status.
3. `python run_alerts.py` → silent if no due events, else alert + Status flip.

## Gotchas
- Live FF host is `nfs.faireconomy.media` (nls is dead as of 2026-08).
- Telegram needs `TELEGRAM_BOT_TOKEN` env + real `telegramChatId` in
  config/settings.ts, else send is skipped (logged, non-critical).
- Notion 2025-09-03: create DB returns empty props; delete=archive PATCH;
  dates stored `+06:00` with `.000` ms (normalize for dedup).
- CSV header case varies → normalize keys to lowercase before reading.

## Downstream deliverable
Telegram briefing + alerts go to `telegramChatId`. Channel output must be clean
(no job IDs/debug/status text).
