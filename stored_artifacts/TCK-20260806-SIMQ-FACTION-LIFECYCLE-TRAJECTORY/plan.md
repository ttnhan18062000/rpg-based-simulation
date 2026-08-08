---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY
artifact_type: plan
tags: [simulation-quality, faction]
---

# plan.md — TCK-20260806-SIMQ-FACTION-LIFECYCLE-TRAJECTORY

## Ordered Steps

1. `src/observability/event_shapers.py`: add `_FACTION_STAGNANT_TICKS = 300` module constant; add
   `_last_territory_change_tick: dict[str, int]` and `_emitted_stagnant: set[str]` class state to
   `FactionShaper`; add `reset_run_state()` classmethod; add detection logic inside the existing
   per-`FactionUpdate` loop in `shape()`.
2. `src/engine/kernel.py`: wire `FactionShaper.reset_run_state()` into `Kernel.__init__` alongside
   the existing `StrategyShaper`/`ProgressionShaper`/`SocialShaper` calls.
3. `config/simulation_quality/scoring_weights.yaml`: add `faction_trajectory_stagnant: -8.0` under
   `FACTION:`.
4. `src/simulation_quality/scorers/faction.py`: add `faction_trajectory_stagnant` to
   `EVENT_TYPES`, add a new `if et == ...` branch in `score()`.
5. `docs/simulation_quality/quality_scoring_contract.md`: add to FACTION's "Event types scored"
   list and Signal/Delta/Tag table.
6. `docs/simulation_quality/event_type_coverage.md`: add to §1.1's Direct Emission table.
7. `docs/parity_ledger/faction.yaml`: new entry.
8. File `TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP` into `tickets/todos/tech-debt/`
   (investigation.md's separate, pre-existing finding — not fixed here).
9. Unit tests: extend `tests/unit/observability/test_event_shapers_economy_faction.py` and
   `tests/simulation_quality/test_faction_scorer.py`.
10. Recalibrate `grade_anchors.json` only if a real scoped/kernel check shows an actual shift.

## Files to Change

- `src/observability/event_shapers.py`
- `src/engine/kernel.py`
- `config/simulation_quality/scoring_weights.yaml`
- `src/simulation_quality/scorers/faction.py`
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/simulation_quality/event_type_coverage.md`
- `docs/parity_ledger/faction.yaml`
- `tests/unit/observability/test_event_shapers_economy_faction.py`
- `tests/simulation_quality/test_faction_scorer.py`
- `tickets/todos/tech-debt/TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP.md` (new)

## Scope Guards

- Do NOT touch `world_dynamics.py` — region/world layers re-confirmed already covered
  (investigation.md).
- Do NOT touch entity-layer (PROGRESSION) — sibling ticket's own scope, already DONE.
- Do NOT fix the `faction_territory_pct` payload gap inline — filed as a separate follow-up.
- Do NOT touch `event_extractor.py`'s legacy FACTION branches — this is shaper-only new code
  (unlike the PROGRESSION ticket), since FactionShaper is already the live-by-default path and
  has everything needed without full-snapshot access.

## Dependency Map

Steps 1-2 must land together (new shaper state needs the reset wiring, or it leaks across runs).
Steps 3-4 depend on step 1's exact event/payload shape. Steps 5-7 depend on 1-4. Step 8 is
independent (a separate finding, filed regardless of this ticket's own implementation order).
Step 9 depends on 1-4. Step 10 depends on 9's real results.

## Acceptance Criteria Map

- AC "investigation.md documents queryable state + region/world re-check" → investigation.md
- AC "plan.md specifies exact rule, tag, delta placeholder" → this file
- AC "new rule implemented, weight in scoring_weights.yaml, no numeric literals in scorer" →
  steps 1, 3-4
- AC "quality_scoring_contract.md §5 + event-type list updated" → step 5
- AC "unit test added" → step 9
- AC "docs/parity_ledger/faction.yaml updated" → step 7
- AC "grade_anchors.json recalibrated if shifted" → step 10
- AC "scoped pytest run passes" → step 9's real run
