---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PROOF
phase: done
date: 2026-07-21
tags: [ai, workflows, agent-monitoring, process-improvement]
---

# TCK-20260721-CODEX-REPLAY-PROOF

## Title
Build a replay-only proof that a Codex slice can run against recorded fixtures

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
A replay-fixture specification and a replay runner/adapter proof demonstrating that an initial Codex slice (e.g. implement-ticket) can execute against recorded Claude workflow fixtures without editing tickets, invoking production hooks, or appending monitoring records. The "no production hooks" requirement is unconditional — including from a sandboxed or isolated working directory — per the source plan's exit-gate wording and Codex's 2026-07-21 ticket-batch review; a fake/no-op recording and hook boundary is injected in place of the real scripts. The fixture format must be sufficient to actually replay workflow phase logic (recorded phase inputs/outputs/transitions), not only the truncated-summary monitoring telemetry in runs.jsonl/events.jsonl/tools.jsonl. Last child in the sequence, depending on the capability matrix, monitoring/writer decision, and contract ADR child tickets.

## Scope
- This ticket may create only isolated contract, replay, fixture, diagnostic, or decision-record work. It must not modify production Claude/Codex workflows, hooks, monitoring writers, live ticket artifacts, or the shared monitoring JSONL corpus.
- Define a versioned replay-fixture envelope sufficient for deterministic workflow replay — the field-for-field runs.jsonl/events.jsonl/tools.jsonl monitoring projection alone is not sufficient (its summary/input_summary fields are truncated to 200/120 chars and do not carry full phase inputs, decisions, or outputs); the envelope must additionally carry the recorded workflow phase input/output/transition data actually needed to replay the implement-ticket slice. At least one real recorded fixture set checked in as an example.
- Build a replay runner/adapter proof that executes the implement-ticket slice against recorded fixtures. The proof must never execute record_run.py, record_events.py, post_tool_hook.py, or pre_tool_hook.py — including via an isolated/sandboxed working directory — this is an unconditional exit-gate requirement, not an implementation detail left to this ticket's own interpretation. Inject a fake/no-op recording and hook boundary in their place.
- The replay runner fails clearly (not silently, not with a best-effort partial replay) when a required fixture field is absent from a given fixture set.
- Evaluate the replay proof's fixture envelope shape against the contract representation decided by TCK-20260721-ORCHESTRATION-CONTRACT-ADR.

## Out of Scope
- Creating any provider-runtime implementation ticket — blocked until all 5 discovery outputs are complete, evidence-backed, and explicitly approved (see parent epic TCK-20260721-PROVIDER-AGNOSTIC-EPIC).
- No implementation of a production Codex adapter — this is a replay-only proof against recorded fixtures.
- Blocked from starting substantive proof work until TCK-20260721-CODEX-CAPABILITY-MATRIX, TCK-20260721-MONITORING-WRITER-DECISION, and TCK-20260721-ORCHESTRATION-CONTRACT-ADR land.

