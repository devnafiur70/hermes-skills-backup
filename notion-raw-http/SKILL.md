---
name: notion-raw-http
description: "Notion API via curl: 2025-09-03 create/PATCH/dual-ID fixes."
version: 1.0.0
author: Hermes agent
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: .env
    description: NOTION_API_KEY (integration token)
metadata:
  hermes:
    tags: [Notion, Productivity, API, Automation, curl]
---

# Notion Raw HTTP Integration

For when `ntn` CLI is unavailable (native `ntn` is macOS/Linux only as of 2026; Windows needs WSL2) or you need fine control. All calls use `curl`/Python `requests` with header `Notion-Version: 2025-09-03`.

Companion to the bundled `notion` skill — this file captures the **2025-09-03 breaking changes** that the bundled skill's examples predate.

## CRITICAL 2025-09-03 gotchas (verified live)
1. **Create DB → `POST /v1/databases`** (NOT `/v1/data_sources`).
2. **Properties passed at create time are IGNORED.** DB is created with only `Name`. Must PATCH `POST /v1/data_sources/{data_source_id}` afterward to add fields, or you get `400 validation_error: "X is not a property that exists"` on row insert.
3. **Two IDs per DB:** `database_id` = root `id` (use as `parent.database_id` for pages); `data_source_id` = `response["data_sources"][0]["id"]` (use for `/query`). Using `database_id` in the query URL → `404`.
4. **Internal integrations cannot create workspace-root pages** — must be child of an already-shared page. Child DB inherits the parent's share.
5. `GET /v1/databases/{id}` may report empty `properties` — trust `GET /v1/data_sources/{id}`.

Full corrected snippets + wttr.in note: `references/notion-api-2025-09-03.md`.

## Minimal create+property flow (Windows bash)
```bash
curl -s -X POST "https://api.notion.com/v1/databases" \
  -H "Authorization: Bearer $NOTION_API_KEY" -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"parent":{"type":"page_id","page_id":"PAGE_ID"},"title":[{"text":{"content":"My DB"}}],"properties":{"Name":{"title":{}}}}'
# grab data_sources[0].id as DS_ID and root id as DB_ID
curl -s -X PATCH "https://api.notion.com/v1/data_sources/$DS_ID" \
  -H "Authorization: Bearer $NOTION_API_KEY" -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties":{"Date":{"date":{}},"Note":{"rich_text":{}},"Tag":{"select":{"options":[]}}}}'
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d "{\"parent\":{\"type\":\"database_id\",\"database_id\":\"$DB_ID\"},\"properties\":{\"Name\":{\"title\":[{\"text\":{\"content\":\"Row 1\"}}]},\"Note\":{\"rich_text\":[{\"text\":{\"content\":\"hi\"}}]}}}"
```

## Architecture pattern that works well for this user
- One root page ("Mother Database") holds all sub-DBs as nested children.
- Migrate local data into Notion to free PC storage; treat Notion as source of truth.
- For dedup/cron: store a History DB in Notion, query it for 30-day window instead of a local JSON file.

## User preferences observed (this account)
- **Never store media as images in Notion.** When analyzing videos/screenshots (e.g. WhatsApp trading screen-recordings), extract the data via frame-by-frame vision and save the *analysis as TEXT* (rich_text) — never upload the frames/images. User stated this explicitly and sharply.
- **Mother Database holds all sub-DBs.** One root page (user renamed it "Mother Database") nests Weather, Tech News, Tech News History, and Trading sub-databases. Build new DBs as children of it.
- **Notion is source of truth; free local PC storage.** Migrate local JSON/state into Notion; do dedup via a Notion `data_source` query (30-day window), not a local file.
- **Trading DB pattern that worked:** properties `Record Type` (Backtest/Live Trade/Strategy Note/WhatsApp Analysis), `Edge Verdict` (Has Edge / No Edge / Overfit / Will Blow / Unclear — user wants brutal honesty, not discouragement), `Symbol`, `Timeframe`, `Net Profit`, `Max Drawdown %`, `Win Rate %`, `Total Trades`, `Source`, `Month`. Store WhatsApp reverse-engineering under Record Type = "WhatsApp Analysis", Source = "WhatsApp Recording".
- **Channel routing:** tech-news must go to its dedicated Telegram channel (`TECH_NEWS_CHANNEL` env var), NOT the home chat. Set the env var and have delivery scripts fall back to it.

