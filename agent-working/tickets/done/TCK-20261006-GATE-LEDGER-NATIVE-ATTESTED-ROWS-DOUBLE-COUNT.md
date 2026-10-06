---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-LEDGER-NATIVE-ATTESTED-ROWS-DOUBLE-COUNT
phase: done
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-LEDGER-NATIVE-ATTESTED-ROWS-DOUBLE-COUNT

## Title
On the native runtime, one gate run writes two gate_verdicts rows under two gate ids

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
This is a known gap stated in #371 (`7366d7985`). A gate behind `shAttested` in `.claude/workflows/implement-ticket.js`
writes two rows per run on the native runtime:
1. `attest_gate.py::_record`, with `gate_type: attested_command` and `gate_id` set to the attestation's gate name
   (e.g. `parity_touched_ledger`).
2. The pipeline-site row, written by `gate_verdicts.py record-batch`, under the gate-policy id
   (`gate_verdicts.policy_gate_id`).

`gate_ledger.py report` counts both. The result is double verdict counts, and one gate split across two rows under
different names. A block then a pass can also fail to pair up in outcome derivation, since the two rows have
different ids. The formal pipeline runs rarely (1 of 37 W41 runs), hence P3. It must be fixed before the first
native-pipeline week is read.

## Scope
- **The attested row is evidence, not a second verdict.**
  - The report and outcome derivation in `gate_ledger.py` count verdicts only from rows that are not
    `attested_command`.
  - `attested_command` rows stay in the ledger as the input trail. They link to their pipeline-site row through
    `inputs_ref.stdout_sha` and `execution_id`.
- **A pipeline-site row whose gate ran through `shAttested`** carries that attestation's `stdout_sha` in
  `inputs_ref`. The child-2 scope asked for this; check that it is wired.
- **An attested-only row has no pipeline-site row** when the run died before record-batch. It is reported under
  "attested, no verdict row" and never silently dropped.

## Out of Scope
- Renaming the attestation gate names. They are part of the MAC and the verifier.
- The hand path. Its CLIs write one row each already.

## Acceptance Criteria
1. With a fixture of one native run, 3 attested gates, and 3 matching pipeline-site rows, the report shows 3
   verdicts under gate-policy ids, not 6.
2. Fixture: an attested FAIL and its pipeline-site block, then on a re-run an attested PASS and its pipeline-site
   pass. Derivation gives exactly one `fixed_and_rerun`, on the gate-policy id.
3. An attested row with no matching pipeline-site row is listed under "attested, no verdict row".
4. Scoped `test_gate_ledger.py`, `test_gate_verdicts.py` and `test_attest_gate.py` pass.

## Related Tickets
- `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER` (parent epic, still OPEN)
- `TCK-20261006-GATE-VERDICT-PIPELINE-SITES`, `TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES` (both done)

## Related Docs
- `docs/agent-monitoring/schema.md` (the gate_verdicts section)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/gate_checks/attest_gate.py` (`_record`)
- `tools/agent-monitoring/gate_ledger.py` (report and derivation)
- `tools/agent-monitoring/gate_verdicts.py`
- `.claude/workflows/implement-ticket.js` (`shAttested` at :149, record-batch at :726)

## Assumptions / Open Questions
- None.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06 from origin/main `7366d7985`.

## Test Summary
`tests/tools/test_gate_ledger.py` (4 new in `TestAttestedRowsAreEvidence`): 3 attested gates plus 3 pipeline rows report 3 verdicts under policy ids; an attested FAIL/block then PASS/pass derives exactly one `fixed_and_rerun` on the policy id; an attested row with no pipeline row (or another ticket's) is listed and the `## Gates` section says so, including in a period with no verdicts. `test_gate_verdict_pipeline_sites.py` pins the JS wiring. Scoped `test_gate_ledger.py`, `test_gate_verdicts.py`, `test_attest_gate.py` and the implement-ticket tests pass (264, 10 skipped).

## Files Changed
- `tools/agent-monitoring/gate_ledger.py` (`_split` drops `attested_command` rows from verdicts, `attested_without_verdict`, `_attested_note`)
- `.claude/workflows/implement-ticket.js` (`pushStaticGate` writes natively too, `lastAttestedStdoutSha`, `pushGate` links `stdout_sha`)
- `tests/tools/test_gate_ledger.py`, `tests/tools/test_gate_verdict_pipeline_sites.py`
- `docs/agent-monitoring/schema.md`

## Completion Summary
Closed 2026-10-06. All four acceptance criteria met. The ticket's premise was half right: on current main a native static gate wrote only the attested row (`pushStaticGate` was a no-op natively), so the double count was a naming split, not two verdicts. I made `pushStaticGate` write the pipeline row natively too, linked to the attestation by `inputs_ref.stdout_sha`, and made the ledger count only non-attested rows; without the JS change the ledger change alone would have dropped every native static verdict. Link key is `stdout_sha` plus `ticket_id`: `attest_gate` rows carry no `execution_id`. Not run on a real native pipeline run, so the JS path is pinned by a source test only. Several attested gates have no pipeline site (e.g. `parity_touched_ledger`), so "attested, no verdict row" will list them on every native run.
