---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-CODEX-PILOT-EXECUTOR
artifact_type: test_plan
---

# Test Plan — TCK-20260731-CODEX-PILOT-EXECUTOR

## Test Layout

Add `tests/agent_codex_pilot_executor/` with a session-level autouse safety fixture equivalent to
the adapter suite's guard.  It snapshots real `agent-monitoring/{runs,events,tools}.jsonl`, the
committed `.codex/config.toml`, and the real ticket snapshot before the suite and asserts all are
unchanged at teardown.  Every fixture root must be `tmp_path`-rooted.

The suite must use a fixed valid ticket ID, a fixed valid `codex-<ticket>-<ms>-<hex>` execution
ID, fixed timestamps, a copied captured PostToolUse payload, and a minimal scratch ticket tree.
It must never use `pilot_requests/` or `agent-monitoring/` from the repository as a target.

## New Tests Required

1. **Structural containment.** AST-scan every executor Python file: no `subprocess` import/call,
   `os.system`, `codex` invocation string, replay-invoker import/load, config-toggle import,
   config write, or CLI entry point.  Assert the committed Codex config remains hook-free.
2. **Scratch-root guard.** Refuse the repository root, real monitoring directory, a symlink/path
   escape, and any requested output outside the injected scratch root before manifest parsing,
   claim creation, or writer invocation.  Spy on writer/adapter to prove zero calls.
3. **Preflight ordering.** Parametrize traversal-shaped ticket ID, missing request, malformed request, ticket mismatch,
   invalid identity, and widened surface.  Each outcome exposes a distinct refusal reason and
   leaves scratch claims and all three scratch JSONL files absent/unchanged.
4. **Atomic claim.** Two concurrent attempts for the same ticket (including both `codex` and a
   same-provider second attempt) yield exactly one acquired unfinished claim.  A different ticket
   may acquire independently.  A pre-existing unfinished claim always refuses.  This test must
   exercise actual multiprocessing locking, including racing replacement of an existing terminal marker, not a mock-only branch.
   Hold an owner beyond the former stale-lock interval and prove a contender cannot enter until
   explicit release or owner process exit; no age-based lock-file deletion is permitted.
5. **Recovery.** Inject failure in each lifecycle append/proof boundary.  Verify no ambiguous
   active claim remains; the selected terminal-failed marker/deletion behavior is exact and a
   subsequent attempt follows the documented recovery rule. Terminalization with a mismatched
   execution ID must refuse and preserve the marker. Assert no partial suffix is called
   a successful lifecycle.
6. **Coherent synthetic lifecycle.** Against one scratch root, assert exactly one terminal run,
   ordered events, and one adapter-generated tools row.  Check all records have identical
   `run_id`, `ticket_id`, `provider="codex"`, and `execution_id`; tool `seq` references the
   PostToolUse event; the tool row is redacted and adapter metadata does not leak.
7. **Writer/component reuse.** Spy or identity-test that the executor invokes the shared writer
   through the existing writer bridge / `write_line` and `write_lines`, uses adapter record
   construction for the tool row, uses guardrail surface and baseline functions, and does not
   define a duplicate append/redaction/identity implementation.
8. **Prefix and exact-suffix proof.** Start with distinct pre-existing lines in all three files.
   Successful simulation accepts unchanged prefixes and precisely the declared ordered suffixes.
   Mutating, deleting, reordering, or inserting a historical line fails.  An extra appended row
   also fails the exact-suffix assertion.
9. **Dashboard ingestion.** Build a `DashboardCache(repo_root=scratch_root)` after the synthetic
   lifecycle.  Assert `get_runs(provider="codex", execution_id=...)`, `get_run(run_id)`, and
   `get_timeline(run_id)` expose the run and ordered events/tool attachment.  A tool-only scratch
   corpus must not be accepted as a completed, dashboard-visible run.
10. **Documentation regression.** Assert `docs/ai/monitoring_writer_decision.md` names
    identity-less pre-pilot records, scratch-only executor/claim semantics, exact prefix proof,
    and the still-separate human approval for a real pilot.

## Existing Regression Surface

- `tests/agent_codex_pilot_guardrails/` — request, surface, baseline, and no-live-path behavior.
- `tests/agent_codex_posttool_adapter/` — payload, identity, redaction, shared writer bridge,
  gated scratch append, and no-live wiring.
- `tests/agent_codex_runtime_shadow/` and `tests/agent_replay_codex/` — remain non-live and
  preserve their existing containment contracts.
- `tests/tools/test_monitoring_writer.py`, `tests/tools/test_agent_monitoring_manifest.py`, and
  `tests/tools/test_agent_ops_dashboard_ingest.py` — shared writing, prefix, and reader behavior.

## Scoped Commands

```bash
.venv/bin/python -m pytest -q \
  tests/agent_codex_pilot_executor \
  tests/agent_codex_pilot_guardrails \
  tests/agent_codex_posttool_adapter \
  tests/agent_codex_runtime_shadow \
  tests/agent_replay_codex \
  tests/tools/test_monitoring_writer.py \
  tests/tools/test_agent_monitoring_manifest.py \
  tests/tools/test_agent_ops_dashboard_ingest.py
```

Run the executor package's AST containment test last as a deliberate final backstop.  The formerly
stale real-corpus provider-count assertion was repaired independently in
`TCK-20260801-PROVIDER-COVERAGE-TEST-STALE`; do not absorb that unrelated guardrail edit into
this ticket.

## Acceptance-Criteria Coverage

| Ticket acceptance criterion | Tests |
| --- | --- |
| Scratch-only and no live/config/subprocess path | 1–2, suite autouse guard |
| Deterministic preflight refusal | 2–3 |
| Atomic exclusive claim and recovery | 4–5 |
| Coherent provider-attributed lifecycle and dashboard visibility | 6, 9 |
| Prefix preservation / ordered declared appends | 5, 8 |
| Durable policy decision and separate human gate | 10 |
