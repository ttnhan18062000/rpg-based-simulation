---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260706-MONITORING-REASON-CODE
artifact_type: investigation
tags: [agent-monitoring, tagging, reporting]
---

# Investigation — TCK-20260706-MONITORING-REASON-CODE

## What already exists (read before designing anything)

`docs/agent-monitoring/schema.md`: `events.jsonl` has one record per agent call —
`run_id`, `seq`, `ts`, `phase`, `agent`, `summary` (≤200 chars), `status`
(`ok`/`failed`/`blocked`/`skipped`), `tool_call_count`. No field distinguishes *why* a
`failed`/`blocked` status occurred beyond the free-text `summary`.

`runs.jsonl`'s `final_status` already gives a coarse reason at the **run** level:
`CONFLICTS_DETECTED`, `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`, `BLOCKED`, `TESTS_FAILED`,
`SECURITY_BLOCKED`, `DOD_BLOCKED`. Cross-referencing `docs/ai/workflows.md`'s Return Values table:
every one of these except `DOD_BLOCKED` maps 1:1 to exactly one phase and one specific meaning
(`NEEDS_CHANGES`/`BLOCKED` distinguish Review vs. Architecture-Verify only by *which phase's event*
carries them, which `phase` already provides). **`DOD_BLOCKED` is the sole exception** — it's a
single status covering all 13 DoD conditions in `done-checker`'s checklist
(`tools/gate_checks/done_checker_static.py`'s 5 static ones plus 8 judged ones), so a grep over
3 days of `events.jsonl` for `DOD_BLOCKED`-adjacent `failed` events cannot distinguish "someone used
an unregistered tag" from "a test wasn't updated" from "staging artifacts incomplete."

Confirmed no other phase has this same catch-all problem — do not add `reason_code` where it would
just duplicate `phase`/`final_status`, per the Out of Scope note.

## Exact wording to match

`tools/tag_registry.py`'s canonical-form/registry-membership error text (surfaced through
`validate_frontmatter.py`'s `_check_tags`, which `done_checker_static.py`'s `check_frontmatter_valid`
calls via `validate_file`/`validate_directory`):

```
{filepath}: tags: {tag!r} is not in the tag registry — register it first via `python3 tools/tag_registry.py add {tag} --category <category> --note "..."`
```

The substring `"is not in the tag registry"` is unique to this one error path (confirmed via
`grep -rn "is not in the tag registry" tools/`) — safe to match against without false positives
from any other `validate_frontmatter.py` error message (canonical-form, forbidden-tag, and
synonym-map messages all use different wording, per `tools/tag_registry.py`'s
`canonical_form_violation`).

## Where the checklist data actually lives at pushEvent time

`done-checker`'s own agent prompt (Verify phase, `implement-ticket.js`) instructs the *agent* to
run `run_static_precheck` itself via `bash()` and cite its output — the *orchestrator* (the JS
workflow script) never sees `run_static_precheck`'s raw output directly. What the orchestrator
*does* have, at the exact point it calls `pushEvent('Verify', 'done-checker', 'failed', ...)`
(line ~867), is `doneCheck.checklist` — the agent's transcribed
`[{"condition","status","evidence"}, ...]`, per `DONE_SCHEMA`. This is sufficient: the 5
static-precheck conditions (including `frontmatter_valid`, the one that would show the tag-registry
substring) are required to be cited verbatim by the agent, not re-derived — so `doneCheck.checklist`
should faithfully carry the same evidence text `check_frontmatter_valid` produced.

## Existing bash()-call-from-orchestrator precedent to mirror

`Architecture-Verify`'s Step 0 (`implement-ticket.js` ~line 489): orchestrator runs a
`python3 -c "..."` via `bash()`, printing `MARKER:` + `json.dumps(...)`, then parses the output by
`indexOf('MARKER:')`. This ticket's new classification call follows the identical shape — a small,
already-proven pattern in this exact file, not a new integration style.
