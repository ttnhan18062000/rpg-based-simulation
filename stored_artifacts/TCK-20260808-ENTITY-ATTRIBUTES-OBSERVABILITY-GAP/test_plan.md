---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP
artifact_type: test_plan
tags: [observability, world]
---

# Test Plan — TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP

New file: `tests/unit/observability/test_event_extractor_attributes.py`

1. `test_attribute_changed_fires_through_real_kernel_tick_once` — real, non-mocked
   `Kernel.tick_once()` loop over enough ticks for at least one non-hero entity to level up
   (reuses `_load_world_state`/`sandbox_world` pattern from the vitals ticket's own test file);
   assert `attribute_changed` appears with a non-empty `deltas` payload.
2. `test_attribute_changed_severity_negative_delta_is_warning` — hand-built `AttributeComponent`
   with one field decreased; assert `severity == "WARNING"`.
3. `test_attribute_changed_severity_positive_only_is_info` — hand-built with only increases;
   assert `severity == "INFO"`.
4. `test_attribute_changed_payload_only_includes_changed_fields` — multi-field delta; assert
   `deltas` keys match exactly the fields that changed, not all 9.
5. `test_attribute_changed_suppressed_in_light_and_long_run_modes` — same suppression pattern as
   the vitals ticket's own sibling test.
6. `test_no_event_on_zero_delta` — identical `AttributeComponent` before/after; assert no
   `attribute_changed` event (guards against a no-op false-positive).

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md identifies every real mutation source for `AttributeUpdate` | Done — 1 live, 1 wired-but-unreachable, 2 dead code, all verified not assumed |
| New event wired and confirmed via a real `Kernel.tick_once()` loop | Test 1 |
| `event_type_coverage.md` and `docs/event_ledger/entity.yaml` updated | Document-Update phase |
| Scoped pytest passes | `tests/unit/observability/` full suite, zero regressions |
