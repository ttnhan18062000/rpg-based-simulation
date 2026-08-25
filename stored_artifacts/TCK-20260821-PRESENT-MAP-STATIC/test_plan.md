---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-PRESENT-MAP-STATIC
artifact_type: test_plan
tags: [api-design, world]
---

# Test Plan — TCK-20260821-PRESENT-MAP-STATIC

## Regression Surface

No existing test targets `StatePresenter.present_map`/`present_static` (confirmed:
`grep -rn "present_map\|present_static" tests/` had no hits before this ticket). Existing
`tests/unit/api/` tests (`test_economy_route.py`, `test_engine_manager.py`,
`test_read_model_cache.py`, `test_read_model_service.py`) and
`tests/architecture/test_api_read_model_guard.py` don't reference `state_presenter.py` directly but
live in the same directory/architecture-boundary space — run alongside the new file as one scoped
pass to confirm no accidental cross-file regression.

## New Tests Required

New file: `tests/unit/api/test_state_presenter.py` (existing `tests/unit/api/` directory).

1. `present_map` — empty terrain returns `{width:0, height:0, grid:[]}`.
2. `present_map` — RLE round-trip correctness: decode the RLE output back to a flat list, compare
   against expected terrain-string-derived codes in row-major `y*width+x` order, on a small
   synthetic terrain dict.
3. `present_map` — deterministic terrain-code assignment: two states with the same terrain-type set
   inserted in different dict order produce byte-identical output.
4. `present_map` — width/height match the real populated terrain extent (not hardcoded/assumed).
5. `present_static` — buildings: `name` derived from `kind` (title-cased), `owner_entity_id` is
   `None`.
6. `present_static` — resource nodes: `name` derived from `kind`, `terrain` matches the node's tile
   in `state.terrain` via the same code mapping used by `present_map`.
7. `present_static` — chests: `guard_entity_id` is `None`, `tier == 1`, `looted` reflects whether
   `items` is empty (both an empty and a non-empty chest covered).
8. `present_static` — regions: `center_x`/`center_y`/`radius` match the `bounds`-derived formula
   exactly (not a stub/placeholder), `difficulty` matches `hazard_level`, `locations == []`.
9. Both methods — read-only: call both on a state carrying at least one of every affected
   collection (terrain, regions, buildings, resource_nodes, chests), then assert the state's own
   collections/fields are unchanged afterward (belt-and-suspenders on top of the frozen-dataclass
   guarantee, matching this project's Architecture Rule requirement to test "read-only logic did not
   mutate live state").

## Scoped Pytest Command

```
.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v
```

Scoped to the directory the new file lives in plus the one architecture guard most relevant to a
presenter-layer change (confirms no raw `AuthoritativeState`/`EntityState` exposure was
introduced) — never the bare `pytest tests/`, per this project's Testing Rule.

## Anti-Drift Test Guards

- **Test 2 (RLE round-trip) and test 3 (determinism)** are the primary guards against silently
  reintroducing non-deterministic terrain-code assignment (e.g. iterating `dict.values()` directly
  without sorting) — a regression here would break `present_map` in a way that's easy to miss
  locally (same machine, same dict insertion order every run) but would produce different output
  across restarts/machines with different hash seeds.
- **Test 9 (read-only)** guards the hardest architectural constraint this ticket touches — presenters
  must never mutate `AuthoritativeState`. `AuthoritativeState` and its component dataclasses are
  `frozen=True`, so any accidental field assignment would already raise `FrozenInstanceError` during
  the method call itself; this test is a second, explicit confirmation on top of that structural
  guarantee.
