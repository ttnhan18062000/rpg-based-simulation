---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION
tags: [ai, testing, bug]
---

# Investigation — TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-VERSION-FIXTURE-CONFLATION

## Failing tests
3 of the 4 `tests/agent_codex_runtime_shadow/` failures found this session (the 4th,
`test_phase_tier_matrix.py`'s stale `workflow_version==1` assertion, was already fixed as its own
hotfix ticket): `test_containment.py::test_shadow_run_produces_zero_diff_in_tickets_and_monitoring`,
`test_containment.py::test_committed_codex_config_remains_hook_free_and_byte_identical`,
`test_shadow_comparison.py::test_shadow_comparison_matches_canonical_fixture` — all raise
`ContractVersionMismatchError: declared workflow_version 1 does not match the real
implement-ticket.yaml's workflow_version 2`.

## Root cause: two independently-owned concepts sharing the name "version"
`tools/agent_codex_runtime_shadow/shadow_runner.py::derive_codex_shadow_outcome()` called
`matrix.validate_contract_version(fixture.version, supported_matrix)`.

- `fixture.version` is `FixtureEnvelope.version` (`tools/agent_replay/fixture_envelope.py`) — the
  **replay-fixture-envelope schema version**, documented (`docs/ai/replay_fixture_spec.md`) as
  "version: 1 # int, currently always 1", pinned by `TCK-20260721-CODEX-REPLAY-PROOF` and asserted
  independently by `tests/agent_replay/test_fixture_envelope.py:70,96`. It describes the YAML
  *format* a fixture file must satisfy — unrelated to any specific `implement-ticket.yaml`
  contract version.
- `matrix.validate_contract_version()`'s real purpose (inferred from its own name and error
  message, and confirmed against `matrix.py`'s own documented pattern) is to check whether THIS
  PACKAGE's own hardcoded phase/gate assumptions (`_SUPPORTED_TIER`, `_SUPPORTED_PHASES`) are
  still valid against the live orchestrator contract.

These two numbers happened to both be `1` when `TCK-20260730-CODEX-RUNTIME-SHADOW` was authored
(2026-07-30) — the bug was invisible then. `agent-orchestration/workflows/implement-ticket.yaml`'s
`workflow_version` was legitimately bumped to 2 by an unrelated ticket
(`TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY`, added `continuation_policy`), which the
fixture-envelope schema version had no reason to track and never changed.

## Why the "obvious" fix (bump the fixture's `version: 1` to `2`) is wrong
Would make the tests pass but would misrepresent the fixture-envelope schema version (breaking
`test_fixture_envelope.py`'s own real assertions), silently violate the shared-fixture invariant,
and require the fixture to be perpetually re-stamped every time `workflow_version` changes for any
reason at all — including reasons entirely unrelated to whether this package's own Scope→
Investigate→Plan→Review phase/gate assumptions are still correct. This is the same category of
"edit to make the gate pass instead of fixing the substance" this repo's CLAUDE.md forbids.

## Design options considered
1. Add a new `workflow_version` field to the fixture envelope (recording which contract version a
   captured run was replayed against), compared per-fixture. Rejected: doesn't match the intended
   "canonical, ongoing compatibility" semantics of a shared fixture used across many tests over
   time — every historical fixture would need re-stamping on every unrelated `workflow_version`
   bump, and it's unclear what a *synthetic* test fixture (not derived from any real historical
   run) should even record.
2. **Chosen**: decouple the check from any individual fixture entirely. The real question
   `validate_contract_version` answers is "does THIS PACKAGE's own hardcoded phase/gate contract
   still match the live orchestrator" — not "was this specific fixture captured under the current
   version." Add a new module-level constant,
   `matrix._VERIFIED_AGAINST_WORKFLOW_VERSION`, hardcoded and manually bumped only after a human/
   agent re-reviews this package's phase/gate assumptions against a real
   `implement-ticket.yaml` change — matching `_SUPPORTED_TIER`/`_SUPPORTED_PHASES`'s own
   already-established "hardcoded-by-design" pattern in the same file. `validate_contract_version()`
   drops its `declared_version` parameter entirely and self-checks
   `matrix.workflow_version != _VERIFIED_AGAINST_WORKFLOW_VERSION`.
