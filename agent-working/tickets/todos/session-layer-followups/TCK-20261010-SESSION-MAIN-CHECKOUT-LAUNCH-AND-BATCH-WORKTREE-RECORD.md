---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD
phase: open
date: 2026-10-10
tags: [ai, process-improvement, governance]
---

# TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD

## Title
Make launching from the main checkout a supported policy, record each implementer's per-batch worktree in role state, and reconcile the function cards

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Practice and the written contract disagree.

**Practice on host ubuntu (2026-10-10).** Every seat launches from the main checkout. Implementers
open a fresh worktree per batch at `~/Work/rpg-<batch>` (codebase-implementer's confirmation on
#476). Planners mostly read and commit only small doc/ticket branches.

**Owner decision (2026-10-10, relayed by lead-planner on #476).**
- Read-mostly seats (lead, planners, designers) launch from the main checkout.
- Implementers get a fresh worktree per batch.
- The launcher records which batch worktree an instance uses.
- asset-planner needs no worktree of its own.

**Written contract.** `docs/guidelines/session_roles/functions/planner.md` (`## Worktree`) and
`designer.md` still say "a designer or planner works in its own worktree and branch (named after the
role)". `status.py` shows every seat against a manifest worktree (`asset-planner`, `perf`, …) that
does not exist on this host.

The result: `status.py` cannot tell where an implementer is actually writing, and the lease (see the
sibling hotfix) attaches to the wrong path.

## Scope
- **Policy.** A role entry may declare that it launches from the main checkout and holds no lease
  there. Planners, designers and the lead default to this. Implementers keep per-batch worktrees.
  Whether this is a new `placement` value or a function default is the planner's call; keep it
  validator-checked.
- **Record.** When an instance is bound to a worktree other than its launch directory (the
  implementer's batch worktree, via `launch.py --worktree <batch path>` or the first commit there),
  record that path in the role state. `status.py` shows it per seat (`writing in: <path>`), and the
  per-batch worktree takes the lease.
- **Cards.** Update the `## Worktree` sections of `functions/planner.md` and `designer.md`, and the
  implementer card if needed, to state the policy above. Regenerate the `.claude/agents/session-*.md`
  files. Stay within the 400-token budget.
- **Plan.** Amend `session_layer_working_process.md` §4/§8 and record the owner decision of
  2026-10-10 in §12.3.

## Out of Scope
- The lease-on-launch-cwd bug itself (sibling hotfix
  `TCK-20261010-SESSION-LEASE-TAKEN-ON-LAUNCH-CWD-NOT-MANIFEST-WORKTREE`; land it first).
- Cross-host visibility of these records (Epic E, E3 heartbeat).
- Pruning or creating batch worktrees automatically.

## Acceptance Criteria
1. The validator accepts the main-checkout launch policy and rejects contradictory combinations,
   for example a writer that also declares "main checkout, no lease".
2. After an implementer starts a batch in `~/Work/rpg-<batch>`, `status.py` shows that path for the
   seat, and the lease sits on that batch worktree, not on the main checkout.
3. The planner and designer cards state the policy, and the generated agent files match the manifest
   (generator check passes).
4. The plan amendment cites the owner decision of 2026-10-10.
5. `pytest tests/tools/test_session_*.py tests/docs` passes.

## Related Tickets
- `TCK-20261010-SESSION-LEASE-TAKEN-ON-LAUNCH-CWD-NOT-MANIFEST-WORKTREE` (land first)
- `TCK-20261007-SESSION-PER-ROLE-WORKTREES`
- `TCK-20261009-REGISTER-OTHER-HOST-SEATS` (PR #476, where the question was raised)
- `TCK-20261009-EPIC-SESSION-LEAD-PLANNER` (E2 fleet view consumes the record)

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` §4, §5, §8, §12.3
- `docs/guidelines/session_roles/functions/{planner,designer,implementer}.md`

## Related Stored Artifacts
None.

## Related Code Areas
`tools/sessions/launch.py`, `tools/sessions/state.py`, `tools/sessions/status.py`,
`tools/sessions/validate.py`, `tools/sessions/generate_agents.py`, `registries/session_roles.yaml`

## Assumptions / Open Questions
- Whether "first commit in a batch worktree" can be detected cheaply (for example by the guard
  hook), or whether recording needs an explicit `launch.py --worktree` relaunch. The planner decides
  this from investigation.
- `registries/session_roles.yaml` edits are governing-file class, so the owner confirms the literal
  diff.

## Implementation Notes
(Open.)

## Test Summary
(Open.)

## Files Changed
(Open.)

## Completion Summary
(Open.)
