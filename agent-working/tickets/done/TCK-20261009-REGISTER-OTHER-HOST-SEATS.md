---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261009-REGISTER-OTHER-HOST-SEATS
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-REGISTER-OTHER-HOST-SEATS

## Title
Seven sessions on host ubuntu (asset, perf and codebase planners and implementers, and lead-planner) are missing from the session-role registry or marked unstaffed

## Status
DONE

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
- AC1: `python3 -m tools.sessions.validate` passes with 17 roles (lead-planner added on the owner's request, relayed on PR #476).
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
- All seven seats commented on PR #476 on 2026-10-09, and their corrections are applied:
  - Seat comments name host `ubuntu`.
  - asset adds `frontend/src/visualAssets/**`, `frontend/rehearsal-capture/**` (split with rpg) and its ADR. Its plan dirs are compacted to `docs/plans/visual-asset-*/**`.
  - perf adds its PERF-D file, `tests/unit/perf/**`, `perf_baselines.json` and `tests/tools/perf_assertions.py` (split with rpg and with agent-working).
  - Planner `may_write` adds `agent-working/agent-monitoring/**`, `docs/REGISTRY.yaml` and, for asset, staging artifacts.
  - The card text is the seats' wording, compressed to the 400-token budget. codebase gains the `test.yml` / decision 8.11 clause.
- New domain `lead` with one planner seat (`lead-planner`). It owns the tech-stack roots and `docs/architecture/**`, and asset's ADR and perf's PERF-D file are split out. No role accepts dispatch from it, and a test checks that.
  - `agent-working/lead/**` is left out until a file exists on main, since an owns glob must match a file.
  - `.github/workflows/pr-body-lint.yml` is NOT given to lead. It is delivery's (agent-working), left unowned for now, because adding it to agent-working pushed agent-working-planner's card over budget.
- Routes that only repeated another domain's ownership were dropped from asset and perf (`.claude/**`, `.mcp.json`, `test.yml`) to keep their cards within budget. route.py still finds those owners by their `owns`.
- Not changed here (open for the owner): how launch.py should model seats that launch from the main checkout and write in per-batch worktrees (`~/Work/rpg-<batch>`). It was raised by codebase, perf and asset. The registry keeps a named placement; physical paths are in comments and go through `launch.py --worktree`. asset-planner's sequential planning commits inside the implementer's worktree are a second writer under today's rule, and the owner decides on its proposed own worktree.

## Test Summary
- `python3 -m tools.sessions.validate`: OK, 0 findings, 17 roles.
- `pytest tests/tools/test_session_*.py tests/docs`: 664 passed, 1 skipped, 1 xfailed. The pins moved from 12 to 17 by owner request; the lead no-dispatch assert is new.
- Card budget: highest is agent-working-planner at 400 (unchanged); the new seats are 391 or less (perf-planner 399).
- `launch.py <seat> --dry-run` resolves every new seat. On host u24desktop-Virtual-Machine each then stops at its missing worktree, which is expected.
- `route.py`: the split files report `split`, `pyproject.toml` is owned by lead, and `pr-body-lint.yml` is unowned.

## Files Changed
- `registries/session_roles.yaml`
- `docs/guidelines/session_roles/domains/{asset,perf,lead,codebase}.md`
- `.claude/agents/session-{asset,perf}-{planner,implementer}.md`, `session-lead-planner.md`, `session-codebase-{designer,planner,implementer}.md`
- `tests/tools/test_session_roster.py`, `tests/tools/test_session_agent_generator.py`

## Completion Summary
The six other-host seats and lead-planner are registered with the ownership, dispatch and card text their sessions confirmed on PR #476. The launcher resolves all of them; on host ubuntu they launch with `--worktree` where the physical path differs. Open for the owner: launcher support for main-checkout launch with per-batch worktrees, and asset-planner's own worktree.
