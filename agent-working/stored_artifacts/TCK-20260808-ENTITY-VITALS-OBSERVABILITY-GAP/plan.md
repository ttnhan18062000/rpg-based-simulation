---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
artifact_type: plan
tags: [observability, world]
---

# Plan — TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP

## Steps (Implement already done during Investigate's own real-verification pass)

1. `src/observability/event_extractor.py`: 5 new diff-based event emissions, inserted after the
   existing `movement` block, matching its own volume-control convention.
2. `tests/unit/observability/test_event_extractor_vitals.py`: the 6 tests from test_plan.md.
3. `docs/simulation_quality/event_type_coverage.md`: register `biological_state_changed`,
   `stamina_changed`, `wound_sustained`, `wound_healed`, `scar_gained` in §5 Unscored Intentional
   (matches their real, deliberate classification — emitted, not scored).
4. `docs/event_ledger/entity.yaml`: flip `ENTITY-009` (`BiologicalUpdate`), `ENTITY-017`
   (`StaminaUpdate`), `ENTITY-018` (`WoundUpdate`) from `silent` to `observed`.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies which vitals transitions warrant an event, with reasoning | Done — full coverage per explicit direction, not a threshold-only subset |
| New event(s) wired and confirmed firing through a real Kernel.tick_once() loop | 2/5 via real loop; 3/5 (combat-gated) via the repo's own precedented hand-built-state pattern |
| event_type_coverage.md and entity.yaml updated | Steps 3-4 |
| Scoped pytest passes | Step 2 |
