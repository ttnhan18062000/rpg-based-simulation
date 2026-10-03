---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
phase: done
date: 2026-08-08
tags: [observability, world]
---

# TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP

## Title
Entity vitals (biological/stamina/wound state) have zero observability events — `event_extractor.py`
never diffs `entity.biological`, stamina, or wound state at all

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260808-ENTITY-EVENT-LEDGER`'s cross-reference of `EntityUpdate`'s durable-state fields
against the observability pipeline's real event coverage (`docs/event_ledger/entity.yaml`
`ENTITY-009`/`ENTITY-017`/`ENTITY-018`) found 3 confirmed-silent mutation types, all "vitals"-class
entity state: `BiologicalUpdate` (sleep debt, hunger, rest pressure), `StaminaUpdate` (current/max
stamina), `WoundUpdate` (new wounds, heals, scars). Confirmed via direct grep of
`event_extractor.py` for both intent-field and real `EntityState` component field names
(`.biological.`, `.stamina`, `.wounds`) — zero matches for all 3. No event of any kind — not even
an unscored-intentional one — observes these state changes.

This means: an entity can starve, exhaust itself, or accumulate wounds/scars across an entire
simulation run with zero observable signal — a real blind spot for anything downstream that wants
to understand entity wellbeing narratively or diagnostically (SimQ's own PROGRESSION/NARRATIVE
pillars, or a future "entity lifecycle health" signal).

## Scope
1. **Investigate**: determine which vitals transitions are narratively/diagnostically meaningful
   enough to warrant a real event (not every biological tick needs one — e.g. hunger crossing a
   critical threshold is meaningful, a routine tick decrement is not). Check whether existing
   threshold constants (`config/simulation_quality/detection_params.yaml` or elsewhere) already
   define meaningful crossing points to reuse rather than inventing new ones.
2. **Plan**: design the specific event(s) — e.g. `vitals_critical` (hunger/rest/stamina crosses a
   critical threshold), `wound_sustained`/`wound_healed`/`scar_gained` — following
   `docs/guides/observability.md`'s "Adding a new event type" process.
3. **Implement**: wire the emission in `event_extractor.py`, register in
   `docs/simulation_quality/event_type_coverage.md` per its own §6 Maintenance Notes, update
   `docs/event_ledger/entity.yaml`'s corresponding entries to `observed`.

## Out of Scope
- Wiring these new events to any SimQ scorer/pillar — that's a separate decision (does any pillar
  need this signal), not assumed by this ticket.
- The other confirmed-silent findings (attributes, equipment, identity role/faction) — tracked in
  their own sibling tickets.

## Acceptance Criteria
- [x] investigation.md identifies which vitals transitions warrant an event, with reasoning
- [x] New event(s) wired and confirmed firing through a real `Kernel.tick_once()` loop, not a mock
      (2/5 events — `biological_state_changed`, `stamina_changed` — verified this way directly;
      the other 3 — `wound_sustained`/`wound_healed`/`scar_gained` — verified via real,
      hand-constructed `WoundState`/`ScarState` objects passed through the real extraction
      function, since combat is corpus-wide gated off and cannot produce a wound through any
      currently-shipped calibration world's tick loop; see Implementation Notes)
- [x] `event_type_coverage.md` and `docs/event_ledger/entity.yaml` updated
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-EVENT-LEDGER (found this gap — DONE)
- TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP, TCK-20260808-ENTITY-EQUIPMENT-OBSERVABILITY-GAP,
  TCK-20260808-ENTITY-IDENTITY-ROLE-FACTION-OBSERVABILITY-GAP (sibling findings from the same audit)

## Related Docs
- `docs/event_ledger/entity.yaml` (`ENTITY-009`, `ENTITY-017`, `ENTITY-018`)
- `docs/core/update_intents.md` (`BiologicalUpdate`, `StaminaUpdate`, `WoundUpdate` definitions)
- `docs/guides/observability.md` "Adding a new event type"

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-ENTITY-EVENT-LEDGER/`

## Related Code Areas
- `src/observability/event_extractor.py`
- `src/core/updates.py` (`BiologicalUpdate`, `StaminaUpdate`, `WoundUpdate`)

