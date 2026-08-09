# EA input optimization — verified recipe

Worked end-to-end against MT5 EXNESS build 6090, XAUUSDm M1, real ticks.
Companion to `references/gold-hunter-v8-case-study.md`, which covers the
default-settings run that motivated the optimization.

## 1. Get the input list

Run the EA once (any single backtest). MT5 writes defaults to:

```
%APPDATA%\MetaQuotes\Terminal\<HASH>\MQL5\Profiles\Tester\<EA filename>.set
```

UTF-16-LE. Example recovered this way:

```
LotSize=0.01||0.01||0.001000||0.100000||N
MagicNumber=5555||5555||1||55550||N
GapPips=50||50||1||500||N
StopLossPips=50||50||1||500||N
TrailPips=20||20||1||200||N
UseTrailing=true||false||0||true||N
DailyProfitTarget=100.0||100.0||10.000000||1000.000000||N
```

Reading this list *is* analysis. There is no TakeProfit input, so profit can
only come from the trailing stop — and `TrailPips=20` ($0.20 on gold) is
smaller than the Exness spread (~$0.24). Mathematically unable to win before a
single tick is simulated.

## 2. Write the sweep `.set` — BOM required

```python
content = """LotSize=0.01||0.01||0.001000||0.100000||N
MagicNumber=5555||5555||1||55550||N
GapPips=100||50||50||300||Y
StopLossPips=150||100||50||400||Y
TrailPips=100||50||50||200||Y
UseTrailing=true||false||0||true||N
DailyProfitTarget=100.0||100.0||10.000000||1000.000000||N
"""
open(path, 'wb').write(b'\xff\xfe' + content.encode('utf-16-le'))
```

`Name=current||start||step||stop||Y|N`. Without the BOM the run dies in ~2 s
with "no optimized parameter selected".

Bool params: leaving `UseTrailing` at `N` halves the pass count. Sweep it only
if the question actually requires it.

## 3. Optimization ini

```ini
[Tester]
Expert=Gold Hunter V8 EA V1.0 MT5 @YoForexPremium.ex5
ExpertParameters=GHv8opt.set
Symbol=XAUUSDm
Period=M1
Login=<account>
Model=4
Optimization=1
OptimizationCriterion=0
FromDate=2026.08.04
ToDate=2026.08.05
Deposit=500
Currency=USD
Leverage=1:2000
Visual=0
ShutdownTerminal=1
```

168 passes took 1 m 44 s across 4 cores (~2.4 s/pass) on 24 h of M1 real ticks.

Confirm completion in `Tester/logs/`:

```
optimization finished, total passes 168
168 new records saved to cache file 'tester\cache\....opt'
```

## 4. Parse the `.opt` cache

```
%APPDATA%\MetaQuotes\Terminal\<HASH>\Tester\cache\
  <EA>.<SYMBOL>.<TF>.<from>.<to>.<n>.<HASH>.opt
```

Verified layout, build 6090 — **stride 304 bytes**, first record at the offset
where the deposit double appears (2739 in the observed file; scan for it rather
than hardcoding):

| Offset | Type | Field |
|---|---|---|
| +0   | f64 | initial deposit |
| +16  | f64 | **net profit** (balance = deposit + this) |
| +24  | f64 | gross profit |
| +32  | f64 | gross loss (positive magnitude) |
| +96  | f64 | max drawdown, money |
| +104 | f64 | max drawdown, % |
| +184 | f64 | Sharpe ratio |
| +216 | i32 | total trades (deals) |
| +224 | i32 | profit trades |
| +228 | i32 | loss trades |
| +272 | i32 | 1st swept input |
| +280 | i32 | 2nd swept input |
| +288 | i32 | 3rd swept input |

Swept inputs appear at +272/+280/+288 in declaration order. Iterate while
`f64@+0` still equals the deposit; stop when it doesn't.

### Mandatory sanity check

Offsets +16 / +24 / +32 are adjacent and easy to transpose. In this session
`+32` (gross loss, 672.34) was first misread as final balance, producing a
reported "+$172 profit" on a run whose real result was **−$393**.

Before quoting anything: re-run the top row as a plain `Optimization=0`
backtest with those exact inputs and diff against the log's `final balance`.

```
parsed  : balance 106.50, gross_profit 278.84, gross_loss 672.34, trades 2400
log     : final balance 106.50 USD
```

Match → mapping trusted. Mismatch → remap, do not publish.

## 5. Results (04 Aug 2026, XAUUSDm M1, real ticks, $500, 1:2000)

| Gap/SL/Trail | Balance | Net | Trades | Win% | PF | DD% |
|---|---|---|---|---|---|---|
| 50/50/20 (default) | $1.85 | −$498 | 1438 | 25.6 | 0.15 | 79.0 |
| 50/100/50 | $106.50 | −$394 | 1200 | 45.5 | 0.41 | 79.0 |
| 250/400/200 (best) | $539.29 | +$39 | 147 | 66.7 | 1.21 | 4.8 |

Only **9 of 167** combinations were profitable.

## 6. Walk-forward — the step that changed the conclusion

Best combination (250/400/200) run unchanged on other days:

| Date | Balance | Net | Win% | PF |
|---|---|---|---|---|
| 04 Aug (in-sample) | $539.29 | +$39.29 | 66.7 | 1.21 |
| 03 Aug | $430.18 | −$69.82 | 56.6 | 0.72 |
| 31 Jul | $396.90 | −$103.10 | 55.8 | 0.57 |
| 30 Jul | $387.28 | −$112.72 | 57.6 | 0.74 |

Four-day total **−$246**. The in-sample win was curve-fit noise.

Supporting evidence that the defect is structural, not a tuning problem:

- 0 TP hits in **every** configuration (no TP input exists).
- ~68 `Invalid price` / error 4756 rejections per run survived every parameter
  set — the EA places orders inside the broker's minimum stop distance.
- Payoff asymmetry: avg win $2.31 vs avg loss $3.82 needs ~62% just to break
  even, so even 66.7% wins is fragile.

Verdict delivered: input tuning cannot rescue this EA; do not run it live.
