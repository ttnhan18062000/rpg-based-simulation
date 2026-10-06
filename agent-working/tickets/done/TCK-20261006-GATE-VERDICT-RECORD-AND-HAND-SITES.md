---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES
phase: done
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES

## Title
A gate_verdicts record, written by the gate CLIs that hand closures run

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER`. Add the record and its writer, then emit from the gate CLIs a
hand closure actually runs. Today those print PASS/FAIL to stdout and nothing keeps it. Hand closures are 36 of
the 37 W41 runs that carry `execution_mode`.

## Scope
- **The `gate_verdicts` shard family.** It sits next to runs, events and tools in
  `data/YYYY-Www/<identifier>.gate_verdicts.jsonl`, through `monitoring_shard_paths.py` and the existing writer.
  Fields:
  - identity: `ts`, `gate_verdict_id` (unique), `run_id` (nullable), `execution_id`, `session_id`,
    `execution_mode` (pipeline|workflow|hand), `ticket_id`
  - the gate: `gate_id` (gate-policy.yaml `phase` + `check_module`/`check_function`, or an agent role; a CLI not
    in gate-policy gets a stable `cli:<module>` id), `gate_type`, `phase`
  - the verdict: `verdict` (the raw enum or PASS/FAIL), `blocking` (bool), `sub_results` (optional
    `{condition: PASS|FAIL|NA}`, e.g. the done-checker checklist)
  - the inputs: `inputs_ref` (`head_sha`, a hash of `files_changed` or cmd, and `stdout_sha` when attested)
- **Schema.** A section in `docs/agent-monitoring/schema.md`, plus `validate.py` coverage.
- **Emit sites.** All of them are hand-reachable:
  - `done_checker_static.py` CLI: verdict plus the per-condition `sub_results`
  - `post_native_run_check.py`
  - `doc_staleness_check.py` CLI
  - `plan_gate_static.py`, through a thin CLI entry point if it has none
  - `attest_gate.py`: persist the ATTEST line it already prints (gate, cmd, exit_code, stdout_sha; never the mac)
- **Opt out.** `--no-record`, plus an env guard so tests and scratch runs can switch it off. Fixture tests must not
  write into the real data root.
- **Session.** `session_id` resolves the same way `record_hand_orchestrated_closure.py` already does it.

## Out of Scope
- `implement-ticket.js` sites (child 2), outcomes and adjudication (child 3), and reporting (child 4).
- CI and the code-health ratchet.

## Acceptance Criteria
1. Running each listed CLI against a fixture ticket writes exactly one valid `gate_verdicts` row with
   `execution_mode`, `gate_id`, `verdict`, `blocking` and `inputs_ref` filled in. This holds for both a passing and
   a failing case.
2. A done-checker row carries the per-condition `sub_results` that the CLI printed.
3. A write failure (unwritable data root) leaves the CLI's exit code and output unchanged and prints one stderr
   warning.
4. `--no-record` or the env guard writes nothing. Existing tests of these CLIs do not write into
   `agent-working/agent-monitoring/data/`.
5. `validate.py` accepts the new rows and rejects one with `verdict` or `gate_id` missing. `schema.md` documents
   the family.
6. The scoped tests under `tests/tools/` for the touched modules are green.

## Related Tickets
- `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER` (parent)
- `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN`

## Related Docs
- `docs/agent-monitoring/schema.md`
- `agent-working/agent-orchestration/gate-policy.yaml`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES/` (plan, investigation, test_plan)

## Related Code Areas
- `tools/agent-monitoring/writer.py`, `monitoring_shard_paths.py`, `validate.py`,
  `record_hand_orchestrated_closure.py` (session resolution)
- `tools/gate_checks/done_checker_static.py` (CLI at :1504), `post_native_run_check.py`, `doc_staleness_check.py`,
  `plan_gate_static.py`, `attest_gate.py`

## Assumptions / Open Questions
- The per-identifier shard key (the branch) works for these rows the same way it does for tools rows.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

New module `tools/agent-monitoring/gate_verdicts.py`: `build_record`, `validate_record`, `record_gate_verdict` (never raises, one stderr warning on a failed write), `gate_id_for` (gate-policy.yaml id, else `cli:<module>`). Rows go through `writer.write_line` and `resolve_write_target("gate_verdicts")`, so the per-branch shard key and the `merge=union` glob apply.

Decisions made while building, each visible in the rows:
- `attest_gate.py` runs its wrapped command with `GATE_VERDICT_NO_RECORD=1`, so a gate CLI inside the wrapper does not write a second row for the same verdict; the wrapper's own row (mode `workflow`, `gate_type: attested_command`) carries gate, command hash, exit code and stdout hash, never the mac.
- `post_native_run_check.py` runs its three checkers with `GATE_VERDICT_EXECUTION_MODE=workflow`, so their rows are labelled as the native run's, not as a hand closure's.
- `plan_gate_static.py` gained a thin CLI (`--plan-path`, `--ticket-id`, exit 1 on unresolved questions).
- `doc_staleness_check.py` strips `--no-record` and `--execution-mode` from argv before its positional parse. `implement-ticket.js` now passes `--execution-mode pipeline` on its one invocation, so a pipeline run is not mislabelled `hand`; the rest of the pipeline sites stay with `TCK-20261006-GATE-VERDICT-PIPELINE-SITES`.
- `tests/conftest.py` sets `GATE_VERDICT_NO_RECORD=1` for every test.
- `validate.py` gained `--data-dir` and an error per invalid row.

## Test Summary
`tests/tools/test_gate_verdicts.py` (25 pass): record validity and uniqueness, each required field rejected when missing, gate_id from gate-policy, writer (one row, env guard, `enabled=False`, execution-mode env, unwritable root warns once and returns None, invalid row not written), every CLI site for a passing and a failing case (done_checker with per-condition `sub_results`, plan gate, post_native_run_check, doc_staleness, attest_gate), and `validate.check_gate_verdicts`.

Touched-module suites also green: `test_attest_gate`, `test_post_native_run_check`, `test_doc_staleness_check`, `test_doc_staleness_gate_wiring`, `test_plan_gate_static`, `test_done_checker_static`, `test_validate_agent_monitoring`, `test_monitoring_writer_single_source`, `tests/agent_orchestration_claude_adapter` (362 pass together with the new file). `python3 -m codebase.health check` in the scratch venv: 0 new, 0 worse. No `gate_verdicts` shard exists in the real data root after the runs.

## Files Changed
- `tools/agent-monitoring/gate_verdicts.py` (new), `tools/agent-monitoring/validate.py`
- `tools/gate_checks/done_checker_static.py`, `post_native_run_check.py`, `doc_staleness_check.py`, `plan_gate_static.py`, `attest_gate.py`
- `.claude/workflows/implement-ticket.js` (one flag on the doc-staleness invocation)
- `tests/conftest.py`, `tests/tools/test_gate_verdicts.py` (new)
- `docs/agent-monitoring/schema.md`

## Completion Summary
Closed 2026-10-06. All six acceptance criteria met: each listed CLI writes exactly one valid `gate_verdicts` row for a passing and a failing case (AC1), done-checker rows carry the printed per-condition `sub_results` (AC2), a write failure leaves exit code and output unchanged with one stderr warning (AC3), `--no-record` and the env guard write nothing and tests never reach the real data root (AC4), `validate.py` accepts valid rows and rejects one missing `verdict` or `gate_id`, and `schema.md` documents the family (AC5), scoped tests green (AC6). Not covered: `execution_id`/`run_id` stay null for a CLI run outside a recorded run, and the formal pipeline's other gate sites are child 4.
