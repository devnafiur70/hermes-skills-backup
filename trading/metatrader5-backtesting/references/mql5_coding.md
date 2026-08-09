# MQL5 coding notes (Nafiur MT5 / Exness XAUUSDm)

## Compile quirks (cost real debugging time — captured here)
- **`trade.BuyStop(vol, price, sym, sl, tp, comment)` → error 262 "cannot convert enum".**
  Drop the `comment` (6th) arg: `trade.BuyStop(vol, price, sym, sl, tp);` OR build `MqlTradeRequest` manually. The comment overload collides with an enum resolution in this MetaEditor build.
- Pass symbol as `string sym = Symbol();` (a variable), NOT the `_Symbol` enum literal, inside the call. Mixing `_Symbol` into CTrade calls triggers enum errors.
- `PositionGetString(POSITION_SYMBOL) == _Symbol` → warning 181. Cast: `== (string)_Symbol` or compare to a `string sym` var. Harmless but pollutes compile output.
- Set files written to `MQL5\Profiles\Tester\` MUST be UTF-16 LE **with BOM** (`\xff\xfe`). Without BOM the tester reads empty/garbage inputs and optimizations abort with "no optimized parameter selected".
- Set-file input format: `Name=Value||def||start||step||stop||flag` where flag is `N` (normal) or `O` (optimize). Example: `LotSize=0.01||0.01||0.001||0.1||N`.

## Safe-grid EA skeleton (validated: SafeGrid_NR_v1.ex5)
Dual-side pending grid, mirrors a screenshot/video the user sent, but hardened:
- Rebuild grid on new bar during session: N Buy Stops above ask (step apart) + N Sell Stops below bid, each carrying its own SL+TP.
- `GridStep`: ATR-based (`InpGridStepAtrMult`) floored by `InpMinStepPoints`; or fixed points.
- Per-order SL = `GridStep * InpSlMult` (floored by broker MinStopDist). TP = RR×SL or N×step.
- Hard cap: `CountPending()+CountOpen() <= InpMaxOrdersTotal` (e.g. 5) before placing each leg.
- Equity-based lot: `riskMoney = balance*RiskPercent/100; lot = riskMoney / ((slDist/tick)*tickValue)` then `NormLot`.
- `OnTick`: `ManageOpenPositions()` first (attach missing SL), then guards.
- Guards: peak-equity drawdown halt (`InpMaxDDPct`), daily-loss halt (`InpMaxDailyLossPct`), net-target reconstitute (`InpNetTargetPct`), session filter, spread guard.
- `CloseAll(inclPending)`: closes positions then (if true) deletes pending orders. Called on halt / net-target / daily reconstitution hour (`InpReconHour`) so no orphaned orders remain.
- Magic number per EA (GoldSniper 880821, SafeGrid 880822) so multiple EAs don't clash.

## EA selection / hygiene
- Check for stray live EAs on the demo account before running tests: `positions_get()` via the `MetaTrader5` python pkg. Nafiur had an unrelated grid/martingale EA (magic 1234567, no SL) running — flag it.
- Always verify a single known run against the `.opt`/log parser before trusting bulk optimization numbers.
