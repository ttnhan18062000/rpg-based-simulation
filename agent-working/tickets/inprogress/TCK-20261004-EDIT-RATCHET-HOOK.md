---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-EDIT-RATCHET-HOOK
phase: inprogress
date: 2026-10-04
tags: [architecture, hooks]
---

# TCK-20261004-EDIT-RATCHET-HOOK

## Title
M6c: Advisory code-health PostToolUse edit hook

## Status
INPROGRESS

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
`codebase/hooks/edit_ratchet_hook.py` reuses `staged_ratchet.check()` (new keyword-only `python` and `timeout`, defaults keep pre-commit behaviour; a missing ruff, detected by "No module named" with empty stdout, or a timeout raises `HookSkipped`, never a clean pass). Repo root comes from the module path, not the cwd; stdin and path are filtered before the health modules are imported (lazy). Prefers `.venv/bin/python3`. Wired as the last PostToolUse group; the owner confirmed the literal diff (AskUserQuestion, 2026-10-04) before commit.

**Finding for agent-working (capability envelope, no schema change):** `tools/capability_envelope_baseline.py` audits only `.claude/settings.local.json` and 4 fields (`permissions.allow` plus 3 MCP fields). It covers neither `hooks` nor `settings.json`, so no row could be added; roadmap 5.8's "new hooks must be added there" is not satisfiable without extending the schema. Also in the codebase-planner outbox (Message 12).

## Test Summary
`tests/codebase/test_edit_ratchet_hook.py` + `test_code_health_staged_ratchet.py` 37 passed; wiring test added in `tests/tools/test_settings_json_hooks_wiring.py`. Wall time: non-src edit 0.05 s (bare python3 0.04 s); src edit 0.31 s warm. One first src-edit run took 17 s; it did not reproduce in 5 later runs (all <= 0.37 s, imports 55 ms, registry load 0.14 s, ruff 0.06 s), so it is attributed to a cold file cache, not measured directly. Only the ruff subprocess has a deadline (5 s); Claude Code's own hook timeout bounds the rest.

## Files Changed
codebase/hooks/edit_ratchet_hook.py (new), codebase/gates/staged_ratchet.py, .claude/settings.json (agent-working's), tests/codebase/test_edit_ratchet_hook.py (new), tests/tools/test_settings_json_hooks_wiring.py, codebase/README.md, docs/guidelines/python_code_standard.md, ticket and staging artifacts

## Completion Summary
