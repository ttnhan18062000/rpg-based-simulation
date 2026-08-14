---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260728-PHASE0-PREREQ-CONFIRMATION
phase: done
date: 2026-07-28
tags: [observability]
---

# TCK-20260728-PHASE0-PREREQ-CONFIRMATION

## Title
Confirm Phase 0 Prerequisite Is Satisfied for Context-Efficient Retrieval Epic

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Verify that the Phase 0 prerequisite — provider-neutral execution identity, shared monitoring writer, and a stable replay/live boundary — is genuinely in place before any later phase work proceeds. This is a confirmation task only, not new implementation; state plainly whether the prerequisite is satisfied or not.

## Scope
- Verify execution_id/provider/ticket_id model is documented and actually written into tools.jsonl (agent_orchestration_contract.md, post_tool_hook.py)
- Verify writer.py write_line()/write_lines() is the sole append path for post_tool_hook.py, record_run.py, record_events.py
- Verify consent_gate.require_live_consent() and enabled_surface.py correctly restrict the Codex pilot surface
- Run assert_monitoring_writer_landed() directly and the full related test suites to confirm current pass state, enumerating the 5 skipped tests individually
- Produce a written confirmation record stating plainly whether the Phase 0 prerequisite is satisfied

## Out of Scope
- Does NOT fix TCK-20260721-MONITORING-WRITER-UNIFICATION's own frontmatter/body status bug (status:active/phase:open/##Status OPEN contradicting its own Completion Summary and working_log.csv) — that is a known, separately-tracked doc-hygiene issue, handled as its own hotfix outside this ticket
- Does not implement any new monitoring writer, execution-identity, or replay/live boundary behavior — confirmation only
- Does not run a live Codex pilot execution to obtain real end-to-end production evidence beyond structural/test-based verification

## Acceptance Criteria
- [ ] Confirmation record states execution_id/provider/ticket_id model is documented and actually written into tools.jsonl, citing post_tool_hook.py:84-86
- [ ] Confirmation record states writer.py write_line()/write_lines() is verified as the sole append path for post_tool_hook.py, record_run.py, record_events.py
- [ ] Confirmation record states consent_gate.require_live_consent() + enabled_surface.py correctly restrict the pilot, evidenced by assert_monitoring_writer_landed() passing directly and full test suite results (61 passed, 5 skipped) with skip reasons enumerated as consent-gated vs broken
- [ ] Confirmation record explicitly notes zero real live Codex pilot executions have occurred; replay/live boundary is proven structurally/via tests only
- [ ] Confirmation record explicitly flags TCK-20260721-MONITORING-WRITER-UNIFICATION's ticket-file status mismatch as a known, separately-tracked issue not fixed here

## Related Tickets
- TCK-20260721-MONITORING-WRITER-UNIFICATION
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC

## Related Docs
- docs/architecture/agent_orchestration_contract.md
- tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md
- tickets/done/TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/writer.py
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent_replay_codex/consent_gate.py
- tools/agent_replay_codex/entry_criterion.py
- tools/agent_replay_codex/provenance_check.py
- tools/agent_codex_pilot_guardrails/enabled_surface.py

## Assumptions / Open Questions
- 5 skipped tests in the full suite run were not individually enumerated to confirm consent-gated vs genuinely broken — needs verification during this ticket's work
- No live Codex pilot has ever run (by design); replay/live boundary is proven structurally/via tests only, not via real end-to-end production execution

## Implementation Notes

**Verdict: Phase 0 prerequisite IS satisfied.** All 5 Acceptance Criteria are confirmed with direct evidence below. This is a read-only confirmation ticket — no `src/`, `tools/`, or `docs/` file was modified; only this ticket file was written.

### AC1 — execution_id/provider/ticket_id model documented and actually written into tools.jsonl

Confirmed. The ticket's citation of `post_tool_hook.py:84-86` is **correct as-is** — no correction needed:

```
tools/agent-monitoring/post_tool_hook.py:84   "execution_id": execution_id,
tools/agent-monitoring/post_tool_hook.py:85   "provider": provider,
tools/agent-monitoring/post_tool_hook.py:86   "ticket_id": ticket_id,
```

These three fields are populated (lines 50-63 of the same file) from `.claude/current_run`'s sidecar JSON (`execution_id`, `provider`, `ticket_id` keys), defaulting to `None` when the sidecar lacks them, and are unconditionally written into every `agent-monitoring/tools.jsonl` record via `write_line()` at line 91.

The model itself is documented in two places, consistent with each other:
- `docs/ai/monitoring_writer_decision.md:91-142` (§2 "Execution Identity Model") — defines the `execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"` format, `run_id` staying a display/reference field, and `ticket_id` being promoted to an explicit top-level join-key field.
- `docs/architecture/agent_orchestration_contract.md:127-173` ("Execution Identity (Consumed Input)") — quotes `monitoring_writer_decision.md` §2 verbatim as an already-decided input, status "Consumed-as-input".

