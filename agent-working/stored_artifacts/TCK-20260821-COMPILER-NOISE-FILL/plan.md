---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-COMPILER-NOISE-FILL
artifact_type: plan
tags: [world, determinism]
---

# Implementation Plan — TCK-20260821-COMPILER-NOISE-FILL

## Summary
Extend `WorldCompiler.compile()`'s region-painting loop (`src/worldbuilding/compiler.py:211-221`) so that a region declaring `terrain_variants` gets per-tile terrain sampled via `DeterministicRNG.weighted_choice()` under `Domain.INIT` (never `Domain.WORLD`), while a region that does not declare variants keeps today's flat-fill behavior byte-for-byte. The investigation already proved the RNG is a stateless composite-key hash (no sequential stream to reorder) and that `Domain.INIT`'s one existing production use (`Kernel.__init__`'s run-suffix draw, `src/engine/kernel.py:122`) cannot collide in effect with this ticket's draws because compile() finishes and returns before any `Kernel` is constructed, and because each call independently constructs its own `random.Random(seed)`. This plan resolves the encoding-scheme and empty-list open questions explicitly below, adds the 10 tests (9 from `test_plan.md` plus 1 added during Review to close a tile-encoding collision), and updates the three required docs (mechanics chapter, parity ledger `SUB-385`, intentional divergences) in the same session per the Authoritative Mechanics Rule.

## Design Decisions

### 1. Tile → entity_id/sub_id encoding scheme

**Corrected during Review (NEEDS_CHANGES, first pass):** the original scheme (`entity_id = region_hash ^ ((x << 8) | y)`) packed `y` into only the low 8 bits, which is not injective for any region with y-extent ≥256 — `(x=0, y=256)` and `(x=1, y=0)` both produce combined offset `256`, causing two genuinely different tiles to draw the identical `weighted_choice()` output. Verified this is a real risk, not hypothetical: `TopologySpec.width`/`height` (`src/worldbuilding/schema.py:16-17`) are `Field(..., gt=0, ...)` with no upper bound anywhere in the schema or resolver, and real existing worlds already reach 211-221 in one or both dimensions (`data/worlds/highland_traverse/resolved/world.resolved.yaml`: 211×211; `data/worlds/swamp_border_world/resolved/world.resolved.yaml`: 221×121) — well within striking distance of 256. The original scheme's own bit-arithmetic writeup only proved *domain-separation* safety (entity_id staying within the 32-bit budget so `domain.value << 48` can't collide across Domains); it never separately proved *per-tile injectivity* within a region, and conflated the two.

