---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-PLANNER-MAY-WRITE-STAGING-ARTIFACTS
phase: open
date: 2026-10-20
tags: [governance, agent-monitoring]
---

# TCK-20261020-PLANNER-MAY-WRITE-STAGING-ARTIFACTS

## Title
Every planner role may write agent-working/staging_artifacts/**, so starting a ticket's staging artifacts stops raising a role_boundary warning

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
From RETRO-2026-W43's final note (40 runs), item 3, proposal D. The owner approved it on 2026-10-20, relayed by lead-planner.

W43 has one `role_boundary` `edit_outside_owns` warning: platform-planner-u24 wrote `agent-working/staging_artifacts/TCK-20261019-SECRET-STATIC-SCAN-WORKFLOW/investigation.md` for its own ticket.

Planner roles' `capability.may_write` includes `agent-working/tickets/**` but not `agent-working/staging_artifacts/**`. A standard-tier dispatch, though, expects the planner to start `plan.md`, `investigation.md` and `test_plan.md` up front; done_checker FAILs without them. So the warning fires on expected work, which is a false-positive class.

## Scope
1. **`registries/session_roles.yaml`.** Add `"agent-working/staging_artifacts/**"` to `capability.may_write` of every role with `function: planner` that already lists `agent-working/tickets/**`. Skip any that already have it (asset-planner may). From the current file, that's rpg-, agent-working-, testing-, codebase-, perf-, lead-, lead-u24-, platform-, platform-u24- and agent-working-u24-planner. Recheck the list against the file.
   - Designers and implementers are unchanged. Implementers have `**`.
   - Follow `docs/guidelines/session_roles/host_suffixed_twins.md`: a `-u24` twin copies its plain twin's `may_write`.
2. **Regenerate** whatever the registry generates: role cards via `tools/sessions/generate_agents.py`, and any doc tables. Their checks must pass. Don't hand-edit the generated `.claude/agents/session-*.md` cards.
3. **Tests.** A `tools/sessions/boundary.py` test: a planner writing `agent-working/staging_artifacts/<id>/plan.md` gets no `edit_outside_owns` warning. A planner writing another domain's path (e.g. `src/x.py`) still does. Run the session-layer tests under `tests/tools/` that cover the roster, boundary and card generation.

## Out of Scope
- Any change to `owns`, `route` or dispatch rules.
- Other `role_boundary` kinds.
- Backfilling or deleting the past warning rows.

## Acceptance Criteria
- Every planner role with `agent-working/tickets/**` in `may_write` also has `agent-working/staging_artifacts/**`.
- The generated cards are regenerated and their drift checks pass.
- The boundary test shows no warning for a planner's staging-artifact write and still warns for a foreign-domain write.

## Related Tickets
- The session-layer roles tickets that introduced `capability.may_write` and `role_boundary` (see `docs/plans/agent_infrastructure/session_layer_working_process.md`)

## Related Docs
- agent-working/agent-monitoring/retro/RETRO-2026-W43.md (final note, item 3)
- docs/guidelines/session_roles/host_suffixed_twins.md

## Related Stored Artifacts
- none

## Related Code Areas
- registries/session_roles.yaml, tools/sessions/roster.py, tools/sessions/boundary.py, tools/sessions/generate_agents.py

## Assumptions / Open Questions
- A planner writes staging artifacts only for tickets in its own domain. The boundary hook can't tell whose ticket a staging dir belongs to, and this ticket doesn't try. That's accepted as advisory-only noise reduction.

## Implementation Notes
- 2026-10-20 (agent-working-planner): owner yes (via lead-planner). Batch 7, dispatched to agent-working-implementer.

## Test Summary

## Files Changed

## Completion Summary
