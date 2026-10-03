---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-MONITORING-RUNID-JOIN
phase: done
date: 2026-07-05
tags: [agent-monitoring, data-quality, root-cause]
---

# TCK-20260705-MONITORING-RUNID-JOIN

## Title
Investigate and harden against run_id/event join mismatches (crashed runs, zero-event runs)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
The first-ever real `make agent-monitoring-retro`/`validate.py` run (`TCK-20260704-RETRO-LOOP-ENFORCEMENT`'s tooling, exercised for real on 2026-07-05) surfaced 21 "crashed" runs (`start_ts` present, no `end_ts`) and 5 runs with zero matching events. **Correction (investigation, 2026-07-05): the "21" figure was stale** — a fresh `validate.py` run at investigation time found **126** incomplete-run warnings (5 zero-event errors, unchanged), because more historical batches had been merged into `runs.jsonl` since the ticket was filed. Of the 126, only **16** `run_id`s are true dedup-resolvable (a legacy no-`end_ts` record coexists with a genuinely-complete sibling record for the same `run_id`); the remaining **107** are true residual with no `end_ts` anywhere under that `run_id`, and an exhaustive (not sampled) cross-check found **107/107 (100%)** represent genuinely completed work recorded under a missing or differently-named completion field, not crashes. Direct investigation also found two distinct, confirmed root-cause patterns behind at least some of these, both a **join failure between `runs.jsonl` and `events.jsonl`**, not necessarily a genuine workflow crash:

1. **Timestamp-generation race.** `run-E43B-1782052024` (in `runs.jsonl`, zero events) vs. `run-E43B-1782052032` (in `events.jsonl`, 7 real Scope/Investigate/Plan/... events) — an 8-second gap between two independently-generated Unix-timestamp-suffixed IDs for what is clearly the same logical run. **Important caveat, confirmed by reading the current code**: `.claude/workflows/implement-ticket.js`'s `tid` (line 109, `const tid = ticketInfo.ticket_id`) and `implement-epic.js`'s `batchRunId` (line 216) are each captured **once** from a stable source and reused consistently for every subsequent write in that same execution — the current workflow scripts, as written, cannot produce this specific race. This mismatch is either (a) debris from an older version of the workflow scripts predating this capture-once pattern, or (b) produced by a direct/manual `record_run.py`/`record_events.py` invocation (e.g. a `manual-hotfix` entry, or an agent generating its own ad hoc run_id) rather than the standard workflow path. Which of these is true is not yet confirmed — that's this ticket's first job.
2. **Ticket-rename mismatch.** `TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN` (the run record) vs. `TCK-20260701-HAZARD-NATIVE-IMMUNITY` (its events, no `-REDESIGN` suffix). Plausible explanation: two separate execution attempts against the same underlying ticket, where the ticket file/ID was renamed between them — the events from an earlier, incomplete attempt got orphaned under the pre-rename ID while a later run wrote the final run record under the renamed ID. Not yet confirmed against actual ticket/git history.

15 of the 21 "crashed" (no `end_ts`) runs cluster tightly around 2026-06-23 00:00–02:00 (the `E62A`–`E62D`/`E63A`–`E63D` phase batch and their parent `EPIC-*` wrappers) — suggesting a specific historical incident on that date (a session crash, a context-compaction event, or a bug in how that particular epic batch's finalization ran) rather than 15 independent occurrences of the same bug. Worth checking whether those underlying tickets are actually `DONE` in `tickets/done/` (i.e. the real work completed fine and only the monitoring write failed) before assuming anything is actually broken in the simulation/engine work itself. **Correction: the true 2026-06-23 cluster is 16 records** (not 15 — investigation.md Class B), all sharing one identical legacy schema shape, all confirmed genuinely completed via `tickets/done/` match; see AC4 below.

## Scope
- Confirm, for each of the 21 crashed runs and 5 zero-event runs, whether the underlying ticket/epic actually completed successfully (check `tickets/done/` and `working_log.csv`) — distinguishing "real workflow crash, work never finished" from "work finished fine, only the monitoring write joined incorrectly."
- Confirm whether pattern 1 (timestamp race) is reproducible with the *current* `.claude/workflows/*.js` code, or whether it is exclusively historical/pre-refactor debris and/or a symptom of `manual-hotfix`-style direct script invocations that don't go through the workflow's single-capture `tid` pattern.
- Confirm whether pattern 2 (rename mismatch) is explained by a genuine two-attempt history for that specific ticket (check `tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN.md` and any git history for a rename).
- Based on findings, add a defensive safeguard appropriate to whatever the confirmed live risk actually is — e.g. `record_run.py`/`record_events.py` warning (not failing — matches this repo's "monitoring write failure must never fail the workflow" hard rule) if a `run_id` passed to one script was never seen by the other within some window, or a stronger convention/lint against direct manual invocation using ad hoc IDs instead of the workflow's stable `tid`.
- Investigate the 2026-06-23 cluster specifically — is there a single, identifiable incident (crash, compaction, bug in a specific commit active that day) that explains 15 of 21 cases at once, rather than treating each as an independent occurrence?

## Out of Scope
- Backfilling or repairing the historical `runs.jsonl`/`events.jsonl` records themselves — append-only log, matching the precedent already established for other agent-monitoring schema drift this session (leave history alone, fix going forward).
- Fixing `validate.py`'s separate schema blind spot around the legacy `status` field (tracked in `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`) — related but independent finding from the same retro run.
- Fixing `generate_retro.py`'s misleading empty-summary/epic-DONE-rate metrics (tracked in `TCK-20260705-RETRO-METRIC-ACCURACY`) — a report-generation issue, not a run_id-join issue.

## Acceptance Criteria
- [x] Each of the 21 crashed runs and 5 zero-event runs is classified: genuine crash (work incomplete) vs. join mismatch (work completed, monitoring write joined incorrectly) vs. legacy-schema debris predating the current write pattern. **Corrected scope**: the live count at investigation time was 126 incomplete-run warnings (not 21) + 5 zero-event runs — the ticket was scoped against a stale count (see Request Summary). `investigation.md` classifies all 126 + 5 in Classes A/B/C/D: **16 true Class A (dedup-resolved) + 107 true Class C residual**, all 107 confirmed genuinely completed work (98/107 direct `tickets/done/` match, 9/107 via explicit terminal-status field + independently-DONE child tickets). Zero genuine crashes or abandoned work found.
- [x] Root cause of the timestamp-race pattern (E43B example) is confirmed: pre-refactor historical debris only — not reproducible by current `.claude/workflows/implement-ticket.js` (single-capture `tid`, capitalized phase names, per-role agent names all differ from the legacy record's shape). See investigation.md "Pattern 1."
- [x] Root cause of the rename-mismatch pattern (HAZARD-NATIVE-IMMUNITY example) is confirmed against actual ticket/git history: `git log --follow` shows a single commit, no file-level rename ever occurred; the `-REDESIGN` suffix was an ad hoc run_id invented for a manual/direct monitoring-write session's run-record write only (events were correctly filed under the true ticket ID). See investigation.md "Pattern 2."
- [x] The 2026-06-23 cluster (16 records, not 15 — corrected count) has an identified common cause: one batch of historical monitoring records sharing an identical legacy schema shape (`start_ts` + `final_status:"DONE"`, no `end_ts` key), most plausibly landed via the large historical merge `6e25d4f2`. All 16 are part of the 107 residual, now resolved by Step 1's legacy-field allowlist. See investigation.md "Class B."
- [x] A safeguard is added matching the live risk actually confirmed: (1) `tools/agent-monitoring/validate.py` now dedupes the incomplete-run check by `run_id` and recognizes legacy completion-field variants via an explicit `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` allowlist, closing 125 of 126 false-positive warnings (verified: 126 -> 107 -> 1; the single residual, `TCK-20260623-TYPE-CHECKER`, is a 6th, uncatalogued legacy shape individually confirmed complete and documented, not added to the allowlist per policy against speculative single-record expansion); (2) `.claude/workflows/implement-epic.js`'s batch monitoring write now has a Step 2b verification gate for the one confirmed live, reproducible gap (Pattern 3); (3) `docs/agent-monitoring/schema.md` documents the 5 legacy schema generations, the allowlist, the manual-write convention, and the final residual.

## Related Tickets
- TCK-20260704-RETRO-LOOP-ENFORCEMENT (shipped the retro skill/hook that surfaced this finding on its first real run)
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP (sibling finding from the same investigation — validate.py's own blind spot)
- TCK-20260705-RETRO-METRIC-ACCURACY (sibling finding — misleading retro report metrics)

## Related Docs
- docs/guides/agent_monitoring.md
- docs/agent-monitoring/schema.md
- agent-monitoring/retro/RETRO-ALL.md (this ticket's originating finding, Notes section)
- docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md (related schema-drift idea from earlier this session — this ticket's findings are additional evidence for that idea, not a duplicate of it)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/validate.py
- .claude/workflows/implement-ticket.js (line 109, `tid` capture)
- .claude/workflows/implement-epic.js (line 216, `batchRunId` capture)
- agent-monitoring/runs.jsonl, agent-monitoring/events.jsonl (read-only — data being investigated)

## Assumptions / Open Questions
- Whether any of these 21+5 cases represent a genuinely incomplete, still-broken piece of work (not just a monitoring artifact) — must be checked against `tickets/done/` before assuming this is purely a bookkeeping issue.
- Whether a "manual-hotfix" or similarly direct invocation path (bypassing the workflow JS's single-capture `tid` pattern) is still in active use anywhere in this repo's current tooling — if so, that's the more likely live risk than the workflow scripts themselves.

## Implementation Notes
Three confirmed patterns from investigation.md:
1. **Timestamp race (`run-E43B-*`)** — historical debris, pre-dating the current single-capture `tid` pattern in `implement-ticket.js`. Not reproducible by current code. Documentation-only (Step 3).
2. **Rename mismatch (`HAZARD-NATIVE-IMMUNITY-REDESIGN`)** — an ad hoc `run_id` suffix invented during a manual/direct monitoring-write session, not a real ticket rename (confirmed via `git log --follow`, single commit). Documentation-only convention added (Step 3): always reuse the exact ticket ID as `run_id` when hand-writing monitoring records.
3. **`implement-epic.js` batch-write gap** — the only pattern confirmed reproducible by current code: the batch events write (Step 2) and batch run-record write (Step 3) had no verification gate between them, allowing a run record to land with zero corresponding events (confirmed live case: `FOLDER-tickets/todos/world-data/`, dated within the current-schema era). Fixed in Step 2.

Classification outcome (corrected from an earlier, non-systematic pass in investigation.md): of 450 distinct `run_id`s in `runs.jsonl`, 16 are true Class A (dedup-resolved — a legacy no-`end_ts` record has a genuinely-complete sibling under the same `run_id`) and 107 are true Class C residual (no record under that `run_id` has `end_ts` at all). All 107 were exhaustively (not sampled) cross-checked against `tickets/done/` and confirmed genuinely completed work — zero abandoned or genuinely incomplete runs found.

**Decision**: extend `validate.py`'s completion check with an explicit, enumerated `LEGACY_COMPLETION_FIELDS` (`end_ts`, `finished_at`, `completed_at`, `ts_end`) / `LEGACY_TERMINAL_STATUS_VALUES` (11-value enumerated terminal set for `final_status`/`status`) allowlist, rather than leave the 107 as a permanent unexplained warning — grounded directly in the 107/107-confirmed-complete evidence. `final_status`/`status` are bounded to the enumerated set, not trusted on truthiness alone (real counterexample found: `final_status:"INPROGRESS"` on a genuinely non-terminal record).

**Step 1** (`tools/agent-monitoring/validate.py`): replaced the per-line `if not run.get("end_ts")` scan with a group-by-`run_id`, aggregate-then-check approach (`_record_is_complete()` checked against every record in a `run_id`'s group; flagged only if none are complete).

**Step 2** (`.claude/workflows/implement-epic.js`): added a "Step 2b — verify" instruction inside the existing single `agent()` prompt (between the existing Step 2 write and Step 3 write), checking `events.jsonl` for a matching `run_id` count and retrying once if short, with an `EVENTS-MISSING:` prefix on the Step 3 warning if still short after retry. Kept advisory (does not fail the workflow), per the hard rule.

**Step 3** (`docs/agent-monitoring/schema.md`): added a "Known Limitations" section documenting the 5 legacy schema generations, the allowlist, the manual-write `run_id` convention, and the final residual (`TCK-20260623-TYPE-CHECKER`).

No deviations from plan.md — all code (`LEGACY_COMPLETION_FIELDS`, `LEGACY_TERMINAL_STATUS_VALUES`, `_record_is_complete()`) used verbatim from the plan.

## Test Summary
`python3 tools/agent-monitoring/validate.py` warning counts, verified via git-stash before/after comparison and an isolated dedup-only intermediate test:
- **Before** (pre-fix): 126 "Incomplete run" warnings, 5 "no events" errors, exit code 1.
- **After dedup-by-run_id alone** (part a only, temporarily isolated): 107 "Incomplete run" warnings.
- **After dedup + legacy-field allowlist** (full fix): **1** "Incomplete run" warning — `TCK-20260623-TYPE-CHECKER` (the single, already-identified, already-verified 6th-legacy-shape residual). "no events" unchanged at 5. Exit code unchanged at 1 (the 5 "no events" hard errors are untouched by this fix).

Regression-guard fixture tests (throwaway single-line `runs.jsonl` copies in a temp directory, real `agent-monitoring/` files never touched — confirmed via `git diff --stat agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` showing zero diff):
- A genuine crash record (no allowlisted field, `status:"INPROGRESS"`) — correctly flagged.
- A record with only `final_status:"INPROGRESS"` (non-terminal) — correctly flagged (proves the allowlist does not treat `final_status` as complete-on-truthiness).
- One fixture per allowlisted field in isolation (`end_ts`, `finished_at`, `completed_at`, `ts_end`, `final_status:"DONE"`, `status:"completed"`) — each correctly recognized as complete, none flagged.

Step 2 (`implement-epic.js`) verified by code inspection only (no live epic batch available): `grep -n "Step 2b\|EVENTS-MISSING\|batchEvents\|record_events.py\|record_run.py" .claude/workflows/implement-epic.js` confirms Step 2b appears between the existing Step 2 and Step 3 text, references the correct `batchRunId`/`batchEvents.length` variables, and the "do NOT raise" contract still covers the full block.

Step 3 (`docs/agent-monitoring/schema.md`) verified via `grep -n "Known Limitations" docs/agent-monitoring/schema.md` — section present with all 3 required points. `make knowledge-index-update` run afterward (1 file re-embedded).

No pytest suite exists for `tools/agent-monitoring/*.py` (pre-existing, documented gap per both sibling tickets) — not introduced by this ticket, per plan's explicit scope guard.

## Files Changed
- `tools/agent-monitoring/validate.py` — dedup-by-run_id + legacy completion-field allowlist for the incomplete-run check.
- `.claude/workflows/implement-epic.js` — added Step 2b verification gate to the batch monitoring write prompt.
- `docs/agent-monitoring/schema.md` — added "Known Limitations" section.
- `tickets/inprogress/TCK-20260705-MONITORING-RUNID-JOIN.md` — this file (AC1/Request Summary correction, closing sections).

## Completion Summary
Implemented all 4 plan steps. `validate.py`'s incomplete-run false-positive count went from 126 to 1 (verified empirically, matching the plan's predicted 126 -> 107 -> 1 sequence exactly), with the single remaining residual already individually confirmed genuinely complete and documented rather than chased into the code. `implement-epic.js`'s one confirmed live, reproducible gap (Pattern 3) now has a self-verifying retry gate, kept advisory per the hard rule. `docs/agent-monitoring/schema.md` documents the full legacy-schema landscape so this doesn't need re-investigating. The ticket's own AC1/Request Summary framing is corrected from the stale "21+5" to the verified "126+5" with the 16/107 split. No deviations from the approved plan were necessary — all code was used verbatim as instructed.
