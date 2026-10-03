---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION
tags: [ai, testing, bug]
---

# Plan — TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION

## Files

1. `tools/agent_codex_runtime_shadow/matrix.py`: add `_VERIFIED_AGAINST_WORKFLOW_VERSION = 2`
   module constant with a full docstring explaining the conflation this replaces and why it's
   deliberately decoupled from `FixtureEnvelope.version`. Change `validate_contract_version()`'s
   signature from `(declared_version: int, matrix: SupportedMatrix)` to `(matrix: SupportedMatrix)`,
   checking `matrix.workflow_version != _VERIFIED_AGAINST_WORKFLOW_VERSION` instead of comparing
   against a caller-supplied value.
2. `tools/agent_codex_runtime_shadow/shadow_runner.py`: update the one call site,
   `matrix.validate_contract_version(fixture.version, supported_matrix)` →
   `matrix.validate_contract_version(supported_matrix)`.
3. `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py`: the only test calling
   `validate_contract_version()` directly with an explicit mismatched value
   (`validate_contract_version(9999, matrix)`) needs updating for the new signature — construct a
   `SupportedMatrix` with a mismatched `workflow_version=9999` instead of passing a
   `declared_version` argument. Added a second test confirming the real, current matrix does NOT
   raise (regression-safety for the common case).

## Why no fixture files need changing
Once the check is decoupled from `FixtureEnvelope.version` entirely, none of the 3 fixtures
involved (`test_containment.py`'s inline synthetic template, the real committed
`tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` used by
`test_shadow_comparison.py`, and `test_shadow_comparison.py`'s own inline synthetic fixtures) need
any modification — `derive_codex_shadow_outcome()` never reads `fixture.version` for this purpose
anymore. This also means `tools/agent_replay/`'s explicit scope-guard ("byte-identical" per
`TCK-20260730-CODEX-RUNTIME-SHADOW`'s own closing ticket) around the shared fixture is trivially
respected — it was never touched.

## Out of scope
- `FixtureEnvelope.version`/`docs/ai/replay_fixture_spec.md` — confirmed correct and untouched;
  the replay-fixture-envelope schema version concept is unrelated to this fix.
- Any change to `tools/agent_replay/` or `tools/agent_replay_codex/` — confirmed via full test
  sweep (171 passed) that nothing in those sibling packages was affected.
- Any other ticket in this batch.
