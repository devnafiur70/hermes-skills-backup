---
name: metatrader5-automation
description: "MT5 via Python: accounts, EA backtests, log parsing."
version: 1.0.0
metadata:
  hermes:
    tags: [metatrader5, mt5, forex, trading, backtest, expert-advisor, xauusd, exness, strategy-tester]
---

# MetaTrader 5 Automation

Use when the user asks to connect to MetaTrader 5, read account state or open
positions, backtest an Expert Advisor (EA), analyse trade history, or evaluate a
strategy's performance.

Two independent channels, and **they conflict**:

| Channel | Use for | Requires |
|---|---|---|
| `MetaTrader5` Python package | live account, symbols, ticks, candles, positions | terminal RUNNING, logged in |
| `terminal64.exe /config:<ini>` | headless Strategy Tester backtests | terminal CLOSED first |

Never try to run a `/config:` backtest while the Python bridge session (or a
normal terminal window) is open — close the terminal, run the test, relaunch.

## Setup

```bash
pip install MetaTrader5 pandas
```

The package is **Windows-only and 64-bit-only**. Verify the interpreter matches:

```bash
python -c "import platform; print(platform.architecture()[0])"   # want 64bit
```

## Live connection

```python
import MetaTrader5 as mt5
if not mt5.initialize():
    print("INIT FAILED:", mt5.last_error()); raise SystemExit(1)
print(mt5.terminal_info()._asdict())
print(mt5.account_info()._asdict())
mt5.shutdown()
```

All the `*_info()` calls return namedtuples — `._asdict()` makes them printable.

### Resolve the symbol name — never hardcode

Brokers add suffixes per account type. Exness "Standard" uses **`XAUUSDm`**, not
`XAUUSD`. Probe candidates and select the symbol into Market Watch:

```python
for c in ["XAUUSD", "XAUUSDm", "XAUUSD.", "GOLD"]:
    si = mt5.symbol_info(c)
    if si:
        if not si.visible:
            mt5.symbol_select(c, True)
        symbol = c
        break
```

Then read `trade_contract_size` (gold = 100 oz/lot), `digits`, `point`,
`volume_min`, and `spread` from `symbol_info()` before computing anything in
money terms. Do not assume contract size.

### `trade_allowed: False` is normal and good

That means the terminal's **Algo Trading** button is off. You can read
everything and place nothing. Treat it as the desired default: report it to the
user, do not instruct them to switch it on unless they explicitly ask to
automate execution.

## Headless backtest

Write an ini and launch the terminal with it. `ShutdownTerminal=1` makes the
process exit when the test finishes, so you can wait on it.

