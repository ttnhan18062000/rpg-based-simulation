---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-COST-PROXY-EPIC-TICKETS
phase: done
date: 2026-09-04
tags: [ai, agent-monitoring]
---

# TCK-20260904-COST-PROXY-EPIC-TICKETS

## Title
Extend cost proxy scoring to epic and ticket-creation workflows

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Only implement-ticket.js currently emits cost_proxy_score/tool_call_count; implement-epic.js and create-tickets.js report null for both, and the proposal framed this as simply wiring the existing tools/agent-monitoring/cost_proxy.py computation into two more call sites — "the same computation, two more call sites, no new logic." Investigation found this significantly understates the real work: implement-epic.js and create-tickets.js never register a .claude/current_run sidecar per agent() call in the first place, which is documented as a DELIBERATE prior exclusion from TCK-20260719-COST-PROXY-WRITE-PATH (with an existing regression test asserting the no-sidecar behavior). This ticket is therefore a deliberate scope reversal of that earlier decision — real work requires adding sidecar-writing calls at ~9 call sites across the two files plus widening record_events.py's hardcoded workflow filter, not just relaxing one filter.

## Scope
- Add orchestrator-side sidecar-writing bash() calls (mirroring implement-ticket.js's writeSidecar(seq, phase, agent) pattern) at every agent() call site in implement-epic.js (lines 86, 287, 316, 353, 796, 818) and create-tickets.js (lines 131, 156, 439)
- Handle implement-epic.js's 2 non-standard fire-and-forget record_events.py calls (hardcoded seq:1, lines 189, 215) case-by-case since they don't fit a straight copy of the writeSidecar(seq) pattern
- Widen tools/agent-monitoring/record_events.py::compute_tool_stats()'s hardcoded infer_workflow(run_id) == "implement-ticket" filter to a set/membership check covering implement-epic ('EPIC-'/'FOLDER-' prefixes) and create-tickets ('CREATE-TICKETS-' prefix) per tools/agent-monitoring/vocabulary.py::infer_workflow()
- Update tests/tools/test_record_events.py::test_implement_epic_and_create_tickets_records_unaffected_no_sidecar to assert non-null values, with a corrected docstring/comment reflecting the reversed design decision
- State explicitly in the ticket that this reverses TCK-20260719-COST-PROXY-WRITE-PATH's declared Out-of-Scope decision, with rationale for why

## Out of Scope
- Backfilling already-written null rows for past runs, including the runs that created earlier tickets in this same batch — historical rows stay null, only future runs after this ships show non-null values
- tests/tools/test_cost_proxy.py's formula/computation logic — unaffected by this change
- Redesigning record_events.py's rule that it always overrides caller-supplied tool_call_count/cost_proxy_score at write time — must extend that rule identically to the two newly-covered workflows, not change it

## Acceptance Criteria
- [ ] After adding sidecar registration at every agent() call site in both files plus widening the filter, a real implement-epic run's events.jsonl rows have non-null tool_call_count/cost_proxy_score matching the real (run_id,seq)-grouped tools.jsonl rows (code lands this run; a real-run confirmation per plan.md Step 7 is still outstanding — see Implementation Notes)
- [ ] A real create-tickets run likewise produces non-null values (same outstanding real-run confirmation as above)
- [x] test_implement_epic_and_create_tickets_records_unaffected_no_sidecar is updated (not left contradicting) to assert non-null values with a corrected docstring/comment reflecting the reversed design decision
- [x] A mixed-batch test confirms implement-ticket/implement-epic/create-tickets buckets compute independently without cross-contamination

## Related Tickets
- TCK-20260708-AGENT-COST-OBSERVABILITY
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260719-COST-PROXY-WRITE-PATH
- TCK-20260719-LIVE-PHASE-AGENT-LABEL
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE
- TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY

## Related Docs
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md (item 10 marked shipped; Doc-Update phase, found this planning doc's roadmap item still described this work as pending)
- docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md (§2 corrected to reflect shipped state; same Doc-Update phase finding)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/cost_proxy.py
- tools/agent-monitoring/record_events.py
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- .claude/workflows/create-tickets.js
- docs/agent-monitoring/schema.md
- tests/tools/test_record_events.py
- tests/tools/test_cost_proxy.py

## Assumptions / Open Questions
- This is a deliberate reversal of TCK-20260719-COST-PROXY-WRITE-PATH's explicit prior exclusion and must be documented as such in the ticket, not treated as an unnoticed oversight
- The 2 non-standard fire-and-forget call sites in implement-epic.js need individualized handling rather than a straight copy of the writeSidecar(seq) pattern
- Both the sidecar-coverage addition and the record_events.py filter-widening are required together — shipping either alone produces no visible effect

## Implementation Notes

Implemented per the architecture-review-approved `staging_artifacts/TCK-20260904-COST-PROXY-EPIC-TICKETS/plan.md` (7 steps), followed exactly, in order:

- **Step 1 (`implement-epic.js`):** Hoisted `batchRunId`'s computation to immediately after `discoverTs` is captured and before the Discover `agent()` call (epicId-first ternary ordering, matching the original, now-deleted `implement-epic.js:272-274` declaration's own priority order — not the plan draft's folder-first ordering, per architecture review's minor wording note). `request` mode gets a provisional `EPIC-REQUEST-<ts>` value. Added a 4-arg `writeSidecar(seq, phase, agentName)` helper (dual-write, closes over `batchRunId`, no `execution_id`/`provider`). Wired it at the 4 real top-level `agent()` sites using the disjoint negative `seq` range `-1, -2, -3, -4` (Discover, batch-monitoring-write, folder-cleanup, tracking-doc-update) — never positive, since `batchEvents` already occupies `seq=1..N` under the same `run_id`. Deleted the now-duplicate old `batchRunId` declaration.
- **Step 2:** No code change (confirmed) — `implement-epic.js`'s 2 fire-and-forget `bash()`-only early-return paths (`request` mode's EPIC_CREATED path, and the `ticketIds.length===0` NOTHING_TO_DO path) are untouched; they legitimately compute `(0, 0.0)` once the filter widens.
- **Step 3 (`create-tickets.js`):** Added the same 4-arg `writeSidecar` helper (using `events.length + 1` seq numbering, this file's own existing convention), placed after `pushEvent`'s definition and before `writeMonitoring`'s definition. Wired at 4 real sites: `comprehend`, `structure`, `write-sequence`, `link-epic`. Added documenting code comments (not silent) at the 3 explicitly excluded sites: `writeMonitoring`'s own `agent()` call, and the 2 `pipeline()` fan-out sites (`investigate:${concern.id}`, `write:${task.short_scope}`).
- **Step 4 (`record_events.py`):** Widened `compute_tool_stats()`'s filter from `== "implement-ticket"` to a membership check against `{"implement-ticket", "implement-epic", "create-tickets"}` (never simplified to "not None" — `simq-audit` stays excluded). Rewrote the function's docstring to describe the new partial-coverage state per workflow.
- **Step 5 (tests):** Renamed and rewrote `test_implement_epic_and_create_tickets_records_unaffected_no_sidecar` → `test_implement_epic_and_create_tickets_records_now_computed_from_real_tools_jsonl` (asserts real non-null values now). Renamed and rewrote `test_compute_tool_stats_only_targets_implement_ticket_workflow` → `test_compute_tool_stats_targets_implement_ticket_implement_epic_and_create_tickets` (4-way mixed batch including an explicitly-absent `simq-audit` key). Added `test_zero_tool_call_no_sidecar_paths_compute_zero_not_null` and `test_batch_top_level_negative_seq_and_child_ticket_positive_seq_do_not_cross_contaminate` (the Step 1 collision-fix regression test, hand-computing expected `cost_proxy_score` via the real `compute_cost_proxy_score()` formula). Added new file `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` with architecture-guard tests: adjacency for all 8 covered sites across both files, exact negative-`seq`-literal-in-order guard, single-hoisted-`batchRunId` guard, absence-of-`writeSidecar` guards (with comment-vs-actual-call disambiguation) for all 4 excluded sites, dual-write guards for both new helpers, fire-and-forget-paths-unchanged guard, and an `execution_id`/`provider`-absence guard.
- **Step 6 (`docs/agent-monitoring/schema.md`):** Corrected the `tool_call_count`/`cost_proxy_score` field-description rows, the `### phase values (create-tickets workflow)` section, and added a new paragraph to `### How tool calls are attributed to agent events` describing the new helpers, their shape, and the 3 `create-tickets.js` exclusions. Left the `### phase values (implement-epic workflow)` section and `docs/parity_ledger/infrastructure.yaml`'s `INFRA-282` untouched, per plan (the latter is a Parity-phase concern).
- **Step 7 (real-run acceptance verification):** Not performed inside this Implement phase — per plan.md this requires a genuinely separate real `implement-epic`/`create-tickets` run after this ticket's own code lands (this ticket itself closes via `implement-ticket.js`, not either of the two workflows it modifies). Flagged as outstanding on AC1/AC2 above; the next natural real invocation of either workflow (e.g. this ticket's own close, or a future batch ticket) is the earliest point this can be confirmed by direct `events.jsonl`/`tools.jsonl` inspection.

