---
name: google-custom-api
description: "Build Google API skills reusing the Workspace OAuth token."
version: 1.0.0
author: Hermes curator
license: MIT
platforms: [linux, macos, windows]
required_credential_files:
  - path: google_token.json
    description: Google OAuth2 token created by the google-workspace skill setup (reused, not re-created)
metadata:
  hermes:
    tags: [Google, OAuth, API, Blogger, YouTube, skill-authoring]
    homepage: https://github.com/NousResearch/hermes-agent
---

# Google Custom API (reuse Workspace OAuth)

When you need to talk to a Google API that the `google-workspace` skill does NOT
cover (e.g. Blogger API v3, YouTube Data API, Analytics, etc.), do NOT create a
second OAuth client or a second token. Reuse the existing `google-workspace`
OAuth token (`~/.hermes/google_token.json`) and its helper modules. This keeps a
single token for the user, avoids a second consent flow, and means adding one
API never breaks another.

This is the canonical pattern — proven when building the `blogger` skill.

## When to use
- User wants to connect a Google product not in `google-workspace` (Blogger,
  YouTube Data, Search Console, Analytics, ...).
- You are authoring a new Google-integration skill.

## Core approach
1. Anchor ALL paths on `HERMES_HOME` — never chained `.parent` (see pitfalls).
2. Append your API's OAuth scope to the workspace `setup.py` `SCOPES` list
   before dispatching to its `main()`.
3. In your API script, reuse `_hermes_home.get_hermes_home()` and build the
   service with `Credentials.from_authorized_user_file(TOKEN_PATH, [YOUR_SCOPE])`.
4. Implement commands and JSON output consistent with `google-workspace`.

## References
- `references/reusing-workspace-oauth.md` — exact working code, the path/pitfall
  notes from the Blogger build (MSYS `/c/` path translation, venv python path,
  chained-`.parent` trap), and the pre-auth test that proves the import chain.

## Rules
- Never publish/delete/write to a user's Google data without confirmation
  (mirror `google-workspace` rules).
- Confirm the user has enabled the relevant API in Google Cloud Console.
- This skill is about REUSE — if the user instead wants a standalone Gmail-only
  setup, the `himalaya` skill is simpler.
