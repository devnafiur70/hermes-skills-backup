---
name: telegram-clean-delivery
description: "Clean Telegram channel delivery from Hermes cron jobs."
---

# Telegram Clean Delivery (Hermes cron → Telegram)

## When to use
- Setting up automated Telegram delivery (news, weather, alerts) via a Hermes `cronjob`.
- The user reports their Telegram message contains "Cronjob Response:", a `job_id`, or "To stop or manage this job..." text. These are Hermes system wrappers, NOT your content.
- Delivering to a **channel that has other members** — the user does NOT want internal/technical info visible to them.

## The trap (what leaks)
When a Hermes cron job has `deliver` set to a Telegram target (user or channel) and the job runs an **LLM agent** (the default), Hermes wraps the output with:

```
Cronjob Response: <job_name>
(job_id: <job_id>)
-------------

<agent output / script output>

To stop or manage this job, send me a new message (e.g. "stop reminder <job_name>").
```

If the job is an LLM-agent job, the agent may ALSO append its own technical status summary (e.g. "⚙️ Pipeline status, Sir: ... DRY-RUN ..."). Both are unwanted in a member-visible channel. See `references/cron_wrapper_anatomy.md`.

## The clean pattern (NO wrapper)
Run the job as a **script-only** cron job so Hermes delivers ONLY the script's stdout verbatim — and configure the script to send to Telegram itself via the Bot API. This bypasses the agent summary AND the Cronjob Response wrapper.

1. Write a Python script that sends via Bot API, reading creds from env:
   ```python
   import os, requests
   TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
   CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")   # channel id e.g. -1004382793117
   # ... build clean message text only ...
   requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                 json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
   ```
2. Create the cron job with `no_agent=True` and `deliver: local` (so Hermes does NOT re-send / wrap anything):
   - `no_agent=True` → only the script runs; stdout is NOT wrapped as a Cronjob Response.
   - `deliver: local` → Hermes doesn't auto-post the job result anywhere; the script does the posting.
3. Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are present in the **cron job's environment**. If missing, the script silently DRY-RUNs and sends nothing.

## Pitfalls
- **Double-send:** never combine `deliver: <telegram target>` WITH a script that also posts via Bot API — you'll get the wrapper AND a clean copy. Use `deliver: local` + script send, OR `deliver: <target>` + agent — not both.
- **DRY-RUN with no error:** if the channel stays empty after a run but logs say "DRY-RUN", the env vars aren't in the cron environment. That is the #1 cause.
- **Channel id format:** private channels use a `-100` prefix (e.g. `-1004382793117`). A wrong id yields "Chat not found". The bot must be an admin of the channel.
- **`print()` to Telegram:** in script-only mode the script's stdout IS the delivered message. Do NOT `print()` debug/status lines — log to a file instead, or they leak into the channel.
- **User-owned skill note:** the user's `deliver-telegram-tech-news` and `daily-weather-briefing` skills already contain the per-job send logic. They were created at the user's request, so they are user-owned — to embed this fix there, recommend `hermes curator adopt <name>` rather than editing directly.

## Channel vs DM
- The user tolerates the Hermes wrapper in their OWN DM (`origin`) but NOT in a member-visible channel. Prefer the script-only pattern for any channel delivery.
