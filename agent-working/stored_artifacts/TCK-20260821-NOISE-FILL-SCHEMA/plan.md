---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-SCHEMA
artifact_type: plan
tags: [world, schema]
---

# Implementation Plan — TCK-20260821-NOISE-FILL-SCHEMA

## Summary

Add a new optional, fully inert `terrain_variants` field to both the authoring-time
(`RegionRecipeSpec`) and resolved-time (`RegionSpec`) region schemas, backed by a single shared
`TerrainVariantSpec` pydantic model, and explicitly forward it through
`WorldAssemblyResolver.resolve_module_contribution()` so it survives the real module pipeline
instead of silently dropping — the exact gap `TCK-20260701-HAZARD-KIND-RESOLVER-GAP` had to
retroactively fix for `hazard_kind`. No compiler consumption, no real content migration, no new
validation semantics: this ticket only adds the schema-level plumbing and its regression tests,
plus a `missing`-status parity ledger entry pointing forward to the ticket that will consume the
field. `WorldCompiler`, the `ValidationContext.MODULE` dummy_spec builder, and all real
`data/content/world_modules/*.yaml` files are untouched.

## Design Decisions

**Where `TerrainVariantSpec` is defined: define once in `src/worldbuilding/schema.py`, import into
`src/worldbuilding/recipe.py`.** Adopting the investigation's primary recommendation, not the named
duplication alternative. Reasoning:

