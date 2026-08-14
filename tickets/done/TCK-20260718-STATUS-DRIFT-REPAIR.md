---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-STATUS-DRIFT-REPAIR
phase: done
date: 2026-07-18
tags: [data-quality, agent-monitoring, observability]
---

# TCK-20260718-STATUS-DRIFT-REPAIR

## Title
Bulk-repair stale `## Status` body sections in `tickets/done/` and normalize lowercase `final_status` values in `agent-monitoring/runs.jsonl`, plus a regression check for both

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Two related data-drift bugs predate the current Finalize step (which now reliably sets `## Status`
to `DONE` on every ticket close) and the current all-uppercase `final_status` enum convention:

**Part A.** 83 files in `tickets/done/` have a body `## Status` section reading something other than
`DONE` (mostly `OPEN`/`INPROGRESS`), even though each file's frontmatter already correctly shows
`status: historical, phase: done`. Re-derived and confirmed via the scan script on 2026-07-18: count
is still exactly 83, most recent stale file dated 2026-07-11
(`TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST.md`). Of the 83: 7 are epic-tier tickets whose
`## Status` correctly reads `EPIC_SCOPED` or `SCOPED` (not a bug — legitimate terminal text for that
tier) and 5 are pre-TCK-naming-convention legacy files (`resource_v2_*_e5_9.md` etc.) — per this
project's established precedent of not forcing new conventions onto genuinely old/legacy-format
tickets (see Memory: "Legacy data scope"), these 5 are treated as out of scope rather than force-fit.
That leaves **71 files** genuinely in scope for a single-line `## Status` value repair.

**Part B.** 7 records in `agent-monitoring/runs.jsonl` have a lowercase `final_status` value
(`"done"` or `"success"`) predating the current all-uppercase status-enum convention documented in
`docs/agent-monitoring/schema.md`'s `final_status` values table. Re-confirmed via direct JSONL scan on
2026-07-18 — still exactly 7, same 7 `run_id`s as originally reported. Each of the 7 was individually
cross-checked against its corresponding `tickets/done/*.md` file's `## Status` section (all 7 exist
and all 7 already read `DONE`), confirming `"DONE"` — not some other terminal value — is the correct
normalized target for every record. This is a live dashboard bug, not cosmetic:
`dashboard-frontend/src/components/GanttBar.tsx`'s `classifyFinalStatus()` does an exact-match on the
literal string `'DONE'`; anything else that isn't `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED` falls
through to the neutral/gray bucket, so these 7 genuinely-successful runs currently render gray instead
of green in the Recent Activity Gantt view.

**Part C.** No automated check currently catches either drift class recurring. A regression
check (script and/or test) is needed for both.

No duplicate ticket or in-flight work was found covering this exact scope (see Related Tickets for
adjacent precedent on similar drift-repair/gate-addition tickets, none of which cover this data).

## Scope
1. For each of the 71 in-scope files under `tickets/done/`, replace only the `## Status` section's
   value with `DONE`. Touch nothing else in the file (no other section, no frontmatter, no whitespace
   changes outside that one value).
2. For the 7 named `agent-monitoring/runs.jsonl` records, normalize `final_status` to `"DONE"` via a
   careful line-preserving JSONL rewrite (no existing rewrite/normalize-in-place helper was found in
   `tools/agent-monitoring/*.py` — implementer writes a small, targeted one; check
   `tools/agent-monitoring/validate.py` and `record_run.py` first for reusable JSON-line-parsing
   patterns before writing from scratch). The 7 target `run_id`s:
   - `TCK-20260610-WORKER-SINGLETON-GUARD` (`"done"` -> `"DONE"`)
   - `run-e51d-renderer-20260622` (`"success"` -> `"DONE"`)
   - `run-e51e-rest-api-20260622` (`"success"` -> `"DONE"`)
   - `TCK-20260619-E52A-COHORT-MODEL-run1` (`"success"` -> `"DONE"`)
   - `TCK-20260619-E52B-MIGRATION-run1` (`"success"` -> `"DONE"`)
   - `TCK-20260619-E52C-AGE-ADVANCEMENT-001` (`"success"` -> `"DONE"`)
   - `TCK-20260619-E52D-DENSITY-SIGNAL-001` (`"success"` -> `"DONE"`)
