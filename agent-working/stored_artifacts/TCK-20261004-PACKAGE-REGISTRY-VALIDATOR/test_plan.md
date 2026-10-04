---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
artifact_type: test_plan
tags: [architecture, planning]
---

# Test plan — TCK-20261004-PACKAGE-REGISTRY-VALIDATOR

Normal flow: real `package_registry.jsonl` validates against the real repo (36 rows, all tracked packages). Edge: non-git root fallback; empty `exemplar_modules`; `system` null. Failure modes (each injected in a scratch repo and expected to be reported): unknown field, missing required field, wrong type, bad `layer`/`status`/`strictness_tier`, duplicate package, row for a package that is not on disk or not tracked, tracked package without a row, nonexistent cited path, unknown `system`, dangling `merge-candidate into`. CLI exit codes 0 and 1. Regression: the CI step is advisory (`continue-on-error: true` on the new step in the `code-health` job); existing CI-pinning tests in `tests/static` and `tests/tools` still pass; `tests/codebase` scoped run in two chunks under the 2 GB cap.

## Proof Plan
level: unit + static; proof kind: injected-violation and real-repo validation; oracle source: the standard's rule M5 and the audit's 36-row table; expected effect: validator exit 0 on main, 1 on each injected defect; selected commands: `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0 .venv/bin/python3 -m pytest tests/codebase/test_package_registry.py`, then the CI-pinning static tests.
