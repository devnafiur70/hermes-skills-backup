---
name: xauusd-foundation-setup
description: "Scaffold the XAUUSD news/alert automation foundation."
version: 1.0.0
author: hermes
license: MIT
tags: [notion, forex, xauusd, gold, news, automation, trading]
---

# XAUUSD News Automation — Foundation Setup

Builds the foundation for an automated Forex Factory news briefing + alert system
for XAUUSD (Gold) traders. User: Nafiur (Kushtia, Asia/Dhaka). Address as "Sir".

## When to use
- Scaffolding a new news/alert pipeline for Gold or any FX pair.
- Creating the Notion "Forex News Pipeline" DB and `config/settings.ts`.

## Folder structure
```
/opt/xauusd-news-automation/   (Windows: C:\opt\xauusd-news-automation\)
  config/      profile & threshold settings
  skills/      custom skills for this project
  logs/        execution logs
  cache/       daily JSON feed cache
```
Create with: `mkdir -p config skills logs cache` (POSIX) or `mkdir` per dir.

## Config: config/settings.ts
TypeScript-style config (consumed by Node/Python scripts):
```ts
const settings = {
  targetCurrencies: ["USD"],   // USD drives Gold
  focusPair: "XAUUSD",
  highImpactAlertMinutes: 30,
  briefingTime: "07:30",       // Asia/Dhaka
  telegramChatId: "<my_chat_id>",
  notionDatabaseId: "<database_id>",
};
export default settings;
```

## Notion integration
Load the `notion` skill for API basics. Key steps:

1. **Find root page** "Mother Databae" (user nests everything under it — do NOT
   place under unrelated pages). Search `Mother Database` via `/v1/search`.
   Known id: `3b577eb9-06da-803d-86f9-e24c914d4274`.
2. **Create DB** via `POST /v1/databases` with
   `parent: {type:"page_id", page_id: ROOT}`, `title`, and a `properties` schema.
   ⚠️ On API version `2025-09-03`, the create response returns EMPTY `properties`
   — the schema is silently dropped.
3. **Set properties** via `PATCH /v1/data_sources/{data_source_id}` where
   `data_source_id` comes from the created DB's `data_sources[0].id`.
   - Include ALL non-title props (Currency select, Impact select, Date&Time date,
     Forecast/Previous/Actual rich_text, Affected Asset multi_select, Status select).
   - ⚠️ Do NOT include a `title` property in the PATCH — you get
     `validation_error: Cannot create new title property.` The title auto-exists
     as `Name`.
4. **Insert rows** via `POST /v1/pages` with
   `parent: {type:"database_id", database_id: DB_ID}`. Use `Name` as the title
   property key in the row body.
5. **Query rows** via `POST /v1/data_sources/{data_source_id}/query`.

### Property schema (reference)
- Event Title → title (auto = "Name")
- Currency → select [USD, EUR, GBP, AUD, JPY, CAD, CHF, NZD]
- Impact → select [High, Medium, Low, Non-Economic]
- Date & Time → date (with time)
- Forecast / Previous / Actual → rich_text
- Affected Asset → multi_select [XAUUSD, Forex, Indices]
- Status → select [Upcoming, Alert Sent, Processed, Passed]

## Pitfalls
- New Notion API (2025-09-03): databases are "data sources". Create DB ≠ define
  properties. Always PATCH the data_source to set the schema.
- `last_edited_time` is a system field — do NOT add it as a user property.

## Verification
- Re-read the DB (`GET /v1/databases/{id}`) → properties should list all 9.
- Insert 1 sample USD High-Impact row (e.g. "US Non-Farm Payrolls (NFP)") and
  confirm via data_sources query.
- Show the directory tree with `ls -R` to the user.
