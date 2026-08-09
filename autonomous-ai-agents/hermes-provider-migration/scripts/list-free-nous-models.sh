#!/usr/bin/env bash
# List zero-cost, tool-capable models on a Hermes OAuth inference provider.
#
# Why this exists: the /v1/models response is ~500KB. Piping it through
# head/grep floods the agent context and truncates mid-JSON. This filters
# server-side-ish (in python) and prints only a handful of lines.
#
# Usage:
#   bash list-free-nous-models.sh                 # all free models
#   bash list-free-nous-models.sh --tools         # only tool-capable
#   bash list-free-nous-models.sh --vision        # only multimodal (for auxiliary.vision)
#
# Requires: an active `hermes login` session (reads auth.json).

set -uo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
API="${HERMES_INFERENCE_API:-https://inference-api.nousresearch.com/v1}"
FILTER="${1:-}"

python - "$HERMES_HOME" "$API" "$FILTER" <<'PY'
import json, os, subprocess, sys

hermes_home, api, filt = sys.argv[1], sys.argv[2], sys.argv[3]

# Prefer the CLI's own credential handling; fall back to auth.json.
token = None
auth_path = os.path.join(hermes_home, "auth.json")
try:
    with open(auth_path, encoding="utf-8") as f:
        auth = json.load(f)
    prov = auth.get("providers", {}).get("nous", {})
    for k in ("api_key", "access_token", "token", "key"):
        if prov.get(k):
            token = prov[k]
            break
except Exception as e:
    print(f"could not read {auth_path}: {e}", file=sys.stderr)

if not token:
    print("No usable token found. Run: hermes login", file=sys.stderr)
    print("(Tokens are short-lived; a 403 usually means it needs refreshing.)", file=sys.stderr)
    sys.exit(1)

# curl is more reliable than urllib here (proxy/TLS handling on Windows).
out = subprocess.run(
    ["curl", "-s", "-m", "45", f"{api}/models", "-H", f"Authorization: Bearer {token}"],
    capture_output=True, text=True, encoding="utf-8",
).stdout

try:
    data = json.JSONDecoder().raw_decode(out[out.find('{"data":'):])[0]
except Exception:
    print("Failed to parse /v1/models response. First 300 chars:", file=sys.stderr)
    print(out[:300], file=sys.stderr)
    sys.exit(1)

rows = []
for m in data.get("data", []):
    p = m.get("pricing", {})
    try:
        if float(p.get("prompt", 1)) != 0 or float(p.get("completion", 1)) != 0:
            continue
    except (TypeError, ValueError):
        continue
    sp = m.get("supported_parameters", []) or []
    mods = (m.get("architecture", {}) or {}).get("input_modalities", []) or []
    tools = "tools" in sp
    vision = "image" in mods
    if filt == "--tools" and not tools:
        continue
    if filt == "--vision" and not vision:
        continue
    rows.append((m["id"], tools, vision, m.get("context_length")))

if not rows:
    print("No free models matched.")
else:
    print(f"{'MODEL':<42} {'TOOLS':<6} {'VISION':<7} CTX")
    for mid, tools, vision, ctx in sorted(rows):
        print(f"{mid:<42} {str(tools):<6} {str(vision):<7} {ctx}")
    print(f"\n{len(rows)} free model(s). Chain 3-4 as fallbacks — free capacity is best-effort.")
PY
