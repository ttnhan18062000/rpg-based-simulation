---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS
tags: [testing, ai, bug]
---

# Test Plan — TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS

## Validation
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"`: valid YAML, 12
  jobs (was 11).

## Normal flow — new job's real scope
- `pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor
  tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration
  tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness
  tests/agent_codex_runtime_shadow tests/agent_orchestration
  tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter
  tests/agent_replay tests/agent_replay_codex -m "not slow and not extra_slow" -q`: 385 passed, 5
  skipped.

## Regression check — modified jobs' FULL real scope (not just the new paths in isolation)
- `unit-gameplay`'s full real invocation (all pre-existing dirs + `tests/unit/actions` +
  `tests/unit/ai`): 1187 passed, 2 deselected.
- `unit-infra`'s full real invocation (all pre-existing dirs + `tests/unit/tools`): 1870 passed, 6
  skipped.

## Results
All 3 modified/new jobs' real, full scopes pass clean. Combined with the earlier
`tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not slow"`
full run (2382 passed, 0 failed) and `tests/integration -m "not slow and not extra_slow"` (900
passed, 2 pre-existing unrelated `pyarrow`-environment failures — see that investigation's own
disclosure), every job touched or added this session has been verified against its real, full CI
invocation, not just the specific files this session's tickets modified.
