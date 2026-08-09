---
name: blogger
description: "Connect to a Google Blogger site via Blogger API v3 and publish posts (drafts or live)."
version: 1.0.0
author: Hermes Agent (custom)
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token with the Blogger scope (created by setup script)
  - path: google_client_secret.json
    description: Google OAuth2 client credentials (Desktop app, downloaded from Google Cloud Console)
metadata:
  hermes:
    tags: [Google, Blogger, Blog, Publishing, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
---

# Blogger

Publish to a Google Blogger site via the Blogger API v3. Connect once with OAuth,
then create posts (as drafts or live) from text, HTML, or content generated
elsewhere (e.g. YouTube summaries, tech-news pipeline).

This skill reuses the Hermes Google OAuth token location (`~/.hermes/google_token.json`)
so it is compatible with the `google-workspace` skill. You can later re-run the
Workspace setup to add more scopes to the same token.

## First-Time Setup

Fully non-interactive — the agent drives it step by step (works on Telegram, etc.).

### Step 0: Check if already set up
```bash
BSETUP="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/blogger/scripts/setup.py"
$BSETUP --check
```
If it prints `AUTHENTICATED`, skip to Usage.

### Step 1: Create OAuth credentials (one-time, ~5 minutes)
1. Create/select a project: https://console.cloud.google.com/projectselector2/home/dashboard
2. Enable the **Blogger API** here: https://console.cloud.google.com/apis/library/blogger.googleapis.com
3. Create OAuth client: https://console.cloud.google.com/apis/credentials
   Credentials → Create Credentials → OAuth 2.0 Client ID → Application type: "Desktop app" → Create
4. If the app is in Testing, add your Google account as a test user:
   https://console.cloud.google.com/auth/audience  (Audience → Test users → Add users)
5. Download the JSON and tell the agent the file path.

Agent runs: `$BSETUP --client-secret /path/to/client_secret.json`

### Step 2: Get authorization URL
```bash
$BSETUP --auth-url
```
Send the printed URL to the user. They authorize, then copy the ENTIRE redirected
URL from the browser address bar (it will fail on localhost:1 — expected) and paste it back.

### Step 3: Exchange the code
```bash
$BSETUP --auth-code "THE_URL_OR_CODE_PASTED_BACK"
```

### Step 4: Verify
```bash
$BSETUP --check
```
Should print `AUTHENTICATED`.

## Usage

```bash
BAPI="python ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/blogger/scripts/blogger.py"

# Find your blog id (from the blog URL, or list all blogs you own)
$BAPI blog-id --url "https://yourblog.blogspot.com"
$BAPI blogs                      # list all blogs you can post to

# Draft a post (does NOT publish — safe default)
$BAPI post --blog-url "https://yourblog.blogspot.com" --title "Hello" --body "<p>Content</p>" --draft

# Publish a post live
$BAPI post --blog-url "https://yourblog.blogspot.com" --title "Hello" --body "<p>Content</p>" --labels "Tech,News"

# List recent posts
$BAPI list --blog-url "https://yourblog.blogspot.com" --max 5
```

All commands return JSON.

## Rules
- Never publish a live post without showing the content to the user and getting approval,
  OR use `--draft` so the user reviews in Blogger before clicking Publish.
- Check auth before first use (`setup.py --check`).
- Blog IDs/URLs must be confirmed before posting.
