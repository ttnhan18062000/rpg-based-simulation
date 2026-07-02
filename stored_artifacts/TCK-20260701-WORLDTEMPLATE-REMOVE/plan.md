---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260701-WORLDTEMPLATE-REMOVE
artifact_type: plan
tags: [world, worldtemplate, schema, deprecation, cli, refactor]
---

# Plan — TCK-20260701-WORLDTEMPLATE-REMOVE

## `create-template` Decision: REPOINT (not remove)

**Decision: repoint `create-template` to scaffold a minimal `worldcomposition.v1` file.**

Rationale:
- `docs/guides/simulation.md`'s "World authoring" section (L31-54) documents `create-template`
  as step 1 of a four-step bootstrap workflow (`create-template` → `validate` → `compile` →
  `inspect`). There is no indication anywhere in the docs, tickets, or SEQUENCE.md that this
  guide is being restructured to drop the bootstrap step — it is the only documented way to
  start a brand-new world from scratch without hand-writing YAML from memory.
- The repointed change is genuinely small: `handle_create_template()`'s body only needs its
  `starter_yaml` dict (L397-461) replaced with a minimal, valid `WorldCompositionSpec`-shaped
  dict (`schema_version`, `world_id`, `name`, `description`, `module_refs: []`,
  `provided_features: []`, `generation_seed: 42`, `validation_profile: "local_dev"`) — using
  `data/worlds/simq_routing_test/world.yaml` as the structural reference the ticket names.
  Everything else in the function (safe-naming check, existing-file guard, `repo.rebuild_index()`
  call, success/error printing) is schema-agnostic and unchanged.
- `provided_features` is confirmed valid on `WorldCompositionSpec` itself (top-level field,
  `src/worldassembly/schema.py:35`) — unlike the trap on `WorldModuleSpec` where it's invalid.
  No schema mismatch risk in the scaffold content.
- An empty `module_refs: []` composition is intentionally a stub — the user is expected to
  populate `module_refs` with real module IDs from `content/world_modules/` afterward (same
  "bootstrap then hand-edit" spirit as the old template, just pointing at modules instead of
  inline recipes). `generate` (the `ProceduralCompositionGenerator`-backed subcommand) remains
  the separate, algorithmic path for producing a filled composition from existing modules —
  `create-template` and `generate` serve different purposes and both stay.
- Full removal would leave `docs/guides/simulation.md`'s documented workflow broken with no
  replacement, which fails the ticket's own preference rule ("prefer repointing ... unless
  investigation finds `docs/guides/simulation.md` is being restructured anyway" — it is not).

## Ordered Steps

### 1. `src/worldbuilding/cli.py`
1. **L16** — change import to `from src.worldbuilding.recipe import WorldTemplateSpec` → remove
   entirely (no longer needed anywhere in this file after steps below).
2. **L100-108** (`handle_validate`) — collapse the `if "worldtemplate" ... else` to a single
   unconditional `spec = repo.load_world(world_id)` (delete L102-106, keep L101's
   `schema_version = raw_data.get(...)` only if still used elsewhere in the function — check at
   implementation time; it is not otherwise used in `handle_validate`, so also delete L101 if
   confirmed unused).
3. **L246-254** (`handle_compile`) — delete the `if "worldtemplate" in schema_version:` block
   (L250-254), keep `is_composition = "worldcomposition" in schema_version` (L248) and the
   `elif is_composition or from_resolved:` / `else:` structure (L255-274) unchanged, just
   converting the leading `if` into a plain `if is_composition or from_resolved: ... else: ...`
   (no longer `elif`).
4. **L336-364** (`handle_inspect`) — delete `is_template = "worldtemplate" in schema_version`
   (L337) and the `if is_template: ... else:` (L339-364), keeping only the body of the former
   `else` branch (L352-364) unconditionally.
5. **L373-476** (`handle_create_template`) — keep function shell (naming/existence guards,
   `rebuild_index()`, print statements); replace `starter_yaml` dict (L397-461) with the minimal
   `worldcomposition.v1` scaffold described in the Decision section above.
6. **L551-554** — no change (subparser signature `template_name`, `world_id` is schema-agnostic,
   stays the same for the repointed command).
7. **L577-578** — no change (dispatch is schema-agnostic).

