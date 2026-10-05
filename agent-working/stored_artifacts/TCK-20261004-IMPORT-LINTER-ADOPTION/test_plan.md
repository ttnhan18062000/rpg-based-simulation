---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-ADOPTION
artifact_type: test_plan
tags: [architecture, planning]
---

# Test plan — TCK-20261004-IMPORT-LINTER-ADOPTION

Normal flow: the committed generated block equals what the generator writes; every registry package is in the `layers` contract; roots equal `{src, visual_assets}` plus every registry package without an `__init__.py`; the 17 contracts are kept on the real tree. Edge cases: a registry layer the order does not know; a config without markers; wrapped and ANSI-coloured `lint-imports` output. Failure modes: an indirect chain refuses `seed-baseline` (exit 2, baseline untouched); `advisory` exits 0 for a broken contract, a stale ignored import, a stale block, a missing or crashing binary, garbage output and an unwritable summary. Regression: the workflow step is last in the job that runs "Package registry" and carries its own `continue-on-error`; `tests/static`, the scenario-lane pin and the `*guard*` tests stay green; no `src/` path in the diff.

## Proof Plan
level: unit + static + injected-violation parity; proof kind: per-test parity in a scratch copy (34 injections: the contract caught all 34, the existing tests missed 11); oracle source: the evaluation's table and the existing tests; expected effect: contracts BROKEN on each injection, KEPT on the clean tree; selected commands: `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0 .venv/bin/python3 -m pytest tests/codebase/test_import_contracts.py`, then `tests/static`, `tests/unit/tools/test_scenario_lane_paths.py`, `tests/tools/test_*guard*.py`, and `tests/codebase` in two chunks.
