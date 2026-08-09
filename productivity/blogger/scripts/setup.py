#!/usr/bin/env python3
"""Blogger OAuth2 setup for Hermes Agent.

Thin wrapper around the google-workspace setup.py. Adds the Blogger scope so the
same Google token (google_token.json) also works for Blogger. Keeps the token
compatible with the google-workspace skill for later expansion.

Commands:
  setup.py --check                # Is auth valid (with Blogger scope)? exit 0=yes
  setup.py --client-secret PATH   # Store OAuth client credentials
  setup.py --auth-url             # Print the OAuth URL (with Blogger scope)
  setup.py --auth-code CODE       # Exchange auth code for token
  setup.py --revoke               # Revoke and delete stored token
  setup.py --install-deps         # Install Python dependencies only
"""

import sys
from pathlib import Path

# Delegate to the google-workspace setup script, injecting the Blogger scope.
# Resolve the workspace script robustly via HERMES_HOME.
import os
_HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
_WS_SETUP = _HERMES_HOME / "skills" / "productivity" / "google-workspace" / "scripts" / "setup.py"

# Blogger scope to request in addition to the Workspace scopes.
BLOGGER_SCOPE = "https://www.googleapis.com/auth/blogger"

if not _WS_SETUP.exists():
    print(f"ERROR: google-workspace setup not found at {_WS_SETUP}")
    sys.exit(1)

# Ensure the Blogger scope is requested by the parent setup script.
import os
os.environ["HERMES_BLOGGER_SCOPE"] = BLOGGER_SCOPE

# Inject the scope into the parent's SCOPES list before it builds the flow.
# The parent import happens here so we can patch SCOPES first.
sys.path.insert(0, str(_WS_SETUP.parent))
import setup as _ws  # noqa: E402

if BLOGGER_SCOPE not in _ws.SCOPES:
    _ws.SCOPES.append(BLOGGER_SCOPE)


def main():
    # Re-dispatch to the parent's main().
    _ws.main()


if __name__ == "__main__":
    main()
