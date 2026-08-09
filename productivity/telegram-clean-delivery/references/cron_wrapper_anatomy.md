# Hermes Cron Telegram Wrapper — Anatomy

## What the user complained about (verbatim copy from a member-visible channel)
```
Cronjob Response: daily-weather-pipeline
(job_id: 0c40f69a4dcf)
-------------

🌤 আজকের আবহাওয়া (কুষ্টিয়া):
Light rain shower, তাপমাত্রা: 28°C (অনুভূত: 33°C)।

⚠️ বৃষ্টি/ঝড়: বাইরে বের হলে রেইনকোট বা ছাতা সাথে রাখুন। আর্দ্রতা 84% — ভ্যাপসা গরম অনুভূত হতে পারে।

📅 আগামীকাল: Light rain shower, সর্বোচ্চ 31°C (সন্ধ্যায় বজ্রবিদ্যুৎসহ হালকা বৃষ্টির সম্ভাবনা)।

To stop or manage this job, send me a new message (e.g. "stop reminder daily-weather-pipeline").
```

## Where each piece comes from
- `Cronjob Response:` + `job_id:` + `-------------` + `To stop or manage this job...`
  → Hermes platform wrapper, added to ANY cron delivery to a Telegram target when the job runs an LLM agent (default `no_agent=False`).
- The weather/tech-news body → the script/skill output, which is fine.
- Extra `⚙️ Pipeline status, Sir: ... DRY-RUN ...` type text (seen on the news job)
  → the LLM agent's OWN status summary appended on top of the wrapper. Also unwanted in a channel.

## Why it happened here
The daily-weather-pipeline job had `deliver: origin` and was an agent job, so Hermes wrapped the result. Same for tech-news-master-pipeline before its delivery target was changed to the channel id — the wrapper travelled with it.

## Fix applied
Convert the job to script-only (`no_agent=True`) with `deliver: local`, and let the Python script post via Bot API. This removes BOTH the platform wrapper and any agent status chatter. Env vars `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` must live in the cron job's environment or the script DRY-RUNs silently.

## Channel id note (real error from session)
User supplied `-1004382793117` but the id was stored as `-1001004382793117` (double `100`). Wrong id → "Chat not found". Private channel ids: `-100` + 13-digit id. Bot must be admin.
