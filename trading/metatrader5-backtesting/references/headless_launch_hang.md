# Headless MT5 backtest launch — observed failure (2026-08-07)

## What was tried (all hung / produced nothing)
1. `metatester64.exe /test:"<profile>/MQL5/Profiles/Tester/FlipSAR_test.ini"`
   → process exited ~immediately, no journal, no report. (GUI subsystem, no console output.)
2. `terminal64.exe /autotest:"<ini>"` (ini has `[Tester]` + absolute `Report=` + `ShutdownTerminal=1`)
   → GUI opened, ~140 MB RAM, ran 10+ min, NO `Tester/logs` line, NO `Experts/<EA>.log`, NO report.
3. `terminal64.exe /autotest` (no path; `[Tester]` patched into `terminal.ini` with `DateFrom`/`DateTo` epoch)
   → same hang.
4. Python `mt5.tester_set(...)` + `mt5.tester_run()` on `MetaTrader5` 5.0.6090
   → `AttributeError: module 'MetaTrader5' has no attribute 'tester_set'`.

## Symptom that the run never started
After launch, check (do NOT just wait):
- `Tester/logs/YYYYMMDD.log` has no new entry for today
- `MQL5/Experts/<EA>.log` not created
- no `Report=` html/xml written
If all three are absent after a few minutes, the test is NOT running — it is a hung GUI window.

## What actually worked
- Compile EA with MetaEditor (`MetaEditor64.exe /compile:...` → verify the `.ex5` mtime, ignore exit code).
- `cp` the `.ex5` + `.mq5` into the target install's `MQL5/Experts/`.
- Run the Strategy Tester manually inside the MT5 GUI (user-driven) — reliable path when headless launch hangs.

## Environment facts
- Exness backtest install: `D0E8209F77C8CF37AD8BF550E51FF075` (base `Exness-MT5Trial14`), has `XAUUSDm` July-2026 ticks.
- `53785E099C927DB68A545C249DBCE06` (base `Default`) has XAUUSD history only, no ticks → `Model=4` impossible there.
- Symbol on Exness = `XAUUSDm` (video showed `XAUUSD-ECN`; Exness uses the `m` suffix).
- `metatester64.exe` orphaned GUI processes may resist `taskkill /F` ("Access is denied") from the agent shell — they live in another session; ask the user to close MT5 manually if needed.