One deviation from plan.md's Step 6, recorded in `staging_artifacts/TCK-20260904-COST-PROXY-EPIC-TICKETS/plan.md`'s new "Deviations" section: Step 6's own Verify note incorrectly claimed `test_schema_doc_no_longer_describes_agent_self_report_mechanism` (a protected test in `test_current_run_sidecar_orchestrator.py`) "targets different text" than the L289 correction — it actually pins the literal substring `"neither ever has"`, which lived inside the sentence Step 6 says to replace. Discovered by running the plan's own scoped Step 5 Verify command. Resolved without touching the protected test file or restoring the false current-state claim: reworded the `### phase values (create-tickets workflow)` paragraph to lead with an explicitly historical sentence ("Prior to TCK-20260904-COST-PROXY-EPIC-TICKETS, neither... — neither ever has until that ticket landed"), which is truthful and preserves the pinned substring for a legitimate documentation reason, followed by the accurate current-state description Step 6 otherwise specifies unchanged. All other steps implemented exactly as specified, including the architecture-review-driven negative-`seq` and hoisted-`batchRunId`-ordering corrections already baked into the approved plan.

## Test Summary

`.venv/bin/python3 -m pytest tests/tools/test_record_events.py tests/tools/test_cost_proxy.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py -q` → **92 passed**, 0 failed. `tests/tools/test_cost_proxy.py` and `tests/tools/test_current_run_sidecar_orchestrator.py` confirmed 100% unmodified (`git diff` empty for both).

