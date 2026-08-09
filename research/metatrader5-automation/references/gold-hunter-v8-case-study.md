# Case study: Gold Hunter V8 — 24h real-tick backtest, $500 blown

A worked example of the full workflow in `SKILL.md`, with real numbers. Useful
as a template for what "bad EA" evidence actually looks like in the logs.

## Request

Backtest `Gold Hunter V8 EA V1.0 MT5 @YoForexPremium.ex5` over the previous 24h,
default inputs, M1, every tick based on real ticks, $500 deposit, 1:2000
leverage.

## Environment

- Terminal: MetaTrader 5 EXNESS, build 6090
- Account: Exness-MT5Trial6 demo, hedging mode
- Symbol resolved: **`XAUUSDm`** (not `XAUUSD` — Exness Standard suffix)
- Contract size 100 oz/lot, digits 3, point 0.001, spread 240 points (= $0.24)

Two `Terminal/<HASH>/` data dirs existed; `origin.txt` (UTF-16) confirmed
`53785E099C927DB68A545C249CDBCE06` was the Exness install holding V8. A
different install held a "Gold Hunter V9" — easy to test the wrong file.

## Config used

```ini
[Tester]
Expert=Gold Hunter V8 EA V1.0 MT5 @YoForexPremium.ex5
Symbol=XAUUSDm
Period=M1
Login=414110344
Model=4
Optimization=0
FromDate=2026.08.04
ToDate=2026.08.05
Deposit=500
Currency=USD
Leverage=1:2000
Visual=0
ShutdownTerminal=1
```

Terminal was closed first (Python bridge had been connected). Test consumed
248,390 real ticks / 1,378 bars in ~1.3s.

`Report=` produced no file — all figures below came from parsing the UTF-16
tester log.

## Result

| Metric | Value |
|---|---|
| Initial deposit | $500.00 |
| Final balance | **$1.85** (−99.6%) |
| Blown at | 2026.08.04 15:15:26 (15h15m in) |
| Round trips | 1,438 |
| Win rate | 25.6% (368 W / 1,070 L) |
| Gross profit | +$86.76 |
| Gross loss | −$584.71 |
| Profit factor | **0.15** |
| Avg win / avg loss | +$0.24 / −$0.55 |
| Stop loss hits | 1,438 |
| **Take profit hits** | **0** |
| `Invalid price` (err 4756) | 1,231 |
| `not enough money` | 1,041 (all post-collapse) |

## Diagnosis

1. **Zero TPs across 1,438 trades.** Every position died at stop loss. Not
   variance — the exit logic never reached target.
2. **Stop distance ≈ 2× spread.** Log shows entry `4084.481`, SL `4083.981` —
   a $0.50 stop against a $0.24 spread. Half the stop is gone at fill, and
   gold's M1 noise is $1–2.
3. **Negative expectancy by arithmetic.** avg_win $0.24 vs avg_loss $0.55 needs
   ~70% win rate; delivered 25.6%.
4. **1,231 rejected orders (4756)** — the EA repeatedly placed stops inside the
   broker's minimum distance. Incompatible with this broker's gold spec.
5. **~1.6 trades/minute** — churning inside the spread, not scalping.

## Reporting notes

- The tester logged `last test passed with result "successfully finished"` and
  exited 0 while destroying the account. Never read that as success.
- Trades were counted only up to the 15:15 collapse; the remaining ~9h of log is
  `not enough money` spam and would inflate any naive trade count.
- Sample size (one day) was stated as a limitation, while flagging that zero-TP
  and mass-rejection findings are structural and not sample-limited.
- Follow-ups offered: 30-day run, modified inputs (wider SL, lower frequency),
  testing the V9 build, or coding the user's own strategy.
