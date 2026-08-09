# Reusing google-workspace OAuth for a new Google API skill

This pattern lets you add a Google API (Blogger, YouTube Data, Analytics, ...) as
a custom skill WITHOUT a second OAuth client or token. It reuses the
`google-workspace` token (`~/.hermes/google_token.json`) and helper modules.
Proven when building the `blogger` skill for Nafiur's Blogger site.

## Working technique

1. **Resolve workspace scripts by HERMES_HOME — never chained `.parent`.**
   The workspace script is at
   `<HERMES_HOME>/skills/productivity/google-workspace/scripts/`. Anchor on the
   env var (stable); counting parent dirs from your script is fragile:

   ```python
   import os
   from pathlib import Path
   _HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
   _WS_SETUP = _HERMES_HOME / "skills" / "productivity" / "google-workspace" / "scripts" / "setup.py"
   _WS_SCRIPTS = _HERMES_HOME / "skills" / "productivity" / "google-workspace" / "scripts"
   ```

2. **Inject your scope into the parent SCOPES, then dispatch to its main().**
   ```python
   sys.path.insert(0, str(_WS_SETUP.parent))
   import setup as _ws
   EXTRA_SCOPE = "https://www.googleapis.com/auth/blogger"
   if EXTRA_SCOPE not in _ws.SCOPES:
       _ws.SCOPES.append(EXTRA_SCOPE)
   _ws.main()
   ```

3. **Reuse the token + `_hermes_home` in your API script.**
   ```python
   sys.path.insert(0, str(_WS_SCRIPTS))
   from _hermes_home import get_hermes_home
   TOKEN_PATH = get_hermes_home() / "google_token.json"
   ```
   Same `google_token.json` works across every skill sharing this location, so
   adding one API never re-does or breaks another's auth.

4. **Build the service from the token with your scope.**
   ```python
   from googleapiclient.discovery import build
   from google.oauth2.credentials import Credentials
   creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), [EXTRA_SCOPE])
   svc = build("blogger", "v3", credentials=creds)
   ```

## Pitfalls (all hit and fixed building the blogger skill)

- **Chained `.parent` resolution is a trap.** First two attempts used
  `Path(__file__).resolve().parent.parent.parent.parent / "google-workspace"/...`
  and got the depth wrong (resolved to `.../blogger/google-workspace/...`). Always
  anchor on `HERMES_HOME`.
- **MSYS path translation on this Windows host.** In `terminal` calls, git-bash
  rewrites `C:/Users/...` to `/c/Users/...`, which Python then fails to open
  (`[Errno 2] No such file or directory`). Pass **native Windows paths**
  (`C:/Users/user/...`, forward slashes OK) to the venv python, never MSYS `/c/...`.
- **`python3` is not on PATH here;** use the Hermes venv interpreter directly:
  `C:/Users/user/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`.
- **Workspace `check_auth` calls `from_authorized_user_file` WITHOUT scopes** on
  purpose (a subset-consent token still validates). Don't "fix" that.
- **Consent screen redirects to `http://localhost:1` and the browser fails — that
  is expected.** Tell the user to copy the ENTIRE redirected URL from the address
  bar and paste it back; the code is extracted from the URL.

## Test before declaring done

With no token yet: `setup.py --check` should print `NOT_AUTHENTICATED`, and the
API script (e.g. `blogger.py blogs`) should print
`{"error": "NOT_AUTHENTICATED: ..."}`. Both prove the import chain and path
resolution work end-to-end before the user even authorizes.