## Acceptance Criteria
- [x] A replay-fixture specification document exists defining a versioned fixture envelope sufficient for deterministic workflow replay — including recorded workflow phase input/output/transition data, not only the field-for-field runs.jsonl/events.jsonl/tools.jsonl telemetry projection (whose summary/input_summary fields are truncated to 200/120 chars) — with at least one real recorded fixture set (from an actual implement-ticket run) checked in as an example.
- [x] A replay runner/adapter script executes the implement-ticket slice against the recorded fixtures and completes, without invoking record_run.py, record_events.py, post_tool_hook.py, or pre_tool_hook.py at any point during the run, including from an isolated/sandboxed working directory — verified by process-level evidence (e.g. no subprocess/import call to those scripts exists anywhere in the replay runner's own code path), not merely by output-diffing. A fake/no-op recording and hook boundary is injected in their place.
- [x] A test (following test_post_tool_hook.py's tmp_path-isolated-cwd subprocess pattern for its isolation technique only, not as license to invoke the real hook scripts) snapshots tickets/** and agent-monitoring/*.jsonl before and after the replay run and asserts byte-for-byte no diff — zero ticket edits, zero monitoring-corpus appends.
- [x] The replay runner fails clearly, not silently, when a required fixture field is absent from a given fixture set — no partial/best-effort replay that masks missing data.
- [x] The replay proof's fixture envelope shape is evaluated against the contract representation decided by TCK-20260721-ORCHESTRATION-CONTRACT-ADR (not an ad hoc format invented in this ticket) — if that ADR is not yet approved when this ticket starts, this ticket is blocked.

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-CODEX-CAPABILITY-MATRIX
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260720-MONITORING-PIPELINE-BUGFIXES

## Related Docs
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_ticket_handoff_codex.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/pre_tool_hook.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tests/tools/test_post_tool_hook.py
- tests/tools/test_monitoring_bypass_fix.py
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- src/engine/replay_manager.py
- src/engine/replay_buffer.py
- src/engine/replay_sink.py

## Assumptions / Open Questions
- No prior art exists in this repo for recording/replaying Claude agent-workflow executions — the only "replay" precedent (src/engine/replay_manager.py etc.) is the simulation engine's deterministic state replay, a different domain entirely (game-tick state, not orchestrator/agent-call records).
- .claude/workflows/*.js files have no JS test runner in this repo — if the replay adapter needs to exercise workflow-phase logic, it can only be verified via source-text pattern matching or full subprocess execution.
- "Must not invoke production hooks" is resolved as an unconditional prohibition, per Codex's 2026-07-21 ticket-batch review: test_post_tool_hook.py's sandboxed/isolated-cwd invocation exists to test the hook script itself (a different purpose) and is not license to relax this ticket's exit-gate requirement — the replay proof injects fake/no-op recording and hook boundaries instead of invoking the real scripts under any condition, sandboxed or not.
- The fixture envelope must carry actual recorded phase input/output/transition data, not only runs.jsonl/events.jsonl/tools.jsonl's truncated-summary telemetry fields (summary capped at 200 chars, input_summary at 120 chars per docs/agent-monitoring/schema.md) — those fields alone are insufficient for deterministic replay, per Codex's 2026-07-21 review.
- Building a Codex adapter proof before TCK-20260721-CODEX-CAPABILITY-MATRIX is approved risks assuming Codex hook/lifecycle capabilities that haven't been verified against current official documentation.
- Depends on TCK-20260721-CODEX-CAPABILITY-MATRIX, TCK-20260721-MONITORING-WRITER-DECISION, and TCK-20260721-ORCHESTRATION-CONTRACT-ADR landing first — last in the sequence per the handoff doc's explicit ordering.

## Implementation Notes
Implemented the plan's 6 steps exactly, in order, against the real `TCK-20260721-ORCHESTRATION-
CONTRACT-ADR` fixture source (`tickets/done/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.md`,
`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/{investigation,plan,test_plan}.md`, and
the real `agent-monitoring/events.jsonl`/`runs.jsonl` rows for that `run_id`, all read-only).

1. `docs/ai/replay_fixture_spec.md` — versioned envelope spec (`version`/`source`/`phases`),
   truncation-insufficiency rationale citing `docs/agent-monitoring/schema.md`'s 200/120-char caps,
   an AC #5 subsection evaluating the envelope against
   `docs/architecture/agent_orchestration_contract.md`'s Contract Representation decision (YAML data
   + hand-written, not generated, validator — explicitly distinguished from the ADR's own future
   `agent-orchestration/contract.yaml`), and explicit unconditional-containment and fail-closed law
   subsections. `python3 tools/validate_frontmatter.py` passes.
2. `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` — real fixture, seq
   1-4 (Scope/Investigate/Plan/Review), all real `status: ok`. Scope's `input.tags` matches the real
   ticket frontmatter tags (`[ai, workflows, process-improvement]`, all pre-registered); Plan/Review
   `input.plan_path` points at the real, permanent `stored_artifacts/.../plan.md` file (confirmed no
   `## Unresolved Questions` heading exists in it) rather than embedding a copy. Review's
   `output.verdict`/`violations` are reconstructed from the real seq=4 event's `status`/`summary`,
   disclosed via an in-file YAML comment per the plan's explicit provenance requirement — this data
   was never persisted as full `REVIEW_SCHEMA` JSON anywhere.
3. `tools/agent_replay/fixture_envelope.py` (+ `tools/agent_replay/__init__.py`) —
   `FixtureValidationError`, `PhaseEntry`/`FixtureEnvelope` dataclasses, `load_fixture()`. Raises
   naming the exact field and phase index on any missing/null required field; an empty dict (`{}`)
   for `input`/`output` is treated as a valid recorded value (distinct from absent/null), needed for
   Investigate's no-branch-logic phase entry.
4. `tools/agent_replay/runner.py` — imports `tag_registry.check_tags_registered` and
   `gate_checks.plan_gate_static.plan_has_unresolved_questions_heading` read-only via the same
   `sys.path.insert(0, 'tools')` convention `implement-ticket.js` itself uses; hand-mirrors the 4
   inline branch decisions (Scope conflicts, Scope tag-check, Plan unresolved-questions, Review
   verdict) with a comment citing the mirrored `implement-ticket.js` line region for each, following
   the `classifyChecklistFailure` "kept in sync by hand" precedent. `_fake_write_monitoring` and
   `_fake_hook_boundary` are pure in-memory no-ops. `replay_slice()` re-derives the Scope tag-check
   from the real function call (never trusts a fixture-precomputed transition), reads the real
   `plan.md` file on disk for the Plan-phase check, and stops at the first non-`ok` outcome.
5. `tests/agent_replay/test_no_mutation_snapshot.py` — snapshots `tickets/**` +
   `agent-monitoring/*.jsonl` before/after `replay_slice()` against the real repo tree (never
   `tmp_path`). See Deviations below re: the dirty-tree branch actually exercised in this repo.
6. `tests/agent_replay/test_runner_no_forbidden_calls.py` — AST scan for forbidden
   imports/`importlib.import_module`/subprocess-and-os.system-call-argument literals, **widened per
   the architecture-review advisory** to also scan every `ast.Constant` string node in the file (not
   just call-argument-scoped ones), plus the positive-control assertion that both fakes exist and
   are actually called inside `replay_slice`'s own function body.

Also added, per the plan's Step verify sections: `tests/agent_replay/test_fixture_envelope.py`
(schema validation, real-fixture anti-drift check, 5-way parametrized fail-closed test),
`tests/agent_replay/test_fixture_spec_doc.py` (doc-content citation checks), and
`tests/agent_replay/test_runner.py` (real-fixture completion + one short-circuit test per branch).

## Test Summary
- `.venv/bin/python -m pytest tests/agent_replay/ -v` — 25 passed.
- `.venv/bin/python -m pytest tests/tools/test_plan_gate_static.py tests/tools/test_tag_registry.py tests/tools/test_monitoring_bypass_fix.py tests/tools/test_post_tool_hook.py -q` — 42 passed (regression surface: proves the real modules this runner imports read-only, and the two static-source-text precedent test files, are unaffected).
- `python3 tools/validate_frontmatter.py docs/ai/replay_fixture_spec.md` — exit 0.
- Full test suite not run (scoped per project testing rule).

## Files Changed
- `docs/ai/replay_fixture_spec.md` (new)
- `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` (new)
- `tools/agent_replay/__init__.py` (new)
- `tools/agent_replay/fixture_envelope.py` (new)
- `tools/agent_replay/runner.py` (new)
- `tests/agent_replay/__init__.py` (new)
- `tests/agent_replay/test_fixture_envelope.py` (new)
- `tests/agent_replay/test_fixture_spec_doc.py` (new)
- `tests/agent_replay/test_runner.py` (new)
- `tests/agent_replay/test_no_mutation_snapshot.py` (new)
- `tests/agent_replay/test_runner_no_forbidden_calls.py` (new)

## Completion Summary
Built the replay-only proof exactly per plan: a versioned fixture-envelope spec doc, one real
fixture derived read-only from `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`'s permanent records, a
fail-closed loader, and a replay runner that re-executes the real Scope/Plan tag-registry and
unresolved-questions gate checks plus hand-mirrored Scope-conflicts/Review-verdict branches against
that fixture — completing with `final_status == 'ok'`, matching the real recorded outcome. Zero
production code (`tools/gate_checks/*.py`, `tools/tag_registry.py`, `.claude/workflows/*.js`,
`tools/agent-monitoring/*.py`) was touched; the four forbidden monitoring/hook scripts are never
imported or subprocessed anywhere in `tools/agent_replay/`, mechanically proven by an AST scan
(widened per architecture-review advisory to scan every string constant in the file, not just
call-argument-scoped ones) and independently by a no-mutation content-hash/porcelain snapshot test
against the real repo tree. All 5 acceptance criteria are met and mapped 1:1 to a passing test (see
`stored_artifacts/TCK-20260721-CODEX-REPLAY-PROOF/plan.md`'s Acceptance Criteria Map). No
`src/` or `tools/agent-monitoring/` runtime behavior changed — this ticket adds new, isolated
docs/tools/tests files only.
