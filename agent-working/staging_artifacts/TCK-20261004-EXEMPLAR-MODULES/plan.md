---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-EXEMPLAR-MODULES
artifact_type: plan
tags: [architecture, planning]
---

# Plan — TCK-20261004-EXEMPLAR-MODULES

## Approach
New module `codebase/structure/exemplars.py` (stdlib only) so the measurement is repeatable and the picks are not hand-curated:
`python3 -m codebase.structure.exemplars {measure,apply}`.
- `measure` (read-only): per `active` package, list qualifying modules and print the picks (max 3). Qualifies = file `src/<pkg>/**/*.py`, not `__init__.py`, 60 to 400 lines, has a module docstring (`ast.get_docstring`), no row in `codebase/baselines/code_health_exceptions.jsonl` for that file (any tool), and not in any registry row's `do_not_imitate`. Ranking: number of other `src` modules that import it (AST `import`/`from` resolved to the module path), then path name, so the result is deterministic.
- `apply`: rewrites only the `exemplar_modules` field of `active` rows in `package_registry.jsonl`, preserving every other field, key order and `reviewed: false`. `legacy`/`frozen` rows get `[]`.
- Ownership of the output: the file `package_registry.jsonl` stays the source; the module only computes picks.

## Steps
1. Add `codebase/structure/exemplars.py` plus tests (`tests/codebase/test_package_exemplars.py`).
2. Run `apply`, review the picks by eye, commit the registry change.
3. Add the "Exemplar criterion" section (criterion, measure command, reseed note) to `docs/plans/codebase_health/src_package_structure_audit.md`.
4. Add the pin test: every exemplar in the real registry has no exceptions row (fails with a "re-pick" message).
5. Ticket AC wording nit from the planner (`(possibly [])`), already applied in the ticket.

## Scope guards
No `src/` diff; no schema change (field already exists, validator unchanged); no change to `code_health_exceptions.jsonl`; `reviewed` stays false; no `do_not_imitate` additions.

## Acceptance-criteria map
- AC1 picks by criterion: steps 1-2. AC2 validator passes: `python3 -m codebase.structure.packages` after step 2. AC3 documented: step 3. AC4 pin test: step 4. AC5 no src diff: `git diff --stat origin/main...HEAD`.

## Open choices (defaults taken unless you object)
- "Imported by other modules" is a ranking preference, not a filter, so a package whose modules nobody imports can still get a pick.
- Importer counting uses the AST of `src/**/*.py` only (tests excluded).
