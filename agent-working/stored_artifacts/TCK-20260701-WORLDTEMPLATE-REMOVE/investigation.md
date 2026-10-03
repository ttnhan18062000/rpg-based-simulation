---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260701-WORLDTEMPLATE-REMOVE
artifact_type: investigation
tags: [world, worldtemplate, schema, deprecation, cli, refactor]
---

# Investigation — TCK-20260701-WORLDTEMPLATE-REMOVE

## Prerequisite Verification
- `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` is in `tickets/done/` (confirmed).
- `grep schema_version data/worlds/sandbox_world/world.yaml` → `"worldcomposition.v1"` (confirmed migrated).
- Checked all 10 `data/worlds/*/` directories (`urban_political`, `highland_traverse`,
  `dungeon_crawl`, `simq_routing_test`, `frontier_extended`, `swamp_border_world`,
  `sandbox_world`, `frontier_living_world`, `wilderness_survival`, `generated_frontier_3_42`)
  — zero `world.yaml` files reference `worldtemplate.v1`. Prerequisite satisfied, safe to
  proceed.

## Current Behavior (exact file:line refs)

### `src/worldbuilding/cli.py`
The ticket's guessed line numbers were close but not exact; confirmed exact locations:

| Site | Lines | Behavior |
|---|---|---|
| Import | L16 | `from src.worldbuilding.recipe import WorldTemplateSpec, WorldTemplateExpander` |
| `handle_validate()` | L101-106 | `schema_version = raw_data.get("schema_version", "")` (L101); `if "worldtemplate" in schema_version:` (L102) → validates via `WorldTemplateSpec.model_validate` + `WorldTemplateExpander.expand(seed=42)`; else branch (L107-108) uses `repo.load_world(world_id)` |
| `handle_compile()` | L247-254 | `schema_version = raw_data.get(...)` (L247); `is_composition = "worldcomposition" in schema_version` (L248); `if "worldtemplate" in schema_version:` (L250) → expand via seed; `elif is_composition or from_resolved:` (L255); `else:` (L272) |
| `handle_inspect()` | L336-351 | `schema_version = raw_data.get(...)` (L336); `is_template = "worldtemplate" in schema_version` (L337); `if is_template:` (L339-351) prints template-shaped metrics; `else:` (L352-364) prints `WorldSpec`-shaped metrics |
| `handle_create_template()` | L373-476 | Full function. Writes `"schema_version": "worldtemplate.v1"` at L398, plus inline `regions`/`factions`/`entities`/`resources`/`buildings`/`quests` recipe content (L407-461) |
| subparser registration | L551-554 | `create-template` argparse subcommand: takes `template_name` and `world_id` positional args |
| dispatch | L577-578 | `elif args.command == "create-template": return handle_create_template(args)` |

None of these branches are dead — all execute today for any world whose `schema_version`
contains `"worldtemplate"`. Since the prerequisite is now satisfied (zero such worlds), they
are dead **in practice** but not dead **in code** — removal requires deleting the branch and
either simplifying to the remaining path or raising a clear "unsupported schema" error, per
ticket step 2.

### `src/worldbuilding/recipe.py` — `WorldTemplateExpander` / `WorldTemplateSpec`
Full file read (261 lines). Two groups of classes exist here, and **they are NOT uniformly
template-only** — this contradicts a implicit assumption in the ticket's scope wording:

**Template-only (safe to delete):**
- `WorldTemplateEntitiesSpec` (L81-84) — only referenced by `WorldTemplateSpec.entities`
- `WorldTemplateSpec` (L87-107) — the `worldtemplate.v1` root model (see Schema section below)
- `WorldTemplateExpander` (L110-260) — the recipe→`WorldSpec` expansion engine

