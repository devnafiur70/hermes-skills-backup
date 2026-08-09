# Grid EA lessons from SafeGrid family backtests (XAUUSDm, 2026-08)

Empirically tested variants on 30-day real ticks (2026.07.07-08.06, $500, M5):
- C  no-SL + harvest(100)        -> -100% (stop-out by 07.14)
- B  no-SL + tight harvest(35) + DD halt 10% -> -100% (stop-out by 07.14)
- A  SL + harvest(100)           -> -7.6% (survived, $462)
- A2 SL + wide step(ATRx1.5) + harvest(20) + DD halt 8% -> -7.0% (survived, $465)
- A3 SL + wide step + harvest(50) + net target +20% + lot 0.10 + daily halt OFF
                              -> -98.4% (stop-out day 1, $7.97)

## Key findings
1. **No-SL dual pending grid blows up on XAUUSD.** Gold's volatility gaps
   against the grid before any harvest; with no SL the account stop-outs.
   SL (per-order, = grid step) is mandatory to merely survive.
2. **The harvest / OCO logic NEVER fired in any variant (0 triggers).** Root
   cause: the EA hits the daily-loss halt on day 1 (price gaps adverse before
   any open leg reaches even +20pts profit), `eaHalted` stays true forever (no
   reset), so it never trades again. Harvest threshold is irrelevant while the
   daily-loss halt fires first.
3. **Surviving != profitable.** A/A2 survived only because halted-forever EA
   let already-open positions "ride" to a favorable close. That is luck of the
   day's trend, not a strategy edge. Net ~ -7%.
4. **`eaHalted` has no reset** -> once halted, dead for the rest of the test.
   If you want the EA to keep trading, reset `eaHalted=false` at the start of
   each new day in `ResetDayIfNeeded()`, or replace the permanent halt with a
   timed cooldown.
5. **A3 proves aggressive growth settings DESTROY the account faster.** Removing
   the daily-loss halt + raising lot to 0.10 (to chase +$100/day on $500) made
   it stop out on day 1 for -98%. Pushing lot up to hit a +20%/day target just
   accelerates the blow-up on the first adverse day. **+20%/day on a grid with
   no directional edge is mathematically impossible without eventually blowing.**

## USER VERDICT (durable — Nafiur, 2026-08-06) — READ THIS BEFORE JUDGING ANY EA
The user's explicit goal is **equity growth**, NOT "survive at a smaller loss".
He CORRECTED the "Plan A survived so it's best" framing: *"surviving at a loss
is NOT acceptable; growing equity is better."* Therefore:
- Judge every EA / trade by **daily equity growth**, never by "lower drawdown"
  or "it didn't blow up". A -7% result is a FAILURE to him, not a win.
- Do NOT present "it only lost 7% instead of 100%" as a positive. State plainly
  that equity did not grow and the strategy failed his goal.
- The grid family cannot meet his +$100/day (+20%) target; pivot to a
  **trend-following** approach (he has an NRTR channel indicator in his
  Indicators folder) which has a real directional edge and can grow equity.

## Next-attempt build recipe (agreed 2026-08-06, not yet built)
User said he'll build a NEW EA next day after resting (he was ill). When he
returns, the agreed direction is **trend-following, NOT a grid**:
- Use the NRTR channel indicator in his `MQL5/Indicators/` folder (MTF
  NRTR). Build an EA that trades breakouts/reversals off the NRTR line with a
  per-trade SL + a trailing stop, so equity compounds on trends instead of
  bleeding on chop.
- If he still wants a grid, FIRST fix the `eaHalted` reset (step 4 above) and
  REMOVE the permanent daily-loss halt, then re-test — but expect the same
  no-edge outcome; the math does not favor it.
- Re-run the SAME 30-day window (2026.07.07-08.06, $500) and judge ONLY by
  daily equity growth. Any variant that ends below $500 is a FAILURE.