```ini
[Tester]
Expert=<EA filename>.ex5
Symbol=XAUUSDm
Period=M1
Login=<account>
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

`Model` values: `0` every tick, `1` control points, `2` open prices,
`4` **every tick based on real ticks** (the accurate one — use it when asked
for real ticks).

### Tick model is also a diagnostic

Running the *same* EA under `Model=4` and `Model=0` and comparing is one of the
cheapest high-value tests available. A large gap means the strategy depends on
intrabar microstructure and its apparent edge is an artefact; a small gap means
its stops are wide relative to spread. One session saw the identical EA, day and
inputs go **$1.85 (real ticks) vs $840.25 (generated)** — an $838 swing from the
tick source alone. That mechanism is also how vendors produce great-looking
backtests for worthless EAs, so ask which model a seller's screenshot used.

Report both, and always label the real-tick figure as the honest one. Never let
a generated-tick number stand as the verdict. See
`references/tick-model-and-ea-authoring.md`.

### Price the spread before blaming direction

For any high-frequency EA, compute the cost bill before theorising about signal
quality: `round_trips × median_spread × point × contract_size × lot`. In the
worked case that was **$345 of a $498 loss — 69% pure spread**. Express the EA's
stop and trail as *multiples of spread* (a $0.20 trail against a $0.24 spread is
unwinnable before a tick is simulated); that one ratio diagnoses most scalper
EAs faster than any equity curve.

`Expert=` is relative to `MQL5/Experts/`. Find the EA and confirm which data
directory belongs to the target install:

```bash
find "$APPDATA/MetaQuotes" -iname "*<EA name>*"
# Multiple Terminal/<HASH>/ dirs are normal (one per install).
# origin.txt holds the install path — it is UTF-16, so decode it:
python -c "print(open(r'<dir>\origin.txt','rb').read().decode('utf-16',errors='ignore'))"
```

Launch:

```bash
powershell -NoProfile -Command "Start-Process -FilePath '<...>\terminal64.exe' -ArgumentList '/config:C:\path\test.ini'"
```

### When the terminal opens normally instead of testing

A `/config:` launch that connects to the account and then just *sits there* —
no `Tester` lines in `Tester/logs/`, no `automatic testing started` — means MT5
rejected the ini and fell back to a normal session. Include `Report=`,
`ReplaceReport=1` and `ExecutionMode=0` in the `[Tester]` block; inis carrying
those keys ran reliably in this session while stripped-down ones silently
opened a normal window.

Also **run one test per launch**. Chaining several `/config:` launches in a
shell loop had later iterations open normally rather than test, even with
identical inis. Kill the terminal, launch one test, wait for exit, then start
the next.

Diagnose by grepping the terminal log for `automatic testing started` and the
tester log for `testing of Experts\<EA>`. Absence of both = the run never
happened; do not go hunting for a bug in the EA.

## Discovering an EA's input parameters

`.ex5` files are compiled and compressed — string extraction yields nothing
useful (typically a lone `Copyright` line). Do not waste time on it.

Instead: **run the EA once**, and MT5 auto-writes every input with its default
value to

```
%APPDATA%\MetaQuotes\Terminal\<HASH>\MQL5\Profiles\Tester\<EA filename>.set
```

That file is UTF-16-LE. Decode it and you have the full input list:

```python
print(open(setpath, 'rb').read().decode('utf-16-le'))
# LotSize=0.01||0.01||0.001000||0.100000||N
# GapPips=50||50||1||500||N
```

Format is `Name=value||start||step||stop||optimize_flag` where the flag is `Y`
or `N`. The tester log for each run also echoes the inputs actually used
(`GapPips=50` etc.) — use that to confirm a run really got the settings you
intended.

Read the input list before theorising. An EA with **no TakeProfit input** can
only realise profit via trailing stop; that single fact explains a run with
hundreds of SL hits and zero TPs.

## Optimization runs

```ini
[Tester]
Expert=<EA filename>.ex5
ExpertParameters=<name>.set
Model=4
Optimization=1
OptimizationCriterion=0
ShutdownTerminal=1
```

- `ExpertParameters` must be a **bare filename**, and the `.set` must live in
  `MQL5/Profiles/Tester/`. A path here fails.
- Keep `Model=4` when the user asked for real ticks — optimization does not
  change that requirement.
- Mark each parameter to sweep with the `Y` flag and give sane `start||step||stop`.
- Passes = product of the swept ranges. Roughly 1.5–3 s per pass on 24 h of M1
  real ticks, parallel across cores.

### The BOM pitfall (silent failure)

A `.set` written as UTF-16-LE **without** the `\xff\xfe` byte-order mark is
silently unreadable to MT5. The terminal starts, logs

```
no optimized parameter selected, please check input(s) to be optimized
and set start, step and stop values
```

and exits in ~2 seconds. Always prepend the BOM:

```python
open(path, 'wb').write(b'\xff\xfe' + content.encode('utf-16-le'))
```

A tester run that exits in a couple of seconds having done nothing is almost
always this, a bad `ExpertParameters` reference, or a missing EA file — check
`Tester/logs/` before assuming the EA is at fault.

### Reading the `.opt` results cache

Optimization results land in a binary cache:

```
%APPDATA%\MetaQuotes\Terminal\<HASH>\Tester\cache\<EA>.<SYM>.<TF>.<from>.<to>.<n>.<HASH>.opt
```

Records are fixed-stride structs. Locate the first record by scanning for the
deposit value as a little-endian double, then confirm the stride by finding the
next occurrence:

```python
for off in range(0, 4000):
    if abs(struct.unpack_from('<d', raw, off)[0] - deposit) < 1e-6:
        print(off)          # candidate record starts
