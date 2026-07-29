---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK
phase: done
date: 2026-07-29
tags: [testing, observability, agent-monitoring]
---

# TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK

## Title
Add structural provider-parity check for the new retrieval-event field shape

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The author wants a test/assertion — mirroring the read-only-invariant style of the existing Codex provenance check — that confirms the new retrieval-event field shape is provider-neutral in its own definitions (no Claude-Code-only or Codex-only field), even though no real Codex execution exists yet to populate it. This must be explicitly labeled as structural/field-shape parity only, not live cross-provider parity, since zero real Codex pilot executions have occurred and none may be attempted as part of this work.

## Scope
- A new structural/field-shape test module mirroring `tools/agent_replay_codex/provenance_check.py`'s style and `tests/agent_replay_codex/test_monitoring_provenance.py`'s assertion patterns
- Validates that the retrieval-event field-name list defined by the sibling schema ticket (TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT) contains no provider-specific (e.g. `codex_*`/`claude_*`-prefixed) field
- Explicit assertions that `execution_id` and `provider` are absent from the retrieval-event's own field list
- A negative-control test proving the check raises when a provider-specific field is deliberately injected into a fixture/schema

## Out of Scope
- No live Codex pilot execution; `CODEX_REPLAY_PARITY_LIVE_CONSENT` must never be set as part of this work
- No `execution_id` or `provider` fields added to `runs.jsonl`/`events.jsonl` or the retrieval-event shape to satisfy a naive notion of parity — the check confirms their absence, it does not add them
- No new writer mechanism — `writer.py`'s `write_line`/`write_lines` remains the only verified write path
- No wiring into any `.claude/workflows/*.js` file
- No new dashboard frontend/UI surface

