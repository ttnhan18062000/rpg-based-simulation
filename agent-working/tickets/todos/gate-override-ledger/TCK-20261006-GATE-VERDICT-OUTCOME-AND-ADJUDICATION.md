---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION
phase: open
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION

## Title
Record what followed a blocking gate verdict, and whether the verdict was right

## Status
OPEN

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

## Test Summary

## Files Changed

## Completion Summary
