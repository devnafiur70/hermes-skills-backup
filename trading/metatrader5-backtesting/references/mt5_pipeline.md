# MT5 Backtest Pipeline — concrete recipe & log parsing

## Headless launcher (.ini) — template-ready
```
[Tester]
Expert=SafeGrid_NR_v1.ex5
ExpertParameters=SG_def.set
Symbol=XAUUSDm
Period=M5
Login=414110344
Model=4                 ; <-- ALWAYS 4 (real ticks). Never change for Nafiur.
ExecutionMode=0
Optimization=0          ; set 1 for param search
FromDate=2026.08.04
ToDate=2026.08.05
ForwardMode=0
Deposit=500
Currency=USD
ProfitInPips=0
Leverage=1:2000
Visual=0
ShutdownTerminal=1
Report=C:\Users\user\rep_NAME
ReplaceReport=1
```
Kill terminal first: `Get-Process terminal64 | Stop-Process -Force`, wait 3s, then `Start-Process ... -Wait`.

## Reading results (terminal tool, NOT execute_code)
```bash
SRC=$(find /c/Users/user/AppData/Roaming/MetaQuotes -path "*Tester/logs/20260805.log" 2>/dev/null | head -1)
iconv -f UTF-16LE -t UTF-8 "$SRC" 2>/dev/null | grep "final balance"
iconv -f UTF-16LE -t UTF-8 "$SRC" 2>/dev/null | grep -A4000 "EXPERT.ex5 from DATE" | grep -c "take profit triggered"
```
execute_code's python sandbox CANNOT see the MetaQuotes path. Use terminal to copy/convert logs into `C:\Users\user\gh_lab\` then read_file.

## Optimization (.opt cache) binary layout
- Path: `...\Tester\cache\<EA>.<SYMBOL>.<TF>.<FROM>.<TO>.<MODE>.<HASH>.opt`
- Stride = **312 bytes** per result (MODE=4 / 30-day). Strides seen: 304 (1-day), 312 (30-day).
- Record ordering: oldest result first, newest last; **parse from the END** for the final run.
- Field offsets (double, LE `struct.unpack('<d', buf[o:o+8])[0]`):
  - 24: profit
  - 32: profit (primary display)
  - 40: balance
  - 88: drawdown abs
  - 112: drawdown %
  - 128: equity profit
  - 144: trades count
  - 152: profit trades
  - 160: loss trades
  - 168: profit factor
  - 192: AHPR %
  - 200: GHPR %
  - 208: sharpe
  - 216: trades count (alt)
  - 240: spread
  - 248: commissions
  - 256: swaps
  - 272: **GapPips** (decode: round((v-50)/50)+50)
  - 280: **StopLossPips**
  - 288: **TrailPips**
  - 296: **UseTrailing** (0/1)
- Cross-check every offset against a single known backtest run before trusting (the field map shifted between 1-day 304B and 30-day 312B layouts; a wrong offset silently gives garbage like "gross loss" read as "balance").
- Filter optimization results: drop trades<100 (fluke), then sort by balance.

## Session facts (Nafiur, Exness demo 414110344)
- XAUUSDm: digits 3, point 0.001, contract 100 oz, min lot 0.01, spread~240 pts (=$0.24 round turn), stops_level 0. Real ticks from ~2026.07.10.
- Gold Hunter V8 (YoForexPremium): no TakeProfit input; default SL 50pts=$0.50 (2.1x spread), trail 20pts=$0.20 (0.83x spread, dead). Blew $500->$1.85 on 04 Aug real ticks. 30-day opt best +$212 in-sample, -$499 out-of-sample.
- SafeGrid_NR_v1: dual pending grid, per-order SL, cap 5, DD halt 20%, daily reconstitution. 04 Aug real ticks: $498.57 (-0.3%), 25 TP / 27 SL, 0 invalid-price.