**Shared with `worldcomposition.v1` / `worldmodule.v1` (must NOT be touched):**
- `RegionRecipeSpec` (L11-28), `PopulationRecipeSpec` (L31-47), `ResourceRecipeSpec` (L50-63),
  `BuildingRecipeSpec` (L66-78) — confirmed via repo-wide grep, these are imported and used by:
  - `src/worldmodules/schema.py:8-11,68-71` — `WorldModuleSpec.regions/population_recipes/
    resource_recipes/building_recipes` fields (the `worldmodule.v1` schema used by every
    `worldcomposition.v1` module)
  - `src/worldmodules/normalizer.py:6-9,29-32` — module normalization
  - `src/worldassembly/resolver.py:33,407` — `WorldAssemblyResolver` constructs
    `PopulationRecipeSpec` directly when merging module contributions
  - `tests/unit/worldassembly/test_archetype_preservation.py`,
    `tests/unit/worldassembly/test_assembly.py`,
    `tests/integration/worldassembly/test_real_content_world_compositions.py` — construct
    `RegionRecipeSpec`/`PopulationRecipeSpec` directly for composition-path tests

  **This is the single biggest risk in this ticket.** These four Recipe classes live in the
  same file as `WorldTemplateExpander` but are load-bearing for the `worldcomposition.v1`
  path (module authoring). Deleting the whole file, or deleting these classes alongside
  `WorldTemplateExpander`, would break `worldmodules`/`worldassembly` and violate the ticket's
  own "Out of Scope: `worldcomposition.v1` resolution logic ... unchanged" clause.

  **Conclusion:** `recipe.py` itself is NOT deleted. Only `WorldTemplateEntitiesSpec`,
  `WorldTemplateSpec`, and `WorldTemplateExpander` are removed from it; the four
  `*RecipeSpec` classes and the module docstring/imports they need remain.

### `src/worldbuilding/schema.py` — ticket's assumption is incorrect
The ticket says (Related Code Areas): *"locate the `worldtemplate.v1` validator/model
(distinct from `WorldSpec`) before removing"* and implies it might be in `schema.py`.
Confirmed by reading the full file and grepping `worldtemplate` (case-insensitive): **there is
no `worldtemplate.v1` model in `schema.py`.** The file's class list is: `InvalidWorldSpecError`,
`TopologySpec`, `RegionSpec`, `FactionSpec`, `PopulationSpec`, `ResourceNodeSpec`,
`BuildingSpec`, `BudgetSpec`, `ValidationSpec`, `QuestDefinition`, `WorldSpec` — none of which
reference `worldtemplate`. **The actual `worldtemplate.v1` validator is `WorldTemplateSpec` in
`src/worldbuilding/recipe.py:87-107`** (has its own `@model_validator` enforcing
`schema_version == "worldtemplate.v1"` at L103-107). No change to `schema.py` is needed —
`WorldSpec`/`worldspec.v1` is confirmed untouched and singular.

### Additional call sites NOT listed in the ticket's "Related Code Areas" (scope expansion required)
Repo-wide grep for `WorldTemplateExpander`/`WorldTemplateSpec` (excluding `reviews/`, which is
an excluded, non-collected export-dump directory per `pyproject.toml` `norecursedirs`) found
two more production call sites the ticket did not mention:

1. **`src/worldbuilding/repository.py:194-198`** (inside `WorldRepository.rebuild_index()`):
   ```python
   if "worldtemplate" in schema_ver:
       from src.worldbuilding.recipe import WorldTemplateSpec
       spec = WorldTemplateSpec.model_validate(raw_dict)
       status_str = "TEMPLATE"
   elif "worldcomposition" in schema_ver:
       ...
   ```
   This branch determines the `status` field written to `world_index.json` for `list`/index
   rebuilding. Needs the same treatment as the `cli.py` branches.