- `terrain_variants` is identical in shape and semantics at authoring time and resolved time — no
  transformation happens between `RegionRecipeSpec.terrain_variants` and `RegionSpec.terrain_variants`
  (confirmed: `normalizer.py:144` does `regions=list(spec.regions)`, a pure passthrough of already-typed
  `RegionRecipeSpec` objects — no per-field regions logic exists in that normalizer at all, confirmed by
  investigation's direct read of `src/worldmodules/normalizer.py:130-157`). This is architecturally the
  same shape as `QuestDefinition`, not the same shape as `count` fields (which differ in type between
  recipe and resolved forms and therefore must be independently defined per investigation.md).
- Precedent already exists and is exercised in the same module family: `QuestDefinition` is defined once
  in `src/worldbuilding/schema.py:188` (`class QuestDefinition(BaseModel):`, confirmed by direct read)
  and imported unchanged into `src/worldmodules/schema.py:13` (`from src.worldbuilding.schema import
  QuestDefinition`, confirmed by direct read), reused as `WorldModuleSpec.quest_definitions`.
  `src/worldmodules/schema.py` already imports from both `src.worldbuilding.recipe` (line 7) and
  `src.worldbuilding.schema` (line 13) together today, so a `recipe.py -> schema.py` import is not a novel
  shape in this module family.
- No cycle risk: confirmed by direct read that `src/worldbuilding/schema.py` (50 lines read, full import
  block at lines 1-7) contains zero references to `src.worldbuilding.recipe` as an import (the only hits
  for the string "recipe" in that file are prose in `description=` strings, not import statements), and
  `src/worldbuilding/recipe.py`'s import block (lines 1-5) contains zero references to
  `src.worldbuilding.schema`. Adding `recipe.py -> schema.py` is a new, strictly one-directional edge.
- The duplication alternative (mirroring `hazard_kind`) is defensible but accepts avoidable drift risk on
  a field with no reason to diverge — rejected for that reason, per investigation's own framing.

Implementer: define `TerrainVariantSpec` in `schema.py` immediately above `class RegionSpec(BaseModel):`
(currently `src/worldbuilding/schema.py:27`), and add `from src.worldbuilding.schema import
TerrainVariantSpec` to `recipe.py`'s import block (currently `src/worldbuilding/recipe.py:1-5`).

## Steps

### Step 1 — Define `TerrainVariantSpec` in `src/worldbuilding/schema.py`

**Files:** `src/worldbuilding/schema.py`

**Change:** Immediately before `class RegionSpec(BaseModel):` (`src/worldbuilding/schema.py:27`, confirmed
by direct read this turn — `RegionSpec` currently starts at line 27 with `model_config =
ConfigDict(frozen=True)` at line 28, no `extra="forbid"`), add:

```python
class TerrainVariantSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    terrain: str = Field(..., min_length=1, description="Terrain type for this variant fill option")
    weight: float = Field(1.0, gt=0.0, description="Relative sampling weight; consumed by the noise-fill compiler logic added in a later ticket (TCK-20260821-COMPILER-NOISE-FILL) — unused/inert here")
```

`BaseModel`, `Field`, `ConfigDict` are already imported at `src/worldbuilding/schema.py:7` (confirmed by
direct read: `from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict,
ValidationError`) — no new imports needed for this class itself.

**Do NOT touch:** `RegionSpec`'s own `model_config` (stays `ConfigDict(frozen=True)`, no `extra="forbid"`
— that is pre-existing, out of this ticket's concern per investigation.md). Do not add `extra="forbid"`
to `RegionSpec` as a "fix" — not requested, not in scope.

**Verify:** Covered indirectly by Step 3's and Step 5's tests (`TerrainVariantSpec` has no standalone
test — it's exercised through `RegionRecipeSpec`/`RegionSpec` construction).

### Step 2 — Add `terrain_variants` field to `RegionSpec`

**Files:** `src/worldbuilding/schema.py`

**Change:** In `class RegionSpec(BaseModel):` (`src/worldbuilding/schema.py:27-45`, confirmed by direct
read), add a new field immediately after the existing `tags` field (currently line 36:
`tags: List[str] = Field(default_factory=list, description="Semantic labels for quest routing (e.g.
mine, forest, ruins, settlement)")`):

```python
terrain_variants: Optional[List[TerrainVariantSpec]] = Field(None, description="Optional set of terrain fill variants for organic in-region terrain; inert until consumed by TCK-20260821-COMPILER-NOISE-FILL")
```

Use `List` from `typing` (already imported at `src/worldbuilding/schema.py:6`: `from typing import
Optional, Any, Dict, List, Literal` — confirmed by direct read), not lowercase `list[...]`, matching this
file's existing convention for every other list-typed field (e.g. `tags: List[str]` on the same class).

**Do NOT touch:** The `@model_validator(mode="after") def validate_bounds` method on `RegionSpec`
(`src/worldbuilding/schema.py:38-45`) — no cross-field validation is being introduced for
`terrain_variants`, it stays a plain optional field.

**Verify:** `test_region_spec_terrain_variants_default_none` (or folded into Step 5's test 2 — see Step 5
for the fold decision) — `tests/unit/worldbuilding/test_worldspec_schema.py`.

### Step 3 — Add `terrain_variants` field to `RegionRecipeSpec`

**Files:** `src/worldbuilding/recipe.py`

**Change:** Add the import at the top of `src/worldbuilding/recipe.py` (current import block, lines 1-5,
confirmed by direct read: `from typing import Optional, Any, List, Union` / `from pydantic import
BaseModel, Field, model_validator, ConfigDict` — no import from `src.worldbuilding.schema` exists today):

```python
from src.worldbuilding.schema import TerrainVariantSpec
```

Then, in `class RegionRecipeSpec(BaseModel):` (`src/worldbuilding/recipe.py:8-26`, confirmed by direct
read — `model_config = ConfigDict(frozen=True, extra="forbid")` at line 9), add a new field immediately
after the existing `tags` field (currently line 17: `tags: List[str] = Field(default_factory=list,
description="Semantic labels for quest routing (e.g. mine, forest, ruins, settlement)")`) and before the
`@model_validator` block (currently starting line 19):

```python
terrain_variants: Optional[List[TerrainVariantSpec]] = Field(None, description="Optional set of terrain fill variants for organic in-region terrain; inert until consumed by TCK-20260821-COMPILER-NOISE-FILL")
```

`Optional` and `List` are already imported (line 4). Use `List[TerrainVariantSpec]`, matching this file's
existing style for every list-typed field.

**Do NOT touch:** `model_config = ConfigDict(frozen=True, extra="forbid")` on `RegionRecipeSpec`
(`src/worldbuilding/recipe.py:9`) — must remain exactly as-is; `extra="forbid"` is the exact protection
whose absence contributed to the original `HAZARD-KIND-RESOLVER-GAP` failure mode, and this ticket's own
Step 5 test explicitly re-asserts it still holds after this field is added. Do not touch
`validate_bounds` (`src/worldbuilding/recipe.py:19-26`).

**Verify:** `test_region_recipe_spec_accepts_terrain_variants_and_defaults_to_none` (Step 5).

### Step 4 — Forward `terrain_variants` in `WorldAssemblyResolver.resolve_module_contribution()`

**Files:** `src/worldassembly/resolver.py`

**Change:** In the `RegionSpec(...)` construction inside `resolve_module_contribution()`
(`src/worldassembly/resolver.py:792-800`, confirmed verbatim by direct read this turn):

```python
regions_spec_list.append(RegionSpec(
    id=f"{prefix}{reg.id}",
    type=reg.type,
    bounds=reg.grid_bounds,
    terrain=reg.terrain,
    hazard_level=reg.hazard_level,
    hazard_kind=getattr(reg, "hazard_kind", "PHYSICAL"),
    tags=list(getattr(reg, "tags", [])),
))
```

add, immediately after the `tags=list(getattr(reg, "tags", []))` line and before the closing `))`:

```python
    terrain_variants=getattr(reg, "terrain_variants", None),
```

Use `getattr(reg, "terrain_variants", None)`, mirroring the `hazard_kind` idiom (`getattr(reg,
"hazard_kind", "PHYSICAL")`) rather than the `tags` idiom (`list(getattr(reg, "tags", []))`) — no `list()`
wrapping is needed since `terrain_variants` is `Optional[List[...]]` (default `None` is itself a valid
value, unlike `tags` which defaults to `[]` and is never `None`).

**Other writers to this construction site (corrected during Review — the investigation's original
enumeration was incomplete):** `RegionSpec(...)` is constructed in exactly 4 places in the codebase, not
1:

1. `resolve_module_contribution()` (`resolver.py:792-800`, this step's target) — the authoritative-path
   writer for the resolved region list that `WorldCompiler` actually consumes. Forwards from a
   `RegionRecipeSpec` source object; gets the new field via this step's change.
2. `WorldAssemblyValidator.validate()`'s `ValidationContext.MODULE` `dummy_spec` builder
   (`resolver.py:95-101`) — already omits `hazard_kind`/confirmed out of scope; not touched.
3. `WorldProceduralGenerator.generate()` (`src/worldgeneration/generator.py:90,99,106`) — constructs
   `RegionSpec` from hardcoded literals (`terrain="GRASS"`, etc.), no `RegionRecipeSpec` input, and
   already omits `hazard_kind`/`tags` too. Confirmed via `grep -rn "WorldProceduralGenerator"` that this
   class has no production caller anywhere in `src/` — only referenced by its own file and
   `tests/unit/worldgeneration/test_generator.py`.
4. `_build_world_spec()` in `src/lab/workflows/generate_simulation_setup.py:280` — a lab tooling script,
   also constructs `RegionSpec` from hardcoded literals with no `RegionRecipeSpec` input, and already
   omits `hazard_kind`/`tags` too.

Sites 2-4 need no `terrain_variants` forwarding: none has a `RegionRecipeSpec` source object to forward
from (they're all synthetic/procedural construction, not module-authored content), and none currently
forwards `hazard_kind` or `tags` either — the new field will correctly default to `None` at all three with
zero code change, consistent with how those two existing optional fields already behave there today. Not
touched by this step.

**Do NOT touch:** Any other kwarg in this construction (`id`, `type`, `bounds`, `terrain`, `hazard_level`,
`hazard_kind`, `tags`) and the `dummy_spec` builder at lines 95-101.

**Verify:** `test_terrain_variants_survive_module_pipeline` (Step 5) — this is the test that specifically
proves forwarding happened rather than a silent drop, per the anti-drift hazard this whole ticket exists
to prevent.

### Step 5 — Add the new tests

**Files:**
- `tests/integration/worldassembly/test_real_content_world_modules.py`
- `tests/unit/worldassembly/test_assembly.py`
- `tests/unit/worldbuilding/test_worldspec_schema.py` (optional — see fold note)

**Change:**

1. **`test_terrain_variants_survive_module_pipeline`** — add to
   `tests/integration/worldassembly/test_real_content_world_modules.py`, placed immediately after
   `test_hazard_kind_survives_module_pipeline` (per test_plan.md and ticket's explicit instruction to
   mirror that test's shape). Two cases in one test function, matching the precedent test's own combined
   structure:
   - **Declared-value case**: construct a synthetic `WorldModuleSpec` in Python (mirroring
     `test_id_collision_prevention`'s pattern at `tests/unit/worldassembly/test_assembly.py:358-375`)
     containing one `RegionRecipeSpec` using the real catalog-registered region id `"hometown"`
     (confirmed present at `data/content/world/runtime_regions.yaml:2` per investigation.md) with
     `terrain_variants=[TerrainVariantSpec(terrain="FOREST", weight=2.0), TerrainVariantSpec(terrain="GRASS", weight=1.0)]`.
     Run through `WorldModuleAuthoringNormalizer.normalize()` then
     `WorldAssemblyResolver.resolve_module_contribution()`; assert the resolved `RegionSpec.terrain_variants`
     equals the declared list exactly (same objects/values, in order).
   - **Default/backward-compat case**: reuse an existing real `MODULE_MATRIX` module (e.g.
     `frontier_village_core`, matching the precedent test's own default-case module), run through the same
     normalize -> resolve pipeline, and assert every resolved region's `terrain_variants is None`.
   - Import `TerrainVariantSpec` from `src.worldbuilding.schema` in this test file (it is the shared class
     per the Design Decisions section — construct instances of it directly, not a `recipe.py`-local
     duplicate, since none exists after Step 1/3).

2. **`test_region_recipe_spec_accepts_terrain_variants_and_defaults_to_none`** — add to
   `tests/unit/worldassembly/test_assembly.py`, placed near the existing `RegionRecipeSpec(...)`
   construction sites (~line 949, per test_plan.md). Three assertions:
   - `RegionRecipeSpec(id=..., type=..., grid_bounds=...)` with no `terrain_variants` kwarg succeeds and
     `.terrain_variants is None`.
   - `RegionRecipeSpec(id=..., type=..., grid_bounds=..., terrain_variants=[TerrainVariantSpec(terrain="FOREST")])`
     succeeds and round-trips the declared list.
   - `extra="forbid"` regression: constructing `RegionRecipeSpec(..., bogus_field=1)` still raises
     `pydantic.ValidationError` — proves the field addition did not weaken/replace the `extra="forbid"`
     policy.

3. **Fold decision for test 3 (`test_region_spec_terrain_variants_default_none`)**: implement it as a
   **separate small test** in `tests/unit/worldbuilding/test_worldspec_schema.py`, not folded into test 2.
   Rationale: `RegionSpec` and `RegionRecipeSpec` are independently defined pydantic models (per Design
   Decisions — only `TerrainVariantSpec` itself is shared, the parent classes are not), each with its own
   field wiring that must be checked independently; folding it into test 2 would mean
   `tests/unit/worldassembly/test_assembly.py` silently also becoming the coverage owner for
   `src/worldbuilding/schema.py`'s `RegionSpec`, which is a different file's concern and where
   `test_worldspec_schema.py` already lives as the natural home. Assert: `RegionSpec(id=..., type=...,
   bounds=...)` with no `terrain_variants` kwarg succeeds and `.terrain_variants is None`.

**Do NOT touch:** Any test that constructs against real `data/content/world_modules/*.yaml` files by
adding `terrain_variants` to that YAML — all new-field test coverage must use synthetic in-test
`WorldModuleSpec`/`RegionRecipeSpec` construction (declared-value case) or existing untouched real modules
(default case).

**Verify:** Run the four scoped pytest commands from test_plan.md (see Verification section below); all
new and pre-existing tests in the four target paths pass.

### Step 6 — Add parity ledger entry

**Files:** `docs/parity_ledger/substrate.yaml`

**Change:** At implementation time, run:
```
grep -o 'SUBSTRATE-NEW-[0-9]*' docs/parity_ledger/substrate.yaml | sort -V | tail -1
```
to get the current highest ID (confirmed as of this plan's writing: `SUBSTRATE-NEW-012` is the highest
existing entry — the implementer's own next-available ID will be `SUBSTRATE-NEW-013` unless another
concurrent session has added entries since; always re-run the grep rather than trusting this plan's
snapshot). Use `tools/parity_ledger_writer.write_entry()` (confirmed present and signature read at
`tools/parity_ledger_writer.py:88`: `write_entry(shard_filename: str, entry: dict, ledger_dir=None,
db_path=None) -> dict` — validates via `validate_entry()` then upserts by `id` into the shard, rebuilding
the derived parity index) — never a raw `Edit` to the YAML file, since the writer both validates against
`docs/parity_ledger/schema.json`'s rules and keeps the derived index in sync.

Entry shape (status `missing` requires no `v2_evidence`/`test_path`/`divergence_note` per
`validate_entry()`'s rules at `tools/parity_ledger_writer.py:64-85` — those are only required for
`verified`/`divergent` status or `P0` priority):
```python
entry = {
    "id": "SUBSTRATE-NEW-0XX",  # next available, confirmed via grep at implementation time
    "text": "RegionRecipeSpec/RegionSpec accept an optional terrain_variants field (List[TerrainVariantSpec]) for future organic in-region terrain fill; field is schema-only and inert, forwarded explicitly through WorldAssemblyResolver.resolve_module_contribution(). No compiler consumption exists yet.",
    "status": "missing",
    "priority": "P2",
    "v2_evidence": None,
    "test_path": None,
    "divergence_note": None,
}
```
Adjust the exact key set to match whatever additional required/optional keys `docs/parity_ledger/schema.json`
defines beyond the ones `validate_entry()` checks (implementer should read `schema.json` once before
calling `write_entry()` to confirm the full property list, e.g. whether a `support_boundary` or similar
note field is expected — investigation.md cites the `infrastructure.yaml` precedent using a
`support_boundary` note for the same "schema-only, no src/ logic yet" shape). Explicitly note in the entry
text that `WorldCompiler` is untouched and this entry is expected to flip to `verified` when
`TCK-20260821-COMPILER-NOISE-FILL` lands.

**Other writers to this resource:** `docs/parity_ledger/substrate.yaml` is a shared shard file — other
tickets/sessions may be appending entries concurrently. `write_entry()`'s upsert-by-`id` behavior
(`tools/parity_ledger_writer.py:101-106`: loops existing entries, replaces on `id` match, else appends)
means a collision only occurs if two sessions independently pick the same next-available ID at the same
time; re-running the `grep ... | tail -1` immediately before calling `write_entry()` (not relying on a
number cached earlier in the session) minimizes this window. `tools/parity_index.py` /
`parity_ledger_scan.py` read this file but do not write it under normal operation. This ticket does not
modify any other shard file.

**Do NOT touch:** Any other parity ledger shard file, any `verified`/`divergent` entry, or the
`hazard_kind`/`tags`-forwarding entry (`SUBSTRATE-NEW-007`'s neighbor per investigation.md) — that entry
already exists and documents different fields.

**Verify:** `python3 tools/parity_ledger_writer.py` round-trip validates without raising
`EntryValidationError`; entry appears once (not duplicated) in `docs/parity_ledger/substrate.yaml` after
the call.

## Scope Guards

Verbatim from investigation.md's "Anti-Drift Hazards":

- **Do not touch `WorldCompiler`** (`src/worldbuilding/compiler.py`) — any consumption of
  `terrain_variants` (noise sampling, thresholding, per-tile painting) belongs to
  `TCK-20260821-COMPILER-NOISE-FILL`. Even a no-op-looking `getattr(r_spec, "terrain_variants", None)`
  read added to `compiler.py` in this ticket would be scope creep per the ticket's own explicit boundary.
- **Do not touch the `ValidationContext.MODULE` `dummy_spec` builder** (`resolver.py:90-105`) — confirmed
  correctly out of scope; do not "fix" it opportunistically since it already omits `hazard_kind` too and
  this ticket's own Out of Scope explicitly names it.
- **Do not author `terrain_variants` into any real `data/content/world_modules/*.yaml` file** — that is
  `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`'s job. The new declared-value test must use a synthetic, in-test
  `WorldModuleSpec`/`RegionRecipeSpec` construction, not a real module fixture.
- **`extra="forbid"` must remain in place** on `RegionRecipeSpec` — do not weaken it while adding the
  field; this is the exact protection whose absence caused the original hotfix's blocking bug.

Additional guards from the ticket body's own Out of Scope:

- Do not add any enum constraint to `terrain` on either schema — none exists today, this ticket does not
  introduce one.
- Do not update `docs/testing/test_taxonomy.md` — investigation confirms Section 1 (lines 56-68) already
  generically documents this exact pattern and names `test_hazard_kind_survives_module_pipeline` as the
  template; no doc drift risk from leaving it as-is.
- Do not update any Mechanics Bible chapter — the field is inert by design; `docs/mechanics/06_worldbuilding_foundation.md`'s
  update is deferred to `TCK-20260821-COMPILER-NOISE-FILL`, which will have real behavior to document.

## Dependency Map

- Step 1 (define `TerrainVariantSpec`) must complete before Step 2 and Step 3, since both reference the
  class.
- Step 2 and Step 3 are independent of each other (different files, different classes) but both depend on
  Step 1.
- Step 4 depends on Step 3 (the `reg.terrain_variants` attribute must exist on `RegionRecipeSpec` before
  the resolver can forward it) and Step 2 (the `RegionSpec(...)` constructor call must accept the kwarg).
- Step 5's tests depend on Steps 1-4 all being complete (they exercise the full pipeline and both schema
  classes).
- Step 6 (parity ledger) is independent of Steps 1-5 code-wise but should be done last, once the final
  field name/shape is locked in, so the ledger entry text accurately describes the shipped field.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| RegionRecipeSpec accepts the new optional field while `extra="forbid"` continues to be enforced on the model. | Step 3 | `test_region_recipe_spec_accepts_terrain_variants_and_defaults_to_none` (Step 5, `extra="forbid"` sub-assertion) |
| Constructing a RegionRecipeSpec without the new field succeeds and the field defaults to None/empty, with zero behavior change. | Step 3 | `test_region_recipe_spec_accepts_terrain_variants_and_defaults_to_none` (Step 5, no-kwarg case) |
| A module YAML that does NOT declare the field, run through normalize() -> resolve_module_contribution(), yields a RegionSpec whose new field equals the same default — byte-identical to today for non-opted-in modules. | Steps 2, 4 | `test_terrain_variants_survive_module_pipeline` (Step 5, default/backward-compat case) |
| A module YAML that DOES declare the field survives normalize() + resolve_module_contribution() with the declared value intact on the resulting RegionSpec, proving explicit forwarding rather than a silent drop. | Steps 1, 2, 3, 4 | `test_terrain_variants_survive_module_pipeline` (Step 5, declared-value case) |
| The full test_real_content_world_modules.py MODULE_MATRIX (all 20 real modules) and test_compiler_seeding_determinism pass unchanged, since none of the 20 real modules declare the new field and compiler.py is untouched by this concern. | Steps 1-4 (by not touching compiler.py or real YAML) | `pytest tests/integration/worldassembly/test_real_content_world_modules.py -v` and `pytest tests/certification/test_world_compile_determinism.py::test_compiler_seeding_determinism -v` |

## Verification

Run exactly the scoped commands from test_plan.md — never `pytest tests/`:

```
pytest tests/integration/worldassembly/test_real_content_world_modules.py -v
pytest tests/certification/test_world_compile_determinism.py::test_compiler_seeding_determinism -v
pytest tests/unit/worldassembly/ -v
pytest tests/unit/worldbuilding/ -v
```

All four must pass in full (not just the new tests) — these cover the ticket's explicitly named
acceptance-criteria test target, the explicitly named determinism regression guard, and both unit
directories containing every direct `RegionRecipeSpec`/`RegionSpec`/resolver construction call site this
ticket's edits touch (`tests/unit/worldassembly/test_assembly.py` lines 364, 373, 949;
`tests/unit/worldassembly/test_archetype_preservation.py` lines 85, 119-120).

## Anti-Drift Notes

- The exact touch-point this ticket exists to prevent recurring: adding the field to only one of
  `RegionRecipeSpec`/`RegionSpec`, or adding it to both schemas but forgetting the explicit forward in
  `resolve_module_contribution()`'s `RegionSpec(...)` kwargs. This is verbatim the
  `TCK-20260701-HAZARD-KIND-RESOLVER-GAP` failure mode. `test_terrain_variants_survive_module_pipeline`
  must exercise the real synthetic-module -> `normalize()` -> `resolve_module_contribution()` pipeline,
  not just direct object construction, or it will not catch this class of gap.
- `test_compiler_seeding_determinism` passing unchanged is itself the strongest guard against scope creep
  into `WorldCompiler` — any accidental read/consumption of `terrain_variants` in `compiler.py` that
  changed RNG draw sequencing or output shape for existing content would flip this test's `state_hash`
  comparison. If this test fails after this ticket's changes, the root cause is almost certainly an
  accidental `compiler.py` touch — revert it, don't chase the RNG.
- Re-run the `SUBSTRATE-NEW-*` ID grep immediately before calling `write_entry()`, not earlier in the
  session — this repo's working directory can be shared by concurrent sessions per CLAUDE.md's Hard
  Rules, so the highest ID may have moved since Step 6 was planned.

## Deviations

**Step 6 — ID format, discovered at implementation time.** This plan assumed the next parity ledger ID
would continue the `SUBSTRATE-NEW-0XX` scheme (`SUBSTRATE-NEW-013`, following the observed
`SUBSTRATE-NEW-012` high-water mark). At implementation time this proved wrong in *shape*, not just
number: `tools/parity_ledger_writer.py`'s `validate_entry()` enforces `_ID_PATTERN =
re.compile(r"^[A-Z]+-[0-9]{3}$")` (single hyphen, exactly 3 digits), which `SUBSTRATE-NEW-013` does not
match — confirmed by direct call, `validate_entry()` raises `EntryValidationError` for it. The
`SUBSTRATE-NEW-008`..`012` entries are pre-existing/grandfathered, written via raw `Edit` before this
validating writer tool existed; `docs/parity_ledger/substrate.yaml` has since moved on to a `SUB-NNN`
scheme (`SUB-001`..`SUB-384` at implementation time, all matching the enforced pattern). The implementer
used `SUB-385` instead of `SUBSTRATE-NEW-013`, re-confirming the true next-available `SUB-` number via
`grep` immediately before the `write_entry()` call, consistent with this plan's own Anti-Drift Notes
guidance to never trust a cached ID snapshot. No other part of Step 6 (entry content, `status: missing`,
`priority: P2`, key set) changed from the plan.