3. Add a regression check (script and/or pytest test) that can catch this class of drift recurring in
   the future for both Part A (a `tickets/done/*.md` file whose `## Status` body reads anything other
   than `DONE`, excluding the documented epic-tier `EPIC_SCOPED`/`SCOPED` exception and pre-TCK-naming
   legacy files) and Part B (a non-uppercase `final_status` value in
   `agent-monitoring/runs.jsonl`'s current-schema records). Follow the existing pattern in
   `tools/gate_checks/*.py` (e.g. `doc_staleness_check.py`, `workflow_meta_conformance.py`) or extend
   `tools/agent-monitoring/validate.py` — implementer's call which fits better; optionally wire into a
   `Makefile` target following the `agent-monitoring-validate` / `gate-expansion` precedent.
4. Opportunistic-only, not required: if the duplicated `## Tier\n## Tier` heading glitch in
   `TCK-20260628-E-NARRATIVE-CONSEQUENCE.md` / `TCK-20260628-E-WORLD-EVOLUTION.md` turns out to be a
   trivial one-line fix while already in that neighborhood, fix it; otherwise leave it and do not
   scope-creep onto it.

## Out of Scope
- The 7 epic-tier tickets whose `## Status` correctly reads `EPIC_SCOPED` or `SCOPED`
  (`TCK-20260619-E13-CONTENT-FOUNDATION.md`, `TCK-20260619-E53A-FACTION-AGENT.md`,
  `TCK-20260619-E53B-DIPLOMACY.md`, `TCK-20260619-E53C-WAR.md`, `TCK-20260619-E53D-HISTORY.md`,
  `TCK-20260619-E61-PROGRESSION.md`, `TCK-20260628-E-RESOURCE-ECOLOGY.md`) — must not be touched.
- The 5 pre-TCK-naming-convention legacy files (`resource_v2_flanking_geometry_e5_9.md`,
  `resource_v2_governor_reactivity_e6_0.md`, `resource_v2_phantom_leader_e5_7.md`,
  `resource_v2_strategic_phase_order_e6_1.md`, `resource_v2_terrain_weight_e5_8.md`) — legacy format,
  left alone per established project precedent.
- The duplicated `## Tier\n## Tier` heading glitch on the two `E-NARRATIVE-CONSEQUENCE`/
  `E-WORLD-EVOLUTION` epic tickets beyond an opportunistic trivial fix (see Scope item 4).
- Any `agent-monitoring/runs.jsonl` field other than `final_status` on the 7 named records (e.g. do
  not backfill a missing `ticket_id`, do not touch `agent_count`, `duration_s`, timestamps, etc.).
- The ~98 older-format `runs.jsonl` records that use the legacy `status`/`started_at`/`completed_at`
  field set instead of `final_status`/`start_ts`/`end_ts` — a different schema shape entirely, not
  addressed by this ticket.
- `LEGACY_TERMINAL_STATUS_VALUES` in `tools/agent-monitoring/validate.py` — left as-is; it remains a
  valid tolerance list for legacy-shaped records outside this ticket's 7-record scope and must not be
  narrowed, removed, or treated as "fixed" by this ticket.
- Any change to `implement-ticket.js`'s Finalize phase itself — already correctly sets `## Status` to
  `DONE` for all new closes; this ticket repairs historical drift only, not the mechanism.
- `dashboard-frontend/src/components/GanttBar.tsx` source code — its `classifyFinalStatus()` logic is
  correct as written; the bug is purely in the underlying data, not the classifier.

## Acceptance Criteria
- [ ] Re-running the Part A scan (`## Status` regex scan over `tickets/done/*.md`) returns exactly the
      12 documented exceptions (7 epic-tier `EPIC_SCOPED`/`SCOPED` + 5 pre-TCK-naming legacy files)
      and zero other non-`DONE` results.
- [ ] Each of the 71 in-scope files shows a single-line diff (only the `## Status` value line changed)
      when compared against its pre-fix version — verified via `git diff --stat` or equivalent showing
      1 changed line per file.
- [ ] All 7 named `runs.jsonl` records have `final_status` == `"DONE"` (exact case), verified via a
      JSON-parsing scan (not string grep, to avoid false negatives from formatting).
- [ ] `agent-monitoring/runs.jsonl` has the same line count after the edit as before, and every field
      on every non-target line is byte-identical to its pre-fix value (line-preserving rewrite,
      verified via a line-by-line diff excluding the 7 target lines).
- [ ] `python3 tools/agent-monitoring/validate.py` exits 0 after the `runs.jsonl` edit.
- [ ] The new regression check exits non-zero when run against a fixture with an injected stale
      `## Status` value (non-`DONE`, non-exception) in a `tickets/done/`-shaped file, and against a
      fixture with an injected lowercase `final_status` value in a `runs.jsonl`-shaped file.
- [ ] The new regression check exits 0 against the post-fix `tickets/done/` + `runs.jsonl` corpus, and
      correctly does not flag the 7 epic-tier exceptions or the 5 pre-TCK-naming legacy files.
- [ ] New regression check has pytest coverage for: clean corpus (pass), injected stale ticket status
      (fail), injected lowercase `final_status` (fail), epic-tier exception correctly ignored,
      legacy-naming file correctly ignored.
- [ ] `dashboard-frontend`'s `classifyFinalStatus()` (verified via existing/new frontend test, or
      manual trace) buckets all 7 corrected runs as `'done'`, not `'neutral'`.

