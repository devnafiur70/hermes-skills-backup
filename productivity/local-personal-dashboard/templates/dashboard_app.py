#!/usr/bin/env python3
"""
TEMPLATE — Local Personal Dashboard (command center)
Copy this file to a working dir and edit the CONFIG block. Copy + adapt.
Verified working 2026-08-09: 3 panels (MT5 / wttr.in weather / tech-news cache).
Zero-token render path. Run: python app.py  ->  http://127.0.0.1:8080
"""
import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# ===== CONFIG — edit these =====
TECH_NEWS_DIR = r"C:/opt/tech-news-bot"
NEWS_CACHE = os.path.join(TECH_NEWS_DIR, "cache", "top_5_news.json")
MT5_TERMINAL = r"C:/Program Files/MetaTrader 5 EXNESS/terminal64.exe"
MT5_LOGIN = 414110344
MT5_SERVER = "Exness-MT5Trial6"
WTT_R_CITY = "Kushtia"
# ==============================

# ---- MT5 ----
def get_mt5():
    try:
        import MetaTrader5 as mt5
    except Exception as e:
        return {"status": "error", "msg": f"MT5 module missing: {e}"}
    if not mt5.initialize(path=MT5_TERMINAL, login=MT5_LOGIN, server=MT5_SERVER):
        mt5.shutdown()
        return {"status": "offline", "msg": "Terminal offline / connect failed"}
    try:
        acc = mt5.account_info()
        if acc is None:
            return {"status": "offline", "msg": "No account info"}
        sym = mt5.symbol_info_tick("XAUUSDm")
        pos = mt5.positions_get(symbol="XAUUSDm") or []
        return {
            "status": "online", "login": acc.login, "server": acc.server,
            "balance": round(acc.balance, 2), "equity": round(acc.equity, 2),
            "free_margin": round(acc.margin_free, 2), "profit": round(acc.profit, 2),
            "xauusd_bid": round(sym.bid, 2) if sym else None,
            "xauusd_ask": round(sym.ask, 2) if sym else None,
            "open_lots_xau": round(sum(p.volume for p in pos), 2),
            "updated": datetime.now().strftime("%H:%M:%S"),
        }
    finally:
        mt5.shutdown()

@app.route("/api/mt5")
def api_mt5():
    return jsonify(get_mt5())

# ---- Weather (wttr.in, zero token) ----
def get_weather():
    try:
        r = requests.get(f"https://wttr.in/{WTT_R_CITY}?format=j1", timeout=10)
        r.raise_for_status()
        d = r.json()
        cur = d["current_condition"][0]
        area = d["nearest_area"][0]
        today = d["weather"][0]
        return {
            "status": "online",
            "area": f"{area['areaName'][0]['value']}, {area['country'][0]['value']}",
            "temp_c": cur["temp_C"], "feels_c": cur["FeelsLikeC"],
            "humidity": cur["humidity"], "desc": cur["weatherDesc"][0]["value"],
            "wind_kmph": cur["windspeedKmph"], "max_c": today["maxtempC"],
            "min_c": today["mintempC"],
            "sunrise": today["astronomy"][0]["sunrise"],
            "sunset": today["astronomy"][0]["sunset"],
            "updated": cur.get("observation_time", ""),
        }
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.route("/api/weather")
def api_weather():
    return jsonify(get_weather())

# ---- News (local cache from tech-news-bot) ----
def get_news():
    if not os.path.exists(NEWS_CACHE):
        return {"status": "empty", "msg": "No news cache. Run tech-news-bot fetcher first.", "items": []}
    try:
        with open(NEWS_CACHE, "r", encoding="utf-8") as f:
            items = json.load(f)
        out = []
        for it in items[:5]:
            raw = it.get("pubDate", "")
            try:
                fdate = datetime.fromisoformat(raw).strftime("%d %b, %Y")
            except Exception:
                fdate = raw[:10] if len(raw) >= 10 else "Recent"
            src = it.get("source")
            src = src.get("title") if isinstance(src, dict) else src
            out.append({
                "title": it.get("title", "(no title)"),
                "summary": (it.get("summary") or "")[:220],
                "link": it.get("link", "#"), "date": fdate, "source": src,
            })
        return {"status": "online", "items": out, "count": len(out)}
    except Exception as e:
        return {"status": "error", "msg": str(e), "items": []}

@app.route("/api/news")
def api_news():
    return jsonify(get_news())

