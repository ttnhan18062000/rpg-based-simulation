
## RETRO-2026-W41: note stamped at 188 runs

<!-- retro-note runs=188 -->
**Addendum 2026-10-09 (agent-working-planner, cadence-triggered: 35 DONE runs since the last dated retro; the text above is left as written).**
The tables above were regenerated over 188 W41 runs on `agent-working-planner-next` (origin/main `f446a2bc8`, #459): 183 DONE (97%),
5 gate failures. `make agent-monitoring-validate`: OK, 2138 runs / 13842 events; 1 warning of 35 falls in W40+ (one DONE run without a
working_log row). The earlier notes carry no `retro-note` marker, so they stay verbatim; this is the first stamped entry.

- **What failed most: the native run, again, and now it is the costliest failure of the week.** The two new non-DONE runs are
  TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES, the vehicle for TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN.
  - `TAGS_NOT_REGISTERED` was the deliberate fail run (`wf_2b717fc9-c97`, Scope only): 294k tokens.
  - `WORKFLOW_ERROR` (`GATE_ATTESTATION_FAILED test_scope_coverage: wrong command`) killed the pass run (`wf_e2dc6921-bdd`) at
    Architecture-Verify: 926k tokens. Cause: the attested command was mangled in agent transport. Fixed by
    TCK-20261009-NATIVE-ATTESTED-COMMAND-TRANSPORT-LOSSY (#459); `--pytest-command` still rides the transport. The ticket was then hand-finished.
  - The Scope-only failure cost 7 agents, because the tag check runs after the scoper and the shell/monitoring dispatches.
    Unfiled: move the tag check before those dispatches if the next native attempt shows the same cost.
- **New finding: the gate ledger shows 31 unresolved blocking verdicts, all `Finalize:...run_finalize_selfcheck`** (10-07 had 0).
  Every ticket concerned is closed and merged. Breakdown:
  - 23 fail only on `precheck.*` conditions (`ticket_location`, `working_log_no_row_yet`, `frontmatter_valid`,
    `ticket_field_values_valid`). These are the post-close false fails noted on 10-06. The CLI's closed-ticket auto-detect
    (`check_ticket_finalized`) did not fire, so `--part both` ran and recorded a blocking FAIL.
  - 8 fail on finalize conditions (`registry_entry_regenerated` 5, `working_log_exactly_one_row` 5, `migration_complete` 3).
  - Later verdicts: 21 have none, 8 have only later FAILs, and 2 have a later PASS that the outcome derivation did not
    pick up.

  So the ledger's "unresolved" column now mostly measures the CLI's part selection, not missed gates. Until that changes, a
  real override cannot be told apart from noise.
  **Proposal (one ticket, hotfix-sized):** record the precheck part under its own gate_id (`run_static_precheck`) even
  inside `--part both`; find why `check_ticket_finalized` returns non-PASS on a just-closed ticket; and derive
  `fixed_and_rerun` when any later PASS exists for the same ticket and gate. Not filed yet; it waits on the owner's word.
- **What was slow:** no measured run is over 30 min (4 runs measured or declared, avg 10 min). Derived duration now covers 22
  of 182 hand closures (12%, up from 4% on 10-07), avg 27 min. Still too thin to read a trend; this stays with the time-gated
  hand-closure epic (after W42).
- **Paths:** all 69 standard·hand runs that carry the path fields omit Investigate, Plan, Review and Architecture-Verify
  (41 `batch_hand_close`). That is the 10-07 finding, now at 69 runs. Parity `unstated` is 27 of 44 skips, so hand closures
  still often skip Parity without a reason. The closure guard from #459 refuses Parity `ok` with no ledger change, but it
  does not require a `skip_reason`. Carry both to TCK-20261006-EPIC-TICKET-PATH-RECORD (after W42), and don't open a separate ticket.
- **Session layer:** `handover recovery` is the largest sampled manual action (15 of 19), and the owner tally is still 0 in
  every category. `session_role` is unresolved on 92 of 188 runs. `role_boundary` is live now (1 `message_class_mismatch`).
  Today's resume (this session) took one owner prompt ("continue as agent-working-planner") and no correction, because the
  handover note was current.
- **Spend proxy:** 22 of 1100 events scored (2%). Unchanged in kind; waits on the hand-closure cost child.
- **What worked (do not revert):** the remote-branch deletion rule held. Two sessions independently checked the same branch
  against #459's merged head, and the second delete failed safely rather than removing anything else. The batch-PR policy
  (7 tickets, one PR, review by comment) landed #459 without a re-review round. The handover-transit rule kept the bundle
  out of #459.
- **Measurement Watchlist:** the single row (TCK-20260924-DELIVERY-COST-MEASUREMENT) is still not checkable. It waits on
  TCK-20261006-HAND-CLOSURE-COST-ATTRIBUTION, which is gated on W42. The row is unchanged.
