---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT
artifact_type: test_plan
tags: [architecture, planning]
---

# Test plan — TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT

Normal flow: `ci` exits 0 on the real tree (17 kept, 0 broken, 0 stale). Edge cases: a contract with 2+ broken pairs names every pair; the generated `layers` block out of date. Failure modes: `ci` exits 1 on a broken contract, a stale ignored import or a stale block, and 2 when it cannot run. Regression: the seven retired tests are removed only with the blocking commit; the static pin of the workflow step; `tests/static`, `tests/architecture`, `tests/docs`, `tests/tools` stay green; no `src/` path in the diff.

## Proof Plan
level: unit + static + injected-violation parity; proof kind: per-test parity in a scratch copy (37 injections: the contract caught all 37, the existing tests missed 9); oracle source: the real `lint-imports` 2.15 output and the existing tests; expected effect: each contract BROKEN and naming its pair on each injection, KEPT on the clean copy; selected commands: `python -m pytest tests/codebase tests/static tests/docs tests/architecture` (815 passed), then `tests/tools` alone under `systemd-run --user --scope -p MemoryMax=2G` (5114 passed), then `python3 -m codebase.structure.import_contracts ci` (17 kept, 0 broken, 0 stale).
