---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL
phase: open
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL

## Title
Phase 2 epic: apply the test-architecture capabilities to the social domain (one batch)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

Phase 1 (Epics A–D) closed on 2026-10-03 (#290). The roadmap says scale-out needs a new owner
decision. This epic carries the Phase 2 plan's single batch for social. **HOLD: no child ticket may
be activated until the owner approves the plan** (`docs/plans/test_architecture/phase2_social_scale_out.md` §9).

## Scope

The six batch items in the plan's §6:
1. Locate: coverage, markers, placement audit.
2. Run: a lane routing test for `src/systems/social_systems/**`, and a scenario-gap record.
3. Oracle map: social tests to ledger ids, P0 first.
4. Effectiveness: one mutation baseline, on `appraisal.py` (fallback `contracts.py`).
5. Workflow: observe only.
6. Triage: a social owner-routing row.

All of the plan's §5 entry gates (G1–G4) must hold before the first child activates.

## Out of Scope

- RPG behaviour or expectation changes.
- Applying ledger status changes or test links. Those are proposed to `rpg-feature-planning`.
- Party (`party*.py`, D-P).
- `src/domains/perception/` and dormant paths.
- Writing social mechanic scenarios.
- Required-check promotion, §9 cleanup, new CI jobs.
- Any other domain.

## Acceptance Criteria

- [ ] The owner approval is recorded in the plan's §9 before any child activates.
- [ ] G2 (social quiet, naming the two 2026-08-22 todos), G3 (determinism stance stated per target)
  and G4 (Rule classification) are each recorded with source and date.
- [ ] Items 1–6 each have an output as listed in the plan's §6, or an honest "not done" with its
  reason.
- [ ] The mutation baseline records the target, selection, full SHA, date, runtime, result
  categories, `stale_after`, and whether the kernel ran.
- [ ] The oracle-map findings list the P0 entries without `test_path`, the 3 divergent entries,
  SOC-052, and the ch07 Bible-table gap. Each is routed to `rpg-feature-planning`.
- [ ] A batch review is recorded against the roadmap §2 measures, with sample sizes, and the owner's
  next-domain or stop decision.

## Related Tickets

- Phase 1: `agent-working/tickets/done/test-architecture/` (Epics A–D, INDEX.md).
- Overlap to re-confirm (G2): `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` and
  `TCK-20260822-SOCIAL-MEMORY-DECISION-CONTEXT`.

## Related Docs

- `docs/plans/test_architecture/phase2_social_scale_out.md`
- `docs/plans/test_architecture/roadmap.md`
- `docs/mechanics/07_social_political_dynamics.md`
- `docs/parity_ledger/social_narrative.yaml`
- `docs/simulation/social_systems_contract.md`
- `docs/simulation/domains/social_memory_contract.md`
- `docs/world_rules/social-lineage/`
- `docs/engine/deterministic_execution.md`

## Related Stored Artifacts

- `tests/mutation/baselines/src_core_conservation_v3.json` (the provenance template)

## Related Code Areas

- `src/systems/social_systems/` (party excluded)
- `tests/unit/social/`
- `tools/test_architecture/scenario_lane_paths.py`

## Assumptions / Open Questions

These are the plan's §9 questions 1–5. Figures are as of `2f520f0dd`, and the epic re-measures at
start.

## Implementation Notes

The detail planner creates the children after G1. The reviewer reviews each child PR.

## Test Summary

Not applicable. This is a scope-only epic.

## Files Changed

None yet.

## Completion Summary

Not complete.
