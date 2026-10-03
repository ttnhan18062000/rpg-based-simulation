---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL
phase: done
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-EPIC-TEST-SCALE-OUT-SOCIAL

## Title
Phase 2 epic: apply the test-architecture capabilities to the social domain (one batch)

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary

Phase 1 (Epics A–D) closed on 2026-10-03 (#290). The roadmap says scale-out needs a new owner
decision. This epic carries the Phase 2 plan's single batch for social. The owner approved the plan on 2026-10-03
(`docs/plans/test_architecture/phase2_social_scale_out.md` §9), with the recommended answers and one
constraint: **RPG feature tests are read-only in this batch.** Child tickets still wait for gate G2.

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
- Editing, moving, marking or strengthening any RPG feature test (owner constraint, 2026-10-03). The only test change is the tooling routing case in `tests/unit/tools/test_scenario_lane_paths.py`.
- Applying ledger status changes or test links. Those are proposed to `rpg-feature-planning`.
- Party (`party*.py`, D-P).
- `src/domains/perception/` and dormant paths.
- Writing social mechanic scenarios.
- Required-check promotion, §9 cleanup, new CI jobs.
- Any other domain.

## Acceptance Criteria

- [x] The owner approval is recorded in the plan's §9 (2026-10-03).
- [x] No RPG feature test file is changed by any child PR. The reviewer checks each diff.
- [x] G2 (social quiet, naming the two 2026-08-22 todos), G3 (determinism stance stated per target)
  and G4 (Rule classification) are each recorded with source and date.
- [x] Items 1–6 each have an output as listed in the plan's §6, or an honest "not done" with its
  reason.
- [x] The mutation baseline records the target, selection, full SHA, date, runtime, result
  categories, `stale_after`, and whether the kernel ran.
- [x] The oracle-map findings list the P0 entries without `test_path`, the 3 divergent entries,
  SOC-052, and the ch07 Bible-table gap. Each is routed to `rpg-feature-planning`.
- [x] A batch review is recorded against the roadmap §2 measures, with sample sizes, and the owner's
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

The plan's §9 questions 1–5 were answered on 2026-10-03. Figures are as of `2f520f0dd`, and the epic re-measures at
start.

## Implementation Notes

The detail planner creates the children after G1. The reviewer reviews each child plan before
implementation, then the one batch PR. Children created 2026-10-03 (order in `SEQUENCE.md`):
`TCK-20261003-SOCIAL-LANE-ROUTING-CASE-AND-SCENARIO-GAP` (hotfix),
`TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING`, `TCK-20261003-SOCIAL-ORACLE-MAP-REPORT`,
`TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE` (standard). Plan item 5 has no ticket.

## Test Summary

Not applicable: this is a scope-only epic. Children ran their own checks: the routing case file 27 passed,
the social selections 296 and 372 passed, the mutation selection 313 passed, and the baseline-record shape
tests 9 passed.

## Files Changed

None directly. Through the children: `tests/unit/tools/test_scenario_lane_paths.py` (one case),
`tests/mutation/baselines/src_systems_social_appraisal_v1.json` (data), `docs/testing/social_test_report_2026-10-03.md`,
one row of `docs/plans/test_architecture/reference/architecture_design_notes.md` §3.1, and the Phase 2 plan, roadmap and
Epic B cost-record updates.

## Completion Summary

**Closed 2026-10-03.** The four children (`TCK-20261003-SOCIAL-LANE-ROUTING-CASE-AND-SCENARIO-GAP`,
`TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING`, `TCK-20261003-SOCIAL-ORACLE-MAP-REPORT`,
`TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE`) are done and each was accepted by test-architecture-reviewer.
No RPG feature test file was changed (the batch's only test paths are the routing case and the baseline data
file). Gate evidence: G2 and G4 are recorded in the plan section 5, and G3 in the baseline record (the kernel
ran in 3 selected files; `audit_mode` and the tick budget were forced in a scratch plugin only). The oracle-map
findings were routed to `rpg-feature-planning` on 2026-10-03. The batch review is in the shared report, section 5.
**Owner decision (2026-10-03, relayed by test-architecture-reviewer): pause scale-out after social.** No next
domain is chosen; watch items (a)-(e) in the roadmap section 6 continue.
