---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON
artifact_type: investigation
tags: [ai, agent-monitoring, governance]
---

# Investigation — TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON

## Context scan performed
`mcp__knowledge-search__search_docs` (queries: "shadow reviewer logging collection default on",
"cost proxy weight change before after comparison recalibration") and `graphify query "shadow
reviewer logging SHADOW_REVIEWER_LOGGING_ENABLED"` run before any grep/file-read, per CLAUDE.md's
Context Scan rule. Surfaced `TCK-20260904-SHADOW-REVIEWER-LOGGING` (done),
`review_independence_epic.md`, `docs/agent-monitoring/schema.md`'s Shadow-reviewer-event field
family section, and `docs/parity_ledger/infrastructure.yaml`'s `INFRA-409` entry as the doc/parity
surfaces to update alongside code.

## Epic staleness (part a)
Directly confirmed all six ticket IDs the epic's own `Assumptions`/`Related Tickets` sections
describe as pending/in-progress are actually in `tickets/done/`:
- `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`
- `TCK-20260904-SHADOW-REVIEWER-LOGGING`
- `TCK-20260904-BASH-SECRET-SCAN-HOOK`
- `TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST`
- `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING`
- `TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN`

The epic's own text already records the item-13 → items-18-20 unblock relationship correctly in
its `Related Tickets` section (added when `FILTERED-REPLAY-EVAL-PILOT` closed) — the stale part is
the `Related Tickets` path annotations for items 14/15 (`tickets/todos/`/`tickets/inprogress/`,
both now `tickets/done/`) and the Bucket-B/C `Assumptions` list, which does not yet state items
16/17's current gating status plainly (16: this ticket's own part (b); 17: still genuinely
un-gated, no false-positive data exists).

## Shadow-reviewer default (part b)
`.claude/workflows/implement-ticket.js` gates both call sites (Architecture-Verify ~1057,
Security-Review ~1502) on strict string equality:
```
if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" = "1" ]; then python3 tools/agent-monitoring/shadow_reviewer_window.py ...; fi
```
Confirmed via `grep -n SHADOW_REVIEWER_LOGGING_ENABLED` — these are the ONLY two call sites that
gate on the env var (the `timeout 15s python3 -c` blocks at ~1112/~1552 that actually emit the
shadow event are nested inside `if (archShadowWindow && archShadowWindow.window_open)`, which is
only ever true if the gated bash call above it ran and printed `SHADOW_WINDOW_JSON:` — so flipping
just the two `[ ]` conditions is sufficient; no second gate exists deeper in the block).

`SHADOW_MAX_SAMPLES = {"architecture-reviewer": 50, "security-reviewer": 10}`
(`tools/agent-monitoring/shadow_reviewer_window.py`) — 60 total, confirmed unchanged per the batch
brief's explicit instruction not to widen it.

Real collection volume: confirmed by the requesting session (not re-derived here per its explicit
instruction) — 3 `-shadow` events total across all weekly `agent-monitoring/data/*/events.jsonl`
shards since `TCK-20260904-SHADOW-REVIEWER-LOGGING` shipped 2026-09-04, far short of the 60-sample
window. Root cause: the env var defaults off, and most ticket closures in this repo are
hand-orchestrated (never invoking `implement-ticket.js`'s actual pipeline, which is the only code
path that ever sets/reads this var) — a limitation that persists even after the default flips, and
is recorded plainly in this ticket rather than treated as something the default flip alone fixes.

## Test surface
`tests/tools/test_shadow_reviewer_call_site.py::test_shadow_reviewer_call_site_is_fail_open_and_env_gated`
(line 230) asserts the literal string `if [ "$SHADOW_REVIEWER_LOGGING_ENABLED" = "1" ]` is present
in both call-site blocks — this is the one test that must change to match the new gate string. No
other test in that file, or in `tests/tools/test_shadow_reviewer_window.py`, asserts on the literal
env-var comparison operator; the rest test `shadow_reviewer_window.py`/`shadow_reviewer_events.py`
behavior directly (unaffected — this ticket does not touch either module).

## Doc/parity surfaces needing the same "off by default" → new-default correction
- `docs/agent-monitoring/schema.md` line ~384: "Gated behind `SHADOW_REVIEWER_LOGGING_ENABLED`
  (strict `"1"` string equality, off by default)".
- `docs/parity_ledger/infrastructure.yaml`, `INFRA-409` `text` field: "Gated behind
  SHADOW_REVIEWER_LOGGING_ENABLED (strict "1" string equality, off by default)". This is a large
  multi-line YAML block-scalar string inside a 12000+-line file — per
  `[[feedback_parity_updater_full_file_yaml_rewrite_risk]]` (session memory), this must be edited
  via `tools/parity_ledger_writer.py` (schema-validating), never a raw string-replace `Edit` against
  the raw YAML, to avoid corrupting the file's YAML quoting.

## Related code confirmed NOT touched
`tools/agent-monitoring/shadow_reviewer_window.py`, `tools/agent-monitoring/shadow_reviewer_events.py`
— read for confirmation only; neither file references `SHADOW_REVIEWER_LOGGING_ENABLED` (grep
confirmed: 0 matches in `tools/agent-monitoring/`), so this ticket's diff is entirely confined to
`implement-ticket.js`, its two comments, the one test assertion, the two docs, and the epic ticket.
