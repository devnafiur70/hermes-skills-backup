---
name: fetch-mobile-tech-news
description: Fetch top mobile tech news with zero LLM token usage.
---

# Fetch Mobile Tech News Skill

This skill provides a zero-token-efficient solution for aggregating top mobile technology news from major RSS feeds using Python, regex keyword filtering, priority ranking, and automatic deduplication.

## Environment & Path Layout

Bot root directory: `/opt/tech-news-bot/` (or `C:/opt/tech-news-bot` on Windows)

```
/opt/tech-news-bot/
├── config/
│   ├── brands.json         # Targeted mobile brand keywords
│   └── categories.json     # Secondary tech filter keywords
├── cache/
│   └── top_5_news.json     # Output JSON containing top 5 filtered news items
├── history/
│   └── sent_urls.json      # Delivered article links (30-day deduplication window)
├── logs/
│   └── fetcher.log         # Execution log file
└── fetcher.py              # Main aggregation script
```

## Supported RSS Feeds

1. GSMArena: `https://www.gsmarena.com/rss-news-reviews.php3`
2. Android Authority: `https://www.androidauthority.com/feed/`
3. 9to5Google: `https://9to5google.com/feed/`
4. TechCrunch Mobile: `https://techcrunch.com/category/mobile/feed/` (fallback: `https://techcrunch.com/tag/mobile/feed/`)
5. PhoneArena: `https://www.phonearena.com/feed`

## Matching & Priority Logic (Zero LLM Tokens)

1. **Targeted Brands (Highest Priority)**:
   Samsung, Xiaomi, Redmi, POCO, Realme, vivo, OPPO, Walton, OnePlus, Apple, Tecno, Infinix, Honor, Google Pixel, Motorola, Nothing.
2. **Secondary Tech Categories**:
   Processor, Hardwares, Mobile Apps, Scams, Leaks, Specs, Buying Guides.
3. **Deduplication**:
   Reads `/history/sent_urls.json`. Excludes any article link delivered within the last 30 days.
4. **Scoring & Sorting**:
   - Brand match = +100 points
   - Category match = +10 points
   - Recency = fractional publication timestamp bonus
   Top 5 articles are saved to `/cache/top_5_news.json`.

## Usage / Execution

Run the python script to update the cache:

```bash
python /opt/tech-news-bot/fetcher.py
```

### Output Format (`/cache/top_5_news.json`)

```json
[
  {
    "title": "Article Title",
    "summary": "Cleaned article summary...",
    "link": "https://...",
    "pubDate": "2026-08-04T00:00:00+00:00",
    "category_matched": "Brand: Samsung, Apple | Category: Specs"
  }
]
```