## Acceptance Criteria
- [x] A test (mirroring `test_monitoring_provenance.py`'s style) asserts the new retrieval-event field-name set contains no field literally naming or prefixing a single provider
- [x] The check/module explicitly asserts `execution_id` and `provider` are absent from the new retrieval-event's own field list, and fails loudly if either is present
- [x] The test module's docstring and test names state plainly that this is structural/field-shape parity only, not live cross-provider parity
- [x] A negative-control test proves the check actually raises when a provider-specific field is deliberately injected into a fixture/schema

## Related Tickets
- TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT
- TCK-20260721-CODEX-REPLAY-PARITY
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260729-CONTEXT-PACKET-ASSEMBLY

## Related Docs
- docs/agent-monitoring/schema.md
- docs/observability/retrieval_retention_redaction_policy.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase4.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent_replay_codex/provenance_check.py
- tools/agent_replay_codex/errors.py
- tests/agent_replay_codex/test_monitoring_provenance.py
- tools/agent-monitoring/writer.py

## Assumptions / Open Questions
- HARD DEPENDENCY: this ticket depends on TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT landing first — no `retrieval_event`/`RetrievalEvent` symbol, module, or field-list constant exists anywhere in `tools/` or `src/` today; this ticket has nothing concrete to validate until that ticket lands and fixes the actual field-list artifact
- The concrete artifact to check (TypedDict/dataclass/constant list vs. inline dict literals) is that sibling ticket's implementation decision, not this ticket's — this ticket's test import path cannot be finalized until that ticket ships and its actual module/constant name is known
- No live data exists to assert against; the assertion is definitional (field names present/absent), not behavioral

## Implementation Notes

Implemented per plan.md's 6 steps, no deviations.

- Created `tools/retrieval_event_parity_check.py`: a new, standalone module beside
  `tools/retrieval_events.py` (Decision 1 — not inside `tools/agent_replay_codex/`, to avoid
  coupling a pure schema-constant check to the live-Codex-invocation package). Contains:
  - `_KNOWN_PROVIDER_TOKENS: frozenset[str] = frozenset({"codex", "claude", "claude-code"})` —
    the closed, documented provider-token set from plan.md Decision 3, anchored to
    `docs/architecture/agent_orchestration_contract.md:137-143`'s provider-adapter vocabulary.
  - `ProviderFieldViolationError(Exception)` — a new, locally-defined exception. Does not
    subclass or import anything from `tools/agent_replay_codex/errors.py`.
  - `assert_no_provider_specific_fields(fields, provider_tokens=_KNOWN_PROVIDER_TOKENS)` — checks
    each field name against an unconditional `execution_id`/`provider` identity rule, plus an
    exact/prefix (`{token}_`)/suffix (`_{token}`) case-insensitive match against the provider
    token set. Zero file I/O; operates purely on the in-memory `fields` argument.
- Created `tests/tools/test_retrieval_event_parity_check.py` with 6 tests (test_plan.md's 5
  required tests, plus one extra negative-control test for the `execution_id`/`provider`
  identity rule specifically, kept distinct from the provider-token negative control per plan.md
  Step 3's "second, distinct injected-fixture" instruction):
  - `test_field_set_contains_no_provider_specific_field` (AC1) — runs against the real
    `tools.retrieval_events.RETRIEVAL_EVENT_FIELDS`.
  - `test_execution_id_and_provider_absent_from_retrieval_event_fields` (AC2 positive half) —
    runs against the real constant, both via direct membership assertion and via the check
    function.
  - `test_negative_control_raises_when_provider_specific_field_injected` (AC4) — injects
    `"codex_latency_ms"` and `"claude_cache_status"` into a copy of the real field set, asserts
    `ProviderFieldViolationError` (exact type, not a bare `Exception`) is raised for each.
  - `test_negative_control_raises_on_execution_id_or_provider_injection` — same shape, injecting
    `"execution_id"`/`"provider"` directly, isolating AC2's "fails loudly if present" half from
    the provider-token rule.
  - `test_docstring_and_test_names_state_structural_only_not_live_parity` (AC3) — asserts the
    module docstring contains "structural" and "live" (and the literal phrase "not live
    cross-provider parity"), and that the check function's name contains none of "live",
    "output", "execution".
  - `test_check_is_read_only_and_never_touches_real_monitoring_files` — source-inspection
    architecture guard confirming no `open(`, `Path(`, `"agent-monitoring"`,
    `CODEX_REPLAY_PARITY_LIVE_CONSENT`, `consent_gate`, `invoker`, or `shadow_mode` references
    anywhere in the new module's source.
- No existing file was modified. `tools/retrieval_events.py`'s `RETRIEVAL_EVENT_FIELDS` constant
  and `tools/agent_replay_codex/errors.py`/`provenance_check.py` were read-only references.
- No new `docs/parity_ledger/infrastructure.yaml` entry added, per plan.md Decision 2 (precedent:
  `TCK-20260721-CODEX-REPLAY-PARITY` has zero `infrastructure.yaml` entries despite a larger
  test-only/structural-guard change; this ticket changes no runtime behavior).

## Test Summary

New: `pytest tests/tools/test_retrieval_event_parity_check.py -v` — 6 passed.

Regression (test_plan.md's scoped command set, all green, none modified):
- `pytest tests/tools/test_retrieval_events.py tests/tools/test_retrieval_event_wrapper_single_source.py -v` — 25 passed.
- `pytest tests/agent_replay_codex/ -v` — 21 passed, 5 skipped (pre-existing skips, unrelated to this change — real-Codex-invocation tests gated by consent/env, untouched).
- `pytest tests/tools/test_record_events.py tests/tools/test_monitoring_writer_single_source.py -v` — 26 passed.

## Files Changed

- `tools/retrieval_event_parity_check.py` (new)
- `tests/tools/test_retrieval_event_parity_check.py` (new)

## Completion Summary

Added a new, standalone structural/field-shape provider-parity check
(`tools/retrieval_event_parity_check.py`) that asserts `tools/retrieval_events.py`'s
`RETRIEVAL_EVENT_FIELDS` constant contains no provider-specific field name (exact/prefix/suffix
match against a closed `{"codex", "claude", "claude-code"}` token set) and no `execution_id`/
`provider` identity field, mirroring the read-only structural-invariant style of
`tools/agent_replay_codex/provenance_check.py` without importing any of that package's
live-Codex-invocation machinery. Covered by 6 new tests in
`tests/tools/test_retrieval_event_parity_check.py` (positive checks against the real constant,
two negative controls, a docstring/naming-contract test, and a source-inspection no-file-I/O
architecture guard), satisfying all 4 acceptance criteria. No existing file was modified, no
runtime behavior changed, and the full scoped regression suite (`test_retrieval_events.py`,
`tests/agent_replay_codex/`, `test_record_events.py`, `test_monitoring_writer_single_source.py`)
remains green and unmodified. No new parity-ledger entry was added, per the cited
`TCK-20260721-CODEX-REPLAY-PARITY` precedent (Decision 2 in plan.md).