## Related Tickets
- TCK-20260710-EPIC-STALENESS-CHECK — adjacent agent-monitoring/ticket-health tooling; different
  failure mode (epic inactivity, not `## Status` body drift).
- TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK — precedent for a small, targeted bug-fix ticket in the
  same tooling area (`tools/agent-monitoring/`), standard tier, low priority.
- TCK-20260709-REGISTRY-DRIFT-CHECK-GATE — direct precedent for the "add a `--check` drift-detection
  gate" pattern this ticket's Part C follows.
- TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK — direct precedent for "automated consistency check for
  hand-maintained/drift-prone data," standard tier, P2 priority (same shape as this ticket).
- TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR — precedent staleness-repair ticket.
- The 7 tickets whose `runs.jsonl` records are normalized in Part B (referenced/verified only, not
  modified): TCK-20260610-WORKER-SINGLETON-GUARD, TCK-20260619-E51D-RENDERER,
  TCK-20260619-E51E-REST-API, TCK-20260619-E52A-COHORT-MODEL, TCK-20260619-E52B-MIGRATION,
  TCK-20260619-E52C-AGE-ADVANCEMENT, TCK-20260619-E52D-DENSITY-SIGNAL.

## Related Docs
- `docs/agent-monitoring/schema.md` — canonical `final_status` values table (confirms `DONE` is the
  correct spelling/casing); also documents `LEGACY_TERMINAL_STATUS_VALUES` as an intentional legacy
  tolerance list in `validate.py` — do not treat that list as "the bug," it is separate parser
  leniency, not a data-correctness claim.
- `docs/guides/agent_monitoring.md` — documents `validate.py`'s dual `final_status`/`status` field
  tolerance and `generate_retro.py`'s matching fallback.