### 2. `src/worldbuilding/recipe.py`
1. Delete `WorldTemplateEntitiesSpec` (L81-84).
2. Delete `WorldTemplateSpec` (L87-107).
3. Delete `WorldTemplateExpander` (L110-260).
4. **Keep unchanged**: `RegionRecipeSpec` (L11-28), `PopulationRecipeSpec` (L31-47),
   `ResourceRecipeSpec` (L50-63), `BuildingRecipeSpec` (L66-78), and the module's imports
   (L7-8) — these remain load-bearing for `worldmodules`/`worldassembly`.

### 3. `src/worldbuilding/repository.py`
1. **L194-198** (`rebuild_index()`) — delete the `if "worldtemplate" in schema_ver:` branch
   (including its local `from src.worldbuilding.recipe import WorldTemplateSpec` import),
   convert the remaining `elif "worldcomposition" in schema_ver:` (L199) to `if`.

### 4. `src/worldbuilding/__init__.py`
1. **L24-31** — remove `WorldTemplateSpec,` and `WorldTemplateExpander` from the
   `from src.worldbuilding.recipe import (...)` block; keep `RegionRecipeSpec`,
   `PopulationRecipeSpec`, `ResourceRecipeSpec`, `BuildingRecipeSpec`.
2. **L54-55** — remove `"WorldTemplateSpec",` and `"WorldTemplateExpander"` from `__all__`;
   keep the four Recipe class name strings above them.

### 5. `src/cli/entry.py`
1. **L211** — delete `from src.worldbuilding.recipe import WorldTemplateSpec,
   WorldTemplateExpander` (part of the local import block inside `_run_cli()`).
2. **L224-229** — collapse `if "worldtemplate" in schema_version: ... else: spec =
   repo.load_world(world_id)` to unconditional `spec = repo.load_world(world_id)`; the now-
   unused `schema_version = raw_data.get(...)` line (L224) and the `raw_data`/`yaml` load
   (L221-222) should be reviewed — `repo.load_world()` re-reads the YAML itself, so the local
   `raw_data` read in `_run_cli()` becomes dead code entirely once the branch is gone. Remove
   the now-unnecessary manual YAML read (L217-222) and `import yaml` (L212) if nothing else in
   `_run_cli()` uses `raw_data`/`yaml_path`/`yaml` after this change — confirm at
   implementation time by reading the full function body once more before deleting.

### 6. Docs
1. **`docs/architecture/world_repository_layout.md`**
   - L27-30: remove the `worldtemplate.v1` bullet; add a short removal note (date + ticket ID)
     in its place or as a trailing sentence; reword the `worldspec.v1` bullet to reflect its
     dual role (standalone authoring schema AND the compiler's canonical internal type that
     every resolved `worldcomposition.v1` output is tagged with) rather than calling it purely
     internal.
   - L46: drop `worldtemplate.v1` from the backwards-compatibility sentence, leaving
     `worldspec.v1`.
2. **`docs/guides/simulation.md`**
   - L35-37: keep the `create-template` example (repoint decision), update the comment if
     needed to reflect it now scaffolds a composition stub, not inline recipe content. Do NOT
     change the "Bootstrap a starter world template" wording more than necessary — the command
     name and workflow step stay the same.
   - Opportunistic (not required): fix the pre-existing arg-count bug (`my_world` → two args)
     while this line is already being touched.
3. **`docs/mechanics/06_worldbuilding_foundation.md`** — no change (confirmed zero references).
4. **`docs/guidelines/intentional_divergences.md`** — append new entry **`### 2.21 Worldtemplate.v1 Schema Removal`**
   directly after L176 (end of entry 2.20), before the L177 `---` separator, following the
   2.20 format: `Subsystem: World / Authoring`; `Old Behavior` (worldtemplate.v1 recipe
   expansion path existed as a second world-authoring schema alongside worldcomposition.v1,
   never resolved catalog stats); `New Behavior` (schema removed entirely — `WorldTemplateSpec`/
   `WorldTemplateExpander` deleted, CLI branches collapsed, `create-template` repointed to
   scaffold `worldcomposition.v1`); `Rationale: **Unified**` (single remaining consumer
   migrated by `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE`, stat-resolution gap was the root
   motivation, `worldcomposition.v1` already provides equal-or-better capability via module
   reuse); `Verification`: point at the updated `tests/cli/test_world_cli.py` and
   `tests/unit/worldbuilding/test_world_repository.py` regression tests from this ticket.

### 7. Tests (see `test_plan.md` for full detail)
1. Delete `tests/unit/worldbuilding/test_world_recipes.py`.
2. Rewrite `tests/cli/test_world_cli.py::test_cli_create_template_bootstraps_correctly`
   (L226-259) to assert `worldcomposition.v1` scaffold output; add
   `test_cli_create_template_rejects_existing_world`.
