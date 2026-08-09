# Resetting MT5 to a clean state (delete profile data, fresh login)

When the user wants to wipe MT5 and re-login (e.g. "remove all profile data, I'll log in again"):

## What a "profile" is
- `C:\Users\user\AppData\Roaming\MetaQuotes\Terminal\<HASH>\` = one account/profile (data folder).
- One MT5 *program* (`C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe`) can serve many profiles — each broker/login gets its own `<HASH>` folder. "Two MT5 apps" is usually just two profiles of one app.
- `origin.txt` inside each `<HASH>` (UTF-16 LE) records which install created it:
  `python -c "print(open(r'<dir>\origin.txt','rb').read().decode('utf-16',errors='ignore'))"`
- `Common/` and `Community/` are shared, not profiles — leave them.

## Steps
1. **Backup the EA first.** The EA (`.ex5`/`.mq5`) lives inside the profile you're about to delete. `cp` it somewhere safe (e.g. `C:\opt\trading-bot\`) before deleting.
2. Kill any running `terminal64.exe` / `metatester64.exe`.
3. `rm -rf` the unwanted `<HASH>` folders.
4. **A default profile may auto-recreate** on next MT5 launch (it did here — `53785E09...` came back). Just `rm -rf` it again while no MT5 process is running.
5. User logs in fresh in the MT5 GUI; a new `<HASH>` appears and real-tick data downloads from the server over time.

## Verified (2026-08-07)
- Removed `53785E09...` and an Exness profile; default recreated once; removed again; left only `Common`/`Community`.
- EA safely preserved in `C:\opt\trading-bot\FlipSAR_EA.ex5` + `.mq5`, then re-copied into the new login's `MQL5/Experts/`.
- Account used afterward: login `414110344`, server `Exness-MT5Trial6`, symbol `XAUUSDm`.
