---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation
`run_dedup.py` groups run rows by `(run_id, execution_id, start_ts)`; it does not group verdicts by ticket and gate, so it does not fit and was not reused.

Native verdict rows come from `attest_gate.py`, which had no ticket id, so a backstop FAIL could not be matched to the native PASS. Fixed by an optional `--ticket-id` that `shAttested` passes when the run has one. The backstop mapping is one pair (`done_checker_static` / `finalize_selfcheck`): the other native gates (`doc_staleness`, `plan_unresolved_questions`, `tag_check`, ...) are not re-run by the backstop, so a disagreement cannot be established for them.
