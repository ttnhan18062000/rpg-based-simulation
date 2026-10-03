---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
artifact_type: test_plan
tags: [observability, world]
---

# Test Plan — TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP

## New tests (`tests/unit/observability/test_event_extractor_vitals.py`)

1. `test_biological_state_changed_fires_through_real_kernel_tick_once` — real `Kernel.tick_once()`
   loop, real `sandbox_world`, confirms `biological_state_changed` fires.
2. `test_stamina_changed_fires_through_real_kernel_tick_once` — same real loop, confirms
   `stamina_changed` fires.
3. `test_wound_sustained_severity_mapping` — hand-built real `WoundState`/`EntityState` (combat is
   corpus-wide gated off, matching this repo's own precedented pattern for gated mechanics),
   confirms `wound_sustained` fires with `CRITICAL` for severity>=0.7, `WARNING` for 0.4-0.7,
   `INFO` below.
4. `test_wound_healed_fires` / `test_scar_gained_fires` — same real-object pattern.
5. `test_vitals_events_suppressed_in_light_and_long_run_modes` — confirms the volume-control guard
   matches `movement`'s own convention.

## Regression coverage

`tests/unit/observability/test_event_extractor_world.py` and the full
`tests/unit/observability/` suite — confirm no existing test broke from the new diff-loop
insertion.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/unit/observability/test_event_extractor_vitals.py tests/unit/observability/ -q`
