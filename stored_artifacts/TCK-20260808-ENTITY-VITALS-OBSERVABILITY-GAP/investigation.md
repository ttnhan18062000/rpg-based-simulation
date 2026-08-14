---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
artifact_type: investigation
tags: [observability, world]
---

# Investigation — TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP

## Docs Requiring Update

- `docs/simulation_quality/event_type_coverage.md`: register the 5 new events (Implement phase)
- `docs/event_ledger/entity.yaml`: flip `ENTITY-009`/`ENTITY-017`/`ENTITY-018` to `observed` (Implement phase)

## Real mutation sources confirmed

- `BiologicalUpdate`: `src/systems/lifecycle_systems/biological.py` (~+0.5 hunger/tick, always-on
  per-entity decay — confirmed via direct read), plus `src/town/inn.py`/`src/town/home.py`
  (rest/sleep recovery), `src/systems/economy_systems/town_service.py` (meal consumption).
- `StaminaUpdate`: `src/engine/movement.py`, `src/engine/domain/{aoe,combat,skill}_actions.py`
  (drain on action use), passive regen via `StaminaComponent.regen_rate`/`rest_regen_rate`.
- `WoundUpdate`: `src/engine/combat.py` only — **tied to real combat resolution**, which is
  corpus-wide gated off (`ENABLE_COMBAT_ENGAGEMENT`, confirmed this session's own
  `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`/`TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE`).

## Design: full coverage (major to minor), not just threshold crossings

Per explicit direction: every real state delta gets an event, not only "meaningful" crossings —
matching the existing `movement` event's own precedent (`docs/simulation_quality/event_type_coverage.md`
§5, "high-volume positional data," still emitted unconditionally). Severity (real
`EventSeverity` field: `DEBUG`/`INFO`/`WARNING`/`ERROR`/`CRITICAL`) distinguishes major from minor
occurrences of the SAME event type, rather than needing separate event types per severity tier:

- `biological_state_changed`: fires on any hunger/sleep_debt/rest_pressure delta. `INFO` by
  default; `WARNING` at 80+, `CRITICAL` at 95+ (reusing `BiologicalComponent`'s own documented
  0-100 scale, not an invented threshold).
- `stamina_changed`: fires on any stamina delta. `INFO` by default; `WARNING` when the result is
  below `StaminaComponent.exhaustion_threshold` — reusing the exact real threshold constant
  combat-penalty logic already keys off, not a new number.
- `wound_sustained`/`wound_healed`/`scar_gained`: fire per real occurrence (these are inherently
  discrete, not continuous deltas). Severity from `WoundState.severity` (a real, existing
  0.0-1.0 field): `INFO` <0.4, `WARNING` <0.7, `CRITICAL` >=0.7.

All 5 emitted unconditionally in non-LIGHT/LONG_RUN modes, matching `movement`'s own volume-control
convention exactly (same `mode not in (LIGHT, LONG_RUN)` guard).

## Precise classification (per the user's own request: scored vs. emitted-but-unscored vs. invisible)

All 5 events, after this ticket: **emitted, `unscored_intentional`** — real
`ObservabilityEventEnvelope`s fire and are visible to any observability consumer (dashboards,
raw-event pulls, future scorers), but are NOT wired to `QualityHub.SCORER_REGISTRY`/any SimQ
pillar in this pass. This is a deliberate, disclosed choice (per this ticket's own Out of Scope:
"Wiring these new events to any SimQ scorer/pillar — that's a separate decision"), not an
oversight — matches `docs/simulation_quality/event_type_coverage.md` §5's own existing
classification for `movement`/`resource_node_regenerated`/etc. (real events, deliberately never
routed to a scorer).

Before this ticket: **fully invisible** (`silent` in `docs/event_ledger/entity.yaml`'s own
schema) — zero corresponding `ObservabilityEventEnvelope` of any kind, confirmed via double grep
(intent-field and state-field names) during the predecessor ticket
(`TCK-20260808-ENTITY-EVENT-LEDGER`).

## Real verification, not a mock

`biological_state_changed`/`stamina_changed` confirmed firing through a real, live
`Kernel.tick_once()` loop (`sandbox_world_seed42`, 15 ticks — both fired). `wound_sustained`/
`wound_healed`/`scar_gained` could NOT be exercised through a real tick loop in this session (no
corpus world currently produces real combat, per the corpus-wide flag gate above) — verified
instead via real, hand-constructed `WoundState`/`ScarState`/`EntityState` objects passed through
the real `EventExtractor.extract()` — the same precedented pattern this repo already uses for
gated mechanics (`test_information_intent_execution_fires_through_kernel_tick_once`'s own sibling
test, `docs/core/update_intents.md` cross-reference). All 3 confirmed firing with correct severity
mapping (severity=0.8 wound correctly produced `CRITICAL`).