**Follow-up fix (plan.md addendum):** Step 1/3's `writeSidecar()` insertions broke a pre-existing, older test's literal-string adjacency assertion in `tests/tools/test_step0_ts_orchestrator.py` (`_IMPLEMENT_EPIC_ADJACENCY`/`_CREATE_TICKETS_ADJACENCY`, from `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`) — confirmed no reordering makes both the old and new adjacency invariants literally true at either site simultaneously (see plan.md addendum for the full proof). Applied the addendum's exact fix: retired both constants (replaced with a retirement comment citing this ticket and the superseding test `test_epic_create_tickets_sidecar_orchestrator.py`), deleted the 2 now-invalid `assert ... in ...` lines in `test_ts_capture_bash_precedes_each_covered_agent_call` (kept `ie_source`/`ct_source` and all other assertions in that function unchanged), and added one clarifying sentence to the module docstring. `_IMPLEMENT_TICKET_ADJACENCY` and every other test function in the file untouched, per addendum.

Isolated before/after (only `test_step0_ts_orchestrator.py` reverted/restored, `test_epic_create_tickets_sidecar_orchestrator.py` and the .js implementation held constant at their already-landed state): `tests/tools/test_step0_ts_orchestrator.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` → **before: 16 passed, 1 failed** (`test_ts_capture_bash_precedes_each_covered_agent_call`, on the `_IMPLEMENT_EPIC_ADJACENCY` assertion) → **after: 17 passed, 0 failed**.