3. Add `rebuild_index()` composition/static regression coverage to
   `tests/unit/worldbuilding/test_world_repository.py`.
4. Run scoped pytest commands listed in `test_plan.md`.

## Scope Guards (do NOT touch)
- `src/worldbuilding/schema.py` — confirmed no `worldtemplate` content exists there; `WorldSpec`
  (`worldspec.v1`, L123-158) stays fully unchanged.
- `src/worldassembly/resolver.py` (`WorldAssemblyResolver`, `CompileProfileResolver`) — confirmed
  zero `worldtemplate` references; not touched.
- `src/worldbuilding/recipe.py`'s `RegionRecipeSpec`/`PopulationRecipeSpec`/`ResourceRecipeSpec`/
  `BuildingRecipeSpec` — shared with `worldmodules`/`worldassembly`, stay untouched; the file
  itself is edited, not deleted.
- Any `data/worlds/*` content — out of scope per ticket (that's `SANDBOX-WORLDCOMP-MIGRATE`,
  already done).
- Historical records: `tickets/working_log.csv`, `docs/parity_ledger/progression.yaml:1113-1119`,
  `docs/audits/D20_simq_integration.md`, `stored_artifacts/TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE/`,
  `tickets/done/TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE.md`, other in-progress tickets referencing
  worldtemplate.v1 historically (`TCK-20260701-SANDBOX-MONSTER-BALANCE`) — none edited.
- `reviews/test_export.py`, `reviews/src_export.py` — generated, pytest-excluded export dumps;
  not edited (regenerate naturally via `reviews/code_exporter.py` on next run, out of scope).
- `tickets/todos/worldtemplate-deprecation/SEQUENCE.md` and
  `TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC.md` — epic-tracking docs, updated at finalize
  time per standard workflow, not part of the implementation diff.

## Dependency Map
```
TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE (DONE, prerequisite satisfied)
        │
        ▼
src/worldbuilding/recipe.py (delete WorldTemplateSpec/Expander, keep shared Recipe classes)
        │
        ├──▶ src/worldbuilding/cli.py (5 call sites: import, validate, compile, inspect, create-template)
        ├──▶ src/worldbuilding/repository.py (rebuild_index() branch)
        ├──▶ src/worldbuilding/__init__.py (export list)
        └──▶ src/cli/entry.py (_run_cli() branch)
                │
                ▼
        docs/architecture/world_repository_layout.md, docs/guides/simulation.md,
        docs/guidelines/intentional_divergences.md (new entry 2.21)
                │
                ▼
        tests/unit/worldbuilding/test_world_recipes.py (delete),
        tests/cli/test_world_cli.py (rewrite one test, add one),
        tests/unit/worldbuilding/test_world_repository.py (add coverage)
```
No step in this chain touches `worldcomposition.v1` resolution logic or `worldspec.v1` — both
are read-only dependencies (imported types/behavior referenced, never modified).

## Acceptance Criteria Mapping
| Ticket Acceptance Criterion | Plan Step(s) |
|---|---|
| No code path in `src/worldbuilding/` branches on `worldtemplate.v1` | Steps 1, 2, 3, 4 |
| `create-template` produces a valid `worldcomposition.v1` file, or is removed with docs updated | Step 1.5 (repoint) + Step 6.2 |
| `worldspec.v1`/`WorldSpec` unchanged and passing all existing tests | Scope Guards (no edit); verified by scoped pytest run |
| All listed docs updated | Step 6 (1-4) |
| `docs/guidelines/intentional_divergences.md` has a new entry | Step 6.4 |
| Full scoped worldbuilding test suite passes | Step 7.4 / `test_plan.md` Scoped Pytest Commands |
| No dead imports or unused functions left behind | Steps 1.1, 2, 3, 4, 5 (explicit import/branch removal at each site, including the two sites — `repository.py`, `entry.py` — the ticket's own scope list omitted) |

## Unresolved Questions
None. Every item the ticket flagged as needing a decision (`create-template` repoint-vs-remove)
is resolved above with concrete rationale grounded in what was found in
`docs/guides/simulation.md`. The one genuinely new finding — that `src/worldbuilding/
repository.py`, `src/cli/entry.py`, and `src/worldbuilding/__init__.py` also branch on/export
`worldtemplate.v1` symbols and were omitted from the ticket's "Related Code Areas" — is not an
open question either; it's folded into the ordered steps above (Steps 3, 4, 5) since the
ticket's own acceptance criteria ("no dead imports or unused functions left behind") already
require it.
