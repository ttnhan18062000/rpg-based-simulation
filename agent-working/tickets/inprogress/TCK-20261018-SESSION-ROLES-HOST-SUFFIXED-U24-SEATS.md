---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS
phase: open
date: 2026-10-18
tags: [ai, process-improvement, governance]
---

# TCK-20261018-SESSION-ROLES-HOST-SUFFIXED-U24-SEATS

## Title
Register host-suffixed `-u24` roles for the platform and agent-working seats that run on host u24desktop

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
GitHub #620 part 1. **Owner decision 2026-10-18, option (a)**, relayed by lead-planner and posted on #620/#634.
- The same role names now run on two hosts:
  - platform since #618;
  - agent-working since #634.
- `registries/session_roles.yaml` has one entry each with `max_sessions: 1`. Leases, handover and runtime state are per host, so neither host sees the other's holder.
- `--name`/`session_name` collide, and monitoring shards keyed by role plus batch can collide.
- Follow the `lead-planner-u24` precedent (TCK-20261013-HOST-LEAD-PLANNER-U24):
  - u24desktop seats get a `-u24` suffix;
  - host ubuntu keeps the plain names.

## Scope
1. `registries/session_roles.yaml`: add five roles, each with the comment `# runs on host u24desktop (#620, owner 2026-10-18)`:
   - `platform-planner-u24`, `platform-implementer-u24` (domain platform);
   - `agent-working-designer-u24`, `agent-working-planner-u24`, `agent-working-implementer-u24` (domain agent-working).
   - Each one mirrors its plain twin's identity/function/capability/handover, with:
     - `session_name` = the role id; `legacy_session_name: null`;
     - `handover: .claude/handover/<role>.md`;
     - `placement.worktree: <role>`, a new distinct worktree, because a worktree hosts exactly one writer role. The u24 seats relaunch once with `launch.py <role>-u24 --worktree <their existing path>` or a fresh `--branch`; document both in the ticket's Completion Summary for u24.
   - `accepts_dispatch_from`, host-local:
     - `agent-working-planner-u24` ← [user, agent-working-designer-u24];
     - `agent-working-implementer-u24` ← [user, agent-working-designer-u24, agent-working-planner-u24];
     - `platform-implementer-u24` ← [user, platform-planner-u24];
     - the designer ← [user].
   - The plain roles' `accepts_dispatch_from` are unchanged unless the owner answers the open question below.
   - `seat_status`/`interim_holder`:
     - plain `agent-working-planner` becomes `staffed` (held on ubuntu since 2026-10-18), and its `interim_holder` is removed;
     - `agent-working-planner-u24` takes `interim_holder: agent-working-designer-u24` unless u24 says it's staffed;
     - plain `agent-working-designer` becomes `unstaffed` (there's no ubuntu designer).
   - **Confirm the u24 rows with u24's designer on #634 before implementation starts.**
2. `card_note` (the existing generator field) on each `-u24` role and its plain twin: one line naming the host and pointing at the twin. Stay within the 400-token card budget.
3. Regenerate `.claude/agents/` (`tools/sessions/generate_agents.py`), so `session-<role>-u24.md` exist.
4. `docs/guidelines/session_roles/`: one short paragraph on host-suffixed twins (when to add one, worktree, handover, shard naming), citing lead-planner-u24 as the first case.
5. Tests in `tests/tools/`:
   - the validator gives 0 findings for the new roster: no duplicate session_name, and one writer per worktree;
   - `tools.sessions.route` still routes each owned path to the **plain** seat (the domain's primary) and doesn't fail or become ambiguous because of a twin;
   - each `-u24` card contains its card note and is ≤ 400 tokens;
   - `launch.py <role>-u24 --dry-run` resolves its own worktree path and handover;
   - `boundary.py`: each `-u24` role's write grant equals its twin's.

## Out of Scope
- Making `max_sessions`/leases host-aware (option b) or cross-host liveness.
- Renaming any live session. The u24 seats relaunch themselves after the merge; this ticket only registers the roles.
- lead/codebase/asset/perf/rpg/testing seats.

## Acceptance Criteria
- The five roles are registered and validate cleanly; agent files are generated; the route/boundary/card/launch tests pass.
- The PR states that the roles diff needs the **owner's confirmation in the PR** (lead-planner asks the owner).
- #620 and #634 get a comment with the relaunch command per u24 seat.

## Related Tickets
- TCK-20261013-HOST-LEAD-PLANNER-U24 (precedent), TCK-20261009-REGISTER-OTHER-HOST-SEATS, TCK-20261018-LAUNCH-RESUME-MISSING-WORKTREE-REFUSE

## Related Docs
- docs/guidelines/session_roles/, docs/guides/cross_session_messages.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261013-HOST-LEAD-PLANNER-U24/ (if present)

## Related Code Areas
- registries/session_roles.yaml, tools/sessions/{validate,generate_agents,route,boundary,launch}.py

## Assumptions / Open Questions
- **For the owner, via lead-planner:** on ubuntu, agent-working-planner and platform-planner are directed by lead-planner under the 2026-10-11 grant, while their registered dispatchers are user/designer. Should `lead-planner` be added to the plain `agent-working-planner` and `platform-planner` `accepts_dispatch_from`? The default if there's no answer is no change.
- **For u24 (on #634):** the current worktree paths and the staffing of each u24 seat.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
