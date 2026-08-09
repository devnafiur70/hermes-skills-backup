# MT5 Backtest Date-Window: VERIFIED two-fix recipe (2026-08-06)

## Symptom: test "passes" in ~2s, no result
Tester log segment (UTF-16LE, `Tester/logs/YYYYMMDD.log`) shows a run whose
first AND last timestamp are both `YYYY.MM.DD 00:00:00`, no `final balance`
line, no `N ticks, M bars generated` line. The EA's OnInit message prints and
orders may even be placed at 09:00, then `Test passed in 0:00:0X` — a zero-length
window.

## Root cause (both are real)
1. Launcher `.ini` not UTF-16 LE + BOM -> MT5 ignores FromDate/ToDate.
2. EVEN with BOM, `config/terminal.ini` -> `[Tester] DateFrom`/`DateTo`
   (Unix epoch seconds, UTC) can be 0 (zeroed by a prior aborted run whose
   `ShutdownTerminal=1` rewrote terminal.ini on exit). MT5 then runs a
   00:00->00:00 window. The BOM fix alone does NOT repair a zeroed terminal.ini.

## Fix (apply both)
### Fix 1 — BOM launcher
Write the launcher `.ini` with:
```
open(out,"wb").write(b"\xff\xfe"); f.write("\r\n".join(lines).encode("utf-16-le"))
```
Use `scripts/make_backtest_ini.py` (it does this). Verified: 1-day runs work
with BOM alone.

### Fix 2 — patch terminal.ini when window is broken
Kill stray `terminal64.exe`, then:
```
python scripts/patch_terminal_ini_dates.py 2026.07.07 2026.08.06
```
This rewrites `DateFrom`/`DateTo` to
`int(datetime(Y,M,D,0,0,0,tzinfo=utc).timestamp())` (e.g. 07.07 = 1783382400,
08.06 = 1785974400). Verify the VERIFY lines print the epochs. THEN launch.
Confirmed: SLA2 only produced a real 30-day result (6.4M ticks / 6072 bars /
final balance 465.04) AFTER this patch — the BOM-only launch aborted at
00:00->00:00.

## Detection after a launch
Grep the log for `SafeGrid_<EA>.ex5 from YYYY.MM.DD 00:00 to YYYY.MM.DD 00:00`
and the trailing `final balance N NN.NN USD` + `N ticks, M bars generated`.
- 2s test / 00:00->00:00 => window broken => re-patch terminal.ini + relaunch.
- Test ends early at a blow-up date with FEWER bars (e.g. 1385) AND a
  `stop out occurred` line => NORMAL. The EA blew up; that IS the result.
  Do NOT mistake this for a broken window.

## Notes
- Log file is named for the EXECUTION day, not the backtest day. A test of a
  past date lands in today's `YYYYMMDD.log`.
- `ShutdownTerminal=1` rewrites terminal.ini on exit; re-verify the window
  before each launch when a prior run may have aborted.
- Wrap launches in `timeout 150` so a hung/non-running test can't wedge the
  session (`-Wait` never returns if no test starts).
