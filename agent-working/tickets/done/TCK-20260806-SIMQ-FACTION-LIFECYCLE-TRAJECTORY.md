---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY
phase: done
date: 2026-08-06
tags: [simulation-quality, faction]
---

# TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY

## Title
FACTION — faction-layer lifecycle trajectory signal (parallels WORLD's trauma_hazard_broken)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
FACTION (`quality_scoring_contract.md` §5, lines 681-718) scores diplomatic/territorial events in
isolation, plus three threshold-style checks: `faction_monopoly` (>80% territory by tick 500),
`all_factions_neutral` (zero diplomatic transitions for the whole run), and `tension_oscillation`
(tension cycling without crossing a threshold, >5 cycles). None of these is a full-run
trajectory-coherence check the way WORLD's existing `trauma_hazard_broken` is ("regional trauma
monotonically increasing with no hazard_level effect", line 942) — a rule that catches a degenerate
*trend*, not a single bad event or a static end-state threshold. A faction whose territory/influence
stays essentially flat for an entire run despite ongoing `military_conflict_resolved` and
`diplomatic_transition` events would not trip any existing FACTION rule unless it happens to also
cross the monopoly or all-neutral thresholds — real "faction lifecycle" data (is this faction
actually rising or falling over its life, per `docs/mechanics/05_world_evolution.md`'s Regional
Sovereignty Influence mechanic, ±100 thresholds) is currently invisible to SimQ. Per
`TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC`'s §7.6 finding (implement after that ticket
lands), this is a new FACTION-pillar scoring rule, not a new pillar — region and world layers are
already covered by WORLD's existing rules and are explicitly out of scope here.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm what faction-level trajectory state is queryable at scoring time: aggregate region
     ownership count per faction, Sovereignty Influence value (`docs/mechanics/05_world_evolution.md`
     — Hero Controlled ≥+100, Monster Controlled ≤−100), and whether this is already tracked
     per-faction over time anywhere in engine state or must be derived from
     `region_ownership_changed`/`territory_ownership_changed` event history within the scorer.
   - Design the rule to mirror `trauma_hazard_broken`'s pattern: a monotonic-or-flat trajectory with
     no counter-effect despite active related events (e.g., territory/influence unchanged across a
     window while `military_conflict_resolved` events continue to fire).
   - Confirm (re-verify, do not assume) that region-layer and world-layer coverage is already
     sufficient via WORLD's existing `trauma_hazard_broken`/`world_static`/`trauma_accumulation_broken`
     rules — if this re-check finds a real gap at those layers, flag it as a new finding rather than
     silently expanding this ticket's scope.
2. **Plan**: design the exact rule, delta value, tag name, and any new event/state read needed,
   following §7.2's steps.
3. **Implement**: add the rule to `src/simulation_quality/scorers/faction.py`, weight to
   `config/simulation_quality/scoring_weights.yaml` (no numeric literals in scorer code), update
   FACTION's §5 table and event-type list in `quality_scoring_contract.md`.
4. Recalibrate `grade_anchors.json` for any scenario whose FACTION grade shifts, and update
   `docs/parity_ledger/faction.yaml` per CLAUDE.md's parity rule.