2. **`src/cli/entry.py:211,224-229`** (inside `_run_cli()`, the actual V2 simulation entry
   point used by `python3 -m src.cli.entry` / `docs/guides/simulation.md`'s "Running a
   simulation" section):
   ```python
   from src.worldbuilding.recipe import WorldTemplateSpec, WorldTemplateExpander
   ...
   schema_version = raw_data.get("schema_version", "")
   if "worldtemplate" in schema_version:
       template = WorldTemplateSpec.model_validate(raw_data)
       spec = WorldTemplateExpander.expand(template, seed=seed)
   else:
       spec = repo.load_world(world_id)
   ```
   This must be simplified in this ticket too — it is a live worldtemplate.v1 branch in the
   main simulation entrypoint, not just the worldbuilding CLI tool. Missing this would leave a
   dead import and an unreachable-but-present branch, violating acceptance criterion "No code
   path in `src/worldbuilding/` branches on `worldtemplate.v1`" in spirit (the branch is in
   `src/cli/`, referencing `src/worldbuilding/recipe`, so it's in scope for "no dead imports or
   unused functions left behind").

3. **`src/worldbuilding/__init__.py:24-31,54-55`** — package `__init__.py` exports
   `WorldTemplateSpec`/`WorldTemplateExpander` alongside the four shared `*RecipeSpec` classes.
   Only the two template-specific names need removing from the import block and `__all__`.

## Mechanics/Engine Constraints
- `docs/mechanics/06_worldbuilding_foundation.md` — grepped case-insensitively for
  `worldtemplate`, **zero hits**. No mechanics doc change required for this ticket (ticket step
  6 correctly says "may have none").
- `docs/architecture/world_repository_layout.md` (full file read, 47 lines) — an ADR-style doc.
  Three spots reference `worldtemplate.v1`:
  - L27-30: schema list — `worldspec.v1` (legacy direct spec), `worldtemplate.v1` (legacy
    template requiring expansion), `worldcomposition.v1` (module-based). The `worldtemplate.v1`
    bullet must be removed/marked-removed, and `worldspec.v1`'s description clarified per
    ticket step 6 ("clarify `worldspec.v1`'s role as internal-only" — note: `worldspec.v1` is
    NOT purely internal-only today; three worlds — `urban_political`, `highland_traverse`,
    `dungeon_crawl`, `frontier_extended`, `swamp_border_world`, `frontier_living_world`,
    `wilderness_survival`, `generated_frontier_3_42` — need checking for whether they're
    `worldspec.v1` directly-authored or `worldcomposition.v1`; either way `worldspec.v1` is
    both a valid standalone authoring schema AND the compiler's canonical internal type per the
    ticket's own Request Summary — the doc edit should clarify this dual role, not claim it's
    purely internal).
  - L46: "All existing tools, scripts, and tests that load `worldspec.v1` and `worldtemplate.v1`
    ... must remain fully supported" — this backwards-compatibility sentence is now stale and
    must be updated to drop the `worldtemplate.v1` guarantee.
- `docs/guides/simulation.md` L35-37 (read full "World authoring" section, L31-54): the
  bootstrap example is a 2-line bash comment + command:
  ```bash
  # Bootstrap a starter world template
  python3 -m src.worldbuilding.cli create-template my_world
  ```
  Note: this example already only passes ONE positional arg (`my_world`), but the actual CLI
  signature requires TWO (`template_name`, `world_id` — L553-554 of `cli.py`). This is a
  **pre-existing doc bug unrelated to this ticket** (predates worldtemplate removal); worth
  fixing opportunistically while touching this line since we're already editing the same
  example, but not a hard requirement.
- Engine contracts (`docs/engine/*`) — no `worldtemplate` references found; the kernel/
  authoritative-pipeline docs operate purely on compiled `WorldState`, downstream of any
  worldtemplate/worldcomposition distinction. No changes needed there.

## Parity Ledger Overlap
- `docs/parity_ledger/progression.yaml:1113-1119` mentions `worldtemplate.v1` in evidence text
  for `PROG-108`, but it's already phrased in past tense ("previously seeded ... but no longer
  does — migrated to worldcomposition.v1 ... by TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE"). This
  was corrected by the prerequisite ticket already. **No further edit needed** — the evidence
  is historically accurate and doesn't claim worldtemplate.v1 is still live.
- No `parity_ledger/*.yaml` entry represents the `worldtemplate.v1` *mechanism* itself (it was
  never a "law" tracked for bit-parity, just a CLI/authoring convenience) — confirmed no
  P0/P1 ledger entry needs a status flip for this removal.

## Prior Work
- `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` (done): migrated the last worldtemplate.v1 world
  (`sandbox_world`) to `worldcomposition.v1`, satisfying this ticket's hard prerequisite.
- `docs/audits/D20_simq_integration.md` "Migration Baseline — worldtemplate.v1 →
  worldcomposition.v1 (2026-07-01)" section documents that migration's outcome — historical
  record, not touched by this ticket.
- `docs/guidelines/intentional_divergences.md` entry `### 2.20 Native Habitat Hazard Exemption`
  (L152-175) is the most recent entry and gives the formatting template to follow:
  `Subsystem` / `Old Behavior` / `New Behavior` / `Rationale` (bold rationale class) /
  (`Known Limitation` optional) / `Verification` (test path). Entry numbering in this file is
  **out of insertion order** (2.19 appears physically before 2.18, then 2.20) — the new entry
  should simply be appended as `### 2.21` directly after 2.20 (L176), before the `---`
  separator (L177) that starts "## 3. Unsupported / Retired Behavior".

## Risks and Open Questions
1. **Scope expansion beyond ticket's listed code areas** — `src/worldbuilding/repository.py`,
   `src/cli/entry.py`, and `src/worldbuilding/__init__.py` all branch on/export
   `worldtemplate.v1` symbols and were not listed in the ticket's "Related Code Areas". These
   must be included in the plan to satisfy the ticket's own acceptance criterion ("No dead
   imports or unused functions left behind from the removed template-expansion code") — not a
   genuinely open question, just a correction to the ticket's scope list, resolved by the plan.
2. **`recipe.py` is a shared file, not a template-only file** — the ticket's step 4 wording
   ("Remove or simplify `WorldTemplateExpander` ... if any part is shared with
   `worldcomposition.v1` resolution, only remove the template-specific parts") already
   anticipates this correctly. Confirmed: only `WorldTemplateEntitiesSpec`, `WorldTemplateSpec`,
   `WorldTemplateExpander` are removed; `RegionRecipeSpec`/`PopulationRecipeSpec`/
   `ResourceRecipeSpec`/`BuildingRecipeSpec` and the file itself remain.
3. **`create-template` decision** — resolved in `plan.md` (repoint, not remove). See plan for
   rationale.
4. **Pre-existing doc bug** in `docs/guides/simulation.md` L37 (`create-template` example
   passes 1 arg, needs 2) — opportunistic fix, not a hard requirement, called out so it isn't
   silently "fixed" as if it were in original scope (traceability).

## Anti-Drift Hazards
- Do NOT delete `src/worldbuilding/recipe.py` wholesale — it hosts shared Recipe classes used
  by the `worldcomposition.v1`/`worldmodule.v1` path (`WorldAssemblyResolver`,
  `WorldModuleSpec`, `WorldCompositionNormalizer`'s dependency chain).
  `tests/unit/worldassembly/test_assembly.py`, `test_archetype_preservation.py`, and
  `tests/integration/worldassembly/test_real_content_world_compositions.py` all import
  `RegionRecipeSpec`/`PopulationRecipeSpec` directly from `src.worldbuilding.recipe` — these
  imports must keep working unchanged.
- Do NOT touch `WorldSpec`/`worldspec.v1` in `schema.py:123-158` — confirmed no worldtemplate
  logic lives there; nothing to remove from that class.
- Do NOT touch `WorldAssemblyResolver` (`src/worldassembly/resolver.py`) or
  `CompileProfileResolver` — confirmed neither references `worldtemplate` at all (grep clean).
- Do NOT edit `tickets/working_log.csv` history, `docs/parity_ledger/progression.yaml:1113-1119`
  evidence text, `docs/audits/D20_simq_integration.md`, or any `stored_artifacts/`/
  `tickets/done/` content that mentions `worldtemplate.v1` in a historical/already-migrated
  context — these are accurate historical records, not live code paths.
- Do NOT touch `reviews/test_export.py` or `reviews/src_export.py` — these are generated,
  pytest-excluded (`norecursedirs` in `pyproject.toml`) code-export dumps regenerated by
  `reviews/code_exporter.py`; they will pick up the change automatically on next export run.
- Do NOT touch `tickets/todos/worldtemplate-deprecation/TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC.md`
  or `SEQUENCE.md` during implementation — those are epic-tracking docs updated at ticket
  completion per the standard workflow (finalize phase), not part of the implementation diff.
