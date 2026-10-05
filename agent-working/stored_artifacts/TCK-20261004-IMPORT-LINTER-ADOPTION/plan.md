---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-ADOPTION
artifact_type: plan
tags: [architecture, planning]
---

# Plan — TCK-20261004-IMPORT-LINTER-ADOPTION

Closure-time record of the plan that was followed (the planner's brief is the source: `docs/plans/codebase_health/import_linter_adoption_ticket_brief.md`).

1. Pin `import-linter==2.15` in the `lint` group; re-lock; re-run `tests/static` (the lint-group membership test names the group).
2. Config in `codebase/structure/importlinter.toml` (planner's placement change: a codebase-owned file, not `pyproject.toml`): `src` + 20 `src.<pkg>` roots (+ `visual_assets`), `include_external_packages = true`, `exclude_type_checking_imports = false` (reason in the ticket).
3. `codebase/structure/import_contracts.py`: generate the `layers` block from the registry, baseline in `import_layers_baseline.txt`, `--check`, `seed-baseline` (refuses an indirect chain), `advisory` (always exit 0).
4. 16 hand-edited contracts (class E rules and loopholes) with pinned exceptions; phase19's five kernel.py imports in c06 "pending rpg decision".
5. Parity table in a scratch copy; no test retired (testing condition 1).
6. One advisory `Import contracts` CI step in the `code-health` job, own `continue-on-error`; `make import-contracts`.
7. Docs and handoffs; ticket 2 `TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT` filed BLOCKED; `SEQUENCE.md`.

Out of scope: any `src/` file; retiring a test; making the step blocking.
