---
name: daily-weather-briefing
description: "Fetches full Kushtia weather (wttr.in), sends a detailed Telegram digest, and archives each day to Notion 'Database For Weather' (zero LLM tokens, script-driven)."
version: 2.0.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files: []
required_environment_variables:
  - NOTION_API_KEY
  - TELEGRAM_BOT_TOKEN
  - TELEGRAM_HOME_CHANNEL
---

# Daily Weather Briefing (v2 — Notion-backed, detailed, zero-LLM)

Fetches **full** weather for Kushtia from `wttr.in` and:
1. Sends a **detailed** Telegram digest (current conditions + next 24h hourly window + warnings + tomorrow preview).
2. **Archives** each day's record into the Notion **"Database For Weather"** (id `f365db5c-fd1a-4b82-9054-94b14dcd3971`, data_source `68c70d66-931d-4a31-985d-c66bdcab3901`).
3. Is **idempotent** — if today is already saved, it skips the Notion write but still delivers, so the user can ask repeatedly and get the same correct data.
4. **Monthly rolling cleanup** — on the first run of a new month it archives (deletes) all rows whose `Month` select != current `YYYY-MM`.
5. Runs with **zero LLM tokens** — pure Python script (`/opt/weather-bot/weather.py`), no agent needed.

### Architecture

- **Schema (Notion DB):** `Name` (title), `Date` (date), `Condition` (select), `Temp C`, `Feels Like C`, `Humidity %`, `Wind km/h`, `UV Index`, `Max Temp C`, `Min Temp C`, `Rain Chance %` (all number), `Month` (select `YYYY-MM`), `Summary` (rich_text).
- **Cron job** `0c40f69a4dcf` runs `weather.py` via `script=` + `no_agent=true` (zero token cost). Schedule `30 10 * * *` (Asia/Dhaka).

### Running

```bash
cd /opt/weather-bot && python weather.py
```

Env (loaded from Hermes `.env`):
- `NOTION_API_KEY` — Notion integration token
- `NOTION_WEATHER_DB_ID` — database object id (default `f365db5c-...`) used as page parent
- `NOTION_WEATHER_DS_ID` — data_source id (default `68c70d66-...`) used for queries
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_HOME_CHANNEL` — delivery target
- `WEATHER_CITY` — override city (default `Kushtia`)

### Behavior notes

- **Detailed report** covers the window **today 10:30 → next-day 10:30** (the bot runs at 10:30, so it previews the full day ahead). Hourly blocks every 3h are listed.
- **Warnings:** heat (>35°C), rain (max chance ≥50%), high UV (≥8).
- **Idempotency:** dedupe key is `Date == today`. Re-running the same day never creates a duplicate row.
- **Monthly cleanup:** safe — only deletes rows from prior months; current month is always preserved.

### Troubleshooting

| Symptom | Fix |
|---------|-----|
| Notion 404 on query | Check `NOTION_WEATHER_DS_ID` — query uses the **data_source** id, not the database object id |
| "properties do not exist" 400 | DB schema missing — PATCH `/v1/data_sources/{DS_ID}` with the property map |
| Telegram not delivered | Verify `TELEGRAM_BOT_TOKEN` + `TELEGRAM_HOME_CHANNEL` in `.env`; bot must be started |
| wttr.in KeyError `lang_en` | Use `?format=j1&lang=en`; description lives under `weatherDesc`/`lang_en` |
