---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-EVALUATION
artifact_type: plan
tags: [architecture, planning]
---

# Plan — TCK-20261004-IMPORT-LINTER-EVALUATION

Report-only evaluation. No change to `pyproject.toml`, `uv.lock`, CI, `tests/` or `src/`. Output: `docs/plans/codebase_health/import_linter_evaluation.md` (decision record, like the type-checker trial) plus, if the phase19 test is a no-op, an outbox note to the testing planner.

## Method

1. **Tooling, uncommitted.** `uvx --from import-linter` (pins recorded) in the scratchpad, every run under `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0`, one at a time. Scratch config in the scratchpad (`.importlinter` with `root_packages`), never in the repo. Scratch copy of `src/` (outside the repo) for every injected violation.
2. **Namespace packages first (planner carry-forward).** Measure, do not assume: build the grimp graph over `src` as is (the audit saw 215 of 744 modules; 20 of 36 top-level packages have no `__init__.py`); then try the supported ways to cover all 20 namespace packages (listed in the record) without adding `__init__.py` to the repo: import-linter/grimp namespace-package options (`root_packages` listing the namespace parts, `namespace_packages` if the installed grimp has it), and the package given as a path/`src.core` form. Record module counts per package for each attempt. If full coverage needs `__init__.py` in a scratch copy only, say so: that is an M7 / rpg decision, and the record states the coverage a `drop` or `add` recommendation would lose without it.
3. **Re-verify the 41-rule inventory.** Read the 31 import-boundary test files (search `tests/` for `ast.walk` / `ImportFrom` / `import` assertions over `src/`), list each rule with file, subject package, forbidden target, what it pins (names, counts, keywords), and whether it skips `TYPE_CHECKING`. Report the true count against the brief's 31 files / 41 rules / 37 expressible / 4 not.
4. **Contracts.** For each expressible rule a `forbidden` contract in the scratch config, each run with and without `allow_indirect_imports` and `exclude_type_checking_imports` (2 x 2); plus one `layers` contract from `codebase/structure/package_registry.jsonl`'s `layer` field (the six layers, in order). Run over `src/` on one commit (record the SHA). Record version, wall time and peak memory (`/usr/bin/time -v` or cgroup stats) per run.
5. **Same violation caught?** For each rule, inject one known violation in the scratch copy (a function-local import and a `TYPE_CHECKING` import where the rule is sensitive to them), run the existing test against the scratch copy (pointing the test at the copy by working directory or by the path constant it uses; where a test cannot be redirected, evaluate its AST logic directly on the injected file) and the contract, and record whether each fails. A contract that passes while its test fails, or the reverse, is a finding.
6. **Current violations per contract** (what an `ignore_imports` baseline would need), and the rules no contract can express (the brief names four: rendering stdlib-only, the `numpy.random` text check, the `random.Random` attribute check, the required `compute_terrain_histogram` import).
7. **phase19 no-op.** Inject a `src.observability` import into `kernel.py` in the scratch copy and run `test_hot_path_does_not_import_heavy_analyzers`: if it still passes, confirm the no-op; then write the finding to the outbox (status: pending), no test edit.
8. **Which hand-written AST tests could become ast-grep rules** (list for ticket 3's follow-ups); no change to them.
9. **Recommendation:** replace (named tests retire; owner and testing planner agree), add (layer order and uncovered rules), or drop; the namespace-package coverage loss is part of the recommendation. Roadmap Section 4: never a second copy of the tests. If adoption is recommended, file the adoption ticket in `todos/python-code-craft-structure/` (not started).

## Scope guards
No dependency, CI, test, `src/` or governing-file change. Heavy runs one at a time under the 2 GB cap (grimp builds on a 510 MB graph are the risk; run each contract set in its own invocation). The scratch `src/` copy lives in the scratchpad and is deleted at close.
