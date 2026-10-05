---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-CAPABILITY-ENVELOPE-COVER-HOOKS
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-CAPABILITY-ENVELOPE-COVER-HOOKS

## Title
Extend the capability envelope baseline to cover `settings.json` hooks

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Roadmap 5.8 says new hooks are registered in `registries/capability_envelope_registry.jsonl`, but `tools/capability_envelope_baseline.py` audits only `.claude/settings.local.json` (4 fields) and reads neither `hooks` nor `settings.json` (verified). The hook PR #318 added has no row.

Source: `docs/plans/codebase_health/handoffs/handoff_to_agent_working.md` (PR #322, codebase-planner, 2026-10-04); structure re-read on `origin/main` by `agent-working-design`.

## Scope
- Read `hooks` from `.claude/settings.json`: one registry row per (event, matcher, command); `seed` registers the existing hooks idempotently; `diff` reports a new, removed or changed hook.
- Extend the registry schema minimally and document it; keep the existing 118 rows valid.
- Any `settings.json` edit stays out of this ticket (read-only).

## Out of Scope
- Changing hook behaviour, auditing hook script contents, new hooks.

## Acceptance Criteria
1. `seed` registers every current hook; `diff` is clean afterwards and reports a seeded fixture's added and changed hook.
2. Existing `settings.local.json` behaviour and rows unchanged (existing tests green).
3. A missing `hooks` key or unreadable `settings.json` degrades without raising. Scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- PR #322 handoff; `TCK-20260904-*` monitoring-anomaly ratchet tickets where cited in the validator

## Related Docs
- `docs/plans/codebase_health/handoffs/handoff_to_agent_working.md`

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/capability_envelope_baseline.py`, `registries/capability_envelope_registry.jsonl`, tests.

## Assumptions / Open Questions
- Whether the envelope should enforce (block) or only report is out of scope; this is report-only like the current `diff`.

## Implementation Notes
- `tools/capability_envelope_baseline.py`: new field `hooks` in `FIELDS`; `extract_hook_entries()` flattens the `hooks` of `.claude/settings.json` into one `("hooks", "<event>|<matcher>|<command>")` row per hook command (matcher empty when absent); `seed`/`diff` take `--hooks-path` (default `.claude/settings.json`) and read only its `hooks` key, so `settings.local.json` behaviour is unchanged. `diff` adds a hooks-only `not_in_live` list so a removed hook is reported (an edited hook shows as both `out_of_envelope` and `not_in_live`). A missing or unreadable file and a missing or malformed `hooks` key degrade to no rows, never raise.
- The registry schema itself is unchanged (`field`/`value` rows); only the allowed field set grew. The 118 existing rows are untouched; 14 `hooks` rows were seeded (`reviewed: false`, bulk seed) and `diff` is now clean against the real `.claude/settings.json`.
- `docs/ai/capability_envelope_baseline.md` documents the hooks rows. No `settings*.json` was edited.

## Test Summary
`tests/tools/test_capability_envelope_baseline.py`: 11 pass, 1 skipped (real `settings.local.json` absent in this worktree). New tests: one row per hook, malformed/missing degrade, idempotent seed, and a fixture where an added, an edited and a removed hook are each reported. The schema test now excludes `hooks` from the `settings.local.json` field set, as intended.

## Files Changed
- tools/capability_envelope_baseline.py
- tests/tools/test_capability_envelope_baseline.py
- registries/capability_envelope_registry.jsonl
- docs/ai/capability_envelope_baseline.md

## Completion Summary
The capability envelope now audits the shared settings.json hooks: seeded, diffable, and reporting added, edited and removed hooks.
