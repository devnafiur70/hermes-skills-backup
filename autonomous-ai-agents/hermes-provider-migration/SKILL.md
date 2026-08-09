---
name: hermes-provider-migration
description: "Switch Hermes providers/models; kill quota errors."
version: 1.0.0
metadata:
  hermes:
    tags: [hermes, provider, model, migration, cron, auxiliary, free-models, quota, rate-limit]
---

# Hermes Provider / Model Migration

Use when the user says any of: "stop using <provider>", "use only free models",
"switch everything to X", "I'm getting 429 / quota exceeded", "make the cron job
use Y instead of Gemini", or when a scheduled job keeps failing on a provider's
free-tier quota.

The trap in this class of task: **the main model is only one of four places a
provider hides.** Changing `model.default` and declaring victory leaves the job
still broken. Audit all four.

## The four surfaces (audit every one)

| # | Surface | Inspect | Change |
|---|---|---|---|
| 1 | Main model | `hermes config get model` | `hermes model`, or `hermes config set model.default/model.provider` |
| 2 | Auxiliary slots | `hermes config get auxiliary` | `hermes config set auxiliary.<slot>.provider/.model` |
| 3 | Cron jobs | `hermes cron list`, `<HERMES_HOME>/cron/jobs.json` | `hermes cron edit <id> --model M --provider P` |
| 4 | External scripts | `grep -rn "hermes -z\|hermes chat" <project>` | patch the script's model flags |

Surfaces 2 and 4 are the ones people miss.

### 1. Main model

```bash
hermes config get model          # -> base_url / default / provider
```

### 2. Auxiliary slots — sweep them ALL

`auxiliary` has ~20 independent slots (`vision`, `compression`, `web_extract`,
`title_generation`, `skills_hub`, `approval`, `mcp`, `memory_query_rewrite`,
`tts_audio_tags`, `triage_specifier`, `kanban_decomposer`, `profile_describer`,
`goal_judge`, `curator`, `monitor`, `background_review`, `moa_*`, ...). Each has
its own `provider` and `model`. A slot left on the old provider will keep
burning that quota in the background.

List the slot names, then sweep:

```bash
hermes config get auxiliary | grep -n "^[a-z_]*:"

for slot in vision web_extract compression skills_hub approval mcp \
            title_generation memory_query_rewrite tts_audio_tags \
            triage_specifier kanban_decomposer profile_describer \
            goal_judge curator monitor background_review; do
  hermes config set auxiliary.$slot.provider <PROVIDER> >/dev/null
  hermes config set auxiliary.$slot.model    <MODEL>    >/dev/null
done
```

Guard rail worth setting when the goal is "free only":

```bash
hermes config set auxiliary.free_only true
```

Note `vision` needs a **multimodal** model — don't blanket-set a text-only model
into it. Pick a vision-capable free model for that slot specifically.

Confirm the old provider is gone:

```bash
grep -in "<oldprovider>" "$HERMES_HOME/config.yaml"    # expect no matches
```

### 3. Cron jobs

A job with `model: null` inherits the global default *at fire time*. `jobs.json`
also carries `provider_snapshot` / `model_snapshot` recording what it last ran
with — **a snapshot is not a pin.** Reading a stale snapshot and assuming the job
is pinned is a real misdiagnosis; check the `model`/`provider` fields.

```bash
hermes cron edit <job_id> --model "<model>" --provider <provider>
```

**The `cronjob` agent tool cannot set model/provider** — those flags are
user-owned and only reachable through the `hermes cron edit` CLI. Use terminal.

Verify the pin landed:

```bash
python -c "import json;j=json.load(open(r'$HERMES_HOME/cron/jobs.json'))['jobs'][0];print(j['model'],j['provider'])"
```

### 4. External scripts calling the Hermes CLI

Any pipeline script invoking a bare `hermes -z "<prompt>"` inherits the global
default — so it silently follows whatever provider is configured. Pin it
explicitly and give it a fallback chain:

```python
MODELS = [os.getenv("MY_MODEL", "<primary>"), "<fallback1>", "<fallback2>"]
for model in MODELS:
    try:
        res = subprocess.run(
            ["hermes", "-m", model, "--provider", "<provider>", "-z", prompt],
            capture_output=True, text=True, encoding="utf-8",
            check=True, timeout=600,
        )
        out = (res.stdout or "").strip()
        if out:
            break
    except Exception as e:
        last_err = f"{model}: {e}"
```

Free models are best-effort capacity — a single-model script WILL fail
eventually. Always chain 3-4.

## Finding free models

Run `scripts/list-free-nous-models.sh`. A model counts as free when
`pricing.prompt == 0` **and** `pricing.completion == 0`. Also check
`"tools" in supported_parameters` — an agent loop needs tool calling.

`hermes models` is **not** a command (it's `hermes model`, singular, and it's
interactive). Query the provider's `/v1/models` endpoint for a scriptable list.

## Verification — the part that actually proves it

Config changes prove nothing on their own. Force a real run:

```bash
hermes cron run <job_id>        # or: cronjob tool, action=run
hermes cron runs <job_id>       # expect the newest attempt = completed
```

`hermes cron runs` keeps the historical failures listed, so read the **newest
row by timestamp** rather than concluding from the presence of old errors.
Also read the run transcript under `$HERMES_HOME/cron/output/<job_id>/` to
confirm which model actually served the request.

## Pitfalls

- **Snapshot ≠ pin.** `provider_snapshot`/`model_snapshot` describe the last run,
  not configuration. Check `model`/`provider`.
- **A green exit code can still mean nothing was delivered.** Scripts that
  degrade to a dry-run when credentials are absent exit 0. Read their log.
- **Cron harness delivery and in-script delivery are separate paths.** The
  harness may deliver the agent's final response even while the pipeline's own
  sender is dry-running. Don't let one mask the other.
- **Don't delete the old provider's API key** as part of a migration unless
  asked. Repointing config is reversible; destroying a credential is not.
- **Editing `config.yaml` by hand is forbidden** — always `hermes config set`.

## Windows: the `/opt` path trap

In git-bash/MSYS a bare `/opt/foo` resolves to `<MSYS_ROOT>/opt/foo` (e.g.
`%LOCALAPPDATA%\hermes\git\opt\foo`), which is a **different directory** from
`C:\opt\foo`. An edit through the POSIX-looking path lands in a phantom copy and
the real script keeps running unchanged — a very convincing "my fix did nothing"
bug. Resolve the true path first (`cd <dir> && pwd -W`), edit the native
`C:\...` path, and verify the change is present there.

## Blocked-command recovery

Two unconditional blocks show up in this work and cannot be bypassed (not with
`--yolo`, not with approvals off) — don't try to route around them:

- **System shutdown/reboot.** Tell the user to restart themselves.
- **Oversized/unparseable inline payloads** (giant one-liners, heredocs). The
  command is saved to `$HERMES_HOME/cache/blocked-scripts/blocked-*.sh`; either
  run that file, or do the work with `write_file`/`patch`/`execute_code`
  instead of a huge inline shell string.

## Reporting back

Report the surfaces changed, the verification evidence (run status + which model
served it), and any residual risk (e.g. free-tier capacity) in a few lines. When
the user then asks a plain status question — "is it fine?", "will it work
tomorrow?" — answer *that question* directly and stop. Do not re-run the audit
or restate the whole changelog.

## Files

- `scripts/list-free-nous-models.sh` — enumerate zero-cost, tool-capable models.
- `references/gemini-to-nous-free-migration.md` — worked example with real
  values, commands, and the failure that triggered it.
