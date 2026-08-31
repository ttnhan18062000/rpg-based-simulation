---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260831-METAMORPHIC-LAB-PILOT
phase: open
date: 2026-08-31
tags: [testing]
---

# TCK-20260831-METAMORPHIC-LAB-PILOT

## Title
Run a real-content pilot for the metamorphic lab tool before idea 37

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
src/lab/metamorphic.py is real and CI-tested but has never been run against real content. Run one small, low-stakes, throwaway pilot before idea 37's ticket starts, to prove the tool works end-to-end on real data shapes — real WorldSpec/ScenarioSpec-authored data, real run_report.json-derived metrics, and a real on-disk lab artifact, not synthetic fixtures.

## Scope
- Author a small MutationSpec targeting a real WorldSpec-addressable field — ResourceNodeSpec.regen_rate or ResourceNodeSpec.count (src/worldbuilding/schema.py:164-171) — inside an existing data/worlds/*/world.yaml, since CampService's constants (src/world/camp.py:17-19) are hardcoded Python class attributes with no WorldSpec field and cannot be targeted.
- Validate the MutationSpec via `python -m src.lab.cli validate-mutation`.
- Run it end-to-end via `run-mutation`, producing a real LabRunManifest and on-disk artifact under the code-verified real path data/lab_runs/ (src/lab/repository.py:303-305, CLI default) — neither data/lab_runs/ nor data/lab_sessions/ exists on disk today.
- Run MetamorphicRuleEngine.evaluate_rules() against the resulting real (not hand-built) variant_metrics and confirm it produces PASSED or FAILED (not INSUFFICIENT_DATA) for a real metric name.
- Verify and flag the doc/code parity gap between docs/simulation/lab_contract.md's stated data/lab_sessions/ path and the real data/lab_runs/ path used by code, for a follow-up doc parity fix if confirmed unintentional.
- Clean up / explicitly mark pilot artifacts as throwaway at ticket close.

## Out of Scope
- Do not target CampService's MATURITY_PER_TICK/RAID_MATURITY_THRESHOLD/CAMP_SPAWN_INTERVAL constants — confirmed not WorldSpec-addressable, contradicts the epic's own suggested example.
- Do not build idea 37's race-relations matrix content or mutation logic (owned by the race-relations-matrix ticket, which is gated on this one landing first).
- Do not silently fix the lab_contract.md doc/code parity gap in this ticket beyond flagging it for a separate doc fix.

## Acceptance Criteria
- [ ] A MutationSpec targeting a real ResourceNodeSpec.regen_rate/count field inside a real data/worlds/*/world.yaml validates via `python -m src.lab.cli validate-mutation`.
- [ ] Running it end-to-end via `run-mutation` produces LabRunManifest.status != FAILED for both variants and a real on-disk artifact under the code-verified real path (data/lab_runs/, not the doc's stated data/lab_sessions/).
- [ ] MetamorphicRuleEngine.evaluate_rules() against the resulting real (not hand-built) variant_metrics produces a PASSED or FAILED result (not INSUFFICIENT_DATA) for a real metric name.
- [ ] Pilot artifacts are explicitly cleaned up / marked throwaway at ticket close.

## Related Tickets
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY
- TCK-20260612-LAB-CONTRACT
- TCK-20260523-METAMORPHIC-VALIDATION
- TCK-20260523-MUTATION-ORCHESTRATION
- TCK-20260523-LAB-ORCHESTRATOR

## Related Docs
- docs/simulation/lab_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/lab/metamorphic.py
- src/lab/mutation_orchestrator.py
- src/lab/mutation.py
- src/lab/schema.py
- src/lab/cli.py
- src/lab/repository.py
- src/world/camp.py
- src/worldbuilding/schema.py

## Assumptions / Open Questions
- CampService constants are NOT usable as the pilot target — must use ResourceNodeSpec instead; this contradicts the epic's own suggested example and is flagged explicitly.
- docs/simulation/lab_contract.md's data/lab_sessions/ claim should be verified against real code and flagged for a doc parity fix if confirmed unintentional, not silently trusted.
- No data/experiments/, data/scenarios/, or data/mutations/ directories exist yet — a small ScenarioSpec/ExperimentSpec/MutationSpec needs to be authored from scratch.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
