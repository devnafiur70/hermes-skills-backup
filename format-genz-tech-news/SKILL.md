---
name: format-genz-tech-news
description: Format RSS news JSON into Gen Z Bangladeshi tech briefing.
---

# Format Gen Z Tech News Skill

This skill processes raw news JSON from `/opt/tech-news-bot/cache/top_5_news.json` into engaging, casual Bangladeshi Gen Z style tech posts.

## Pipeline Workflow

1. Reads `/opt/tech-news-bot/cache/top_5_news.json`.
2. Extracts minimal fields (`title`, `summary`, `pubDate`, `link`) to strictly optimize prompt token usage.
3. Invokes LLM formatting script `/opt/tech-news-bot/formatter.py`.
4. Writes formatted text output to `/opt/tech-news-bot/cache/formatted_briefing.txt`.

## Output Structure (Strict 6-Part Layout for Each Article)

১) [Headline in Banglish/Bangla]  
২) [1-line catchy hook/most interesting part]  
৩) [Date - e.g. 03 Aug, 2026]  
৪) [Category: Choose ONE from allowed list]  
   *(Allowed Categories: মোবাইল লঞ্চ / প্রসেসর ও হার্ডওয়্যার / অ্যাপ ও ওয়েবসাইট ট্রেন্ড / মোবাইল লিকস / মোবাইল স্পেক / মোবাইল কম্পেয়ার / প্রবলেম সল্যুশন / বাইং গাইড / হিডেন ফিচার / টেক এক্সপ্লেইন্ড / অনলাইন স্ক্যাম অ্যালার্ট / নতুন টুল ও রিসোর্স / ইনভেনশন / ট্রেন্ডিং টপিক / টিপস)*  
৫) [Details: Under 200 words engaging Gen Z Bangla breakdown]  
৬) [Source: Brand Name (URL Link)]  

## Inference Provider (IMPORTANT)

This skill uses **Nous Portal free models only — never Google Gemini.**

`formatter.py` calls `hermes -m <model> --provider nous -z "<prompt>"` and walks a
fallback chain of zero-cost Nous models until one returns output:

1. `tencent/hy3:free` (default, override with `TECH_NEWS_MODEL` env var)
2. `stepfun/step-3.7-flash:free`
3. `inclusionai/ling-3.0-flash:free`
4. `poolside/laguna-s-2.1:free`

If a new free model appears on `https://inference-api.nousresearch.com/v1/models`
(pricing.prompt == 0 and pricing.completion == 0), add it to `NOUS_FREE_MODELS`
in `formatter.py`. Do NOT add any Gemini/Google model — the free Gemini tier
returns HTTP 429 RESOURCE_EXHAUSTED and breaks the pipeline.

## Execution Command

```bash
python /opt/tech-news-bot/formatter.py       # Linux
python C:/opt/tech-news-bot/formatter.py     # Windows
```

Note on Windows: the real bot directory is `C:\opt\tech-news-bot`. A bash `/opt/...`
path inside git-bash resolves to `%LOCALAPPDATA%\hermes\git\opt\...`, which is a
DIFFERENT folder. Always edit/copy to `C:\opt\tech-news-bot\` on Windows.
