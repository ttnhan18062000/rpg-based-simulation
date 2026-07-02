# Investigation — TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE

## Current Behavior (file:line refs)

`data/worlds/sandbox_world/world.yaml` is `schema_version: worldtemplate.v1`:
- `topology`: 128×128 grid
- `regions`: `town_center` (`[10,10,40,40]`, GRASS, hazard 0.0), `woods` (`[50,50,110,110]`,
  FOREST, hazard 1.5)
- `factions`: `villagers` (civilian), `monsters` (hostile)
- `entities.populations`: 15 `citizen` (villagers, spawn_region town_center), 5 `monster`
  (monsters faction, region_random in woods), 3 `hero` (villagers, town_center) — 23 total
- `resources`: 10 wood in woods; `buildings`: 2 tavern in town_center; `quests: []`

Because this schema's compile path (`src/worldbuilding/cli.py`) always calls
`WorldCompiler.compile(spec, seed=seed, context=None)`, no entity ever gets catalog-resolved
stats — every entity, monster or citizen, gets flat `hp=100/atk=10/def=0`
(`src/worldbuilding/compiler.py:264-283`). This is the schema-level gap this migration fixes.

## Reference: worldcomposition.v1 pattern

`WorldCompositionSpec` (`src/worldassembly/schema.py:21-39`, `extra="forbid"`) accepts either
a `modules:` shorthand list of module IDs OR structured `module_refs:` (never both — enforced
by `normalize_modules_shorthand` validator). Minimal working example,
`data/worlds/highland_traverse/world.yaml` (14 lines):
```yaml
schema_version: "worldcomposition.v1"
world_id: "highland_traverse"
name: "Highland Traverse"
description: "..."
modules:
  - "mountain_pass"
  - "river_crossing"
  - "nomadic_herd"
  - "settled_quarter"
default_perspectives: [...]
generation_seed: 91
```
`default_perspectives`, `catalog_refs`, `pack_refs`, `provided_features` all default to empty
lists (optional). `generation_seed` defaults to 42 if omitted.

## Chosen module pair: `frontier_village_core` + `wolf_den_near_forest`

Read both module files in full (`data/content/world_modules/`):

- **`frontier_village_core`** (settlement): region `hometown`, `grid_bounds: [10,10,40,40]`
  — **identical bounds** to sandbox_world's current `town_center`. Population:
  `frontier_village_population` (town council/workers/guards — real catalog-driven roles,
  unlike the flat citizen/hero split in the old file). Factions: `town_council`,
  `merchant_league`.
- **`wolf_den_near_forest`** (ecology): `requires: ["frontier_village_core"]` — these two
  modules are already designed as a pair. Two regions: `near_forest` (hazard 1.0) and
  `wolf_den` (hazard 2.0, both higher than sandbox_world's old `woods` at 1.5). Population:
  `wolf_pack_small`. Faction: `wild_beast_pack`. Its own description: *"Animal ecology module
  proving contextual hostility instead of enemy-by-type"* — this is a strong signal that
  hostility/faction relationships in this module are handled contextually rather than by a
  blanket `EntityRole.MONSTER == always hostile` rule, which is directly relevant context for
  the sibling ticket `TCK-20260701-HAZARD-NATIVE-IMMUNITY` (worth checking there whether
  `wolf_pack_small` entities already survive `wolf_den`'s hazard 2.0, or share the same bug).

This is a solid match: reuses two modules already paired by `requires:`, preserves the
town+wilderness shape, and needs zero new module authoring.

## Region/faction naming will change (expected, not a defect)

Old: regions `town_center`/`woods`, factions `villagers`/`monsters`.
New: regions `hometown`/`near_forest`/`wolf_den`, factions `town_council`/`merchant_league`/
`wild_beast_pack`. Grepped `tests/` for any literal string dependency on the old names — found
none. `tests/unit/worldbuilding/test_quest_definition.py:222` references
`data/worlds/sandbox_world/world.yaml` generically (`quests: []`), not by region name.

## Mechanics/Engine Constraints

- `WorldCompiler.compile()` and `WorldAssemblyResolver` are unmodified by this ticket — pure
  content migration through existing mechanisms.
- Resolution produces `data/worlds/sandbox_world/resolved/world.resolved.yaml` +
  `provenance_manifest.json`/`assembly_report.json`/`validation_report.json`/
  `compile_report.json` per `docs/architecture/world_repository_layout.md` §2.

## Parity Ledger Overlap

No parity ledger entry references `sandbox_world`'s composition specifically (checked
`substrate.yaml`, `world_dynamics.yaml` — grep for `sandbox_world` and `worldtemplate` found
no hits). No parity update expected for this ticket.

## Prior Work

- `TCK-20260701-SANDBOX-MONSTER-BALANCE` (`stored_artifacts/`) — both rejected fix attempts;
  the `WorldCompiler.compile()` context-gap trace from attempt 1 is the direct motivation here.
- `TCK-20260630-WORLD-DEPLOY-MODULES` — precedent for compiling new worlds from existing
  unused modules (same category of work, different worlds).

## Risks and Open Questions

1. **Grade regression anchors WILL break.** `tests/simulation_quality/test_grade_regression.py`
   hard-anchors `sandbox_world_seed42_200t`, `seed137_200t`, `seed999_200t`, `seed42_1000t`
   against `tests/simulation_quality/fixtures/grade_anchors.json`. Migrating fundamentally
   changes entity composition/behavior, so these WILL need regeneration
   (documented procedure exists in that test file's docstring: re-run calibration via
   `tools/calibrate_simq.py`, update `grade_anchors.json`, re-run to confirm). **This must be
   in the Implement plan — it is not optional cleanup.**
2. Entity count will differ from 23 (old) — module-driven population counts are whatever
   `frontier_village_population` + `wolf_pack_small` resolve to. Confirmed acceptable per
   ticket Assumptions (approximate replication, not exact).
3. Whether `wolf_pack_small` entities currently survive `wolf_den`'s hazard_level 2.0 is
   unknown until compiled and run — flag for the sibling `HAZARD-NATIVE-IMMUNITY` ticket, do
   not investigate deeply here (out of scope for this ticket).

## Anti-Drift Hazards

- Do not hand-invent a new module when `frontier_village_core`/`wolf_den_near_forest` already
  fit and are already paired by `requires:`.
- Do not attempt to preserve old region/faction IDs (`town_center`, `woods`, `villagers`,
  `monsters`) — that would mean forking the modules instead of reusing them, defeating the
  point of the migration.
- Do not silently skip regenerating `grade_anchors.json` — a failing `test_grade_regression.py`
  after this change is expected and must be fixed as part of this ticket, not left broken.
