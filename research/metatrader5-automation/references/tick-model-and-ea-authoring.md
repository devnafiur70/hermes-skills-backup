# Tick models as a diagnostic, and authoring a replacement EA

Companion to `references/gold-hunter-v8-case-study.md` (the failing EA) and
`references/ea-input-optimization.md` (the sweep that could not rescue it).
Everything here verified on MT5 EXNESS build 6090, XAUUSDm, Exness demo.

## 1. Real ticks vs generated ticks — the delta is the finding

Same EA, same day, same default inputs, only `Model` changed:

| | `Model=4` real ticks | `Model=0` every tick (generated) |
|---|---|---|
| Final balance | **$1.85** | **$840.25** |
| Net | −$498.15 | +$340.25 |
| Win rate | 25.6% | 55.7% |
| Profit factor | 0.15 | 1.94 |
| Avg win | +$0.236 | +$0.794 |
| Avg loss | −$0.546 | −$0.515 |
| Max DD | 79% | 3.5% |

An $838 swing from the tick source alone.

**Why.** `Model=0` interpolates ticks from M1 OHLC — smooth, well-behaved paths.
Real ticks carry the actual spread stream and intrabar spikes. An EA whose stop
and trail distances are near the spread lives or dies entirely inside that
intrabar detail, so the generated path flatters it enormously. Avg win tripled
under generated ticks while avg loss barely moved: the trailing stop was
"locking" profit that never existed in the real stream.

**Use it deliberately.** Running both models is a cheap, powerful diagnostic:

- Large real-vs-generated gap → the strategy is **cost/microstructure
  dependent**. Its apparent edge is an artefact. Expect live results to track
  the real-tick number, not the pretty one.
- Small gap → the strategy's stops are wide relative to spread and the result
  is at least structurally plausible.

This also explains how vendors show great backtests for worthless EAs: a
generated-tick run on a cherry-picked window. When a user reports a seller's
screenshot, ask which tick model produced it.

Never substitute generated ticks for real ticks in a verdict. Run it as a
*comparison*, report both, and label the real-tick figure as the honest one.

## 2. Quantify the cost bleed before blaming direction

Pull the broker's real spread distribution from live data, then price the EA's
own turnover against it:

```python
si = mt5.symbol_info(SYM)                 # point, trade_contract_size
df = pd.DataFrame(mt5.copy_rates_range(SYM, mt5.TIMEFRAME_M1, start, end))
spread_price = df['spread'].median() * si.point          # $0.240
cost_rt      = spread_price * si.trade_contract_size * lot  # $0.240 @ 0.01 lot
print(round_trips * cost_rt, "spread bill vs", net_loss, "actual loss")
```

Worked result: 1438 round trips × $0.24 = **$345 of the $498 loss (69%) was
pure spread**. The EA's stop was $0.50 (2.1× spread) and its trail $0.20
(**0.83× spread** — below cost, unwinnable before a tick is simulated).

Report stop and trail distances as *multiples of spread*. That single ratio
diagnoses more scalper EAs than any equity curve.

## 3. Search for an edge with a baseline control

Before writing a replacement, test whether any signal actually beats doing
nothing. Score candidate signals by MFE/MAE (max favourable vs adverse
excursion over a fixed horizon, in ATR units) and **always include a
no-logic baseline in the same table**:

| signal | n | MFE | MAE | MFE/MAE |
|---|---|---|---|---|
| BASELINE long (control) | 615 | 2.19 | 2.54 | 0.862 |
| **BASELINE short (control)** | 615 | 2.54 | 2.19 | **1.160** |
| breakout 20-bar high (long) | 202 | 2.52 | 2.24 | 1.123 |
| breakdown 20-bar low (short) | 258 | 2.64 | 2.19 | 1.201 |
| squeeze → breakdown (short) | 80 | 3.46 | 2.52 | 1.370 |
| EMA20<100 pullback (short) | 380 | 2.97 | 2.66 | 1.119 |

Without the control rows this looks like a pile of working short signals. With
them it is obvious that **gold simply fell that month** — random shorts scored
1.16, and the best engineered signal only reached 1.20. Nearly all the apparent
edge was directional drift in the sample.

Skipping the baseline is how a month of trend gets mistaken for alpha. Report
the honest conclusion even when it is "no strong edge found".

## 4. Compiling MQL5 from the CLI

Write the `.mq5` into `MQL5/Experts/`, then compile with MetaEditor. The
invocation that works is running the binary from its own install directory with
an **absolute** source path:

```bash
cd "/c/Program Files/MetaTrader 5 EXNESS"
./MetaEditor64.exe /compile:"C:\Users\<user>\AppData\Roaming\MetaQuotes\Terminal\<HASH>\MQL5\Experts\MyEA.mq5" /log
```

- `/log` with no argument writes `MyEA.log` **next to the `.mq5`** — that file
  is UTF-16, decode it (`iconv -f UTF-16LE` or Python) to read errors.
- Success looks like `Result: 0 errors, 0 warnings, ... ms elapsed` and a fresh
  `MyEA.ex5` appearing beside the source.
- MetaEditor returns exit code 0 even when it compiles nothing, so **verify the
  `.ex5` exists and check its mtime** rather than trusting the exit status.

## 5. Design rules for a replacement EA

Derived from the autopsy above; these are the inversions that mattered.

| Failure in the old EA | Rule for the new one |
|---|---|
| SL 2.1× spread | ATR-based SL, floored at N× current spread **and** at `SYMBOL_TRADE_STOPS_LEVEL` |
| No TakeProfit input at all | Real TP as a multiple of measured risk (RR) |
| 1438 trades/day | Hard `MaxTradesPerDay` + cooldown after each close |
| Traded around the clock | Session filter from the measured hourly volatility profile |
| Unlimited concurrent positions | One position at a time; no grid, no martingale |
| No account protection | Daily-loss cap and an equity-drawdown halt |
| Fixed lots | Lot sized from a risk % against the actual stop distance |

Implementation notes that avoided broker rejections (`Invalid price` / 4756
dropped from ~1231 per run to **0**):

- Compute a `MinStopDist()` from `max(stops_level + margin, spread × 1.5)` and
  clamp every SL/TP against it, on entry *and* on every modify.
- Evaluate signals on the **closed** bar (`shift 1`) behind a new-bar gate;
  manage open positions on every tick.
- Never widen a stop — reject any modify that moves it the wrong way.
- Derive lots from `SYMBOL_TRADE_TICK_VALUE`/`TICK_SIZE`, not assumed pip value.

### Results (real ticks, $500, 1:2000, M15)

| Window | Balance | Net | Trades | Win% | PF | Max DD |
|---|---|---|---|---|---|---|
| 04 Aug (1 day) | $489.69 | −$10.31 | 1 | 0% | — | 2.1% |
| 06 Jul – 05 Aug | $448.40 | −$51.60 | 33 | 39.4% | 0.80 | 22.9% |
| 05 Jun – 06 Jul (OOS) | $635.40 | +$135.40 | 30 | 60.0% | 1.70 | 11.2% |

What genuinely improved: `Invalid price` 1231 → 0, TP hits 0 → 14, no account
blow-up in any window, worst drawdown 99.2% → 22.9%.

What did **not** get claimed: one window profitable and one not, 63 trades
total, and the baseline test had already shown no strong predictive edge. The
honest framing delivered was "this fixes the cost bleed and the risk control;
it does not predict" — with forward-testing on demo recommended over any
further backtest tuning.

Fixing survivability is a real, reportable win. Do not let it get dressed up as
a proven edge.
