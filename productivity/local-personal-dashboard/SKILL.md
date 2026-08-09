---
name: local-personal-dashboard
description: "Build local Flask dashboard of personal live data (MT5)."
version: 1.0.0
tags: [dashboard, flask, mt5, wttr, weather, news, personal, command-center, local]
---

# Local Personal Dashboard (command center)

Use when the user wants a single local web page that shows several of their
live personal data feeds together — e.g. MT5 equity, Kushtia weather, and
tech news — in one place, auto-refreshing, zero or low token cost.

This is the class of "build me one page that watches my stuff". The working
reference implementation lives in `templates/dashboard_app.py` (copy + adapt).
Data-source integration quirks (key names, offline handling, cache paths) are
in `references/data-source-quirks.md`.

## Architecture (proven pattern)

- **Backend:** Flask app, one route `/` (HTML) + one JSON API route per source
  (`/api/mt5`, `/api/weather`, `/api/news`). Each API route wraps a getter that
  returns a dict with a `status` field (`online` / `offline` / `error` / `empty`).
- **Frontend:** single HTML page, vanilla JS `fetch()` + `setInterval(..., 60000)`
  auto-refresh, a "Refresh Now" button, a colored status pill per card
  (green LIVE / red OFF). No build step, no framework.
- **Resilience:** every getter catches exceptions and returns a degraded status
  instead of 500-ing. A dead source must never blank the whole page.
- **Cost:** weather via `wttr.in` (zero token); news via the local
  `tech-news-bot` cache file (zero token); MT5 via the `MetaTrader5` Python
  bridge (zero token). No LLM call in the render path.

## Steps

1. `pip install flask` (also needs `MetaTrader5` for the MT5 panel).
2. Copy `templates/dashboard_app.py` to a working dir (e.g. `C:/opt/dashboard/`).
3. Edit the CONFIG constants block at the top: `TECH_NEWS_DIR`, news cache path,
   `MT5_TERMINAL`, `MT5_LOGIN`, `MT5_SERVER`, and the wttr city.
4. Run: `python app.py` → serves on `http://127.0.0.1:8080`.
5. Verify each `/api/<source>` with `curl -s ... | python -m json.tool` BEFORE
   trusting the browser render — the page's JS fetch can lag one paint (shows
   "Loading…" on first paint, then fills in). Confirm via curl + a second
   browser navigation / screenshot.
6. To keep it up after a reboot: launch as a startup item or a background
   process; it does not auto-relaunch on PC restart.

## Panel integration notes (see references for detail)

- **MT5:** `mt5.initialize(path=..., login=..., server=...)`; check the return
  value — `False` means the terminal is closed → return `offline`, do NOT
  `SystemExit`. Read `account_info()`, `symbol_info_tick("XAUUSDm")`,
  `positions_get(symbol=...)`. Always `shutdown()` in a `finally`.
- **Weather:** `https://wttr.in/<City>?format=j1`. NOTE the current_condition key
  is `observation_time`, not `localObsDateTime` (KeyError trap). `nearest_area`
  may return a sub-locality name (Kushtia → "Ghorai"), not the city.
- **News:** reuse `C:/opt/tech-news-bot/cache/top_5_news.json` (list of
  `{title, summary, link, pubDate, source}`). If missing/empty, run
  `python fetcher.py` in that dir to populate it. Show raw items — do not call
  the LLM formatter for a dashboard.

## Pitfalls

- wttr.in `format=j1` current_condition has **no** `localObsDateTime` key —
  use `observation_time` or `.get(...)` defensively.
- The browser first paint often shows "Loading…" for cards whose `fetch()`
  hasn't resolved; verify with `curl`, not just the first screenshot.
- MT5 `initialize()` returns `False` (not raises) when the terminal is offline —
  handle it as a status, or the dashboard crashes on a closed terminal.
- News cache can be an empty list `[]` or a 2-byte stub file after a no-hit
  fetch — guard `count` and show "EMPTY" rather than iterating.
- `MetaTrader5` is Windows/64-bit only; the Python interpreter must be 64-bit.
- Don't put an LLM call in the dashboard render path — it defeats the
  zero-token design and adds latency to every refresh.

## Files

- `templates/dashboard_app.py` — known-good, copy-and-adapt reference app.
- `references/data-source-quirks.md` — exact key names, return shapes, and the
  offline-degrade pattern for each data source.