Both docs are consistent with each other and with the actual field names written by `post_tool_hook.py`.

### AC2 — writer.py's write_line()/write_lines() is the sole append path

Confirmed. Grepped `post_tool_hook.py`, `record_run.py`, `record_events.py` for any `open(` call — **zero results** in all three files; the only file-open calls in this area live inside `tools/agent-monitoring/writer.py` itself (the locked append path and the lock-free diagnostic sidecar writer). All three call sites import `write_line`/`write_lines` from `writer.py` (`post_tool_hook.py:9`, `record_run.py:10`, `record_events.py:12`) and route their entire append step through it — `record_run.py:68`, `record_events.py:145`, `post_tool_hook.py:91`. `record_events.py` additionally does a **read-only** `TOOLS_FILE.read_text()` (line 60) to compute `tool_call_count`/`cost_proxy_score` from existing rows — this is a read, not a write, so it does not bypass the append path. This is independently machine-verified by `tests/tools/test_monitoring_writer_single_source.py` (`test_no_call_site_does_its_own_lock_file_open`, `test_each_call_site_imports_shared_writer`, `test_no_call_site_imports_fcntl`), all passing (see Test Summary).

### AC3 — consent_gate.require_live_consent() + enabled_surface.py correctly restrict the pilot

Confirmed.
- `tools/agent_replay_codex/consent_gate.py::require_live_consent()` (lines 18-30) raises `ConsentNotGrantedError` unless `env[CODEX_REPLAY_PARITY_LIVE_CONSENT] == "1"` exactly — no truthy coercion, so unset/empty/`"true"`/`"0"` all refuse.
- `tools/agent_codex_pilot_guardrails/enabled_surface.py` restricts the pilot's enabled surface to `EVIDENCED_HOOK_EVENTS = {"PostToolUse"}` and `EVIDENCED_WRITER_FUNCTIONS = {"write_line", "write_lines"}` (lines 19-20), enforced by `assert_enabled_surface_subset()` (raises `EnabledSurfaceExceedsEvidenceError` on any superset attempt) and cross-checked against the schema-declared vocabulary in `agent-orchestration/hook-events.yaml` by `assert_evidenced_events_are_schema_valid()`.
- `assert_monitoring_writer_landed()` (`tools/agent_replay_codex/entry_criterion.py:19-47`) was run directly (not just via pytest) and **passed with no exception** — confirms `tools/agent-monitoring/writer.py` is importable and exposes both `write_line`/`write_lines` as callables.
- Full related test suites (`tests/agent_replay_codex/` + `tests/agent_codex_pilot_guardrails/`, the "Replay and pilot guardrail suites" scope named in `docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_response_codex.md:59`) were run: **61 passed, 5 skipped — exact match of the ticket's expected count.**

5 skipped tests, individually enumerated, all consent-gated (expected/by-design, none genuinely broken):
1. `tests/agent_replay_codex/test_containment_real_process.py::test_real_invocation_produces_zero_tickets_or_monitoring_diff`
2. `tests/agent_replay_codex/test_no_production_hook_invocation.py::test_committed_codex_config_byte_identical_across_real_invocation`
3. `tests/agent_replay_codex/test_phase_parity.py::test_codex_execution_path_matches_python_runner_output`
4. `tests/agent_replay_codex/test_pre_post_snapshot.py::test_ac_explicit_pre_post_snapshot_around_real_invocation`
5. `tests/agent_replay_codex/test_shadow_mode_comparison.py::test_n1_comparison_against_existing_fixture`

All 5 carry the identical skip reason string: `"real Codex invocation requires CODEX_REPLAY_PARITY_LIVE_CONSENT=1 (not set) — skipping, not failing"`. Each test's own skip condition is a direct `pytest.skip` gated on the `CODEX_REPLAY_PARITY_LIVE_CONSENT` env var, matching `consent_gate.py`'s own gate exactly — these are structurally consent-gated, not incidentally skipped, and none indicate broken functionality.

Additionally verified: `tools/agent_replay_codex/provenance_check.py::assert_no_codex_provider_writes()` is a read-only structural invariant check (never writes) confirming no record in `runs.jsonl`/`events.jsonl`/`tools.jsonl` has `provider == "codex"`; its corresponding test `test_real_monitoring_corpus_has_zero_codex_provider_records` passed against the real corpus.

### AC4 — zero real live Codex pilot executions have occurred

