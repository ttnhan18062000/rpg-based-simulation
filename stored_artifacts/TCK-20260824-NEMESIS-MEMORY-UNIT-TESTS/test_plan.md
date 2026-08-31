---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS
artifact_type: test_plan
tags: [social, testing]
---

# Test Plan — TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS

## Regression Surface

This ticket is purely additive (one new test file exercising previously-untested, currently
production-unreachable static methods — see investigation.md's "dead code" finding). No source
file changes are planned, so the regression surface is narrow: tests that construct
`EntityState`/`AuthoritativeState`/`RegionState`/`SocialUpdate` the same way the new tests will, and
tests that already cover the `SocialMemoryService` import surface.

Unit:
- `tests/refactor/test_public_facades.py::test_system_public_facades` — asserts
  `SocialMemoryService` importable from `src.systems.social_memory`; must keep passing unchanged.
- `tests/refactor/test_import_compatibility.py` — same facade import assertion.
- `tests/unit/combat/test_combat_ecology.py` — documents `SocialComponent.grudge_history`/
  `.nemesis_ids` shape (`hasattr`/`isinstance` checks); must keep passing since new tests rely on
  the same field shapes.
- `tests/unit/social/` (whole directory) — new test file lands alongside these; run the full
  directory to catch any naming/fixture collisions with existing `test_social_memory.py` (which
  tests an unrelated module — see investigation.md's Anti-Drift Hazards).
- `tests/unit/progression/test_progression_quests.py`, `tests/unit/world/test_influence.py`,
  `tests/unit/world/test_calamity_pressure_propagator.py` — establish the `RegionState(...)`
  direct-construction convention the new tests will reuse; not modified, but good canaries if that
  convention shifts.

Integration:
- None directly required — `tick_place_attachment`/`check_nemesis_promotion` have no live caller in
  `src/engine/apply.py` or elsewhere (confirmed dead code, see investigation.md), so no
  integration/scenario test currently exercises them even indirectly.

Arena-combat: Not applicable — no combat-path code touched.

## New Tests Required

Target file: `tests/unit/social/test_social_memory_service.py` (new — named after the class under
test, `SocialMemoryService`, to avoid collision with the unrelated existing
`tests/unit/social/test_social_memory.py`, which tests `src.domains.campaigns.social_memory`).

### `tick_place_attachment()`

1. **`test_tick_place_attachment_uses_explicit_region_id`**
   Category: unit.
   Verifies: passing a non-empty `region_id` explicitly skips the auto-detection scan entirely and
   returns `SocialUpdate(place_attachment_delta={region_id: 0.001})` keyed on the passed value —
   even when the entity's actual position does not fall inside any region with that ID (proves the
   function trusts the caller-supplied `region_id` without cross-checking `state.regions`).

2. **`test_tick_place_attachment_auto_detects_containing_region`**
   Category: unit.
   Verifies: `region_id=None`, entity position falls inside exactly one region's bounds → the
   region is auto-detected via the `state.regions` scan and the returned update is keyed on that
   region's `id`.

3. **`test_tick_place_attachment_returns_none_when_no_region_contains_position`**
   Category: unit.
   Verifies: `region_id=None`, entity position falls inside no region's bounds → returns `None`.

4. **`test_tick_place_attachment_returns_none_when_no_regions_exist`**
   Category: unit.
   Verifies: `region_id=None`, `state.regions` is empty → returns `None` (distinct code path
   trigger from case 3, same outcome — both must be tested since they reach the guard from
   different inputs).

5. **`test_tick_place_attachment_boundary_position_matches_region_edge`**
   Category: unit / edge case.
   Verifies: entity position placed exactly on a region's boundary (e.g. `ex == xmax`) still
   matches, pinning the inclusive `<=`/`>=` comparison at `memory.py:27`.

6. **`test_tick_place_attachment_empty_string_region_id_falls_back_to_auto_detect`**
   Category: unit / edge case (anti-drift/regression pin, not a new requirement — see
   investigation.md Risks).
   Verifies: passing `region_id=""` behaves identically to `region_id=None` (falls through to the
   auto-detection scan) rather than being treated as an explicit-but-empty region — pins current
   behavior so a future refactor cannot silently change this without a visible test failure.

### `check_nemesis_promotion()`

7. **`test_check_nemesis_promotion_empty_grudge_history_returns_none`**
   Category: unit.
   Verifies: `entity.social.grudge_history == {}` → returns `None`.

8. **`test_check_nemesis_promotion_below_threshold_not_promoted`**
   Category: unit.
   Verifies: a single grudge entry with value `< 3.0` (e.g. `2.9`) → not promoted → returns `None`.

9. **`test_check_nemesis_promotion_already_nemesis_not_repromoted`**
   Category: unit.
   Verifies: a single entry with `grudge >= 3.0` whose `eid` is already in `entity.social.
   nemesis_ids` → excluded by the `not in` guard → returns `None` (proves already-promoted entities
   are not re-added / re-flagged).

10. **`test_check_nemesis_promotion_qualifying_entry_promoted`**
    Category: unit.
    Verifies: a single entry with `grudge >= 3.0` and `eid` not already in `nemesis_ids` → returns
    `SocialUpdate(nemesis_promotion=[eid])`.

11. **`test_check_nemesis_promotion_exact_threshold_boundary_promoted`**
    Category: unit / edge case.
    Verifies: `grudge == 3.0` exactly → promoted (pins the inclusive `>=` at `memory.py:46`).

12. **`test_check_nemesis_promotion_mixed_entries_only_new_qualifying_promoted`**
    Category: unit.
    Verifies: a multi-entry `grudge_history` containing (a) one below-threshold entry, (b) one
    already-nemesis qualifying entry, and (c) one new qualifying entry, in one call → the returned
    `nemesis_promotion` list contains only entry (c)'s `eid`, exactly — proving per-entry filtering
    rather than any short-circuit, and pinning list order against `grudge_history` insertion order.

### Architecture guard (optional, cheap add-on given the investigation's dead-code finding)

13. **`test_social_memory_service_functions_are_pure_and_do_not_mutate_entity`**
    Category: architecture guard.
    Verifies: calling either function does not mutate the passed-in `entity`/`state` objects
    (both are frozen dataclasses per `docs/core/state.md`'s immutability law, so this should already
    hold structurally, but an explicit `entity_before == entity_after` / identity check makes the
    "decision logic reads state, does not mutate it" architecture rule machine-verified for this
    file specifically, matching this project's "Architecture tests" testing-rule requirement).

## Scoped Pytest Commands

```
pytest tests/unit/social/ tests/refactor/test_public_facades.py tests/refactor/test_import_compatibility.py -v
```

Optionally, to also confirm the `grudge_history`/`nemesis_ids` shape assumptions still hold:

```
pytest tests/unit/social/ tests/refactor/test_public_facades.py tests/refactor/test_import_compatibility.py tests/unit/combat/test_combat_ecology.py -v
```

Never: `pytest tests/` (unscoped — forbidden by project Testing Rule).

## Anti-Drift Test Guards

- New tests must import `SocialMemoryService` from `src.systems.social_systems.memory` (or the
  `src.systems.social_memory` facade) — never add test cases to the existing, unrelated
  `tests/unit/social/test_social_memory.py` or `tests/integration/scenarios/test_social_memory.py`
  (both test `src.domains.campaigns.social_memory`, a different module — see investigation.md).
- Test 1 (`test_tick_place_attachment_uses_explicit_region_id`) must deliberately place the entity
  *outside* the named region's bounds (or use a `region_id` string with no matching entry in
  `state.regions` at all) — this is what actually proves the explicit-`region_id` branch skips
  validation, rather than merely happening to agree with the auto-detected region.
- Test 12's assertion must check the exact returned list (not just set membership / `in`) to pin
  both filtering correctness and iteration-order determinism — a test using `set(result) ==
  {expected_id}` would pass even if extra invalid entries leaked in via a future refactor with
  duplicate ids, or if order became nondeterministic.
- None of the new tests should import from `src.domains.campaigns.*` (CampaignOrchestrator,
  GriefUrgencyImporter, NemesisRelationImporter) — any such import is scope creep into
  `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`'s explicitly separate territory.
- Do not assert against the SOC-050/SOC-066 parity ledger `text` fields ("PlaceAttachment... supports
  sentiment", "Nemesis milestone creation") as if they were binding specs — the investigation found
  those legacy-checklist entries are not a confirmed 1:1 match to the current V2 dict/set-based
  implementation; tests must assert against the real `memory.py` code, not the older ledger wording.
