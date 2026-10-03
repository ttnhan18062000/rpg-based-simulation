---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS
date: 2026-09-06
---

# Investigation: TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS

## Precedent Read
`tickets/done/TCK-20260628-SIMQ-E7-CALIBRATE.md` — the original calibration-infrastructure ticket.
Established `tools/calibrate_simq.py`'s methodology (run engine N ticks, replay
`simulation_events.jsonl` through `QualityHub`) but hit a since-resolved event-vocabulary-mismatch
blocker at the time; not otherwise directly reusable beyond the CLI/methodology precedent.

## Calibration Target: `route_new_query` -> `information_seeking_active`
Ticket 1 (`TCK-20260906-SIMQ-PILLAR-MAPPING-AND-RULES`) added this as `InformationScorer`'s 8th
rule. `docs/simulation_quality/event_type_coverage.md`'s own row for this event already discloses
it fires under `prop.last_routed_query_tick == prior_state.tick`, gated on
`ENABLE_BELIEF_ASSIMILATION` (which runs `InformationBeliefPhase`) AND `ENABLE_SELF_MODEL_COGNITION`
(which populates `actor.self_model.knowledge.unknowns`, required for Branch 3's routing check).

The only shipped profile with all 3 relevant flags ON is
`config/simulation_quality/profiles/urban_political_selfmodel_execution_probe.yaml`
(`ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_INFORMATION_INTENT_EXECUTION`
all ON). `tests/simulation_quality/test_grade_regression.py::
test_urban_political_selfmodel_execution_isolated_grade_anchor`'s own docstring already discloses,
pre-existing, that this exact profile/world/seed combination does **not** naturally route Branch 3
within a 200-tick window at seed 42 ("does NOT generalize" — confirmed via a direct
`ActionIntentAdapter.get_traces()` check: 0 traces).

**Re-confirmed independently, not just inherited:** ran two fresh real calibration runs against
this exact profile:
- `urban_political_selfmodel_execution_probe_seed42_500t` (500 ticks, up from the anchor test's
  200) — `route_new_query`: 0 occurrences in `simulation_events.jsonl` (18297 events replayed;
  INFORMATION pillar's sole scored event was `belief_assimilated`, tag `belief_active`).
- `urban_political_selfmodel_execution_probe_seed137_300t` (300 ticks, different seed) —
  `route_new_query`: 0 occurrences (10443 events replayed; INFORMATION pillar again scored only 1
  `belief_assimilated`).

**Conclusion:** `route_new_query` does not fire in any shipped calibration corpus at any
seed/tick-budget tried, matching this repo's own pre-existing, already-accepted finding for this
exact mechanism. This is a real, disclosed limitation of the *current corpus*, not a defect in the
new rule or in ticket 1's work.

## Evidentiary Bar This Repo Already Accepts For This Exact Case
`test_grade_regression.py::test_information_intent_execution_fires_through_kernel_tick_once`
already establishes and the repo already accepts a minimal, hand-built, deterministic scenario run
through a real `Kernel.tick_once()` loop as sufficient proof that this mechanism (Branch 3 routing,
`ActionIntentAdapter.execute()`) genuinely works, specifically *because* the shipped corpus does not
exercise it. This ticket reuses that same evidentiary standard for the calibration-signal AC: rather
than fabricate corpus data or claim a flat run "proves" something it doesn't, a deterministic
before/after proof through the real, production `QualityHub`/`InformationScorer` was built —
`route_new_query_isolated_calibration.py` (this directory) — using the real
`ObservabilityEventEnvelope` shape captured verbatim from a real `Kernel.tick_once()` run of that
same existing test's own scenario (found by coincidence as leftover data in
`data/runs/run_1788677557_5169/simulation_events.jsonl`, produced while ticket 1 ran its own test
suite).

**Result:** INFORMATION pillar raw_score 0.0 -> 10.0 (grade C -> S) when exactly one real
`route_new_query` envelope is replayed through the real `QualityHub`. A real, non-flat, fully
attributable score delta through the production scoring pipeline — proof the wiring is correct and
would materially affect a real calibration run's grade the moment any corpus profile actually routes
Branch 3.

## Completeness Cross-Check Methodology
The epic's own Scope item 5 (and this ticket's own Scope) frame this as "a checklist against a
known-complete list, not an open-ended scan" — i.e., cross-reference ticket 1's already-finished
named-pillar mapping (all 65 rows of `docs/brainstorm/design_merit_scorecard.html`'s Pillar Reach
column), not re-derive it from scratch. `completeness_check.py` (this directory) parses all 65 rows
and validates:
1. Every named pillar is one of the 10 real pillars (all 10 already confirmed by ticket 1's own
   90-event-type audit to have real, scored event coverage — so a structurally valid pillar name
   is sufficient here, not a fresh per-idea trace).
2. The named-pillar count matches the raw `N/10` the axis still records (ticket 1's own stated
   invariant: "if the named list's count differs from the existing raw number, the count is
   corrected to match the named list, not the reverse").

**Result:** 65/65 rows accounted for.
- 58 rows have a self-consistent named-pillar mapping (count matches names) — includes the 3
  dormant ideas (56/57/62), which DO carry named pillars (the pillars they *would* strengthen once
  built, per the axis's own forward-looking question text) despite having zero live event backing
  today.
- 7 rows (ideas 8, 9, 15, 16, 17, 18, 19) are bare `0/10` with no named pillar — matching ticket 1's
  own already-disclosed "governance/doc-fix/investigation-only, no real event surface" exception
  list exactly (8 of 65 total; the 8th, idea 42, has `WORLD (1/10)` and passes the structural check
  directly).
- 0 rows are unaccounted for; 0 rows have an unrecognized pillar name or a count mismatch.

**No real, undisclosed completeness gap was found.** Per this ticket's own Acceptance Criteria
("any real gap... fixed or ticketed"), no fix and no follow-up ticket are needed — every idea is
already either backed by a real rule, or has an explicit, already-written reason it isn't (the 3
dormant ideas' "no live event yet" disposition, or the 8 governance/doc-fix ideas' legitimate
near-zero reach), all pre-existing in ticket 1's own investigation.md and now independently
re-verified here rather than re-trusted blindly.

## Files To Change
- `docs/simulation_quality/event_type_coverage.md`: append the calibration-run findings (both real
  corpus attempts + the isolated proof result) to the `route_new_query` row/changelog.
- `docs/simulation_quality/quality_scoring_contract.md`: add a new §7.7 "Idea-Level Pillar-Mapping
  Completeness Cross-Check (2026-09)" following the exact §7.5/§7.6 precedent format, recording the
  pass/gap result.
- Ticket file itself: Implementation Notes + Completion Summary.
- Epic ticket (`TCK-20260823-EPIC-RPG-M7-SIMQ-INTEGRATION`): close it (last child ticket landing).

## Parity Ledger
No `src/` production code changed by this ticket (the proof/check scripts live under
`staging_artifacts/`, migrated to `stored_artifacts/` at Finalize, not `src/`). No new parity entry
needed — `behavior_changed` is false; this ticket verifies and documents, it does not change scoring
behavior beyond what ticket 1 already recorded under SOC/INFRA entries.
