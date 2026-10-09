---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-REGISTER-OTHER-HOST-SEATS
phase: open
date: 2026-10-09
tags: []
---

# TCK-20261009-REGISTER-OTHER-HOST-SEATS

## Title
Six sessions running on the other host (asset, perf and codebase planners and implementers) are missing from the session-role registry or marked unstaffed

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
On 2026-10-09 the owner asked agent-working-planner to register asset-implementer, asset-planner, codebase-implementer, codebase-planner, perf-implementer and perf-planner, which run on the other machine. Context those sessions hold is collected by PR comment. Before this ticket, `registries/session_roles.yaml` had no `asset` or `perf` domain and listed both codebase seats as `unstaffed` with agent-working interim holders. So `launch.py` refused the asset and perf names, the sessions got no generated role card, and route and dispatch checks could not name them.

## Scope
- `registries/session_roles.yaml`:
  - new domains `asset` and `perf` with `owns` and `routes`;
  - two `ownership_splits` (`tests/visual_assets/**` shared by rpg and asset; `src/perf/**` and `tests/perf/**` shared by rpg and perf);
  - four roles (`asset-planner`, `asset-implementer`, `perf-planner`, `perf-implementer`) and four worktrees;
  - `codebase-planner` and `codebase-implementer` set to `staffed`.
- `docs/guidelines/session_roles/domains/{asset,perf}.md` card templates.
- The regenerated `.claude/agents/session-*.md`.
- The owned paths, dispatch sources and card text are drafted from the repo: `docs/assets/session_handoff/*`, the perf roadmap's "Ownership model" section (2026-10-02) and `docs/plans/codebase_health/handoffs/session/*`. Each of the six sessions confirms or corrects them on the PR.

## Out of Scope
- `registries/session_authority.yaml`: the function defaults cover all six. No per-role grant is added, because the own-branch rule already allows push and open_pr. The codebase planner's handover lists an owner-only "codebase-seat diff of session_authority.yaml"; it stays owner-only and is not in this ticket.
- Creating worktrees or handover notes on either host.
- Any designer seat for asset or perf (none exists; the planners take dispatch from the user).

## Acceptance Criteria
- AC1: `python3 -m tools.sessions.validate` passes with 16 roles.
- AC2: `launch.py <each of the six> --dry-run` resolves the role (it may refuse for other reasons, such as a missing worktree on this host).
- AC3: the generate_agents check shows no drift; `pytest tests/tools/test_session_*.py` is green.
- AC4: each of the six sessions has commented on the PR, or the owner waived it, and the corrections are applied.

## Related Tickets
- TCK-20261009-RPG-IMPLEMENTER-THIRD-SEAT (#467)
- TCK-20261009-PER-INSTANCE-HANDOVER-NOTE (pending batch)

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md`
- `docs/assets/session_handoff/`, `docs/plans/codebase_health/handoffs/session/`
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md`

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `registries/session_roles.yaml`, `docs/guidelines/session_roles/domains/`, `.claude/agents/`

## Assumptions / Open Questions
Questions for the six sessions are in the PR body:
- Q1: owned paths per domain.
- Q2: worktree names and physical paths on the other host. Those sessions use `~/Work/rpg-perf` and `~/Work/rpg-aseprite-mcp`, not `.claude/worktrees/<name>`. `launch.py --worktree` covers this, but the registry name still matters for the writer lease.
- Q3: current session titles (`legacy_session_name`).
- Q4: dispatch sources.
- Q5: card text.
- Q6: whether the perf or asset planner should own `docs/engine/performance_contract.md` or the frontend art wiring.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
