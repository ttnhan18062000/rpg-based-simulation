---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION
tags: [ai, testing, bug]
---

# Test Plan — TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION

## Normal flow
- `pytest tests/agent_codex_runtime_shadow/ -v`: all 39 tests pass, including the 3 originally
  failing (`test_shadow_run_produces_zero_diff_in_tickets_and_monitoring`,
  `test_committed_codex_config_remains_hook_free_and_byte_identical`,
  `test_shadow_comparison_matches_canonical_fixture`).

## Edge case
- `test_contract_version_mismatch_rejected`: constructs a `SupportedMatrix` with a deliberately
  mismatched `workflow_version=9999` and confirms `validate_contract_version()` still raises
  `ContractVersionMismatchError` — the mismatch-detection behavior itself is preserved, only its
  input source changed.
- `test_contract_version_accepted_when_matrix_matches_verified_version` (new): confirms the real,
  current `load_supported_matrix()` result does NOT raise — regression-safety for the common case.

## Regression check
- `pytest tests/agent_replay tests/agent_replay_codex tests/agent_orchestration
  tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter -m "not slow
  and not extra_slow" -q`: 171 passed, 5 skipped — confirms zero impact on sibling packages
  (expected, since no fixture files or sibling-package code were touched).

## Results
- `pytest tests/agent_codex_runtime_shadow/ -v`: 39 passed.
- `pytest tests/agent_replay tests/agent_replay_codex tests/agent_orchestration
  tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter -m "not slow
  and not extra_slow" -q`: 171 passed, 5 skipped.
