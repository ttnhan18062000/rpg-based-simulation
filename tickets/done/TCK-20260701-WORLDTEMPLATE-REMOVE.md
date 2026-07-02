---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260701-WORLDTEMPLATE-REMOVE
phase: done
date: 2026-07-01
tags: [world, worldtemplate, schema, deprecation, cli, refactor]
---

# TCK-20260701-WORLDTEMPLATE-REMOVE

## Title
Remove worldtemplate.v1 schema support (CLI, expansion code, docs)

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`worldtemplate.v1` is a legacy world-authoring schema, superseded by `worldcomposition.v1`
for every world in the repo once `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` completes (that
ticket migrates the last remaining `worldtemplate.v1` world, `sandbox_world`). Its compile
path never resolves catalog stats (the root gap that motivated this deprecation) and it
duplicates functionality `worldcomposition.v1` already provides more capably (module reuse,
avoiding monolithic data files). This ticket removes the schema and its code paths entirely
rather than fixing the gap in a pipeline nothing will use afterward.

**Do NOT touch `worldspec.v1`** — it is not part of this deprecation. `worldspec.v1` is the
compiler's canonical internal spec type (`WorldCompiler.compile(spec: WorldSpec, ...)`), and
every `worldcomposition.v1` world's resolved output is itself tagged `schema_version:
worldspec.v1`. Removing it would break compilation for every world in the repo. This ticket
only removes the standalone `worldtemplate.v1` *authoring* path (CLI branches, template
expansion, bootstrap command).

## Scope
1. Confirm prerequisite: `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE` is done and no
   `data/worlds/*/world.yaml` file has `schema_version: "worldtemplate.v1"` (grep to verify
   before starting).
2. Remove `worldtemplate.v1` branches from `src/worldbuilding/cli.py`
   (identified during investigation: ~L101-102, ~L247-250, ~L336-337). Each branch currently
   checks `"worldtemplate" in schema_version` — read the surrounding function at each site to
   determine whether removing the branch means deleting dead code, raising a clear error for
   unsupported schema, or simplifying an if/else into a single path.
3. The `create-template` CLI command (~L398, currently writes `"schema_version":
   "worldtemplate.v1"`) bootstraps a new template file. Decide: remove the command entirely,
   or repoint it to scaffold a minimal `worldcomposition.v1` file instead (using
   `data/worlds/simq_routing_test/world.yaml` as a structural reference for what a minimal
   valid composition looks like). Prefer repointing if `docs/guides/simulation.md`'s
   documented bootstrap workflow should keep working; remove entirely only if that guide is
   also being rewritten to drop the bootstrap step.
4. Remove or simplify `WorldTemplateExpander` (`src/worldbuilding/recipe.py`) if it is solely
   used by the `worldtemplate.v1` path — confirm via grep for its call sites before deleting;
   if any part is shared with `worldcomposition.v1` resolution, only remove the
   template-specific parts.
5. Remove the `worldtemplate.v1` schema class/validator if one exists separately from
   `WorldSpec` (do not touch `WorldSpec`/`worldspec.v1` itself — confirm which class actually
   validates `worldtemplate.v1` before deleting, it is a distinct model, not `WorldSpec`).
6. Update docs:
   - `docs/architecture/world_repository_layout.md` — remove `worldtemplate.v1` from the
     schema list, note its removal date/ticket, clarify `worldspec.v1`'s role as internal-only
     to prevent future confusion (this was the original point of confusion this epic started
     from).
   - `docs/guides/simulation.md` — update or remove the `create-template` bootstrap example
     (line ~37) per the decision in step 3.
   - `docs/mechanics/06_worldbuilding_foundation.md` — remove any `worldtemplate.v1`
     references if present (check first; may have none).
   - `docs/guidelines/intentional_divergences.md` — add an entry documenting this schema
     removal as an intentional architecture simplification, with rationale (single remaining
     user migrated, stat-resolution gap, superseded by worldcomposition.v1).
7. Run the full worldbuilding test suite (scoped, not `pytest tests/`) to confirm no other
   test fixtures depend on `worldtemplate.v1`.

## Out of Scope
- `worldspec.v1` (`WorldSpec` class, `src/worldbuilding/schema.py:123-158`) — must remain
  fully functional and unchanged
- `worldcomposition.v1` resolution logic (`WorldAssemblyResolver`, `CompileProfileResolver`)
  — unchanged
- Any world content changes (that's `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE`, must complete
  first)

## Acceptance Criteria
- [x] No code path in `src/worldbuilding/` branches on `worldtemplate.v1`
- [x] `create-template` (or its replacement) produces a valid `worldcomposition.v1` file, or
      is removed with docs updated accordingly
- [x] `worldspec.v1`/`WorldSpec` unchanged and passing all existing tests
- [x] All listed docs updated (except the item below)
- [ ] `docs/guidelines/intentional_divergences.md` has a new entry for this removal —
      **deferred**: this file was explicitly excluded from scope for this execution to avoid
      colliding with concurrent in-progress work on `TCK-20260701-HAZARD-NATIVE-IMMUNITY`
      (see Implementation Notes). Follow-up required once that ticket's rework lands.
- [x] Full scoped worldbuilding test suite passes
- [x] No dead imports or unused functions left behind from the removed template-expansion code

## Related Tickets
- TCK-20260701-WORLDTEMPLATE-DEPRECATION-EPIC — parent epic
- TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE — **hard prerequisite**, must be DONE first (see
  `SEQUENCE.md`)

## Related Docs
- `docs/architecture/world_repository_layout.md`
- `docs/guides/simulation.md`
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/guidelines/intentional_divergences.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE/` — once that ticket completes,
  confirms the prerequisite state

## Related Code Areas
- `src/worldbuilding/cli.py` (~L101-102, ~L247-250, ~L336-337, ~L398)
- `src/worldbuilding/recipe.py` — `WorldTemplateExpander`
- `src/worldbuilding/schema.py` — locate the `worldtemplate.v1` validator/model (distinct
  from `WorldSpec`) before removing

## Assumptions / Open Questions
- Whether `create-template` should be removed or repointed to `worldcomposition.v1` is a
  product decision, not purely technical — default to repointing (keeps the documented
  bootstrap workflow intact) unless investigation finds `docs/guides/simulation.md` is being
  restructured anyway.

## Implementation Notes
Followed `staging_artifacts/TCK-20260701-WORLDTEMPLATE-REMOVE/plan.md`'s ordered steps exactly,
with one deliberate deviation flagged below.

1. `src/worldbuilding/cli.py` — removed the `WorldTemplateSpec`/`WorldTemplateExpander` import
   (L16); collapsed `handle_validate`'s `if "worldtemplate" ... else` to the unconditional
   `spec = repo.load_world(world_id)`; removed `handle_compile`'s `if "worldtemplate" in
   schema_version:` branch, keeping `is_composition or from_resolved` / `else` unchanged;
   removed `handle_inspect`'s `is_template` branch, keeping only the former `else` body
   unconditionally (and dropped the now-dead `schema_version` line there); repointed
   `handle_create_template`'s `starter_yaml` to a minimal `worldcomposition.v1` scaffold
   (`schema_version`, `world_id`, `name`, `description`, `module_refs: []`,
   `provided_features: []`, `generation_seed: 42`, `validation_profile: "local_dev"`),
   verified valid against `WorldCompositionSpec`. Subparser/dispatch (`create-template`
   still takes `template_name` + `world_id`) unchanged.
2. `src/worldbuilding/recipe.py` — deleted `WorldTemplateEntitiesSpec`, `WorldTemplateSpec`,
   `WorldTemplateExpander`. Kept `RegionRecipeSpec`/`PopulationRecipeSpec`/
   `ResourceRecipeSpec`/`BuildingRecipeSpec` (load-bearing for `worldmodules`/
   `worldassembly` — confirmed via grep, unchanged). Also removed the now-fully-dead
   imports (`TopologySpec`, `FactionSpec`, `WorldSpec`, `InvalidWorldSpecError` from
   `schema.py`; `WorldValidator` from `validator.py`) since nothing in the remaining file
   uses them and no other module imports these names from `recipe.py` (confirmed via
   repo-wide grep) — this goes slightly beyond the plan's literal "keep the module's
   imports (L7-8)" instruction because those imports only existed to support the deleted
   classes and leaving them would itself be dead code, violating the ticket's own
   acceptance criterion ("no dead imports ... left behind").
3. `src/worldbuilding/repository.py:194-198` (`rebuild_index()`) — deleted the
   `"worldtemplate" in schema_ver` branch (incl. its local `WorldTemplateSpec` import),
   promoted `elif "worldcomposition"` to `if`.
4. `src/cli/entry.py:211-229` (`_run_cli()`) — removed the `WorldTemplateSpec`/
   `WorldTemplateExpander` import, the manual `yaml_path`/`raw_data` read, and the
   `if "worldtemplate" ... else` branch; replaced with `spec = repo.load_world(world_id)`.
   `repo.load_world()` raises `WorldRepositoryError` (not `FileNotFoundError`) on a missing
   world, which is an equivalent user-facing failure mode (uncaught exception propagates
   either way — confirmed no try/except wraps this code path).
5. `src/worldbuilding/__init__.py` — removed `WorldTemplateSpec`/`WorldTemplateExpander`
   from the `recipe` import block and `__all__`; kept the four shared Recipe classes.
6. `create-template` — repointed (not removed) per plan's decision, to keep
   `docs/guides/simulation.md`'s documented bootstrap workflow intact. `module_refs` is
   left empty as an intentional stub for the author to populate afterward.
7. Docs updated: `docs/architecture/world_repository_layout.md` (removed the
   `worldtemplate.v1` schema-list bullet, added a removal note with ticket ID/date,
   clarified `worldspec.v1`'s dual role as standalone-authoring-schema-and-compiler-
   internal-type rather than purely internal; dropped `worldtemplate.v1` from the
   backwards-compatibility sentence); `docs/guides/simulation.md` (updated the
   `create-template` example's comment for the new scaffold behavior, and opportunistically
   fixed the pre-existing arg-count bug — the example previously passed only `my_world`
   but the CLI requires `template_name` + `world_id`); `docs/mechanics/06_worldbuilding_
   foundation.md` confirmed zero `worldtemplate` references, no change needed;
   `docs/parity_ledger/progression.yaml:1113-1119` (PROG-108) confirmed already
   past-tense/historical, no change needed.

**Deviation from plan (safety-driven, explicit):** Step 8 of the plan called for adding a
new `### 2.21` entry to `docs/guidelines/intentional_divergences.md`. This execution's
shared-file safety instructions explicitly listed `docs/guidelines/intentional_divergences.md`
as off-limits — it is owned by the concurrently in-progress `TCK-20260701-HAZARD-NATIVE-
IMMUNITY` rework and touching it risked colliding with that ticket's uncommitted work. Per
the repo's Priority Order ("1. Safety and user instruction" outranks plan-literal execution),
this edit was skipped entirely rather than guessed around. `git diff`/`git log` confirmed the
file is currently clean (HAZARD-NATIVE-IMMUNITY hasn't written to it yet), but the explicit
instruction was honored regardless since another session could write to it concurrently.
**Follow-up required:** once `TCK-20260701-HAZARD-NATIVE-IMMUNITY` lands, a small follow-up
change (or the next ticket touching that file) must append a `### 2.21 Worldtemplate.v1
Schema Removal` entry per the format specified in `staging_artifacts/TCK-20260701-
WORLDTEMPLATE-REMOVE/plan.md` step 6.4 (moved to `stored_artifacts/` on completion). This is
the one acceptance criterion ("`docs/guidelines/intentional_divergences.md` has a new entry
for this removal") not satisfied by this ticket's changes, and it is intentionally, visibly
deferred rather than silently dropped.

## Test Summary
- Deleted `tests/unit/worldbuilding/test_world_recipes.py` in full (every test in it
  exercised `WorldTemplateSpec`/`WorldTemplateExpander`, both deleted; no behavior remains
  to test).
- Rewrote `tests/cli/test_world_cli.py::test_cli_create_template_bootstraps_correctly` to
  assert the repointed `worldcomposition.v1` scaffold output (schema_version, world_id,
  name, empty module_refs) and round-trip it through `WorldCompositionSpec.model_validate()`.
- Added `tests/cli/test_world_cli.py::test_cli_create_template_rejects_existing_world`
  (existing-file guard regression).
- Added `tests/unit/worldbuilding/test_world_repository.py::
  test_repository_index_rebuild_classifies_composition_worlds` — regression guard for
  `rebuild_index()`'s `VALIDATED`/`COMPOSITION` classification now that the `TEMPLATE`
  branch is gone.
- Ran the scoped commands from `test_plan.md`, all green:
  - `pytest tests/unit/worldbuilding/ -q` → 92 passed
  - `pytest tests/cli/test_world_cli.py -q` → 9 passed
  - `pytest tests/cli/test_entry_parity.py -q` → 4 passed
  - `pytest tests/unit/worldassembly/ tests/integration/worldassembly/ -q` → 91 passed
  - `pytest tests/unit/worldmodules/ -q` → 51 passed
- Anti-drift check: `grep -rn "WorldTemplateSpec\|WorldTemplateExpander\|WorldTemplateEntitiesSpec" tests/ src/`
  → zero hits (excluding this ticket's own new docstring text and generated
  `graphify-out/` cache, which was refreshed via `graphify update .`).
- `python3 -m src.worldbuilding.cli list` against the real `data/worlds/` tree (all 10
  worlds) → all classify as `worldcomposition.v1` / `COMPOSITION`, confirming the
  prerequisite migration and the `repository.py` edit are both correct in production data.

## Files Changed
- `src/worldbuilding/cli.py`
- `src/worldbuilding/recipe.py`
- `src/worldbuilding/repository.py`
- `src/worldbuilding/__init__.py`
- `src/cli/entry.py`
- `docs/architecture/world_repository_layout.md`
- `docs/guides/simulation.md`
- `tests/cli/test_world_cli.py`
- `tests/unit/worldbuilding/test_world_repository.py`
- `tests/unit/worldbuilding/test_world_recipes.py` (deleted)
- `data/worlds/world_index.json` (regenerated byproduct of running `list`/`rebuild_index()`
  for verification against real data; not a content change)

## Completion Summary
Removed the legacy `worldtemplate.v1` authoring schema and all its code paths
(`WorldTemplateEntitiesSpec`, `WorldTemplateSpec`, `WorldTemplateExpander`, and every CLI/
repository/entrypoint branch that checked for it) now that its single consumer
(`sandbox_world`) was migrated to `worldcomposition.v1` by the prerequisite ticket. The
`worldcomposition.v1`/`worldmodule.v1` path (including the four shared `*RecipeSpec`
classes in `recipe.py`) and `worldspec.v1`/`WorldSpec` are fully unchanged and passing.
`create-template` was repointed (not removed) to scaffold a minimal `worldcomposition.v1`
stub, keeping `docs/guides/simulation.md`'s documented bootstrap workflow intact; that doc's
pre-existing arg-count example bug was fixed opportunistically. All scoped worldbuilding,
CLI, entry-parity, worldassembly, and worldmodules test suites pass (247 tests total across
the five scoped runs). One acceptance criterion — the `docs/guidelines/intentional_
divergences.md` entry — is intentionally deferred as a follow-up due to an explicit
shared-file safety constraint protecting concurrent work on `TCK-20260701-HAZARD-NATIVE-
IMMUNITY`; this is documented above, not silently dropped.
