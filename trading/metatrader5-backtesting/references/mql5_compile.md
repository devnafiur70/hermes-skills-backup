# Headless MQL5 compile (MT5 EA dev)

When you edit an `.mq5` EA, the `.ex5` must be recompiled or the terminal runs stale code.

## Command (Windows, from terminal tool)
```
"C:\Program Files\MetaTrader 5 EXNESS\MetaEditor64.exe" /compile:"<abs_path_to>.mq5" /log:"C:\Users\user\gh_lab\compile.log"
```
- Use a `timeout 120`/`-Wait` wrapper; `-compile` returns immediately but the log finishes a moment later.
- The log is **UTF-16 LE** (no BOM). Decode with `raw.decode("utf-16-le", errors="replace")` in Python, then grep for `Result:` / `error` / `warning`.

## Result line
`Result: 0 errors, 3 warnings, 921 ms elapsed, cpu='X64 Regular'` → exit code may be 1 even on success; trust the `Result:` line, not `rc`.

## Common warnings (cosmetic, safe to ship)
- **warning 181 implicit conversion 'number' to 'string'** on `PositionGetString(POSITION_SYMBOL) == _Symbol`: `_Symbol` is an enum. Fix by comparing against `Symbol()` (returns string) or a `string msym = Symbol();` variable, not `(string)_Symbol`.
- Unused `string cmt = "..."` locals: just delete them.

## Compile-quirk reminders (from EA dev)
- `trade.BuyStop(lot, price, sym, sl, tp)` — pass `sl`/`tp` as `0.0` for NO stop; the 6th `comment` arg triggers error 262, omit it. Pass `sym` as a `string` variable from `Symbol()`, not the `_Symbol` enum.
- After writing a new `.mq5`, confirm the `.ex5` mtime advanced before backtesting.