Fuller regression sweep after fix: `.venv/bin/python3 -m pytest tests/tools/test_record_events.py tests/tools/test_cost_proxy.py tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_epic_create_tickets_sidecar_orchestrator.py tests/tools/test_step0_ts_orchestrator.py -q` → **98 passed**, 0 failed.

## Files Changed

- `.claude/workflows/implement-epic.js` — hoisted `batchRunId`, added `writeSidecar` helper, wired 4 sites with negative `seq`
- `.claude/workflows/create-tickets.js` — added `writeSidecar` helper, wired 4 sites, documented 3 exclusions
- `tools/agent-monitoring/record_events.py` — widened `compute_tool_stats()`'s workflow filter + docstring
- `tests/tools/test_record_events.py` — renamed/rewrote 2 tests, added 2 new tests
- `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` — new architecture-guard test file
- `docs/agent-monitoring/schema.md` — corrected 4 locations per plan.md Step 6
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — Doc-Update phase: item 10's inventory row, its "remaining to implement" counts, and the Horizon-2 standalone-items summary corrected to reflect item 10 as shipped (code)/real-run-confirmation-outstanding
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` — Doc-Update phase: §2 rewritten from "ready, schedule later" to shipped-with-outstanding-verification, describing what actually landed
- `tests/tools/test_step0_ts_orchestrator.py` — follow-up fix (plan.md addendum): retired `_IMPLEMENT_EPIC_ADJACENCY`/`_CREATE_TICKETS_ADJACENCY` with a retirement comment, removed the 2 now-invalid assertions, added one docstring sentence
- `tickets/inprogress/TCK-20260904-COST-PROXY-EPIC-TICKETS.md` — this file (Implementation Notes/Test Summary/Files Changed/Completion Summary/AC checkboxes)
- `staging_artifacts/TCK-20260904-COST-PROXY-EPIC-TICKETS/investigation.md` — created during this run's Investigate phase (pre-existing before this Implement phase started, included per ticket-hygiene requirement)
- `staging_artifacts/TCK-20260904-COST-PROXY-EPIC-TICKETS/plan.md` — created/revised during this run's Plan phase (2 architecture-review revision cycles), approved before this Implement phase began
- `staging_artifacts/TCK-20260904-COST-PROXY-EPIC-TICKETS/test_plan.md` — created during this run's Investigate phase
- `docs/parity_ledger/infrastructure.yaml` (modified, by this ticket's own Parity phase — updated `INFRA-282`'s stale "stay untouched" text and added a new `INFRA-407` entry for the sidecar-coverage reversal)

Not touched by this run (pre-existing, unrelated changes from sibling ticket
`TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`, already Finalized but not yet committed in this
shared worktree at the time this ticket's own Verify phase ran): `docs/REGISTRY.yaml`,
`docs/guidelines/agent_working_environment.md`, `docs/guidelines/artifact_retention_classification.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`.

## Completion Summary

Added dual-write orchestrator-side sidecar coverage (`writeSidecar(seq, phase, agentName)`) to `implement-epic.js` (4 top-level sites, disjoint negative `seq` range `-1..-4` to avoid colliding with the pre-existing `batchEvents` positive `seq=1..N` range) and `create-tickets.js` (4 of 7 sites — `writeMonitoring` and the 2 `pipeline()` concurrent fan-out sites stay permanently excluded), then widened `record_events.py::compute_tool_stats()`'s workflow filter to a membership check covering all 3 workflows (`simq-audit` excluded). This reverses `TCK-20260719-COST-PROXY-WRITE-PATH`'s deliberate prior scope-narrowing, so `implement-epic`/`create-tickets` events now get real, non-null `tool_call_count`/`cost_proxy_score` values at their covered sites instead of being passed through untouched. Tests renamed/rewritten/added accordingly (92/92 passing in the scoped suite), and `docs/agent-monitoring/schema.md` updated to match. Real-run acceptance verification (plan.md Step 7) remains outstanding, to be confirmed at this ticket's own close or the next real invocation of either workflow.