- `docs/ai/ticket-lifecycle.md` — documents `runs.jsonl` run-record shape and ticket lifecycle.
- `docs/ai/system_overview.md` — documents the `workflow`/`tier`/`final_status`/`agent_count`/
  `duration_s` run-record field set.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-EPIC-STALENESS-CHECK/`
- `stored_artifacts/TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK/`
- `stored_artifacts/TCK-20260709-REGISTRY-DRIFT-CHECK-GATE/`
- `stored_artifacts/TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK/`
- `stored_artifacts/TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR/`

## Related Code Areas
- `tickets/done/*.md` — 71 files to edit (Part A); 12 documented exceptions must not be edited.
- `agent-monitoring/runs.jsonl` — 7 records to edit (Part B).
- `tools/agent-monitoring/validate.py` — existing `LEGACY_TERMINAL_STATUS_VALUES` tolerance logic;
  read for constraints, not modified.
- `tools/agent-monitoring/record_run.py`, `vocabulary.py` — checked for reusable rewrite/normalize
  helpers; none exist today, implementer writes a small targeted one.
- `tools/gate_checks/doc_staleness_check.py`, `tools/gate_checks/workflow_meta_conformance.py` —
  closest existing patterns for the new Part C regression check.
- `dashboard-frontend/src/components/GanttBar.tsx` — `classifyFinalStatus()`, the consumer whose
  gray/neutral misrendering motivates Part B; read-only reference, not modified.
- `Makefile` — `agent-monitoring-validate`, `gate-expansion` targets as possible wiring precedent for
  the new regression check.

## Assumptions / Open Questions
- Assumes `"DONE"` is the correct normalized target for all 7 `runs.jsonl` records — verified during
  scoping (2026-07-18) by cross-checking each record's `run_id` against its corresponding
  `tickets/done/*.md` file's `## Status` section; all 7 exist and all 7 already read `DONE`. If this
  assumption is wrong for any record, that record's normalization target changes and Part B's AC must
  be re-derived for it.
- Assumes the 71-file in-scope count (83 total minus 7 epic-tier exceptions minus 5 legacy-naming
  files) is accurate as of 2026-07-18. Ticket closes happen continuously; implementer should re-run
  the derivation scan at implementation time rather than trusting this ticket's file list as final,
  and reconcile any delta.
- Assumes no existing safe line-preserving JSONL rewrite helper exists anywhere in
  `tools/agent-monitoring/` — confirmed by listing and inspecting all 12 `.py` files in that directory;
  none expose a rewrite-in-place or normalize function. If implementation later finds one was missed,
  prefer it over a new script.
- Open question: does any downstream tool depend on JSON key order within a `runs.jsonl` line? Not
  found evidence either way in this scoping pass; implementer should verify before assuming
  `json.loads`/`json.dumps` round-tripping (which does not guarantee key order preservation unless
  handled explicitly, e.g. via `object_pairs_hook`) is safe, or use a key-order-preserving approach.
- Layer was set to `observability` on the judgment call that the dashboard-rendering impact (Part B)
  and the new regression-check tooling (Part C) are the more architecturally load-bearing pieces;
  `ticket` is also a valid `LAYER_VALUES` option and could reasonably apply instead since Part A
  concerns ticket body content specifically. Flagged here rather than silently picked.
- Tier was set to `standard` rather than `hotfix`: while Parts A and B are mechanical, low-risk data
  edits, Part C requires designing and testing new regression-check tooling (not a self-evident
  one-liner), which matches the `standard` tier definition and the precedent set by
  TCK-20260709-REGISTRY-DRIFT-CHECK-GATE and TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK (both
  similarly-scoped drift/consistency-check additions, both `standard` tier).

## Implementation Notes

**Step 1 — derive/freeze the 71-file list.** Wrote
`staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/derive_status_drift_scope.py`
(read-only). Re-ran the baseline regex (`^## Status\s*\n+\s*(\S+)`, multiline) against the live
`tickets/done/` tree on 2026-07-18: **71 in-scope, 7 epic-tier (`EPIC_SCOPED`/`SCOPED`), 5
pre-TCK-naming legacy, 6 same-line colon-suffixed drift files** — exact match to plan.md's frozen
list, byte-for-byte, disjointness assertion passed. No delta since the plan was written; no
reconciliation needed.

**Step 2 — bulk-fix.** Wrote
`staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/fix_status_drift_tickets.py`, which
imports Step 1's derivation (not a hand-copied list) and replaces only the captured `## Status`
value token with `DONE`, preserving each file's existing blank-line layout. Fixed all 71 files.
Verified: re-running Step 1's script post-fix shows 0 in-scope / 12 exceptions remaining (AC1);
`git diff --numstat tickets/done/` shows exactly 71 files, each with 1 insertion + 1 deletion — a
genuine single-line value replace (AC2; spot-checked via `git diff` on one file to confirm no
whitespace/structure change beyond the value token).

**Step 3 — runs.jsonl normalizer.** Wrote
`staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/fix_runs_jsonl_final_status.py`. Before
writing, independently re-verified all 7 target lines' `run_id` and byte layout against
investigation.md's table (line numbers, substring occurrence counts) — all matched exactly. Applied
pure line-scoped string substitution (`'"final_status":"done"'`→`'"final_status":"DONE"'` for
`TCK-20260610-WORKER-SINGLETON-GUARD`; `'"final_status":"success"'`→`'"final_status":"DONE"'` for
the other 6), no `json.loads`/`json.dumps` round trip, written via temp-file-plus-atomic-rename.
Verified: all 7 target `run_id`s now read `final_status == "DONE"` exactly (AC3); line count
unchanged (641 before/after) and a full line-by-line diff confirms every non-target line is
byte-identical to its pre-fix value (AC4).

**Step 3b — schema.md documentation.** Added a "Historical Corrections" subsection to
`docs/agent-monitoring/schema.md`'s `## agent-monitoring/runs.jsonl` section, documenting the Step
3 in-place edit as a one-time, audited historical correction distinct from the file's ongoing
append-only contract for new writes.

**Step 4 — new gate check.** Wrote `tools/gate_checks/status_drift_check.py`, mirroring
`doc_staleness_check.py`/`workflow_meta_conformance.py`'s shape: `check_ticket_status_drift()`,
`check_runs_jsonl_final_status_drift()`, and an aggregate `check_status_drift()`, all returning
`List[dict]` with `MARKER:`-prefixed JSON stdout in `__main__`. The ticket-status regex is
byte-identical to Step 1's baseline pattern (asserted via
`test_regex_matches_baseline_scan_pattern`). Exemptions are structural only (value-based
`{"EPIC_SCOPED", "SCOPED"}`, filename-pattern-based `not name.startswith("TCK-")`) — no hardcoded
filename lists. Per plan.md's explicit Step 4 spec (not sibling-script precedent — neither
`doc_staleness_check.py` nor `workflow_meta_conformance.py` actually calls `sys.exit()` in their own
`__main__` blocks), `__main__` exits non-zero when any entry is `FAIL`. Ships unwired: no `Makefile`
target, no workflow invocation added. Wrote `tests/tools/test_status_drift_check.py` with 13 tests
(covers all 10 named cases from test_plan.md plus 3 supporting cases) — all pass.

**Step 5 — full-corpus verification.**
- `python3 tools/gate_checks/status_drift_check.py` against the live, now-fixed
  `tickets/done/`+`runs.jsonl` corpus: exit 0, both scans `PASS`.
- `pytest tests/tools/test_status_drift_check.py -v`: 13/13 passed.
- `pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_run.py
  tests/tools/test_doc_staleness_check.py tests/tools/test_workflow_meta_conformance.py
  tests/tools/test_generate_retro.py tests/tools/test_validate_frontmatter.py -v`: 148 passed, 1
  xfailed (pre-existing, unrelated known architecture-question xfail in
  `test_workflow_meta_conformance.py`, not touched by this ticket).
- `python3 tools/agent-monitoring/validate.py`: exits 1 — **see Deviations below and
  `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/plan.md`'s "Deviations" section.** Confirmed
  via before/after comparison that this ticket's edit introduces zero new `ERROR`-level findings
  (the pre-existing `errors` list, which drives the exit code, is byte-identical before/after); the
  6 `ERROR: Run with no events` lines causing exit 1 predate this ticket and name run_ids entirely
  outside Part B's 7-record scope. This ticket's edit adds 4 new `WARNING`-level lines only (never
  affects exit code per `validate.py`'s own docstring).
- Manual trace: `GanttBar.tsx`'s `classifyFinalStatus('DONE')` returns `'done'` (source read
  directly, no code change); `dashboard-frontend/src/test/GanttBar.test.tsx` lines 18 and 95 already
  exercise `final_status: 'DONE'` fixtures. No new frontend test required.
- Final `git status`/`git diff --stat` sanity: exactly the expected file set touched (71
  `tickets/done/*.md`, `agent-monitoring/runs.jsonl`, `docs/agent-monitoring/schema.md`, the two new
  `tools/gate_checks/`/`tests/tools/` files, staging-artifact scripts). `agent-monitoring/tools.jsonl`
  also shows as modified — expected side effect of this session's own tool calls being recorded by
  the monitoring hooks, not a Part A/B/C change.

**Deviations from plan.md:** One — see plan.md's "Deviations" section (added this session): AC5's
literal "`validate.py` exits 0" wording is not achievable within this ticket's approved scope,
because the script already exited 1 before this ticket's edit due to 6 pre-existing, unrelated
zero-event errors. Confirmed this ticket's edit is not the cause and does not worsen it (same errors
set, exit code unchanged, before and after). No other deviation from plan.md's 5 steps.

## Test Summary

- `pytest tests/tools/test_status_drift_check.py -v` — 13 passed (10 named cases from test_plan.md
  plus 3 supporting: `test_runs_jsonl_clean_uppercase_passes`,
  `test_check_status_drift_aggregates_both_scans`, `test_regex_matches_baseline_scan_pattern`).
- `pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_record_run.py
  tests/tools/test_doc_staleness_check.py tests/tools/test_workflow_meta_conformance.py
  tests/tools/test_generate_retro.py tests/tools/test_validate_frontmatter.py -v` — 148 passed, 1
  xfailed (pre-existing, unrelated).
- `python3 tools/gate_checks/status_drift_check.py` (live corpus) — exit 0, all-`PASS`.
- `python3 tools/agent-monitoring/validate.py` — exit 1, pre-existing and unrelated to this ticket's
  edit (see Deviations).
- Data-fix verification (test_plan.md's manual checklist): all 6 items confirmed — Part A scan
  clean (12 exceptions only), `git diff --numstat` 71×(1,1), 7/7 `runs.jsonl` records `DONE`, line
  count unchanged + non-target lines byte-identical, `validate.py` exit code unchanged
  before/after, `classifyFinalStatus` manual trace confirmed.

## Files Changed

- 71 files under `tickets/done/*.md` — single-line `## Status` value fix (full list: re-derivable
  via `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/derive_status_drift_scope.py`, or
  `git diff --name-only tickets/done/`; also enumerated in investigation.md).
- `agent-monitoring/runs.jsonl` — 7 lines' `final_status` casing corrected.
- `docs/agent-monitoring/schema.md` — new "Historical Corrections" subsection.
- `docs/parity_ledger/infrastructure.yaml` — new entry `INFRA-277` recording this ticket's regression
  check and data-repair as verified parity (added during the Parity phase, after Implement).
- `tools/gate_checks/status_drift_check.py` — new regression check (unwired).
- `tests/tools/test_status_drift_check.py` — new, 13 tests.
- `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/derive_status_drift_scope.py` — new,
  one-off (Step 1).
- `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/fix_status_drift_tickets.py` — new,
  one-off (Step 2).
- `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/scripts/fix_runs_jsonl_final_status.py` — new,
  one-off (Step 3).
- `staging_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/plan.md` — added "Deviations" section.
- `agent-monitoring/tools.jsonl` — auto-updated by monitoring hooks during this session (not a
  direct edit).

## Completion Summary

Repaired two independent historical data-drift bugs and shipped a regression check for both. Part A:
71 `tickets/done/*.md` files' body `## Status` value corrected from stale `OPEN`/`INPROGRESS` to
`DONE` (12 documented exceptions — 7 epic-tier, 5 pre-TCK-naming legacy — correctly left untouched;
6 same-line colon-suffixed drift files explicitly excluded per plan.md's scope decision). Part B: 7
`agent-monitoring/runs.jsonl` records' `final_status` normalized from lowercase (`"done"`/`"success"`)
to `"DONE"` via line-scoped string substitution, fixing a live dashboard bug where these successful
runs rendered gray instead of green in the Recent Activity Gantt view. Part C: new
`tools/gate_checks/status_drift_check.py` (13 pytest cases) ships unwired, ready for a future ticket
to gate on. One documented deviation: `validate.py`'s exit code (1) is unaffected by this ticket's
edit — the non-zero exit predates this ticket and is caused by 6 unrelated zero-event errors, not by
anything in this ticket's approved scope (see plan.md Deviations). All other acceptance criteria
verified clean against the live, post-fix corpus.