## Out of Scope
- Entity-layer signals — `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s scope.
- Region-layer or world-layer changes — already covered by WORLD's existing rules per this
  ticket's own Investigate re-check; do not modify `world_dynamics.py` unless that re-check finds a
  genuine gap, in which case stop and report it rather than silently expanding scope.
- Any change to diplomatic/military gameplay behavior — observability signal addition only.

## Acceptance Criteria
- [x] `investigation.md` documents what faction-trajectory state is queryable today and confirms
      (or refutes, with a flagged finding) that region/world layers need no change — confirmed
      sufficient, no change needed
- [x] `plan.md` specifies the exact rule, tag, and delta value placeholder
- [x] New FACTION scoring rule implemented in `faction.py`, weight added to
      `scoring_weights.yaml`, no numeric literals in scorer code
- [x] `quality_scoring_contract.md` §5 FACTION table and event-type list updated
- [x] Unit test added for the new rule (weights injected via fixture)
- [x] `docs/parity_ledger/faction.yaml` updated with new entry/status — `FAC-014`
- [x] `grade_anchors.json` recalibrated for any scenario with a shifted FACTION grade — not
      recalibrated: signal verified reachable in principle (unit tests, no crashes in real-kernel
      runs) but did not fire in either of the 2 real-kernel scenarios checked (diplomatic activity
      front-loaded at tick 1 in both, never recurring — a case already covered by the existing
      `diplomacy_dormant` rule), so no anchor shift to recalibrate against
- [x] Scoped pytest run (`tests/simulation_quality/`, FACTION-relevant) passes

## Related Tickets
- TCK-20260806-SIMQ-LIFECYCLE-PILLAR-BOUNDARY-DOC (rationale source — must land first)
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (sibling, entity-layer equivalent)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 FACTION (681-718), §5 WORLD DYNAMICS
  (`trauma_hazard_broken`, line 942, pattern precedent), §7.2 (Adding a Scoring Rule to an Existing
  Pillar)
- `docs/mechanics/05_world_evolution.md` (Regional Sovereignty, Influence thresholds, Regional
  Trauma)

## Related Stored Artifacts
None yet — will be created at `staging_artifacts/TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY/`
during implementation.

## Related Code Areas
- `src/simulation_quality/scorers/faction.py`
- `src/simulation_quality/scorers/world_dynamics.py` (reference only, for the `trauma_hazard_broken`
  pattern — not expected to be modified)
- `config/simulation_quality/scoring_weights.yaml`
- `docs/parity_ledger/faction.yaml`

## Assumptions / Open Questions
- Assumes region/world-layer lifecycle coverage is already sufficient (per this session's doc-scan
  of WORLD's existing rules); this ticket's own Investigate phase must re-confirm rather than trust
  that assumption blindly, per CLAUDE.md's "do not guess when uncertainty affects architecture" rule.

## Implementation Notes
Unlike the sibling PROGRESSION ticket (implemented in `event_extractor.py`, unconditional/not
flag-gated), this ticket implements directly in `FactionShaper` (`event_shapers.py`) — FACTION's
own live-by-default path since Phase 1 of the push-migration epic — since the signal only needs
`FactionUpdate.territory_add`/`territory_remove`/`diplomatic_relations_set`, all typed deltas
`FactionShaper` already reads, with no need for full-snapshot reconstruction. This is the first
cross-tick state `FactionShaper` carries; added `reset_run_state()` and wired it into
`Kernel.__init__` alongside the other stateful shapers.

Re-confirmed region/world-layer trajectory coverage is already sufficient via WORLD's existing
`trauma_hazard_broken`/`world_static`/`trauma_accumulation_broken` rules — no gap found,
`world_dynamics.py` untouched, matching §7.6's own conclusion.

Found and disclosed (not fixed here, filed as `TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP`): a
separate, pre-existing, unrelated bug — neither `event_extractor.py`'s legacy nor `FactionShaper`'s
live construction of `territory_ownership_changed` ever sets the `faction_territory_pct` payload
key `FactionScorer`'s `faction_monopoly`/`faction_conquest_degenerate` branches depend on, so
neither can ever fire in either path.

Verified via a real, non-mocked kernel run (`dungeon_crawl`, 1000 ticks): confirmed
`diplomatic_transition` genuinely fires (29 times) but is entirely front-loaded at tick 1 (world
initialization) and never recurs — explaining why `faction_trajectory_stagnant` correctly does not
fire in this corpus (its precondition, *ongoing* diplomatic activity, genuinely isn't met; this
specific degenerate shape is already caught by the existing `diplomacy_dormant` rule instead, a
different check for a different condition).

## Test Summary
`tests/unit/observability/test_event_shapers_economy_faction.py` (5 new tests:
`TestFactionTrajectoryStagnant`), `tests/simulation_quality/test_faction_scorer.py` (1 new test).
Scoped run: 41 passed. Broader `tests/unit/observability/ tests/simulation_quality/` run
(excluding `test_grade_regression.py`, pre-existing unrelated staleness): 1377 passed, 9 skipped.
`tests/unit/kernel/` (kernel.py touched): 53 passed. Real-kernel verification: `urban_political`
(1500t) and `dungeon_crawl` (1000t) both ran without error, correctly tracked per-faction state
from first observation; `faction_trajectory_stagnant` did not fire in either (explained above, not
a defect).

## Files Changed
- `src/observability/event_shapers.py` — `FactionShaper` new state, `reset_run_state()`, detection
  logic
- `src/engine/kernel.py` — `FactionShaper.reset_run_state()` wired into `Kernel.__init__`
- `config/simulation_quality/scoring_weights.yaml` — new `FACTION.faction_trajectory_stagnant`
  weight
- `src/simulation_quality/scorers/faction.py` — new `EVENT_TYPES` entry + `score()` branch
- `docs/simulation_quality/quality_scoring_contract.md` — §5 FACTION table + event-type list
- `docs/simulation_quality/event_type_coverage.md` — §1.1 Direct Emission table
- `docs/parity_ledger/faction.yaml` — new `FAC-014` entry
- `tests/unit/observability/test_event_shapers_economy_faction.py`
- `tests/simulation_quality/test_faction_scorer.py`
- `tickets/todos/tech-debt/TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP.md` (new follow-up)

## Completion Summary
Implemented FACTION's trajectory-coherence signal (`faction_trajectory_stagnant`) per
`quality_scoring_contract.md` §7.6's own audit finding, mirroring WORLD's `trauma_hazard_broken`
pattern exactly. Re-confirmed region/world layers need no change. Implemented in `FactionShaper`
(the live-by-default path for FACTION, unlike the PROGRESSION sibling's extractor placement — a
deliberate, reasoned difference per each domain's own current architecture), adding the first
cross-tick state that shaper has carried, wired correctly into `Kernel.__init__`. Verified via
real-kernel runs across 2 worlds; the rule's zero-firing in both is explained, not a defect. Found
and disclosed one separate, pre-existing, unrelated bug (`faction_territory_pct` payload gap),
filed as its own follow-up rather than fixed inline. This closes the final ticket of
`tickets/todos/simq-pillar-lifecycle-depth/` — all 3 remaining tickets in that folder are now
DONE.
