---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION
phase: done
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION

## Title
Record what followed a blocking gate verdict, and whether the verdict was right

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER`. A verdict row alone cannot measure precision. Two more things
are needed:
- what happened next: fixed and re-run, overridden, stopped, or re-run with no change;
- a judgement of whether the block, or the pass, was right.

Neither is recorded today. 27 NEEDS_HUMAN_INPUT rows have no resolution. Overrides appear only in retro prose.
Re-runs exist only implicitly, as `run_dedup.py` checkpoint groups.

## Scope
- **Two append-only row kinds in the `gate_verdicts` family**, keyed by `gate_verdict_id`. Edits in place are not
  allowed.
  - `outcome`: `accepted` | `fixed_and_rerun` | `rerun_no_change` | `overridden` | `stopped`, plus an optional
    `followup_verdict_id` and a `note`.
  - `adjudication`: `true_block` | `false_block` | `true_pass` | `false_pass` | `unknown`, plus `adjudicated_by`
    (a role or `owner`) and a `reason`.
- **A CLI** `tools/agent-monitoring/gate_ledger.py` with `outcome`, `adjudicate` and `list --unresolved`. A
  session calls it when it overrides or stops on a gate, or when the owner rules.
- **Derived outcomes, no hand entry needed:**
  - a blocking row followed, on the same ticket and gate, by a later passing row becomes `fixed_and_rerun`;
  - a blocking row followed by an identical blocking verdict with the same `inputs_ref` becomes `rerun_no_change`.

  Reuse `run_dedup.py` grouping where it fits.
- **The native backstop.** When `post_native_run_check.py` disagrees with a native PASS for the same gate and
  ticket, it writes `adjudication: false_pass, adjudicated_by: orchestrator-backstop`. This is the one automatic
  adjudication, because the attestation design names that backstop as authoritative.
- **Docs.** A line in CLAUDE.md "After Work" and in `docs/guides/delivery_process.md`: when you override or stop on
  a gate, record it with `gate_ledger.py outcome`. The existing rule against editing an artifact to pass a gate is
  unchanged; recording an override is not a way around it.

## Out of Scope
- Backfilling outcomes for historical runs. History would be invented.
- Any automatic adjudication other than the native-versus-backstop disagreement.

## Acceptance Criteria
1. `gate_ledger.py outcome` and `adjudicate` append valid rows. An unknown `gate_verdict_id` is rejected with a
   non-zero exit.
2. Derivation on fixtures:
   - block, then pass on the same ticket and gate gives `fixed_and_rerun`;
   - block, then a block with the same `inputs_ref` gives `rerun_no_change`;
   - a lone block gives no derived outcome and shows in `list --unresolved`.
3. A fixture where the native verdict is PASS and the backstop says FAIL writes exactly one `false_pass`
   adjudication.
4. A later adjudication for the same verdict supersedes the earlier one in reads (latest wins), and both rows are
   kept.
5. CLAUDE.md and `delivery_process.md` carry the one-line instruction. Scoped tests are green.

## Related Tickets
- `TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES` (depends on it)
- `TCK-20260915-DUPLICATE-RUN-RECORDS`, `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN`

## Related Docs
- `docs/agent-monitoring/schema.md`, `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md` (:54-61)

## Related Code Areas
- `tools/agent-monitoring/run_dedup.py`, new `tools/agent-monitoring/gate_ledger.py`
- `tools/gate_checks/post_native_run_check.py`

## Assumptions / Open Questions
- `true_pass` is recorded only when someone checked a pass on purpose. Unchecked passes stay unadjudicated; they
  are not assumed true.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

New `tools/agent-monitoring/gate_ledger.py` (CLI `outcome | adjudicate | list [--unresolved]`, plus `load_rows`, `derive_outcomes`, `resolved_view`, `unresolved`, `record_outcome`, `record_adjudication`, `backstop_adjudicate`). `outcome` and `adjudication` rows share the `gate_verdicts` shard family and are told apart by `row_kind`; `gate_verdicts.validate_record` dispatches on it, so `validate.py` checks them unchanged.

Decisions, each visible in the code:
- Derivation is read-time and never stored: only the next verdict on the same (ticket, gate) is compared. A block followed by a block with different inputs gets no derived outcome (not guessed).
- `run_dedup.py` was not reused: it groups run rows by execution identity, not verdicts by ticket and gate.
- The backstop needs the native verdict to carry its ticket, so `attest_gate.py` takes `--ticket-id` and `implement-ticket.js` passes it. The mapping is one entry, `done_checker_static` against the native `finalize_selfcheck`; no other native gate has a backstop counterpart, so none is adjudicated automatically.
- `backstop_adjudicate` writes at most one `false_pass` per native verdict and honours `GATE_VERDICT_NO_RECORD`.
- CLAUDE.md "After Work" gained one bullet, added with the owner's approval (asked with the literal text on 2026-10-06); `delivery_process.md` and `schema.md` carry the detail.

## Test Summary
`tests/tools/test_gate_ledger.py` (17 pass): block-then-pass gives `fixed_and_rerun`; block-then-same-inputs-block gives `rerun_no_change`; different inputs, other tickets and other gates give no derived outcome; a lone block is in `list --unresolved`; explicit beats derived; unknown id refused (library and CLI exit 2); invalid values refused; latest adjudication wins with both rows kept; native PASS plus backstop FAIL writes exactly one `false_pass` (a repeat writes none, hand rows and other tickets are untouched); the env guard disables it; `post_native_run_check.run` calls it once per failed check. `test_attest_gate.py` gained a check that `shAttested` passes the ticket id (14 pass there, node harness defines `ticketId`).

Touched-module suites green together (338 pass): gate_ledger, gate_verdicts, attest_gate, post_native_run_check, doc_staleness wiring, done_checker_static, validate_agent_monitoring, writer single-source, native refusal, claude_adapter conformance.

## Files Changed
- `tools/agent-monitoring/gate_ledger.py` (new), `tools/agent-monitoring/gate_verdicts.py`
- `tools/gate_checks/post_native_run_check.py`, `tools/gate_checks/attest_gate.py`, `.claude/workflows/implement-ticket.js`
- `tests/tools/test_gate_ledger.py` (new), `tests/tools/test_attest_gate.py`
- `CLAUDE.md`, `docs/guides/delivery_process.md`, `docs/agent-monitoring/schema.md`

## Completion Summary
Closed 2026-10-06. All five acceptance criteria met: `outcome` and `adjudicate` append valid rows and an unknown `gate_verdict_id` exits 2 (AC1); derivation on fixtures gives `fixed_and_rerun`, `rerun_no_change`, and an unresolved lone block (AC2); a native PASS contradicted by the backstop writes exactly one `false_pass` (AC3); the latest adjudication wins and both rows are kept (AC4); CLAUDE.md and `delivery_process.md` carry the instruction and scoped tests are green (AC5). Not done: any other automatic adjudication, and backfill of history (both out of scope). Until a native run's rows exist in a real week, the backstop path is proven on fixtures only.
