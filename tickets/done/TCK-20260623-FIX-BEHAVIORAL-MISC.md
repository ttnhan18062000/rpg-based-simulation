---
status: done
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260623-FIX-BEHAVIORAL-MISC
phase: done
date: 2026-06-23
tags: [test-repair, ci-gate, rejection-audit, hunger, pipeline, P2]
---

# TCK-20260623-FIX-BEHAVIORAL-MISC

## Title
Fix remaining behavioral regression tests — CI gate / rejection audit / hunger (~4 failures)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Four integration failures that each have distinct root causes but share low failure breadth.
Implement this ticket AFTER all P0/P1 repair tickets land, as some may resolve as cascades.

**1 — CI Gate returns WARNING instead of PASS:**
```
integration/observability/test_scenario_level_report_flow.py:
  assert 'CI Gate Evaluation Result: PASS' in output
  actual: 'CI Gate Evaluation Result: WARNING'
```
CI gate threshold or scoring formula changed. The gate now produces WARNING for a scenario
that previously passed. Either the scoring weights shifted (via balance tuning) or an
outlier run detection threshold changed.

**2 — Rejection audit events not captured:**
```
integration/pipeline/test_rejection_audit.py:
  AssertionError: Expected rejection audit events, but none were captured.
```
Pipeline no longer emits rejection audit events. This may be a cascade from the kernel
phase contract change (TCK-20260623-FIX-KERNEL-PHASES) — if `_phase_init` or audit
emission was restructured, the events may be emitted under a different name or not at all.

**3 — Hunger satiation never completes in 400 ticks:**
```
integration/scenarios/test_hunger_satiation.py:
  AssertionError: No HUNGER project reached COMPLETED status in 400 ticks
```
Hunger-satiation loop broken in scenario context. May cascade from:
- TCK-20260623-FIX-WORLDASSEMBLY (food resource nodes missing if content validation blocks world assembly)
- TCK-20260623-FIX-INVENTORY-DEFAULTS (inventory full blocks food pickup)
- Or independent regression in hunger urgency / quest generation logic

**4 — Phase skip parity (62 unexpected skips):**
```
integration/optimization/test_phase_skip_parity.py:
  Expected 0 phase skips during reference full run, got 62 skips.
```
Phase-skipping logic is now triggering 62 times during a run that should have zero skips.
Likely a cascade from TCK-20260623-FIX-KERNEL-PHASES (`_phase_init` restructuring changed
when phase eligibility conditions are evaluated).

## Scope
- Implement AFTER P0/P1 tickets: FIX-WORLDASSEMBLY, FIX-KERNEL-PHASES, FIX-INVENTORY-DEFAULTS
- Re-run all 4 tests after P0/P1 land; remove from scope any that resolve as cascades
- For remaining failures: trace each to its source and fix
- CI gate: check if gate threshold constant changed or if scoring weights changed
- Rejection audit: check if audit event type/name changed in the pipeline
- Hunger satiation: if still failing after content + inventory fixes, trace the hunger
  urgency → project generation → completion path
- Phase skip: if still failing after kernel fix, check phase-skip eligibility conditions

## Out of Scope
- New CI gate features
- Rejection audit redesign
- Hunger mechanic changes beyond aligning with Mechanics Bible

## Acceptance Criteria
- `tests/integration/observability/test_scenario_level_report_flow.py::test_cli_gate_scenario_level_flow` passes
- `tests/integration/pipeline/test_rejection_audit.py::test_rejection_audit_aggregation` passes
- `tests/integration/scenarios/test_hunger_satiation.py::test_hunger_satiation_resolves_in_food_world` passes
- `tests/integration/optimization/test_phase_skip_parity.py::test_phase_skip_parity` passes

## Related Tickets (prerequisites — implement those first)
- TCK-20260623-FIX-WORLDASSEMBLY (P0) — may resolve hunger satiation
- TCK-20260623-FIX-KERNEL-PHASES (P0) — may resolve phase skip + rejection audit
- TCK-20260623-FIX-INVENTORY-DEFAULTS (P1) — may resolve hunger satiation

## Related Docs
- `docs/mechanics/05_world_evolution.md` (ecology / hunger pressure)
- `docs/engine/kernel.md` (phase ordering)
- `docs/parity_ledger/infrastructure.yaml` (CI gate parity)
- `docs/parity_ledger/town_resource.yaml` (hunger/food resource entries)

## Related Code Areas
- `src/observability/reporting/` (CI gate scoring and threshold)
- `src/engine/pipeline_phases/` (rejection audit event emission)
- `src/domains/adventure/` or `src/quests/` (hunger project generation + completion)
- `src/engine/optimization/` (phase skip eligibility)
- `tests/integration/observability/`
- `tests/integration/pipeline/test_rejection_audit.py`
- `tests/integration/scenarios/test_hunger_satiation.py`
- `tests/integration/optimization/test_phase_skip_parity.py`

## Assumptions / Open Questions
- Which failures survive after P0/P1 tickets land? (Re-evaluate before starting this ticket)
- Did rejection audit events change name? Check `src/engine/pipeline_phases/` for audit event emission

## Implementation Notes
All 4 failures resolved as cascades after P0/P1 tickets landed. No code changes needed in
this ticket.

- CI gate WARNING→PASS: resolved by TCK-20260623-FIX-CONTENT-REGISTRY (content families now
  registered, warmup no longer hits hot-path violations that inflated run cost)
- Rejection audit events: resolved by TCK-20260623-FIX-DOCS-INTEGRITY (kernel phase pipeline
  contract corrected; audit emission now reaches the correct phase)
- Hunger satiation: resolved by TCK-20260623-FIX-WORLDASSEMBLY + FIX-INVENTORY-DEFAULTS
  (food nodes present, inventory defaults allow pickup)
- Phase skip parity: resolved by TCK-20260623-FIX-KERNEL-PHASES (phase eligibility logic
  restored to reference behavior)

## Test Summary
Run: `pytest tests/integration/observability/test_scenario_level_report_flow.py::test_cli_gate_scenario_level_flow tests/integration/pipeline/test_rejection_audit.py::test_rejection_audit_aggregation tests/integration/scenarios/test_hunger_satiation.py::test_hunger_satiation_resolves_in_food_world tests/integration/optimization/test_phase_skip_parity.py::test_phase_skip_parity --tb=short`
Result: 4 passed

## Files Changed
None — all failures resolved by prior tickets.

## Completion Summary
All 4 acceptance criteria met via cascade resolution. Zero code changes in this ticket.
