---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS
phase: active
date: 2026-10-20
tags: []
---

# TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS

## Title
Every seed of a world emits the same (id, group, key) rows, taken from declared domains, with true zeros; a share is two count rows and a pooled row

## Status
INPROGRESS

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Run 39212800104's documents are sparse: a row exists only when something happened, so seeds of one world carry different row sets and the candidate step refuses ("every seed must report the same rows"). Testing ruled (TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED) that the row set is declared, never observed, and an absent row is never read as 0. Designer ruling on shares: a share is not a run row; its numerator and denominator are two dense count run rows, the share is a pooled row only (sum num / sum den), and `value: null, reason: "empty_denominator"` when the pooled denominator is 0.

## Scope
- `src/observability/rpg_gate_metrics.py`: GROUPS = the kind groups of the world compiled for each seed of the gate config's seed set before any tick (union); death causes = the `DeathCause` enum; transfer sources = `TRANSFER_SOURCES` (a declared tuple, kept equal to every `source_kind` literal under src/ by a unit test); O3 groups = declared groups with a meat diet and at least one declared body without the trade trait.
- Rows emitted on every seed: O1.starved, O1.at_risk, O2.survivors, O2.population (every sampled tick plus the final), O2.deaths (group x every DeathCause), O3.attacks_on_people (every declared wild meat-eater), O4.accepted (group x every declared source), O6.* and the validity rows. Value 0 when nothing happened.
- O1.starvation_share is now a pooled row only (starved sum / at-risk sum per group; null with reason empty_denominator when the sum is 0); it names its `numerator` and `denominator` rows.
- Something seen in a run outside its declaration (group, death cause, source, wild meat-eater) raises GateDataMissingError (no-data), except a group whose only way in was an UNSOURCED add, which V8 already fails with the entity named.
- Tests: unit (two seeds with different events give identical row identities; the enumerations; the source-literal drift guard; the strays raise; the share is two count rows and a null pooled row; numerator/denominator fields), real kernel (two seeds of one world give identical row identities).

## Out of Scope
- k/floor values: proposed by the designer's principle in the module and flagged to the designer; the designer rules.
- Reading authored-arrival spawn declarations to extend the group domain beyond the compiled tick-0 groups (a sourced arrival of a new kind group raises, so the gap is loud, not silent).

## Acceptance Criteria
- Two seeds of one world emit identical (id, group, key, tick) row identities in a unit test and in a real-kernel run; the final state hash is unchanged; observability, rpg_gate and harness tests, mypy, import contracts and code-health are green; the tiny dry chain (harness, report, candidate) passes the same-rows check.

## Related Tickets
- TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED
- TCK-20261019-O2-POPULATION-FLOOR-IS-ONE-VALUE-PER-WORLD

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/rpg_gate_metrics.py

## Assumptions / Open Questions
- Group domain: the compiled tick-0 groups. A kind group that only appears through an authored arrival or a birth of an undeclared species would raise; confirm on the full 3-world x 5-seed run.

## Implementation Notes
Replaces `O1.starvation_share` as a run row (it is no longer a run row). Proposed k/floor (designer to rule): O1.starved and O1.at_risk (2.0, 3.0): the O2.population rule (never under three) with the source row's k; O1.starvation_share (2.0, 0.10): ten points absolute. Flag: the 0.05 share floor of the old fiction ("one more in twenty") is replaced by the principle's 0.10; the designer rules.

## Test Summary
See the report to rpg-planner.

## Files Changed
src/observability/rpg_gate_metrics.py, tests/unit/observability/test_rpg_gate_metrics.py, tests/simulation_quality/rpg_gate/test_v8_fires.py, tests/integration/observability/test_gate_rows_are_the_same_on_every_seed_through_the_real_kernel.py, tests/integration/observability/test_gate_validity_checks_fire_through_the_real_kernel.py (helper takes a seed set)

## Completion Summary
Built; closure is handled when the pre-v1 fixes are combined.
