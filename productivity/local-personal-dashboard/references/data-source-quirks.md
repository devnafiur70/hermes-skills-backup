# Data-source quirks (verified this session, 2026-08-09)

## wttr.in — `?format=j1` (Kushtia / any city)
GET `https://wttr.in/<City>?format=j1` (zero token).

Structure:
- `data["current_condition"][0]` — current weather. Keys:
  `temp_C`, `FeelsLikeC`, `humidity`, `weatherDesc` (list of `{value}`),
  `windspeedKmph`, `cloudcover`, `pressure`, `uvIndex`, `visibility`,
  `winddir16Point`, `precipMM`.
  - TIMESTAMP KEY IS **`observation_time`** — NOT `localObsDateTime`.
    Using `localObsDateTime` raises `KeyError`. Use `cur.get("observation_time", "")`.
- `data["nearest_area"][0]` — `areaName[0]["value"]` is often a **sub-locality**,
  e.g. Kushtia resolves to `"Ghorai"`. Don't assume it equals the requested city.
- `data["weather"][0]` — today's forecast. `maxtempC`, `mintempC`, and
  `astronomy[0]["sunrise"]` / `["sunset"]` (e.g. `"05:37 AM"`).

## tech-news-bot cache
Path: `C:/opt/tech-news-bot/cache/top_5_news.json` (Windows native path; the
bot also resolves `C:/opt/tech-news-bot` under `os.name == "nt"`).

Shape: JSON list of 5 items:
`{"title": str, "summary": str, "link": str, "pubDate": ISO8601,
  "source": str-or-dict}`.
- `source` may be a bare string OR a dict `{"title": ...}` — normalize with:
  `isinstance(it.get("source"), dict) and it["source"].get("title") or it.get("source")`.
- `pubDate` is ISO (`2026-08-09T...`); format with `datetime.fromisoformat`.
- If the file is missing OR an empty list `[]` (a 2-byte `[]` stub appears after
  a no-hit fetch), run `python fetcher.py` in that dir to repopulate. The fetcher
  pulls RSS from GSMArena / AndroidAuthority / 9to5Google / PhoneArena, selects
  top 5, and also archives to Notion. Do NOT call the LLM `formatter.py` for a
  dashboard — show raw items.

## MetaTrader5 live bridge (Exness XAUUSDm)
```python
import MetaTrader5 as mt5
if not mt5.initialize(path=r"C:/Program Files/MetaTrader 5 EXNESS/terminal64.exe",
                      login=414110344, server="Exness-MT5Trial6"):
    # terminal is CLOSED or login failed — return {"status":"offline", ...}
    mt5.shutdown()
    return offline_payload
try:
    acc = mt5.account_info()          # balance, equity, profit, margin_free, login, server
    tick = mt5.symbol_info_tick("XAUUSDm")   # .bid / .ask
    pos  = mt5.positions_get(symbol="XAUUSDm") or []
    open_lots = sum(p.volume for p in pos)
finally:
    mt5.shutdown()
```
- `initialize()` returns `False` when the terminal is offline — it does NOT raise.
  Treat as a status, never `SystemExit`, or the dashboard 500s on a closed terminal.
- `MetaTrader5` is Windows + 64-bit only; confirm the interpreter is 64-bit.
- Symbol for Exness Standard is `XAUUSDm` (suffix matters). Probe if unsure.
- `account_info()` / `symbol_info_tick()` return `None` if not available — guard.