```

**Never report `.opt` numbers off a guessed field mapping.** Field offsets are
not documented and adjacent doubles are easy to confuse — in one session
`gross_loss` was misread as `final_balance`, turning a −$393 loss into a
fabricated +$172 profit. The mandatory check: take the top row, re-run it as a
single `Optimization=0` backtest with those exact inputs, and confirm the log's
`final balance` matches your parsed value. Only then quote the table.

A mapping verified against MT5 build 6090 (stride 304) is recorded in
`references/ea-input-optimization.md`, along with the sanity-check recipe.

## Reading results — parse the log, not the report

The `Report=` ini key is unreliable. The authoritative record is the tester log:

```
%APPDATA%\MetaQuotes\Terminal\<HASH>\Tester\logs\YYYYMMDD.log
```

**These logs are UTF-16-LE.** `cat`/`tail` return interleaved-null garbage. Always:

```python
txt = open(path, 'rb').read().decode('utf-16-le', errors='ignore')
lines = [l.strip() for l in txt.splitlines() if l.strip()]
```

`scripts/parse_mt5_tester_log.py` does the whole extraction — pass it the log
path and it prints deposit, final balance, round-trip stats, win rate, profit
factor, SL/TP counts, order-rejection counts, and the blow-up timestamp.

Key lines to pull: `initial deposit`, `final balance`, `deal #N buy|sell ... done`,
`stop loss triggered`, `take profit triggered`, `not enough money`,
`Invalid price`, and the `N ticks, M bars generated` summary.

Round trips = deals paired in sequence (entry, exit). P/L per trade:

```python
pl = (exit_price - entry_price) * contract_size * volume   # buy
pl = (entry_price - exit_price) * contract_size * volume   # sell
```

That is price-only — it excludes spread, commission and swap, so state that
caveat when you quote it, and prefer `final balance - deposit` as the headline.

## Interpreting a result honestly

**"Test passed successfully" only means the run completed.** It says nothing
about profitability. A blown account also "passes". Always read final balance.

Diagnostics that separate a bad run from a broken strategy:

- **Zero TP hits with hundreds of SL hits** — structural, not bad luck.
- **SL distance vs spread.** Compare the EA's stop distance to
  `symbol_info().spread * point`. A $0.50 stop against a $0.24 spread means half
  the stop is consumed at entry; on gold's M1 noise it cannot survive.
- **`Invalid price` / error 4756 in bulk** — the EA is placing orders inside the
  broker's minimum stop distance; it is incompatible with this broker's spec.
- **Required win rate.** `avg_loss / (avg_win + avg_loss)`. If the EA needs 70%
  and delivers 26%, the edge is negative by arithmetic, not by variance.
- **Trades per hour.** Triple-digit daily counts on M1 usually means the system
  is churning inside the spread.
- **Post-blowup noise.** After the balance dies, logs fill with `not enough
  money`. Count trades only up to the collapse; report the collapse time.

### Optimization results are not findings until walk-forward validated

**An optimized result on the same window you optimized over is worthless.**
Sweeping N combinations and reporting the winner is curve-fitting: with 168
passes over one day, the top row is fitting that day's noise, not an edge.

This is not optional extra rigour — it is the step that decides whether the
number you are about to show the user is real. The workflow:

1. Optimize over window A.
2. Take the best combination and run it **unchanged** on 3+ other windows.
3. Report the out-of-sample results with equal prominence to the in-sample one.

A real session outcome, best-of-168 on 04 Aug then replayed:

| Date | Net | Win% | PF |
|---|---|---|---|
| 04 Aug (optimized) | **+$39** | 66.7% | 1.21 |
| 03 Aug | −$70 | 56.6% | 0.72 |
| 31 Jul | −$103 | 55.8% | 0.57 |
| 30 Jul | −$113 | 57.6% | 0.74 |

In-sample profit, out-of-sample loss on every single window. Presenting only
the first row would have been actively misleading.

Also watch **win rate vs payoff asymmetry**: 66.7% wins looks strong, but with
avg win $2.31 against avg loss $3.82 the system needs ~62% just to break even,
so it is one bad session from negative. Always compute the required win rate
(`avg_loss / (avg_win + avg_loss)`) and compare it to the achieved one.

If tuning inputs cannot produce out-of-sample profit, say plainly that the
problem is the strategy logic, not the settings. Structural defects
(zero TPs, bulk `Invalid price` rejections) persist across every parameter set —
note when a defect survives optimization, because that is proof it is not a
tuning issue.

## Writing a replacement EA

When the user asks for a new/better EA, do the analysis first — an EA written
before the autopsy just reproduces the same failure with different constants.

### Search for an edge with a baseline control

Score candidate signals by MFE/MAE (max favourable vs adverse excursion over a
fixed horizon, in ATR units) and **always include a no-logic baseline row** in
the same table. In one session random shorts scored 1.16 while the best
engineered signal reached only 1.20 — the "edge" was almost entirely that gold
fell that month. Without the control that table looks like a pile of winning
signals. Report "no strong edge found" when that is the answer.

### Compile from the CLI

```bash
cd "/c/Program Files/MetaTrader 5 EXNESS"
./MetaEditor64.exe /compile:"C:\...\MQL5\Experts\MyEA.mq5" /log
```

