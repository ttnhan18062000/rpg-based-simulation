---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-SCHEMA
artifact_type: investigation
tags: [world, schema]
---

# Investigation — TCK-20260821-NOISE-FILL-SCHEMA

## Current Behavior

**`RegionRecipeSpec`** (`src/worldbuilding/recipe.py:8-26`) — the `worldcomposition.v1` module-authoring
schema for a region. `model_config = ConfigDict(frozen=True, extra="forbid")` (line 9) — unknown
fields are rejected outright at YAML-load time. Current fields: `id`, `type`, `grid_bounds`,
`terrain: Optional[str] = "GRASS"`, `hazard_level: Optional[float] = 0.0`,
`hazard_kind: Optional[str] = "PHYSICAL"`, `tags: List[str] = []`. No nested pydantic sub-model
exists anywhere in this file today — every field is a scalar, tuple, or `List[str]`. Pydantic v2
style throughout (`ConfigDict`, `model_validator(mode="after")`).

**`RegionSpec`** (`src/worldbuilding/schema.py:27-45`) — the resolved/compiled-world-spec
counterpart. `model_config = ConfigDict(frozen=True)` (no `extra="forbid"` here — schema.py's
top-level specs don't set `extra` at all, so `RegionSpec` currently accepts unknown kwargs
silently; this is pre-existing and out of this ticket's concern). Fields are the same
`id`/`type`/`bounds`/`terrain`/`hazard_level`/`hazard_kind`/`tags` shape as `RegionRecipeSpec`,
duplicated verbatim rather than shared — this is the established pattern across every
recipe/resolved pair in these two files (`PopulationRecipeSpec`/`PopulationSpec`,
`ResourceRecipeSpec`/`ResourceNodeSpec`, `BuildingRecipeSpec`/`BuildingSpec`): two independently
maintained classes, not one shared base, even for byte-identical fields like `hazard_kind`/`tags`.

**`WorldAssemblyResolver.resolve_module_contribution()`** (`src/worldassembly/resolver.py:755-929`,
region-construction block at :784-800) — the exact current kwargs list forwarded into the
`RegionSpec(...)` construction at :792-800:
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
All kwargs are fully explicit — no `**kwargs`/passthrough. `hazard_kind` uses `getattr(reg, ...,
default)`, `tags` uses `list(getattr(reg, ..., []))`; the two most recently added fields use two
slightly different idioms, both are safe patterns to replicate for a new field.

**Second `RegionSpec(...)` construction site** — confirmed at `src/worldassembly/resolver.py:95-101`
(read in full), inside `WorldAssemblyValidator.validate()`'s per-module `dummy_spec` builder
(`ValidationContext.MODULE`). This site forwards only `id, type, bounds=r.grid_bounds, terrain,
hazard_level, tags` — **it already omits `hazard_kind` today** (confirmed by direct read; matches
`TCK-20260701-HAZARD-KIND-RESOLVER-GAP`'s own Implementation Notes, which explicitly left this site
untouched and unaffected). This independently corroborates the current ticket's Out-of-Scope claim:
the omission pattern for a schema-only, not-yet-consumed field at this site is precedented, feeds
only a throwaway validation `WorldSpec` (never the resolved output real content depends on), and a
missing `terrain_variants` here would at most cause `ValidationContext.MODULE` structural checks to
see the region as flat-terrain (today's exact behavior) — no error, no blast radius. **Verified
correct, not merely trusted.**

**`WorldModuleAuthoringNormalizer.normalize()`** (`src/worldmodules/normalizer.py:130-157`) — for
regions specifically, does `regions=list(spec.regions)` (line 144), a pure passthrough of the
already-typed `RegionRecipeSpec` pydantic objects (`WorldModuleSpec.regions: List[RegionRecipeSpec]`,
`src/worldmodules/schema.py:68`). **No normalizer change is needed** — once the field exists on
`RegionRecipeSpec`, it survives `normalize()` automatically as part of the object, the same way
`hazard_kind`/`tags` do today. Confirmed by direct read of the full file; this module has no
per-field logic for `regions` at all (unlike `resources`/`buildings`/`services`, which go through
`normalize_count_map()`).

**`WorldCompiler`** (`src/worldbuilding/compiler.py`) — confirmed genuinely untouched by this
ticket's scope. The region-painting loop (:202-219) reads `r_terrain = getattr(r_spec, "terrain",
"GRASS")` and flat-fills the bounding box; it has no knowledge of any variants field and none is
being added here. `grep terrain src/worldbuilding/compiler.py` shows only this single-terrain
flat-fill path — no other `terrain`-adjacent logic.

**Naming precedent check** — `grep -rn "TerrainVariant" src/ tests/ docs/` returns only the epic's
own planning doc (`docs/plans/world_generation_organic_terrain_epic.md:170`, the source of the
`terrain_variants: list[TerrainVariantSpec]` suggestion). No collision anywhere in source or tests.
`terrain_variants` is likewise unused as a field name anywhere. Both names are safe to adopt.

**Cross-file model-sharing precedent** — `QuestDefinition` (defined once in
`src/worldbuilding/schema.py:188-212`) is imported directly into `src/worldmodules/schema.py:13`
(`from src.worldbuilding.schema import QuestDefinition`) and reused unchanged as
`WorldModuleSpec.quest_definitions: List[QuestDefinition]` — the authoring-layer and resolved-layer
specs share the *same* class for this field, with `normalizer.py` doing a pure
`quest_definitions=tuple(spec.quest_definitions)` passthrough, no per-item transformation. This is
architecturally the closest existing precedent to `terrain_variants`, which is likewise intended to
be inert and identical in shape at both authoring and resolved time (unlike e.g. `count` fields,
which differ in type between recipe (`Union[int, str]` template) and resolved (`int`) forms and
therefore *must* be independently defined). **Recommendation for the planner:** define
`TerrainVariantSpec` once in `src/worldbuilding/schema.py` and import it into
`src/worldbuilding/recipe.py` (`from src.worldbuilding.schema import TerrainVariantSpec`), mirroring
the `QuestDefinition` pattern exactly, rather than duplicating the class definition the way scalar
fields like `hazard_kind` are duplicated. Confirmed safe: `schema.py` currently has zero imports
from `recipe.py` (checked both files' import blocks directly), so `recipe.py -> schema.py` is a new,
one-directional dependency with no cycle risk — and `worldmodules/schema.py` already imports from
both files together today (`from src.worldbuilding.recipe import (...)` at line 7 and `from
src.worldbuilding.schema import QuestDefinition` at line 13), so this import shape is already
exercised in the same module family. If the planner instead prefers strict mirroring of the
scalar-duplication convention (two independent `TerrainVariantSpec` classes), that is a defensible
alternative but carries drift risk this ticket's own field does not need to accept, since nothing
about `terrain_variants` differs between authoring-time and resolved-time.

**Proposed minimal `TerrainVariantSpec` shape** (inert data container only — no compiler-consumption
semantics designed here, per ticket's explicit Out of Scope):
```python
class TerrainVariantSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    terrain: str = Field(..., min_length=1, description="Terrain type for this variant fill option")
    weight: float = Field(1.0, gt=0.0, description="Relative sampling weight; consumed by the noise-fill compiler logic added in a later ticket (TCK-20260821-COMPILER-NOISE-FILL) — unused/inert here")
```
Two fields is the minimum that is simultaneously (a) a valid, useful data point for the next
ticket's noise-thresholding logic and (b) fully inert — no validation here depends on any other
region state, no cross-field logic, `extra="forbid"` matches the file's existing convention for
every other model in both `recipe.py` and `schema.py`. `weight` defaulting to `1.0` (not `None`)
keeps a declared-but-degenerate single-variant entry meaningful without introducing an
undefined/zero case. The compiler ticket may find it needs a `threshold` instead of/in addition to
`weight`, or additional fields (e.g. `min_size`) — this is explicitly the next ticket's design
call, not settled here; the model is deliberately minimal so it doesn't overcommit an unconsumed
design.

**Field on `RegionRecipeSpec`/`RegionSpec`** — recommend `terrain_variants: Optional[List[TerrainVariantSpec]]
= Field(None, description="...")`, using `List` from `typing` (not lowercase `list[...]`) to match
both files' existing import convention (`from typing import ... List ...`, used for every other
list-typed field in both files) — this is a deliberate correction of the ticket body's own
suggested `list[TerrainVariantSpec]` wording, which doesn't match either file's style.

## Mechanics / Engine Constraints

No Mechanics Bible chapter or engine contract currently governs "terrain variant declaration" as a
law, because no behavior exists yet — the field is inert by explicit ticket design. The nearest
chapter is `docs/mechanics/06_worldbuilding_foundation.md` (Declarative topology / worldbuilding
foundation), which mentions "Terrain, Biomes, & Ecologies" only as a one-line heading (line 151,
confirmed by direct read) with no field-level formula or law to violate. Nothing in this ticket's
scope conflicts with any authoritative law: `WorldCompiler` (the only place a law about terrain
*fill* could live) is untouched, and `RegionRecipeSpec`/`RegionSpec` remain `frozen=True` (durable
state / immutability law, `docs/core/state.md`) — the new field does not weaken that.

## Docs Requiring Update

- `docs/parity_ledger/substrate.yaml`: add a new entry (new ID, e.g. `SUBSTRATE-NEW-0XX` — next
  available number to be picked at implementation time) documenting the schema-only addition of
  `terrain_variants` on `RegionRecipeSpec`/`RegionSpec`, `status: missing` (no consuming logic
  exists yet — nothing to mark `verified` against), explicitly noting `WorldCompiler` is untouched
  and pointing forward to `TCK-20260821-COMPILER-NOISE-FILL` for the entry that will flip this to
  `verified`. This mirrors the precedent at `docs/parity_ledger/infrastructure.yaml` (~line 9152,
  entry immediately preceding INFRA-342) for a prior schema-only ticket in the same batch style
  (`support_boundary` note: "no `src/` read/write logic against the new table exists yet
  (schema-only, by this ticket's own explicit Out of Scope)") — same shape of claim, different
  subsystem file. This is a judgment call: `TCK-20260701-HAZARD-KIND-RESOLVER-GAP` (the ticket this
  one explicitly cites as its plumbing-gap precedent) added *no* parity entry, but that was
  data-plumbing for an *already-verified* law (`hazard_kind` mechanics were already `verified`
  elsewhere before that hotfix); this ticket introduces a field with no existing law behind it at
  all, which is closer to the INFRA-341 "genuinely new, not-yet-wired schema" shape than to the
  HAZARD-KIND "existing law, missing plumbing" shape.

No Mechanics Bible chapter update is needed now — there is no behavior to document (field is inert
by design), and documenting an unconsumed field's semantics prematurely risks the doc drifting from
whatever `TCK-20260821-COMPILER-NOISE-FILL` actually implements. That ticket, not this one, should
own the `docs/mechanics/06_worldbuilding_foundation.md` update once real noise-fill behavior exists
to describe accurately. Flagging this explicitly as a deliberate deferral, not an oversight.

## Parity Ledger Overlap

No existing parity ledger entry currently covers `RegionRecipeSpec.terrain_variants` /
`RegionSpec.terrain_variants` (searched `docs/parity_ledger/substrate.yaml` for
`terrain|RegionSpec|RegionRecipeSpec`: only hits are `test_all_terrains_have_names` /
`test_all_terrains_have_race_labels` — unrelated content-catalog checks — and the `tags`-forwarding
entry, `SUBSTRATE-NEW-007`'s neighbor, which documents the `RegionSpec.tags`/`RegionRecipeSpec.tags`
forwarding pattern this ticket's `terrain_variants` forwarding directly mirrors). No P0 entries are
touched by this ticket. See "Docs Requiring Update" above for the new entry this ticket should add.

## Prior Work

`TCK-20260701-HAZARD-KIND-RESOLVER-GAP` (`tickets/done/TCK-20260701-HAZARD-KIND-RESOLVER-GAP.md`,
read in full) is the direct precedent this ticket is explicitly modeled on. Its fix shape:
1. Added `hazard_kind: Optional[str] = Field("PHYSICAL", description="...")` to `RegionRecipeSpec`,
   copied verbatim from `RegionSpec`.
2. Added `hazard_kind=getattr(reg, "hazard_kind", "PHYSICAL")` to the resolver's `RegionSpec(...)`
   construction, immediately after the `hazard_level=reg.hazard_level` line.
3. Added `test_hazard_kind_survives_module_pipeline` to
   `tests/integration/worldassembly/test_real_content_world_modules.py`, which is now the
   `test_plan.md`-mandated template for this ticket's own new test.
4. Left the `ValidationContext.MODULE` `dummy_spec` builder (resolver.py ~line 95-101) untouched,
   explicitly noting it's out of scope and low-blast-radius — this ticket's own Out of Scope item 3
   independently re-derives and confirms the same conclusion for `terrain_variants`.
5. Added a process-guard note to `docs/testing/test_taxonomy.md` (Section 1, lines 56-68, read in
   full) that already generically covers *this exact ticket's own situation* ("adding a new content
   field to a `worldspec.v1` schema... must also be added to the corresponding `worldcomposition.v1`
   recipe schema... and forwarded in `resolve_module_contribution()`"). **No update needed to this
   doc for the current ticket** — it already documents the pattern generically and cites
   `test_hazard_kind_survives_module_pipeline` as the template by name, which is exactly what this
   ticket is asked to mirror.

`test_id_collision_prevention` and `test_resolved_bundle_includes_compile_context_and_preserves_profiles`
(`tests/unit/worldassembly/test_assembly.py:352-473`) establish the pattern for constructing a
synthetic `WorldModuleSpec` directly in Python (not via a real YAML file) with a `RegionRecipeSpec`
using the real catalog-registered region id `"hometown"` (confirmed present in
`data/content/world/runtime_regions.yaml:2`, and confirmed via `CatalogRepository.get_region()`
that it will resolve without a `ResolverError`). This is the pattern the new "declared-value" test
should use, since no real module YAML may be modified to author `terrain_variants` (that's
`TCK-20260821-WOLF-DEN-NOISE-MIGRATION`'s explicit job, out of scope here).

## Risks and Open Questions

- **Where `TerrainVariantSpec` is defined (shared vs. duplicated)** — flagged above with a concrete
  recommendation (define once in `schema.py`, import into `recipe.py`, mirroring `QuestDefinition`)
  and a clear architectural rationale. Not fully "pre-decided" per the ticket's own Assumptions
  section, but this investigation narrows it to one clearly-precedented answer with one named
  alternative; the planner should pick one and state it explicitly rather than leaving it open.
- **Parity ledger entry ID** — the next available `SUBSTRATE-NEW-0XX` number in
  `docs/parity_ledger/substrate.yaml` should be confirmed at implementation time (this investigation
  did not exhaustively enumerate the full file to find the exact highest current number; a quick
  `grep -o 'SUBSTRATE-NEW-[0-9]*' docs/parity_ledger/substrate.yaml | sort -V | tail -1` at
  implementation time will settle it in seconds). Not a blocking unknown, just noting it wasn't
  pinned to an exact ID here.
- None of the above are blocking — both are narrow, mechanical decisions with a clearly-stated
  recommended default.

## Anti-Drift Hazards

- **The exact touch-point this ticket exists to prevent recurring**: adding the field to only one
  of `RegionRecipeSpec`/`RegionSpec`, or adding it to both schemas but forgetting the explicit
  forward in `resolve_module_contribution()`'s `RegionSpec(...)` kwargs — this is verbatim the
  `TCK-20260701-HAZARD-KIND-RESOLVER-GAP` failure mode. The new test must exercise the real
  YAML/synthetic-module -> `normalize()` -> `resolve_module_contribution()` pipeline, not just
  direct object construction, or it will not catch this class of gap (this is explicitly why the
  prior gap went undetected for as long as it did).
- **Do not touch `WorldCompiler`** — any consumption of `terrain_variants` (noise sampling,
  thresholding, per-tile painting) belongs to `TCK-20260821-COMPILER-NOISE-FILL`. Even a
  no-op-looking `getattr(r_spec, "terrain_variants", None)` read added to `compiler.py` in this
  ticket would be scope creep per the ticket's own explicit boundary.
- **Do not touch the `ValidationContext.MODULE` `dummy_spec` builder** (`resolver.py:90-105`) —
  confirmed correctly out of scope above; do not "fix" it opportunistically since it already omits
  `hazard_kind` too and this ticket's own Out of Scope explicitly names it.
- **Do not author `terrain_variants` into any real `data/content/world_modules/*.yaml` file** —
  that is `TCK-20260821-WOLF-DEN-NOISE-MIGRATION`'s job. The new "declared-value" test must use a
  synthetic, in-test `WorldModuleSpec`/`RegionRecipeSpec` construction (per the `test_assembly.py`
  precedent), not a real module fixture.
- **`extra="forbid"` must remain in place** on `RegionRecipeSpec` — do not weaken it while adding
  the field; this is the exact protection whose absence caused the original hotfix's blocking bug
  (before `hazard_kind` was added, `extra="forbid"` correctly rejected the unrecognized field —
  the bug was the missing field, not the forbid policy, which worked as designed).