## Assumptions / Open Questions
- Whether every biological tick decrement should be observable, or only threshold crossings — not
  assumed; Investigate must determine the right granularity to avoid a high-volume, low-value
  event (same concern already documented for `movement`'s own unscored-intentional status).

## Implementation Notes
- **Subagent spawn cap reached this session** — Investigate/Plan/Implement/Document-Update/
  Parity/Verify for this ticket were all performed directly, not via `Agent(subagent_type=...)`
  calls.
- **Scope pivot mid-implementation, per explicit user direction**: the ticket's own original
  Scope text (above) framed this as "not every biological tick needs one" — a threshold-crossing
  design. The user's own later instruction ("we aiming to full cover every event from major to
  minor related to entity") overrode this before any code was written. Redesigned to emit
  unconditionally on every real delta, using `EventSeverity` (INFO/WARNING/CRITICAL) to carry the
  major/minor distinction instead of gating emission itself — matches the existing `movement`
  event's own unscored-intentional, always-on precedent in the same file.
- 5 new event types added to `src/observability/event_extractor.py`'s diff loop, inserted after
  the existing `movement` block: `biological_state_changed` (hunger/sleep_debt/rest_pressure delta,
  severity by worst-of-three vs 80/95), `stamina_changed` (stamina.current delta, WARNING when
  below the existing `StaminaComponent.exhaustion_threshold`), `wound_sustained` (new wound ID,
  severity by the existing `WoundState.severity` field vs 0.4/0.7), `wound_healed` (existing
  wound's `healed` flag False→True), `scar_gained` (new scar ID). All reuse existing, already-
  defined thresholds — no new numeric constants invented. Suppressed in LIGHT/LONG_RUN
  observability modes, matching the file's own volume-control convention.
- Real bug found and fixed during Implement: unconditional `entity.biological`/`.stamina` access
  broke 82 pre-existing tests using bare `MagicMock()` entity fixtures that never wired those
  components (`TypeError: '>' not supported between MagicMock and MagicMock`). Fixed with a local
  `_is_real_number(*values) -> bool` isinstance guard applied before every biological/stamina
  comparison, plus `isinstance(x, list)` guards before iterating `.wounds`/`.scars`. Zero
  regressions confirmed after the fix (see Test Summary).
- Wound/scar verification could not use a live `Kernel.tick_once()` loop — `ENABLE_COMBAT_ENGAGEMENT`
  is corpus-wide gated off (`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`), so no
  shipped calibration world can currently produce a wound through a real tick. Verified instead via
  real, non-mocked `WoundState`/`ScarState` objects constructed by hand and passed directly through
  the real `EventExtractor.extract()` function — this repo's own precedented pattern for verifying
  gated mechanics (see `test_information_intent_execution_fires_through_kernel_tick_once`).
- **Classification precision** (per explicit user direction to distinguish scored vs. emitted-
  unscored vs. invisible, not a binary): all 5 new events are classified `unscored_intentional`
  (`docs/simulation_quality/event_type_coverage.md` §5) — real, observed, firing events, not wired
  to any SimQ pillar. This is a separate, deliberate decision (Out of Scope), not a residual gap.
  `wound_sustained`/`wound_healed`/`scar_gained` additionally carry a "currently unreachable in
  practice" caveat (code path real and tested, but combat is corpus-wide off).
- **Parity**: `src/observability/event_extractor.py` maps to 7 parity-ledger subsystems via
  `expected_subsystems_for_files()`; `find_p0_intersection()` flagged 3 pre-existing P0 entries
  (COMB-295, TOWN-190, INFRA-326) — all confirmed unrelated to this change (push-shaper cutover
  work in a different code region of the same file), not touched. Added `SUB-375`
  (biological/stamina, `docs/parity_ledger/substrate.yaml`) and `COMB-296` (wound/scar,
  `docs/parity_ledger/combat_movement.yaml`) as the real new entries for this change, split across
  files matching the existing SUB-/COMB- domain convention (biological+stamina are entity-core
  state → substrate.yaml; wounds+scars are a CombatUpdate field → combat_movement.yaml). Cross-
  reference gate (`cross_reference_touched`) confirmed PASS.

## Test Summary
- `tests/unit/observability/test_event_extractor_vitals.py` (new, 6/6 pass):
  `test_biological_state_changed_fires_through_real_kernel_tick_once`,
  `test_stamina_changed_fires_through_real_kernel_tick_once`,
  `test_wound_sustained_severity_mapping`, `test_wound_healed_fires`, `test_scar_gained_fires`,
  `test_vitals_events_suppressed_in_light_and_long_run_modes`.
- `tests/unit/observability/` full suite: 958 passed, 6 skipped, 0 failed (zero regressions after
  the `_is_real_number` guard fix).

## Files Changed
- `src/observability/event_extractor.py` — 5 new event emission blocks
- `tests/unit/observability/test_event_extractor_vitals.py` — new, 6 tests
- `docs/simulation_quality/event_type_coverage.md` — §5 Unscored Intentional table (3 new rows),
  Summary counts (13→18)
- `docs/event_ledger/entity.yaml` — `ENTITY-009`, `ENTITY-017`, `ENTITY-018` flipped
  `silent`→`observed`
- `docs/parity_ledger/substrate.yaml` — new entry `SUB-375`
- `docs/parity_ledger/combat_movement.yaml` — new entry `COMB-296`

## Completion Summary
Entity vitals (biological pressures, stamina, wounds/scars) went from zero observability coverage
to full-coverage, severity-tagged event emission — 5 new event types spanning all 3 previously-
silent `EntityUpdate` mutation sources found by `TCK-20260808-ENTITY-EVENT-LEDGER`. Design pivoted
mid-implementation from a threshold-crossing subset to full unconditional coverage per explicit
user direction, with `EventSeverity` carrying the major/minor distinction. All 5 events verified
firing for real (2 through a live `Kernel.tick_once()` loop, 3 through this repo's own precedented
hand-built-state pattern for combat-gated mechanics). A real 82-test regression from unconditional
component access on unwired `MagicMock()` fixtures was found and fixed with a defensive isinstance
guard. Classified `unscored_intentional` in `event_type_coverage.md`, not wired to any SimQ pillar
by design. Parity ledger updated with 2 new entries (`SUB-375`, `COMB-296`); 3 pre-existing P0
entries flagged by the file-level intersection scan were confirmed unrelated and left untouched.
