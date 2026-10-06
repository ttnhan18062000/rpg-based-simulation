---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES
phase: open
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES

## Title
A gate_verdicts record, written by the gate CLIs that hand closures run

## Status
OPEN

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
- None.

## Related Code Areas
- `tools/agent-monitoring/writer.py`, `monitoring_shard_paths.py`, `validate.py`,
  `record_hand_orchestrated_closure.py` (session resolution)
- `tools/gate_checks/done_checker_static.py` (CLI at :1504), `post_native_run_check.py`, `doc_staleness_check.py`,
  `plan_gate_static.py`, `attest_gate.py`

## Assumptions / Open Questions
- The per-identifier shard key (the branch) works for these rows the same way it does for tools rows.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

## Test Summary

## Files Changed

## Completion Summary
