# Python Tick-Replay Backtest (working alternative when headless MT5 hangs)

When `terminal64.exe /autotest` and `MetaEditor64.exe /compile` both hang/fail headless
on this Windows box, the reliable programmatic path is a **tick-replay simulation** that
re-implements the EA's `OnTick` logic in Python, fed by the *working* `MetaTrader5` live
bridge (`mt5.copy_ticks_range`).

## Why this works
- The live bridge (`mt5.initialize`, `copy_ticks_range`, `copy_rates_range`) functions.
- The built-in `mt5.tester_*` API is absent at 5.0.6090 — so you can't call the tester
  programmatically. A hand-rolled replay sidesteps it entirely.
- Spread is real (fills use actual bid/ask), so edge screening is honest.

## Minimal pattern
```python
import MetaTrader5 as mt5, numpy as np
from datetime import datetime
mt5.initialize()
sym = "XAUUSDm"
t0, t1 = datetime(2026,8,6,0,0,0), datetime(2026,8,6,23,59,59)
ticks = mt5.copy_ticks_range(sym, t0, t1, mt5.COPY_TICKS_ALL)   # struct: time,bid,ask,...
np.save("C:/opt/trading-bot/ticks_2026-08-06.npy", np.array(ticks))
mt5.shutdown()

# Replay (fixed-until-flip pending model)
POINT=0.001; LOT=0.01; TICK_VALUE=0.1; PNL= TICK_VALUE*LOT
bids=ticks['bid'].astype(float); asks=ticks['ask'].astype(float)
running=None; pending=None; trades=[]; equity=0.0
for i in range(len(bids)):
    bid,ask=bids[i],asks[i]
    if pending is not None:
        if pending['type']=='SELLSTOP' and ask>=pending['price']:
            # close old running at bid (if BUY) / ask (if SELL); open SELL at level
            ...
        elif pending['type']=='BUYSTOP' and bid<=pending['price']:
            ...
    # place opposite pending at ask+off*POINT (SELLSTOP) / bid-off*POINT (BUYSTOP)
```
Close logic: `BUY` closes at `bid`, `SELL` closes at `ask`; pnl = `(close-open)/POINT * PNL`.
Sweep `off` (pending offset, points) and a hard `sl` (points) in loops; report
net, win%, profit factor, max DD.

## Caveats
- Models pending as FIXED until a flip (EA does not re-quote each tick) — matches the
  FlipSAR design.
- Does NOT model MT5 internal STOP-trigger slippage / execution queue. Good for edge
  screening, not for exact equity curves.
- Cache ticks per day with `np.save`; reload to avoid re-fetching (slow first pull).

## Verified results — FlipSAR_EA (XAUUSDm, M1, lot 0.01)
5 days, 1.4M real ticks (2026-08-03..07), avg spread ~246 pts.
- V0 (video EA, offset=1pt, no SL): 5d net **-$264**, PF 0.13. BROKEN (offset ≪ spread).
- V1 (offset sweep 50..1000pts, no SL): consistently **-$200..-$264**. WR 97-99% but
  avg loss $135-270 (counter-trend runaway). No edge.
- V2 broker-tuned (offset≥spread+buffer, hard SL 400-900pt, EMA 20/50 trend filter):
  best **-$4,153**, all configs negative. NO EDGE.
Conclusion: the flip/SAR mechanism is incompatible with XAUUSDm @ Exness spread. Do not
run live; keep EA as reference only.
