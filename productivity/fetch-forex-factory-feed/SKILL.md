---
name: fetch-forex-factory-feed
description: "Fetch FF calendar, filter USD/XAUUSD, sync to Notion."
version: 1.0.0
author: hermes
license: MIT
tags: [notion, forex, xauusd, gold, news, forexfactory, automation]
---

# Fetch Forex Factory Feed + Notion Sync

Fetches the weekly economic calendar, filters USD / XAUUSD-affecting events
(High + Medium impact), converts timestamps to Asia/Dhaka, and syncs into the
Notion "Forex News Pipeline" database (dedup by Title + Date).

## Endpoints (2026-08 reality)
The user's primary endpoint `https://nls.forexfactory.com/forex-calendar/this-week.json`
is DEAD (host no longer resolves). The live FF calendar now lives at:
- `https://nfs.faireconomy.media/ff_calendar_thisweek.json`  (JSON — works)
- `https://nfs.faireconomy.media/ff_calendar_thisweek.csv`   (CSV fallback)
- `https://nfs.faireconomy.media/ff_calendar_thisweek.xml`   (XML)

Try in order: nls (user spec) → nfs json → nfs csv. Fall back to cache file if
all 429/blocked. NOTE: this box gets intermittent 429 / Cloudflare challenges
from nfs; retry with backoff or use a cached payload for testing.

## FF JSON schema
`[{"title","country","date":"2026-08-07T08:30:00-04:00","impact":"High|Medium|Low|Holiday","forecast","previous"},...]`
- Date carries `-04:00` (EDT) offset.
- No explicit "XAUUSD" tag — treat `country=="USD"` (and `country=="All"` with
  `impact=="High"`, e.g. FOMC) as Gold-affecting.

## Filtering pipeline
- Keep `country in targetCurrencies` (default ["USD"]) OR (`country=="All"` and impact High).
- Keep impact in {High, Medium}.
- Convert date to Asia/Dhaka (UTC+6, no DST) via `datetime.fromisoformat(...).astimezone(DHAKA)`.

## Notion sync (DB: Forex News Pipeline)
- DB id `b8b1052b-71f2-45a8-b01d-3616e9f0245d`, data_source id `6a9bfc75-...`.
- Dedup key = (Name title, normalized Date). Normalize BOTH sides to
  `YYYY-MM-DDTHH:MM:SS` (strip microseconds + offset) — Notion stores
  `+06:00` with `.000` ms, so naive string match FAILS. This is the #1 bug.
- Missing → create with Status="Upcoming".
- Exists → PATCH Forecast/Previous/Actual.

## Notion API gotchas (version 2025-09-03)
- Create DB via `/v1/databases` returns EMPTY `properties`; set schema via
  `PATCH /v1/data_sources/{data_source_id}` WITHOUT a `title` prop
  ("Cannot create new title property"). Title auto-exists as `Name`.
- Query rows via `POST /v1/data_sources/{id}/query`.
- DELETE a row = `PATCH /v1/pages/{id}` with `{"archived": true}` (the
  `DELETE` method returns HTTP 400 on this API version).
- `last_edited_time` is system-only; never add as user property.
- Root page is "Mother Databae" (`3b577eb9-...`); nest DBs under it.

## Status output
```json
{ "totalEventsFetched": 45, "usdEventsFiltered": 12, "highImpactCount": 4, "syncedToNotion": 12 }
```

## Reference engine
`/opt/xauusd-news-automation/fetch_forex_factory.py` (Windows:
`C:\opt\xauusd-news-automation\fetch_forex_factory.py`).
Run: `python fetch_forex_factory.py [--use-cache]` (--use-cache uses cache/ff_thisweek.json).
