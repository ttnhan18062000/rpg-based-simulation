---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
artifact_type: plan
tags: [architecture, planning]
---

# Plan — TCK-20261004-PACKAGE-REGISTRY-VALIDATOR

## Design

**Layout** (owner decision 2026-10-04): `codebase/structure/{__init__.py,packages.py}`; data file `codebase/structure/package_registry.jsonl`. Direction rule holds (codebase imports nothing from `tools`; none needed).

**Row schema** (all fields required except `system`, which may be null; unknown fields rejected): `package` (str, unique), `purpose` (str), `layer` (one of `foundation | content-pipeline | domain | engine | simulation-systems | consumer`, the audit's L0 to L5), `status` (`active | legacy | frozen`), `strictness_tier` (one of `baseline | strict | exemplar`), `exemplar_modules` (list of 0 to 3 repo paths), `do_not_imitate` (list of `{path, reason}`), `system` (null or a name in `registries/system_registry.jsonl`), `audit_decision` (`keep | retire-candidate | investigate | merge-candidate into <pkg>` with `<pkg>` a registered package), `added_date` (ISO date), `reviewed` (bool).

**Tier names** (defined here, enforced by the validator, no gate reads them yet): `baseline` = ratchet-only, the current state of every package; `strict` = future: reviewed rows only, no new findings in the package; `exemplar` = future: highest bar, a package agents should imitate. Every seeded row is `baseline`.

**Status mapping at seeding:** audit `keep` and `investigate` become `active`; `retire-candidate` and `merge-candidate` become `legacy`; `frozen` is accepted and unused. `reviewed` is `false` for all rows (bulk-seeded from the audit, same convention as the code-health registry). `exemplar_modules` and `do_not_imitate` are empty and `system` is null at seeding: picking exemplars is a judgement the audit did not make, and the validator allows 0.

**Validator** (`codebase/structure/packages.py`, same shape as `codebase/health/registry.py`: `validate_file` returns a list of problems, `load_rows` raises `RegistryError`): rejects not-JSON lines, missing or unknown fields, wrong types or enum values, duplicate `package`, a `package` that is not a tracked top-level `src/` package, a tracked top-level package with no row (the standard's rule M5 made checkable), a cited `exemplar_modules` or `do_not_imitate` path that does not exist, an unknown `system`, a `merge-candidate into X` whose X is not a row. Tracked packages come from `git ls-files src` (top-level dirs with a tracked file); a root that is not a git repo falls back to on-disk directories holding a `.py` file. CLI: `python3 -m codebase.structure.packages validate [--root DIR]`, exit 0 clean, 1 problems (one per line). Advisory only.

**Seeding:** a one-off generator (scratchpad, not committed) parses the audit doc's table (package, purpose, layer, decision) into the 36 rows; the generated file is what is committed. Sorted by `package`, stable key order, like `write_rows`.

## Steps

1. Package, loader, validator, CLI.
2. Seed `package_registry.jsonl` from the audit; `validate` passes on the real repo.
3. Tests `tests/codebase/test_package_registry.py`: real registry validates; scratch git repos with an injected unknown field, a missing package row, a row for a nonexistent package, a nonexistent cited path, a duplicate package, a bad enum, an unknown system, a dangling merge target; non-git fallback; CLI exit codes.
4. CI: one advisory step in the `code-health` job (`continue-on-error: true`), after the ratchet step. Edit the tests that pin the job's step list only if they fail (decision 8.11; tell the testing planner via outbox).
5. Docs: roadmap 6.4 (path `codebase/structure/package_registry.jsonl`, fields as built); `codebase/README.md` row for `structure/`; standard rule M5 Enforcement cell; `docs/guidelines/subsystem_ownership_lifecycle.md` row.
6. File `TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING` (BLOCKED, soak end 14 days after this ticket's merge, to be written at merge).
7. Add the namespace-package assumption to the import-linter ticket (planner carry-forward).

## Scope guards
No `src/` path; no change to M4 thresholds or the rows in `code_health_exceptions.jsonl`; no `tests/architecture/` edit; no governing-file edit; the CI step is advisory.

## Amendments after planner review (2026-10-04)

1. **Problem classes.** The validator returns `Problem(kind, message)` with `kind` `schema` or `completeness`. `schema`: JSON, fields, types, enums, duplicate package, cited paths exist, `system` known, `merge-candidate into X` resolves to a row. `completeness`: a tracked top-level package with no row; a row for a package that is not tracked or not on disk. `validate --schema-only` reports only the first class. The later flip ticket promotes `completeness` without a rewrite.
2. **Which test asserts what.** The real-repo test (`tests/codebase/`, tools-a-e job, not advisory) asserts ONLY that the committed file loads and has no `schema` problem. It never asserts completeness against the live tree, so a new top-level `src/` package without a row cannot fail a PR through the test lane. Both completeness checks are tested only in scratch-repo fixtures. The advisory CI step runs the full `validate` (both classes).
3. **`do_not_imitate` seeding** from the owner-approved roadmap Section 2 worst cases, each with a reason and a size re-measured on current main with `ast` (2026-10-04): `src/api/server.py` (`create_v2_app` 2,409 lines containing a 2,093-line nested function), `src/observability/event_extractor.py` (`EventExtractor.extract` 1,588 lines; the roadmap says 1,585), `src/engine/tactical.py` (`evaluate_entity_intent` 713), `src/systems/strategic_systems/intelligence.py` (`evaluate_strategic_intent` 541). Exemplars stay empty; recorded as an open follow-up (M6 or owner) in the Completion Summary.
4. **Source of truth.** The registry's README row and the audit doc each say: after seeding the registry is the source of truth, the audit table is a dated snapshot (2026-10-04).
