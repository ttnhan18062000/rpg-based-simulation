---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-EDIT-RATCHET-HOOK
phase: open
date: 2026-10-04
tags: [architecture, hooks]
---

# TCK-20261004-EDIT-RATCHET-HOOK

## Title
M6c: Advisory code-health PostToolUse edit hook

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`codebase/hooks/edit_ratchet_hook.py` reports a new or worse ruff finding to the agent right after it edits a `src/**/*.py` file. Advisory only: exit 0 always, silent on pass.

## Scope
- Read PostToolUse JSON from stdin; act only for Edit/Write/MultiEdit on an existing `src/**/*.py` inside the repo
- Refactor `codebase/gates/staged_ratchet.py` so the hook and pre-commit share one function; pre-commit behaviour and tests unchanged
- On NEW or WORSE print `hookSpecificOutput.additionalContext` (about 20 lines, count of the rest, rule IDs); silent on pass
- Always exit 0; cannot-run cases (no ruff, no registry, about 5 s budget) print nothing
- Wire one `Edit|Write|MultiEdit` PostToolUse entry in `.claude/settings.json` (`python3 -m codebase.hooks.edit_ratchet_hook 2>/dev/null || true`); owner confirms the literal diff via AskUserQuestion BEFORE commit
- Extend `tests/tools/test_settings_json_hooks_wiring.py`; check and update `hook-surface-policy.yaml` if it lists commands
- Capability envelope: check whether `tools/capability_envelope_baseline.py` covers hooks; if yes add the row, if no record a finding here and in the codebase-planner outbox for agent-working; do NOT extend the schema
- Docs: `codebase/README.md` hooks row, standard Section 2, `agent_working_environment.md` if it lists hooks
- Tests in `tests/codebase/`: new violation, grandfathered-only, non-src/non-py/outside-repo/malformed stdin, missing ruff, time budget, pre-commit still rejects NEW/WORSE

## Out of Scope
- ast-grep, complexipy, line-count in the hook
- `tools/**` and `tests/**` files
- Making any hook blocking

## Acceptance Criteria
- [ ] Hook exits 0 in every tested case and is silent on pass
- [ ] Owner confirmed the settings.json diff before commit
- [ ] Wiring test extended and passing
- [ ] Capability-envelope result recorded (row or finding)
- [ ] Pre-commit ratchet tests unchanged and passing
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
None.

## Related Docs
- docs/plans/codebase_health/python_code_craft_m6_agent_integration_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/python_code_standard.md
- codebase/README.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/hooks/
- codebase/gates/staged_ratchet.py
- .claude/settings.json (owned by agent-working)
- agent-working/agent-orchestration/hook-surface-policy.yaml

## Assumptions / Open Questions
- Owner decision 8.17 (2026-10-04): codebase implements M6 although `.claude/**` is agent-working's territory; the PR body names agent-working as owner of those paths
- Nothing here blocks a PR or tool call; M4 and M5 soaks are not disturbed

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
