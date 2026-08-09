# Notion API — 2025-09-03 Gotchas (learned the hard way, verified live)

Integration: Hermes "Hermis70", on Windows via curl / Python `requests` (no `ntn` CLI — native `ntn` is macOS/Linux only).

## 1. Create database → wrong endpoint
OLD (broken): `POST /v1/data_sources`
NOW (correct): `POST /v1/databases`

Error if you use the old one:
> "Creating new databases with data sources is not supported in this endpoint for API version 2025-09-03 and later. Use the Create Database API instead."

```bash
curl -s -X POST "https://api.notion.com/v1/databases" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"parent":{"type":"page_id","page_id":"PARENT_PAGE_ID"},"title":[{"text":{"content":"My DB"}}],"properties":{"Name":{"title":{}}}}'
```
Parent MUST be an existing shared page id. Workspace-root `parent:{workspace:true}` fails for internal integrations with a validation_error.

## 2. Property-creation bug (critical)
The `properties` map passed at CREATE TIME IS IGNORED. The DB is created with ONLY `Name` (title). You will later get `400 validation_error: "X is not a property that exists"` when inserting rows.

FIX — after create, PATCH the **data source**:
```bash
curl -s -X PATCH "https://api.notion.com/v1/data_sources/{data_source_id}" \
  -H "Authorization: Bearer $NOTION_API_KEY" -H "Notion-Version: 2025-09-03" \
  -H "Content-Type: application/json" \
  -d '{"properties":{"Temp C":{"number":{}},"Date":{"date":{}},"Note":{"rich_text":{}}}}'
```
`data_source_id` comes from the create response: `response["data_sources"][0]["id"]` — NOT the root `id`.

## 3. Two IDs per database — do not conflate
- `database_id` = root `id` of the `POST /v1/databases` response. Use as `parent` when creating pages/rows:
  `POST /v1/pages` → `{"parent":{"type":"database_id","database_id":"<db_id>"},"properties":{...}}`
- `data_source_id` = `response["data_sources"][0]["id"]`. Use for queries:
  `POST /v1/data_sources/{data_source_id}/query`

Using `database_id` in the query URL → `404 Could not find data_source with ID: ...`.

## 4. Internal integration limits
- Cannot create workspace-root pages (`parent:{workspace:true}` → validation_error). Create as a child of a page you already shared with the integration.
- A newly created child DB inherits the share from its parent page automatically (no extra "Connect to" step needed if the parent is already shared).
- Rate limit ~3 req/s average.

## 5. Verify a DB quickly
`GET /v1/databases/{database_id}` shows `title` + `properties` but may report empty properties even when the data source has them. Trust `GET /v1/data_sources/{data_source_id}` for the real schema.

## 6. wttr.in note (for weather bots)
`wttr.in/Kushtia?format=j1` does NOT include `lang_en` by default. Add `&lang=en` and read descriptions from `weatherDesc` (a list of `{value}`), not `lang_en`. `current_condition[0]` uses `temp_C`, `FeelsLikeC`, `humidity`, `windspeedKmph`, `uvIndex` directly (no nested list).
