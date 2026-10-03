---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION
phase: done
date: 2026-08-17
tags: [ai, testing, bug]
---

# TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION

## Title
Fix `agent_codex_runtime_shadow`'s contract-version check conflating a fixture's own envelope
schema version with the live workflow contract version

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
3 of 4 real, pre-existing failures in `tests/agent_codex_runtime_shadow/` (found while auditing
the 16 test directories added by commit `29d78798` that were never wired into any CI job — the
4th, a stale `workflow_version==1` assertion, was already fixed as its own hotfix ticket):
`test_containment.py::test_shadow_run_produces_zero_diff_in_tickets_and_monitoring`,
`test_containment.py::test_committed_codex_config_remains_hook_free_and_byte_identical`,
`test_shadow_comparison.py::test_shadow_comparison_matches_canonical_fixture` — all raise
`ContractVersionMismatchError: declared workflow_version 1 does not match the real
implement-ticket.yaml's workflow_version 2`.

Root cause: `shadow_runner.py` passed `fixture.version` (`FixtureEnvelope.version` — the
replay-fixture-**envelope schema** version, pinned at 1, owned by an unrelated ticket
`TCK-20260721-CODEX-REPLAY-PROOF`) into `matrix.validate_contract_version()`, which actually
checks whether this package's own hardcoded phase/gate assumptions still match the live
`implement-ticket.yaml` contract — two independently-owned concepts that happened to both be 1
when authored, and diverged the moment `workflow_version` was legitimately bumped for an unrelated
reason.

## Scope
- `tools/agent_codex_runtime_shadow/matrix.py`: add `_VERIFIED_AGAINST_WORKFLOW_VERSION = 2`
  (hardcoded-by-design, matching `_SUPPORTED_TIER`/`_SUPPORTED_PHASES`'s own established pattern
  in the same file). `validate_contract_version()` drops its `declared_version` parameter and
  self-checks the live matrix against this constant instead.
- `tools/agent_codex_runtime_shadow/shadow_runner.py`: update the one call site.
- `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py`: update the one test calling
  `validate_contract_version()` directly for the new signature; add a regression-safety test for
  the non-mismatched case.

## Out of Scope
- `FixtureEnvelope.version`/`docs/ai/replay_fixture_spec.md` — confirmed correct, untouched. The
  "obvious" fix (bump the fixture's `version: 1` to `2`) was rejected — would misrepresent the
  schema version, require perpetual re-stamping on every unrelated `workflow_version` bump, and is
  exactly the "edit to make the gate pass instead of fixing the substance" this repo forbids.
- Any change to `tools/agent_replay/`/`tools/agent_replay_codex/` — confirmed unaffected via full
  sweep; the shared fixture's own explicit "byte-identical" scope guard from
  `TCK-20260730-CODEX-RUNTIME-SHADOW`'s closing ticket is trivially respected since it was never
  touched.
- Any other ticket in this batch.

## Acceptance Criteria
- [x] All 3 originally-failing tests pass.
- [x] The mismatch-detection behavior itself is preserved (tested via a deliberately mismatched
      matrix), not merely disabled.
- [x] No regression in sibling `agent_replay`/`agent_replay_codex`/`agent_orchestration*` packages.

## Related Tickets
- `TCK-20260817-HOTFIX-PHASE-TIER-MATRIX-WORKFLOW-VERSION-STALE` (the 4th, already-fixed sibling
  failure in the same investigation batch)

## Related Docs
None — `docs/ai/replay_fixture_spec.md` confirmed correct and unrelated to this fix.

## Related Stored Artifacts
`stored_artifacts/TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION/`

## Related Code Areas
- `tools/agent_codex_runtime_shadow/matrix.py`
- `tools/agent_codex_runtime_shadow/shadow_runner.py`
- `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Decoupled the contract-version check entirely from any individual fixture: added a module-level
`_VERIFIED_AGAINST_WORKFLOW_VERSION` constant to `matrix.py` (manually bumped only after
re-reviewing this package's phase/gate assumptions against a real orchestrator change), and
changed `validate_contract_version()` to self-check the live matrix against it, dropping its
`declared_version` parameter. This required no changes to any fixture file (synthetic or real,
shared or package-local) — the check never needed fixture-derived data in the first place.

## Test Summary
- `pytest tests/agent_codex_runtime_shadow/ -v`: 39 passed (was 3 failed + 36 passed before).
- `pytest tests/agent_replay tests/agent_replay_codex tests/agent_orchestration
  tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter -m "not slow
  and not extra_slow" -q`: 171 passed, 5 skipped — no regression.

## Files Changed
- `tools/agent_codex_runtime_shadow/matrix.py`
- `tools/agent_codex_runtime_shadow/shadow_runner.py`
- `tests/agent_codex_runtime_shadow/test_phase_tier_matrix.py`

## Completion Summary
Fixed the real conflation at its source: `validate_contract_version()` never actually needed a
fixture's own schema version — it was answering a question about this package's own phase/gate
contract, not about any individual fixture. Decoupling the two required no fixture changes at all,
avoiding the fragile "re-stamp every fixture on every unrelated contract bump" alternative.