Confirmed structurally, not just asserted. `test_real_monitoring_corpus_has_zero_codex_provider_records` passed against the real `agent-monitoring/*.jsonl` corpus, and the 5 skipped tests above (all requiring `CODEX_REPLAY_PARITY_LIVE_CONSENT=1`, which is not set in this or any prior recorded environment) are the only tests in the suite that would exercise a real Codex invocation. No live pilot has run; the replay/live boundary is proven structurally and via tests only, exactly as this ticket's Out of Scope states it should be (no live pilot execution is attempted or claimed here).

### AC5 — TCK-20260721-MONITORING-WRITER-UNIFICATION status mismatch flagged, not fixed

Confirmed present, and explicitly **not fixed as part of this ticket** (per this ticket's own Out of Scope). Verified directly: `tickets/done/TCK-20260721-MONITORING-WRITER-UNIFICATION.md` has frontmatter `status: active` (line 2) and body `phase: open` (line 7) and `## Status` / `OPEN` (lines 17-18), despite living in `tickets/done/`, having a fully-filled `## Completion Summary` (line 241 onward), and `tickets/working_log.csv:1118` recording it as `DONE` with a stored-artifacts path. This is a known, separately-tracked doc-hygiene issue (ticket-file status/phase/body fields never updated to closed values when the ticket was moved to `done/`) and is intentionally out of scope for this confirmation ticket — it should be handled as its own hotfix.

### Conclusion

The Phase 0 prerequisite (provider-neutral execution identity, shared monitoring writer, stable replay/live boundary) is genuinely in place: the execution-identity model is documented and actually written into every `tools.jsonl` record; `writer.py` is verified (by grep and by dedicated tests) as the sole append path across all 3 call sites; the Codex pilot surface is correctly restricted by both the consent gate and the evidenced-surface guard, with `assert_monitoring_writer_landed()` passing directly and the full related suite at the expected 61 passed / 5 skipped, all 5 skips consent-gated by design; and no live Codex pilot execution has ever occurred, with that boundary proven structurally/via tests only. Later phase work (the context-efficient retrieval epic) may proceed on top of this prerequisite. The one known adjacent issue — TCK-20260721-MONITORING-WRITER-UNIFICATION's own ticket-file status/phase mismatch — is noted but explicitly not remediated here.

## Test Summary

Verification-only ticket; no new tests were written (none were needed — this ticket confirms existing coverage, it does not change behavior).

Tests run directly, all passing, confirming Phase 0 prerequisite state:
- `tests/agent_replay_codex/` + `tests/agent_codex_pilot_guardrails/` (full directories): **61 passed, 5 skipped** — matches the ticket's expected count exactly. All 5 skips are consent-gated (`CODEX_REPLAY_PARITY_LIVE_CONSENT` unset), none broken (enumerated above).
- Narrower targeted run also performed for direct evidence on writer/hook/consent modules specifically (`tests/agent_codex_pilot_guardrails/test_enabled_surface.py`, `tests/tools/test_post_tool_hook.py`, `tests/tools/test_monitoring_writer_lockfile_candidate.py`, `tests/tools/test_monitoring_writer_single_source.py`, `tests/tools/test_monitoring_writer.py`, `tests/agent_replay_codex/test_consent_gate.py`, `tests/agent_replay_codex/test_monitoring_provenance.py`, `tests/agent_replay_codex/test_entry_criterion.py`): **37 passed, 0 skipped**.
- `assert_monitoring_writer_landed()` invoked directly via a one-off Python call (not through pytest): passed with no exception raised.

## Files Changed
- `tickets/inprogress/TCK-20260728-PHASE0-PREREQ-CONFIRMATION.md` (this file only — confirmation record, no production code changed)

## Completion Summary

Confirmed the Phase 0 prerequisite for the context-efficient retrieval epic is satisfied. Verified with direct file:line evidence that `post_tool_hook.py:84-86` writes `execution_id`/`provider`/`ticket_id` into every `tools.jsonl` record per the documented model (`docs/ai/monitoring_writer_decision.md` §2, consumed by `docs/architecture/agent_orchestration_contract.md`); confirmed by grep and passing tests that `writer.py`'s `write_line`/`write_lines` is the sole append path for `post_tool_hook.py`, `record_run.py`, and `record_events.py`; ran `assert_monitoring_writer_landed()` directly (passed) and the full replay/pilot-guardrail test suites (`tests/agent_replay_codex/` + `tests/agent_codex_pilot_guardrails/`), getting the expected 61 passed / 5 skipped, with all 5 skips individually enumerated and classified as consent-gated-by-design (none genuinely broken). Explicitly flagged, but did not fix, `TCK-20260721-MONITORING-WRITER-UNIFICATION`'s own ticket-file status/phase mismatch as a separately-tracked doc-hygiene issue. No code was changed; this is a read-only verification ticket.
