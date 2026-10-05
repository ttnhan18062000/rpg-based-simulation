---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING
artifact_type: test_plan
tags: [architecture, delivery]
---

# Test plan — TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING

1. Real-repo: the committed registry has no schema and no completeness problem against the live tree.
2. Workflow pin: the `Package registry` step has no `continue-on-error` and runs `validate` with `--summary-out` and `--annotate`.
3. Static pin (`test_ci_uv_install.py`): tolerant steps of `code-health` are exactly `{"Paths this PR changed"}`.
4. Existing scratch-repo tests (completeness both ways, git fallback, spaces, crash, missing file) stay green.
Mutation proof: add a tracked top-level `src/zz/` dir in a scratch clone or remove one row from the registry copy: test 1 must fail on a `completeness` problem naming it (not on a load error). Run `tests/codebase` in two chunks, `tests/static`, guard tests, `test_scenario_lane_paths`.