**Corrected scheme:** for a region `r_spec` and in-bounds tile `(x, y)`:
- `region_hash = 0; for ch in r_spec.id: region_hash = (region_hash * 31 + ord(ch)) & 0xFFFFFFFF` — unchanged from the original scheme (reuses `DeterministicRNG._composite_seed`'s own string-hash algorithm, `src/platform/rng.py:74-79`).
- `tile_offset = ((x & 0xFFFF) << 16) | (y & 0xFFFF)` — 16 bits allocated to each axis (up to 65,535 per dimension), replacing the original 8-bit `y` packing. This is injective for any `x, y` pair where both stay below 65,536 — a bound roughly 300x larger than the largest real world found in this repo (221) and far beyond any topology size that is remotely plausible for this engine's performance envelope (`docs/engine/performance_contract.md` has no explicit tile-count ceiling, but a 65,536×65,536 world is ~4.3 billion tiles, orders of magnitude past any realistic simulation scale). This bound is practical, not absolute — documented honestly as such, not claimed as literally unconditional for all topology sizes the schema's bare `gt=0` would technically permit.
- `entity_id = (region_hash ^ tile_offset) & 0xFFFFFFFF` — stays within the same confirmed-safe 32-bit budget as the original scheme (the final `& 0xFFFFFFFF` mask is a defensive no-op here since both operands are already ≤32 bits, but keeps the invariant explicit and self-documenting).
- `sub_id = 1` (a fixed non-zero constant, not `0`) — unchanged from the original scheme. `entity_id` alone already varies per-tile (via `tile_offset`), so `sub_id` only needs to be a fixed, distinct "purpose" tag, and `1` differs from Kernel's `Domain.INIT` run-suffix draw's `sub_id=0` (`src/engine/kernel.py:122`, `get_int(Domain.INIT, 0, 0, 1000, 9999)` — no `sub_id` kwarg, defaults to `0` per `get_int`'s signature at `src/platform/rng.py:90`).
- `tick = 0` — matches every other draw in `compile()` (investigation confirmed literal `0` everywhere; no tick concept exists inside `compile()`).

Call shape: `rng.weighted_choice(Domain.INIT, tick=0, entity_id=entity_id, seq=[v.terrain for v in r_spec.terrain_variants], weights=[v.weight for v in r_spec.terrain_variants], sub_id=1)`.

**Why this stays inside the confirmed-safe bit ranges** (per investigation's `_composite_seed` bit-layout analysis, `src/platform/rng.py:65-83`, confirmed by direct read above, and re-derived independently during Review): `domain.value << 48` occupies bits ≥48 (`Domain.INIT == 11`, 4 bits), `tick << 32` occupies bits 32-47 (`tick=0` here), `entity_id << 16` occupies bits 16-47 (`entity_id` masked to 32 bits, consistent with every other `entity_id` already flowing through `compile()` — string-hashed faction/resource/building/entity IDs are all folded through the same 32-bit hash). `sub_id=1` occupies bits 0-15 unshifted, well within the `sub_id < 128` convention the investigation observed at every other `compile()` call site. No term here touches bits ≥48 except `domain.value`, so two different `Domain` values provably cannot produce the same composite seed — this ticket's own `Domain.INIT` draws are structurally isolated from `Domain.WORLD`'s draws regardless of coincidental `entity_id`/`sub_id` overlap. **This is a separate proof from per-tile injectivity** (established by the `tile_offset` construction above) — the plan now states both explicitly rather than conflating them, per Review's required correction.

**Confirms Scope requirement:** this deliberately does *not* land on `(entity_id=0, sub_id=0)` for tile `(0,0)` of the first-declared region (`region_hash` for any non-empty region id string is virtually never exactly `0`, and even if it were, `sub_id=1 != 0` guarantees no exact match with Kernel's `(entity_id=0, sub_id=0)` draw) — satisfying the investigation's cosmetic-hygiene recommendation without adding any correctness dependency on it.

### 2. `terrain_variants=[]` (empty list) behavior
**Decision: treat empty list identically to `None` (flat-fill fallback).** The gating condition is `if r_spec.terrain_variants:` — Python truthiness already treats `[]` as falsy, so no special-casing is needed or should be added. `RegionSpec.terrain_variants: Optional[List[TerrainVariantSpec]] = Field(None, ...)` (`src/worldbuilding/schema.py:43`) permits `[]` as a valid value distinct from `None` at the schema level, but this plan treats them as behaviorally identical at the compiler level — no error, no warning, no special log line. This is the simplest correct behavior and matches how the rest of `compile()` already treats optional/empty collections (e.g. `getattr(r_spec, "terrain", "GRASS")` pattern). Test #9 (`test_compiler_terrain_variants_empty_list_behaves_as_not_declared`) asserts exactly this: a region with `terrain_variants=[]` produces the same flat-fill `state.terrain` content as the same region with `terrain_variants=None`/omitted.

## Steps

### Step 1 — Branch the region-painting loop on `terrain_variants`
**Files:** `src/worldbuilding/compiler.py`
**Change:** Replace the current flat-fill block at lines 214-221 (confirmed by direct read above):
```python
r_terrain = getattr(r_spec, "terrain", "GRASS")
for x in range(min_x, max_x + 1):
    for y in range(min_y, max_y + 1):
        if 0 <= x < spec.topology.width and 0 <= y < spec.topology.height:
            terrain[(x, y)] = r_terrain
            if r_spec.type == "town":
                town_tiles.add((x, y))
```
with:
```python
r_terrain = getattr(r_spec, "terrain", "GRASS")
region_hash = 0
if r_spec.terrain_variants:
    for ch in r_spec.id:
        region_hash = (region_hash * 31 + ord(ch)) & 0xFFFFFFFF
for x in range(min_x, max_x + 1):
    for y in range(min_y, max_y + 1):
        if 0 <= x < spec.topology.width and 0 <= y < spec.topology.height:
            if r_spec.terrain_variants:
                tile_offset = ((x & 0xFFFF) << 16) | (y & 0xFFFF)
                entity_id = (region_hash ^ tile_offset) & 0xFFFFFFFF
                tile_terrain = rng.weighted_choice(
                    Domain.INIT, tick=0, entity_id=entity_id,
                    seq=[v.terrain for v in r_spec.terrain_variants],
                    weights=[v.weight for v in r_spec.terrain_variants],
                    sub_id=1,
                )
            else:
                tile_terrain = r_terrain
            terrain[(x, y)] = tile_terrain
            if r_spec.type == "town":
                town_tiles.add((x, y))
```
(Corrected during Review: `tile_offset` now allocates 16 bits per axis instead of packing `y` into 8 bits, closing the `y >= 256` collision the original scheme had — see Design Decisions §1.)
`RegionSpec.terrain_variants` is confirmed to exist as `Optional[List[TerrainVariantSpec]] = Field(None, ...)` at `src/worldbuilding/schema.py:43`, and `TerrainVariantSpec` (`schema.py:27-31`) has `terrain: str` and `weight: float = 1.0` fields — confirmed by direct read. `rng` is the local `DeterministicRNG(seed)` constructed at `compiler.py:198`; `Domain` is already imported in this file (used elsewhere for `Domain.WORLD` draws in the same function) — confirmed no new import needed beyond `Domain.INIT` being a pre-existing enum member (`src/core/enums.py:168`, confirmed by investigation's direct grep).
**Other writers to `terrain`/`town_tiles`:** the base topology fill at lines 202-205 (`terrain[(x,y)] = "PLAIN"` for every tile) runs once before this loop and is fully overwritten by this loop for any tile inside a region's bounds — unchanged, this step does not touch that block. No other code path in `compile()` writes to `terrain` or `town_tiles` (confirmed by investigation's full read of `compiler.py`); `RegionState` itself carries no terrain field (`compiler.py:228-237`, confirmed). This step is the sole writer to both structures within the region loop, so no ordering/race concern applies — `compile()` is single-threaded and synchronous.
**Do NOT touch:** the `if 0 <= x < spec.topology.width and 0 <= y < spec.topology.height:` clamp line itself (structure and condition unchanged); the `if r_spec.type == "town": town_tiles.add((x, y))` line (unchanged, still executes unconditionally for every in-bounds tile of a town region regardless of which branch computed `tile_terrain`); the `RegionState(...)` construction immediately following (lines 223-237, reads `r_spec.type`/`r_spec.bounds`/`r_spec.hazard_level`/`r_spec.hazard_kind`, none of which this step touches).
**Verify:** tests #1-7, #9-10 from Step 2 below; existing tests `test_compiler_minimal_world`, `test_compiler_placement_bounds`, `test_compiler_faction_bravery_bias_produces_real_population_skew`, `test_compiler_faction_bravery_bias_produces_real_action_style_skew` (regression surface, must stay green unmodified).

### Step 2 — Add the 10 new tests (9 from test_plan.md + 1 added during Review)
**Files:** `tests/unit/worldbuilding/test_world_compiler.py`
**Change:** Add all 10 tests, following the `create_base_valid_spec()` dict-copy + `model_validate` + `compile()` pattern documented in investigation.md's "test fixture patterns" section:
1. `test_compiler_terrain_variants_declared_produces_per_tile_variation`
2. `test_compiler_terrain_variants_deterministic_same_seed`
3. `test_compiler_terrain_variants_different_seed_differs`
4. `test_compiler_terrain_variants_never_writes_outside_bounds`
5. `test_compiler_terrain_variants_town_tiles_membership_unaffected_by_terrain_choice`
6. `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` (the load-bearing anti-regression guard — assert `state.terrain` dict content directly, never `state_hash` equality, since `StateFingerprinter.get_fingerprint()` does not read `state.terrain` at all — confirmed by investigation's direct read of `src/replay/fingerprint.py`)
7. `test_compiler_terrain_variants_reuses_weighted_choice_respects_weight`
8. `test_domain_world_entity_resource_building_draws_unaffected_by_terrain_variants_declaration`
9. `test_compiler_terrain_variants_empty_list_behaves_as_not_declared` — per Design Decision 2, assert `state.terrain` content for a region with `terrain_variants=[]` equals the flat-fill content for the same region with `terrain_variants=None`.
10. **`test_compiler_terrain_variants_tile_offset_injective_across_wide_regions`** (added during Review, closing the collision Review found in Design Decision 1's original encoding) — construct a region with `terrain_variants` populated and bounds spanning y >= 256 within a topology tall enough to contain it (e.g. `grid_bounds=(0, 0, 5, 300)`, topology `height >= 301`), compile once, and assert every tile in `state.terrain` restricted to that region's bounds was independently sampled — concretely, assert that `entity_id` values (recomputed in the test using the same `tile_offset = ((x & 0xFFFF) << 16) | (y & 0xFFFF)` formula) are unique for every distinct `(x, y)` pair in the region. This test would have failed against the original `(x << 8) | y` encoding for exactly the `(x=0,y=256)` vs `(x=1,y=0)` collision Review identified.

**Test #8 file placement decision:** place it in `tests/unit/worldbuilding/test_world_compiler.py`, not a new `tests/architecture/` file. Checked `tests/architecture/`'s existing convention directly (e.g. `test_no_new_hardcoded_gameplay_truth.py`, confirmed by direct read): every existing file in that directory is a **static source-code scan** (regex/AST over `.py` files, cross-referenced against a YAML allowlist) — none of them construct a `WorldSpec`, call `compile()`, or make behavioral assertions about runtime RNG-derived output. Test #8 does the latter (compiles twice, compares entity/resource/building positions), so it belongs with the other behavioral compiler tests in `test_world_compiler.py`, consistent with `tests/architecture/`'s actual scope (structural/static guards) rather than stretching that directory's convention.
**Do NOT touch:** any of the existing tests enumerated in test_plan.md's "Regression Surface" section — they must keep passing unmodified, not be edited to accommodate the new tests.
**Verify:** `pytest tests/unit/worldbuilding/test_world_compiler.py -v` — all 10 new tests plus every pre-existing test in the file green.

### Step 3 — Update the Mechanics Bible
**Files:** `docs/mechanics/06_worldbuilding_foundation.md`
**Change:** Add a new subsection after `### Spatial Laws` (which ends before line 36, `## 3. Entity & Resource Distribution` begins at line 36 — confirmed by direct grep of the file's heading structure) — insert as `### Noise-Fill Terrain Law` under `## 2. Regional Boundaries & Sovereignty`. Content: document that (a) a region with a populated `terrain_variants` list gets per-tile terrain sampled via weighted threshold sampling (`DeterministicRNG.weighted_choice`, keyed under `Domain.INIT`, never `Domain.WORLD`) within the region's existing bounds; (b) a region without `terrain_variants` (`None` or empty list, both treated identically) keeps the existing single flat-terrain fill; (c) in both cases the existing topology bounds-clamp (`0 <= x < width and 0 <= y < height`) continues to gate every terrain write identically, and `town_tiles` membership remains driven solely by `r_spec.type == "town"`, independent of which terrain string is written. Cite `src/worldbuilding/compiler.py` (region-painting loop) as the implementing code.
**Do NOT touch:** any other section of this file (`## 1`, `## 3`-`## 9`) — this is a documentation-only addition, not a rewrite.
**Verify:** `tests/docs/test_doc_integrity.py` (already modified per git status — confirm it still passes after this addition; do not diagnose or fix pre-existing modifications to that file, they are out of this ticket's scope unless this step's edit breaks it).

### Step 4 — Flip `SUB-385` to `verified` in the parity ledger
**Files:** `docs/parity_ledger/substrate.yaml` (write only via `tools/parity_ledger_writer.write_entry()`, never raw Edit — per Hard Rules)
**Change:** Confirmed by direct read of `tools/parity_ledger_writer.py:64-85` (`validate_entry`): for `status: "verified"`, both `v2_evidence` and `test_path` must be non-empty strings (this rule applies regardless of `priority` — the `priority == "P0"` branch at line 82-85 is a *separate*, additional requirement for `test_path`, not the only source of the requirement; investigation's note that "P2 doesn't strictly require test_path" is about the `priority`-triggered branch specifically, but the `status == "verified"` branch at line 71-75 independently requires it regardless of priority). Current entry (`docs/parity_ledger/substrate.yaml:4806-4824`, confirmed by direct read): `status: missing`, `v2_evidence: null`, `test_path: null`. Call `write_entry("substrate.yaml", entry_dict, ...)` with the existing entry's `id`/`text`/`priority`/`support_boundary` fields preserved, updating: `status: "verified"`, `v2_evidence: "src/worldbuilding/compiler.py:211-237 (region-painting loop, weighted per-tile noise-fill under Domain.INIT when terrain_variants declared)"`, `test_path: "tests/unit/worldbuilding/test_world_compiler.py::test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict"`. Confirmed by direct read of `docs/parity_ledger/schema.json:34-36`: `test_path` is typed `["string", "null"]` — a single string, not a list — so cite exactly one test path. Cite `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` specifically (not, e.g., test #1) because it is the load-bearing anti-regression guard the entry's own committed text is really certifying (the entry's text is about `terrain_variants` gaining real compiler consumption without breaking non-declaring regions — this test is the direct proof of the "without breaking" half).
**Other writers to `docs/parity_ledger/substrate.yaml`:** this is a shared multi-entry YAML shard — other parity entries (SUB-272 through at least SUB-384+, confirmed present in the file) are written by other tickets' `parity-updater` agent runs, potentially in other concurrent sessions per this repo's shared-working-directory convention (Hard Rules). `write_entry()`'s upsert-by-`id` logic (confirmed at `tools/parity_ledger_writer.py:101-106`) only touches the entry whose `id == "SUB-385"`, leaving all other entries in the shard byte-identical — safe by construction against concurrent entries, but if another session is mid-write to the same shard file at the exact same moment, a raw last-write-wins file overwrite race is possible (the module does no file locking, confirmed by reading `write_entry`'s body). Mitigate by running `git status`/`git diff docs/parity_ledger/substrate.yaml` immediately before this write to check no other session has an uncommitted change to this file already in flight.
**Do NOT touch:** any other entry in `substrate.yaml`.
**Verify:** `write_entry()`'s own return value confirms success; re-read the shard afterward to confirm only `SUB-385` changed. `python3 tools/parity_index.py build` is auto-invoked in-process by `write_entry()` (confirmed at `tools/parity_ledger_writer.py:110`) — no separate manual index rebuild step needed for this write specifically, though the ticket-close workflow's `agent-monitoring` retro metric visibility caveat (noted in the module's own docstring) is a known pre-existing gap, not something this step needs to work around.

### Step 5 — Record the Domain.INIT decision in intentional_divergences.md
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** Append a new entry as `### 2.46 Noise-Fill Terrain Draws Namespaced Under Domain.INIT, Not Domain.WORLD (TCK-20260821-COMPILER-NOISE-FILL)` (confirmed next available number: existing entries run through `### 2.45 ...` per direct grep of section headings above; follow the established `### 2.N Title (TICKET-ID)` heading format and `Subsystem`/`Rationale`/`Verification`/`Status` field structure used by neighboring entries, e.g. `### 2.45`). Content: state that `WorldCompiler.compile()`'s new per-tile noise-fill terrain draw is keyed under `Domain.INIT` rather than sequenced within `Domain.WORLD`'s existing entity/resource/building draw order, because `DeterministicRNG` is a stateless composite-key hash (no sequential stream to reorder) and `Domain.INIT`'s one existing production consumer (`Kernel.__init__`'s run-suffix draw, `src/engine/kernel.py:122`) is structurally isolated by call-ordering (compile() returns before Kernel is constructed) and by RNG statelessness (each call builds its own `random.Random(seed)`). Rationale class: **Bounded** (a scoping/collision-avoidance choice, not a behavior-correctness fix, per investigation's explicit recommendation). Verification: `tests/unit/worldbuilding/test_world_compiler.py::test_domain_world_entity_resource_building_draws_unaffected_by_terrain_variants_declaration` (test #8 from Step 2). Status: ACTIVE.
**Do NOT touch:** any other entry in the file, including the `## 3. Unsupported / Retired Behavior` table and `## 5. Economy Divergences` section that follow. Do not renumber existing entries.
**Verify:** `tests/docs/test_doc_integrity.py` still passes; the new entry is present and correctly formatted (matches sibling entries' field structure).

## Scope Guards
Verbatim from investigation.md's "Anti-Drift Hazards":
- Do not gate the new draw on anything except `if r_spec.terrain_variants:` (or equivalent truthy/non-empty check). Any broader condition (e.g. "if region type is X") risks silently changing behavior for regions that happen to match that condition but don't declare variants.
- Do not touch the `if r_spec.type == "town": town_tiles.add((x, y))` line at all — it must remain reachable and execute identically regardless of which terrain-fill branch (flat vs. noise) runs above it.
- Do not let the noise-fill draw's `entity_id`/`sub_id` selection reuse `Domain.WORLD`'s existing conventions (0/1 for position, 10-14 for personality/class, ≥100 for reroll) even by accident — `Domain.INIT` was chosen specifically to avoid needing to reason about this at all; reverting to `Domain.WORLD` "for consistency" would reintroduce the exact class of risk this ticket exists to eliminate.
- Do not rely on `state_hash` equality as the sole proof of "no change for non-declaring worlds." `state_hash`/`StateFingerprinter` structurally excludes terrain content and cannot detect a terrain-painting regression at all. Test #6 (direct `state.terrain` dict-content assertion) is the load-bearing guard, not the certification determinism tests.
- Do not expand scope into validating terrain-type semantics against `legality.py`'s blocking/cover/high-ground vocabulary — that's a real, identified risk (WALL/FOREST/MOUNTAIN/HILL terrain strings have tactical meaning) but belongs to ticket #5 (real content migration, `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`) or a future ticket, not this one.
- `TerrainVariantSpec.weight` must be used as a true relative sampling weight via `rng.weighted_choice` — do not silently ignore `weight` and pick uniformly, and do not reinvent weighted sampling by hand.

Additional guards from this plan's own scope:
- Do not add the `terrain_variants` field itself to `RegionRecipeSpec`/`RegionSpec` — already landed by `TCK-20260821-NOISE-FILL-SCHEMA` (out of scope, prerequisite).
- Do not migrate any real world module (`wolf_den_near_forest.yaml`, `forest_warden_grove.yaml`) to declare `terrain_variants` — that is `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`, a separate ticket.
- Do not author a dedicated golden-hash tile-level regression test beyond what `test_plan.md` specifies — that is `TCK-20260821-NOISE-FILL-DETERMINISM-TEST`, a separate ticket; this ticket only needs the existing determinism tests to keep passing plus the 10 new tests in Step 2.

## Dependency Map
- Step 1 has no dependencies (schema field already exists per `TCK-20260821-NOISE-FILL-SCHEMA`).
- Step 2 depends on Step 1 (tests assert behavior of the new branch).
- Step 3 depends on Step 1 (documents the landed behavior; can be drafted in parallel but should not be finalized/verified until Step 1's code is stable).
- Step 4 depends on Step 1 and Step 2 (needs both real `v2_evidence` file:line and a real, passing `test_path`).
- Step 5 depends on Step 2 (cites test #8 by name; test must exist and pass before this doc entry is added).
- Steps 3, 4, 5 are independent of each other and can be done in any order once their respective dependencies are satisfied.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Compiling any world spec where no region declares variants produces a bit-identical state_hash and coordinates to pre-change output, verified against the certification corpus. | Step 1 (else-branch preserves `r_terrain` flat-fill exactly) | `tests/certification/test_world_compile_determinism.py::test_compiler_seeding_determinism`, `test_compiler_layout_variation_under_different_seeds`; plus Step 2 test #6 (`test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict`) as the direct content-level guard `state_hash` alone cannot provide |
| When a region declares variants, compiling twice with the same seed produces identical per-tile terrain assignment within bounds; compiling with different seeds produces a measurably different distribution within the same bounds. | Step 1 (`rng.weighted_choice` under `Domain.INIT`, deterministic per `(region_hash, x, y)`) | Step 2 tests #2 (`test_compiler_terrain_variants_deterministic_same_seed`) and #3 (`test_compiler_terrain_variants_different_seed_differs`) |
| Noise-filled terrain never writes outside region bounds or exceeds topology width/height — the existing clamp continues to gate every write. | Step 1 (clamp line untouched, still gates both branches) | Step 2 test #4 (`test_compiler_terrain_variants_never_writes_outside_bounds`) |
| town_tiles membership for a variant-declaring town region is unaffected by which terrain string the noise-fill assigns — still driven solely by r_spec.type == "town". | Step 1 (`town_tiles.add` line untouched, unconditional on terrain branch) | Step 2 test #5 (`test_compiler_terrain_variants_town_tiles_membership_unaffected_by_terrain_choice`) |
| Noise-fill draws are keyed under a distinct RNG Domain (e.g. Domain.INIT) from Domain.WORLD's existing entity/resource/building draws, eliminating collision risk by construction rather than by draw-order sequencing. | Step 1 (all noise-fill draws use `Domain.INIT`, Design Decision 1's encoding scheme) | Step 2 test #8 (`test_domain_world_entity_resource_building_draws_unaffected_by_terrain_variants_declaration`); existing tests `test_compiler_faction_bravery_bias_produces_real_population_skew`/`test_compiler_faction_bravery_bias_produces_real_action_style_skew` (must stay green, proving `Domain.WORLD` sub_id 10-14 draws untouched) |

## Verification
Exact scoped pytest commands from `test_plan.md`:
```
pytest tests/unit/worldbuilding/ tests/certification/test_world_compile_determinism.py -v
```
```
pytest tests/unit/worldbuilding/ tests/certification/test_world_compile_determinism.py tests/integration/kernel/test_phase2_determinism.py -v -m "not slow"
```
Never run the bare `pytest tests/`. A green run of `tests/certification/test_world_compile_determinism.py` alone is never sufficient proof of no regression (state_hash-blindness to terrain, per investigation) — always pair with `tests/unit/worldbuilding/` in the same invocation.

## Anti-Drift Notes
- `DeterministicRNG` has **no sequential stream** — `get_float`/`get_int`/`choice`/`weighted_choice`/`sample` each construct a fresh `random.Random(seed)` per call (confirmed by direct read, `src/platform/rng.py:85-108`); only the deprecated `next_float`/`next_int` touch `self._rng_map`, and `compile()` never calls those. Do not reason about this change in terms of "draw order" — reason about it in terms of composite-key collision, which is what Design Decision 1 actually addresses.
- `state_hash` (`StateFingerprinter.get_fingerprint()`, `src/replay/fingerprint.py`) and `CanonicalStateHasher.to_canonical_data()` (`src/engine/checkpoint.py`) both structurally exclude `state.terrain` — confirmed by investigation's direct read of both. A regression in terrain painting for non-declaring regions would pass every existing hash-based test silently. Test #6 exists specifically to close this gap; treat it as the single most important new test in this plan, not an incidental addition.
- `Domain.INIT`'s one real production use today is `Kernel.__init__`'s run-suffix draw (`src/engine/kernel.py:122`, `get_int(Domain.INIT, 0, 0, 1000, 9999)`, implicit `sub_id=0`). This is safe to share the Domain with (not just "probably fine") because of two independent, verified reasons: call-ordering (compile() always finishes before Kernel is constructed in every real call path — `src/cli/entry.py:203-235`, `src/lab/orchestrator.py:196-215`) and RNG statelessness (no shared mutable state between the two calls even if their keys coincided). Design Decision 1's `sub_id=1` additionally avoids exact key coincidence as a debugging-hygiene courtesy, not a correctness requirement — do not treat this as fixing a real bug, because there was none.
- `scenario_checkpoint.py:100-108`'s comment about `Domain.INIT` "advancing the stream" is stale/inaccurate relative to the current stateless RNG implementation and is unrelated to this ticket (a different `DeterministicRNG` instance entirely, restored via `set_state()` after `compile()` has already finished) — do not attempt to fix or reconcile that comment as part of this ticket; it is out of scope.
- `legality.py`'s real tactical meaning for `WALL`/`FOREST`/`MOUNTAIN`/`HILL` terrain strings is a genuine downstream risk once real content declares variants including those strings, but no real content does yet (that's ticket `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`, out of scope here) — do not add any terrain-semantic validation to `compile()` in this ticket.