PAGE = """
<!DOCTYPE html><html lang="bn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dashboard</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--acc:#2ea043;--acc2:#58a6ff;--txt:#e6edf3;--mut:#8b949e;--bad:#f85149;}
*{box-sizing:border-box;margin:0;padding:0;font-family:'Segoe UI',system-ui,sans-serif;}
body{background:var(--bg);color:var(--txt);padding:18px;min-height:100vh;}
h1{font-size:20px;} .sub{color:var(--mut);font-size:13px;margin:4px 0 16px;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;}
.card{background:var(--card);border:1px solid #21262d;border-radius:14px;padding:18px;}
.card h2{font-size:15px;color:var(--acc2);margin-bottom:12px;}
.row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px dashed #21262d;font-size:14px;}
.row:last-child{border:none;} .k{color:var(--mut);} .v{font-weight:600;}
.pill{font-size:11px;padding:2px 8px;border-radius:20px;font-weight:700;}
.on{background:var(--acc);color:#04260f;} .off{background:var(--bad);color:#2a0606;}
.err{background:var(--warn,#d29922);color:#2a1d00;}
.news-item{padding:10px 0;border-bottom:1px dashed #21262d;}
.news-item a{color:var(--acc2);text-decoration:none;font-weight:600;font-size:14px;}
.news-meta{color:var(--mut);font-size:11px;margin:3px 0;} .news-sum{font-size:12px;color:#c9d1d9;}
.big{font-size:32px;font-weight:800;color:var(--acc);}
</style></head><body>
<h1>🛰️ Command Dashboard</h1><div class="sub">auto-refresh 60s</div>
<button class="pill on" onclick="loadAll()">⟳ Refresh</button>
<div class="grid" style="margin-top:14px;">
<div class="card"><h2>💰 MT5 <span id="mt5-pill" class="pill off">…</span></h2><div id="mt5-body"></div></div>
<div class="card"><h2>🌤️ Weather <span id="wx-pill" class="pill off">…</span></h2><div id="wx-body"></div></div>
<div class="card"><h2>📰 News <span id="news-pill" class="pill off">…</span></h2><div id="news-body"></div></div>
</div>
<script>
function setPill(id,s){const e=document.getElementById(id);e.className='pill '+(s==='online'?'on':(s==='error'?'err':'off'));e.textContent=s==='online'?'LIVE':(s==='error'?'ERR':'OFF');}
function row(k,v){return `<div class="row"><span class="k">${k}</span><span class="v">${v}</span></div>`;}
async function loadMT5(){try{const d=await(await fetch('/api/mt5')).json();setPill('mt5-pill',d.status);
if(d.status==='online'){document.getElementById('mt5-body').innerHTML=`<div style="text-align:center;margin-bottom:10px"><div class="big">$${d.equity}</div><div class="k" style="font-size:12px">EQUITY</div></div>`+row('Balance',`$${d.balance}`)+row('Profit',`$${d.profit}`)+row('Free Margin',`$${d.free_margin}`)+row('XAUUSDm Bid',d.xauusd_bid)+row('Open Lots',d.open_lots_xau)+row('Login',d.login)+row('Updated',d.updated);}
else document.getElementById('mt5-body').innerHTML=`<div class="row"><span class="k">${d.msg||'Offline'}</span></div>`;}catch(e){setPill('mt5-pill','error');}}
async function loadWeather(){try{const d=await(await fetch('/api/weather')).json();setPill('wx-pill',d.status);
if(d.status==='online'){document.getElementById('wx-body').innerHTML=`<div style="text-align:center;margin-bottom:10px"><div class="big">${d.temp_c}°C</div><div class="k" style="font-size:12px">${d.desc}</div></div>`+row('Feels Like',`${d.feels_c}°C`)+row('Humidity',d.humidity+'%')+row('Wind',d.wind_kmph+' km/h')+row('Min/Max',`${d.min_c}° / ${d.max_c}°`)+row('Sunrise',d.sunrise)+row('Sunset',d.sunset)+row('Area',d.area);}
else document.getElementById('wx-body').innerHTML=`<div class="row"><span class="k">${d.msg||'Error'}</span></div>`;}catch(e){setPill('wx-pill','error');}}
async function loadNews(){try{const d=await(await fetch('/api/news')).json();setPill('news-pill',d.status);
if(d.status==='online'&&d.items.length){document.getElementById('news-body').innerHTML=d.items.map(it=>`<div class="news-item"><a href="${it.link}" target="_blank">${it.title}</a><div class="news-meta">${it.date} • ${it.source||'Source'}</div><div class="news-sum">${it.summary}…</div></div>`).join('');}
else document.getElementById('news-body').innerHTML=`<div class="news-item"><span class="k">${d.msg||'No news'}</span></div>`;}catch(e){setPill('news-pill','error');}}
function loadAll(){loadMT5();loadWeather();loadNews();}
loadAll();setInterval(loadAll,60000);
</script></body></html>
"""
@app.route("/")
def index():
    return render_template_string(PAGE, now=datetime.now().strftime("%Y-%m-%d %H:%M"))

if __name__ == "__main__":
    print("Dashboard at http://127.0.0.1:8080")
    app.run(host="127.0.0.1", port=8080, debug=False)
