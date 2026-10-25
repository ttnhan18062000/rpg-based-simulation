---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION
phase: open
date: 2026-10-24
tags: [knowledge-store, process-improvement]
---

# TCK-20261024-GRAPHIFY-ON-PATH-IS-NOT-THE-PINNED-VERSION

## Title
The `graphify` that hooks and sessions run is the pinned `requirements-knowledge.txt` version, not a stray user-site install

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found reviewing TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS (agent-working-planner, 2026-10-24, host ubuntu). That
ticket pins graphifyy==0.9.70 and installs it in `.venv-knowledge`, but the bare `graphify` on PATH is
`~/.local/bin/graphify` (shebang `/usr/bin/python3`, user-site graphifyy **0.6.7**). The PostToolUse edit hook in
`.claude/settings.json` (`graphify update .` on src/tests edits in the main checkout) and every `graphify query` an
agent runs therefore use 0.6.7, so the pin and its security fix do not cover them. graphifyy 0.9 also changes the node-ID
scheme (pre-#1504 note; `graphify extract --force` re-keys to path-qualified IDs), so the version mismatch can
corrupt the shared `graphify-out/` if two versions write it.
Not yet checked: what u24desktop's PATH resolves to.

## Scope
1. Measure on both hosts: `command -v graphify`, its interpreter and graphifyy version; the `.venv-knowledge` one.
2. Decide and implement one resolution, with the reason recorded: e.g. the hook and docs call
   `.venv-knowledge/bin/graphify` through one resolver (like `PYTHON_KNOWLEDGE` in the Makefile), or a documented
   setup step that removes or replaces the user-site install. Whatever writes `graphify-out/` must be the pinned version.
3. Plan the one-time shared-graph rebuild under 0.9 (`graphify extract --force` or the documented full rebuild, then
   `tools/graphify_prune.py`) from the main checkout on `main`. Say who runs it and when; the owner approves the
   rebuild time because every seat reads that graph.
4. Docs: `docs/guidelines/agent_working_environment.md` names the resolved binary.

## Out of Scope
- Changing graphify's own behaviour; other knowledge-stack pins.

## Acceptance Criteria
- On both hosts, the graphify that the edit hook and the docs' commands run reports graphifyy 0.9.70 (or the current pin).
- A test or check fails if the hook goes back to resolving bare `graphify` from PATH (if the resolution is in code).
- The shared graph is rebuilt once under the pinned version, or the ticket records the rebuild as scheduled with the owner.

## Related Tickets
- TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS, TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR

## Related Docs
- `docs/guidelines/agent_working_environment.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261024-KNOWLEDGE-STACK-SECURITY-BUMPS/` (after that ticket lands)

## Related Code Areas
- `.claude/settings.json` (PostToolUse graphify hook), `tools/graphify_link.py`, `tools/graphify_prune.py`, `Makefile`

## Assumptions / Open Questions
- `.claude/settings.json` is a governing file: any edit to it needs direct user confirmation (AskUserQuestion) at the time.

## Implementation Notes
Owner decisions 2026-10-26, in agent-working-planner's terminal (logged on #715 issuecomment-6401808628; batch assigned on #715 issuecomment-6401480227):
1. Resolution: a make target points `~/.local/bin/graphify` at `.venv-knowledge/bin/graphify` (run once per host), plus a SessionStart advisory line that warns when the `graphify` resolved from PATH does not report the pinned graphifyy version. No `.claude/settings.json` or `CLAUDE.md` edit. Reason: the shim covers the edit hook AND every bare `graphify query` an agent runs; a hook-only path change would leave agents' queries on 0.6.7.
2. The shared graph is rebuilt once under the pin (`graphify extract --force`, or the documented full rebuild, then `tools/graphify_prune.py`) from the main checkout on `main`, right after this batch merges, on host ubuntu. u24desktop rebuilds after its own shim is in place (lead-planner-u24 is told through lead-planner).
3. Measured on host ubuntu by lead-planner 2026-10-25: `~/.local/bin/graphify` = user-site graphifyy 0.6.7; `.venv-knowledge` = 0.9.70; 0.9.70 warns that `~/.copilot/skills/graphify` is from 0.6.7 (report whether the shim run should refresh it; do not change it without asking). u24desktop's values come through lead-planner.
4. The advisory must fail open (missing venv, missing binary, slow `--version`: print nothing), like the other SessionStart checks. The make target must refuse to overwrite a `~/.local/bin/graphify` that is neither the user-site 0.6.7 script nor already the shim, and print what it did.

## Test Summary

## Files Changed

## Completion Summary