Run the binary from its install directory with an **absolute** source path.
`/log` writes `MyEA.log` beside the source (UTF-16 — decode it). MetaEditor
exits 0 even when it compiles nothing, so verify the `.ex5` exists and check its
mtime rather than trusting the exit code.

### Design rules that came out of the autopsy

ATR-based stops floored at both N× spread and `SYMBOL_TRADE_STOPS_LEVEL`; a real
TP as a multiple of measured risk; a hard trades-per-day cap plus cooldown; a
session filter from the measured hourly volatility profile; one position at a
time; daily-loss and equity-drawdown halts; lots sized from risk % against the
actual stop distance using `SYMBOL_TRADE_TICK_VALUE`. Clamping every SL/TP
against a computed `MinStopDist()` took `Invalid price` rejections from ~1231
per run to **0**.

Full rationale, the results table, and the honest-framing example are in
`references/tick-model-and-ea-authoring.md`.

**Report a rewrite honestly.** Fixing survivability (no blow-ups, drawdown
99.2% → 22.9%, TP hits 0 → 14) is a genuine win and worth stating plainly — but
if one window is profitable and another is not on ~60 trades, it is not a proven
edge, and the baseline test may already have shown no edge exists. Say what was
fixed (cost bleed, risk control, broker compatibility) and what was not
(prediction). Recommend demo forward-testing over further backtest tuning.

### Reporting

Lead with the number that matters (final balance / % change), then the stats
table, then *why*. Be direct when a strategy is destructive — this protects real
money and is the whole point of the exercise. Also be fair about sample size: a
single-day backtest is not proof on its own, so say so explicitly, while noting
which findings (zero TPs, mass order rejections) are structural rather than
sample-limited. Offer concrete next steps (longer window, altered inputs,
different EA) rather than ending on the verdict.

Never recommend live deployment off a backtest, and never place or modify orders
on a live/demo account unless the user explicitly asks.

## Pitfalls

- Python bridge and `/config:` tester **cannot run simultaneously** — close the
  terminal between them.
- Tester logs, `origin.txt` and `.set` files are **UTF-16**; decode explicitly.
- A `.set` file **must** carry the `\xff\xfe` BOM or MT5 silently ignores it and
  the optimization exits with "no optimized parameter selected".
- `ExpertParameters=` takes a bare filename from `MQL5/Profiles/Tester/`, not a path.
- Don't try to read inputs out of a compiled `.ex5` — run it once and read the
  auto-generated `.set`.
- Never quote `.opt` cache numbers without re-running the top row as a single
  backtest to confirm the field mapping.
- Never present an in-sample optimization winner without out-of-sample runs.
- Symbol suffixes differ per broker/account (`XAUUSDm`) — always probe.
- `Report=` may silently produce nothing; parse the log instead.
- Multiple `Terminal/<HASH>/` folders exist; confirm via `origin.txt` before
  assuming which install holds the EA.
- Don't equate a 0 exit code or "successfully finished" with a good outcome.
- A `/config:` launch that opens a normal terminal window ran **no test** — add
  `Report=`/`ReplaceReport=1`/`ExecutionMode=0` and launch one test per process.
- MetaEditor exits 0 even when it compiles nothing — verify the `.ex5` exists.
- Don't report a generated-tick (`Model=0`) result as the verdict; it flatters
  spread-sensitive EAs enormously. Compare against `Model=4` and lead with that.
- Don't score candidate signals without a no-logic baseline row — a trending
  sample makes random entries look like an edge.
- When a parsed log shows a negative balance, a `([\d.]+)` regex silently misses
  it. Match `(-?[\d.]+)` — accounts can finish below zero.

## Files

- `scripts/parse_mt5_tester_log.py` — decode a UTF-16 tester log and print full stats.
- `references/gold-hunter-v8-case-study.md` — worked example: a 24h real-tick run
  that blew a $500 account, with the exact numbers and diagnosis.
- `references/ea-input-optimization.md` — full optimization recipe: reading EA
  inputs from `.set`, the BOM requirement, verified `.opt` binary field mapping
  (build 6090), and the walk-forward validation that overturned an in-sample win.
- `references/tick-model-and-ea-authoring.md` — real vs generated ticks as a
  diagnostic ($838 swing on one EA), spread-cost quantification, MFE/MAE edge
  search with baseline controls, MetaEditor CLI compilation, and the design
  rules + honest reporting for a replacement EA.
