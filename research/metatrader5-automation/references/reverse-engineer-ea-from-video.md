# Reverse-engineering an EA from a WhatsApp / screen recording

Verified workflow (Nafiur session, 2026-08-07). Goal: a 1:1 replica of an EA seen trading in a phone video — **no invented logic**.

## 1. Extract frames
Phone recordings are typically 720x1280, 30fps. 1 frame/sec is enough to catch pending-order triggers without exploding the file count.
```
mkdir -p "C:/Users/user/AppData/Local/hermes/cache/wa_frames"
ffmpeg -i "C:/Users/user/Desktop/WhatsApp Video ....mp4" -vf fps=1 "C:/Users/user/AppData/Local/hermes/cache/wa_frames/frame_%03d.png"
```
~30 frames for a 30s clip. Verify ffmpeg/ffprobe present first.

## 2. Read frames
For each frame, call `vision_analyze` with an exact-transcription prompt:
> Transcribe ALL text/numbers exactly: platform, symbol, timeframe, every pending order (type+price+lot), every open trade (type+lot+profit), current price. Note what changed vs the previous frame (order triggered? new trade opened? profit taken?).

Do not summarise — capture verbatim.

## 3. Store as TEXT, never images (hard user constraint)
Write the transcribed frame sequence into the Notion **Trading** DB as an analysis/notes row. Discard the PNGs. Never attach screenshots to the database.

## 4. Identify the mechanism from the sequence
The user's guess is often partially wrong. Worked example:
- User guessed: "two pending orders shuffle profit to each other."
- Frames showed: exactly **one running trade + one opposite pending STOP** at all times. When price hit the pending STOP, it became the new running trade and the prior trade closed at its profit.
- Real mechanism: **Stop-And-Reverse (SAR) flip**, not a two-pending grid.
Always state plainly when the user's mental model was off.

## 5. Build the MQL5 EA (same-to-same)
Replicate ONLY observed behaviour:
- 1 running trade + 1 opposite pending STOP (Buy Stop above when running BUY, Sell Stop below when running SELL).
- No SL/TP if none were visible in the video.
- Fixed lot size as seen (e.g. 0.01).
- Add NOTHING extra (no hidden TP, no martingale, no filter) beyond what the frames showed.

Pattern skeleton:
```
CTrade trade;
#define MAGIC 20260807
int OnInit(){ trade.SetExpertMagicNumber(MAGIC); return INIT_SUCCEEDED; }
// OnTick: if 0 running + 0 pending -> open first BUY at market, place SELL STOP above.
// if 1 running + 1 pending -> on flip (pending triggered / 2 running) close oldest, keep 1 running, place opposite pending.
```
Compile via MetaEditor CLI. Error 262 `cannot convert enum` on `trade.BuyStop/SellStop`: drop the 6th `comment` arg (call `trade.BuyStop(vol,price,sym,sl,tp)`).

## 6. Backtest
On this Windows environment the headless launcher (`terminal64 /autotest`, `metatester64 /test`) hangs in a non-interactive shell and never runs (see metatrader5-backtesting Pitfalls: `headless_launch_hang`). Reliable path:
- `cp` the compiled `.ex5` (and `.mq5`) into the target install's `MQL5/Experts/`.
- Run the Strategy Tester **in the MT5 GUI** (or have the user run it) on the correct symbol (XAUUSDm) with Real Ticks (Model=4).
- Do NOT present a backtest you could not actually execute.

## 7. Report
Lead with whether the mechanism matched the user's guess, the exact observed cycle, and the honest caveat that a 1-day/sample backtest is not proof. Offer the GUI backtest as the next step if headless failed.
