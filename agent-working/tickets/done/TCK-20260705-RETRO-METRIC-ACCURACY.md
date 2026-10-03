---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-RETRO-METRIC-ACCURACY
phase: done
date: 2026-07-05
tags: [agent-monitoring, retro, data-quality]
---

# TCK-20260705-RETRO-METRIC-ACCURACY

## Title
Fix two misleading metrics in generate_retro.py: empty-summary false alarm, epic DONE-rate miscalculation

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
The first-ever real retro run (`RETRO-ALL.md`/`RETRO-2026-W27.md`, generated 2026-07-05 via `TCK-20260704-RETRO-LOOP-ENFORCEMENT`'s tooling) produced two metrics that direct investigation shows are actively misleading, not just imprecise:

1. **"246 empty summaries — check agent prompts for `summary` field" is a false alarm.** Every single empty-summary event (246/246, confirmed by direct count) comes from an `events.jsonl` record with `agent: null`, and 239 of those 258 `agent: null` records use a pre-schema-normalization legacy format (`"event": "ticket_finalized"` / `"ticket_complete"` / `"epic_completed"` instead of the current `phase`+`agent`+`status`+`summary` schema) that never had a `summary` field to begin with. **0 of 1698 current-schema events (`agent` is set) have an empty summary** — verified directly. The report's advice ("check agent prompts") is actively wrong: there is no current agent-prompt problem to fix; the number is 100% legacy-data noise.
2. **The epic-tier "44% DONE rate" (26/58) undercounts real epic health.** `EPIC_SCOPED` is a correct, expected terminal status for scope-only epic tickets (per `implement-ticket.js`: epic tier returns `EPIC_SCOPED` and explicitly does no implementation) — it is not a failure or an incomplete run. 19 of the 58 epic-tier runs are `EPIC_SCOPED`. Excluding them, epics that actually attempted implementation are DONE at 31/39 = **79%**, not 44%. The report currently has no way to distinguish "epic correctly scoped, nothing more to do" from "epic incomplete."

A third, smaller finding survives scrutiny and should be preserved, not "fixed away": **38 current-schema events genuinely truncate past 200 chars** — a real, live prompt-verbosity issue, distinct from the empty-summary false alarm. The fix for finding 1 must not accidentally suppress or hide this real signal.

## Scope
- In `tools/agent-monitoring/generate_retro.py`'s Summary Quality section: compute the empty-summary count over current-schema events only (events where `agent` is set, or more precisely where the record's schema version is the current one — decide the exact predicate during Investigate, matching whatever the retro-loop-enforcement/validate.py tooling already uses to distinguish schema generations). Report legacy-schema records with no `summary` field as a separate, clearly-labeled bucket (e.g. "N legacy-format records, summary field not applicable") rather than silently excluding them or conflating them with genuine empty-summary problems.
- In the Tier Distribution section: exclude `EPIC_SCOPED` runs from the epic tier's DONE-rate denominator, or add a distinct column/row showing "scoped only, no implementation attempted" separately from the DONE-rate calculation, so `epic` tier's real completion rate (of runs that actually attempted implementation) is visible without being diluted by correctly-scope-only epics.
- Preserve the truncated-summary (>200 chars) count exactly as-is — this finding is real and should remain visible in the report.
- Add a short note to `docs/guides/agent_monitoring.md`'s "Report Sections" table clarifying both corrected semantics, so a future reader of the report doesn't need to re-derive this investigation from scratch.

## Out of Scope
- Fixing the 38 real truncated summaries themselves (tightening the actual agent prompts that produce them) — that's a prompt-engineering follow-up informed by this report, not part of fixing the report's own accuracy.
- Any change to `validate.py` (tracked separately in `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`) or to the run_id/event join issues (tracked in `TCK-20260705-MONITORING-RUNID-JOIN`) — this ticket only touches `generate_retro.py`'s metric computation and reporting.
- Re-running/regenerating the two already-committed reports (`RETRO-ALL.md`, `RETRO-2026-W27.md`) as part of this ticket — their existing Notes sections already manually document these findings; regenerating them with the fixed tool is a natural but separate follow-up action, not a blocking requirement of this ticket's Acceptance Criteria.

## Acceptance Criteria
- [x] Empty-summary count in generated retro reports is computed over current-schema events only; legacy-schema records with no `summary` field are reported in a separate, clearly-labeled category, not merged into the same warning.
- [x] Re-running `python3 tools/agent-monitoring/generate_retro.py --all` after the fix shows 0 empty summaries under the "current schema" count, with 258 legacy records now reported separately and clearly labeled as not applicable.
- [x] Epic tier's DONE-rate calculation excludes `EPIC_SCOPED` runs from the denominator via a new `Scoped` column — re-running the all-time report shows epic tier at 79% (31/39), not 44% (26/58). Also fixed the same missing `final_status`/`status` fallback throughout `done_count`/`gate_fails`/`_update_index()` — the same root cause already fixed in the sibling `validate.py` ticket, without which the 79% target was mathematically unreachable (only 67%).
- [x] The truncated-summary (>200 char) count is unchanged at 46, and remains visible.
- [x] `docs/guides/agent_monitoring.md`'s Report Sections table documents both corrected semantics, plus a Validation-section note that `generate_retro.py` now shares the same fallback pattern as `validate.py`.

## Related Tickets
- TCK-20260704-RETRO-LOOP-ENFORCEMENT (shipped the tooling that produced the first real report surfacing these findings)
- TCK-20260705-MONITORING-RUNID-JOIN (sibling finding, distinct root cause — run_id/event join mismatches)
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP (sibling finding, distinct root cause — validate.py's own blind spot)

## Related Docs
- docs/guides/agent_monitoring.md (Report Sections table — needs the clarifying note)
- agent-monitoring/retro/RETRO-ALL.md and RETRO-2026-W27.md (this ticket's originating findings, already documented in their Notes sections)
- docs/agent-monitoring/schema.md (for the precise legacy-vs-current schema distinction to reuse consistently)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py (Summary Quality section, Tier Distribution section)
- agent-monitoring/events.jsonl, agent-monitoring/runs.jsonl (read-only — data being reported on)

## Assumptions / Open Questions
- The exact predicate for "current schema vs. legacy" should be decided consistently with however `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` and the broader schema-enforcement idea doc (`docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md`) end up defining it — ideally a single shared definition, not three independently-invented ones across different tools. Worth checking during Plan whether a small shared helper (e.g. `is_legacy_schema_record(record)`) belongs in a common location rather than being reimplemented per-tool.

## Implementation Notes
Implemented all 6 steps from `staging_artifacts/TCK-20260705-RETRO-METRIC-ACCURACY/plan.md` exactly, no deviations.

1. Added `_resolve_status(r)` (`final_status or status`, exact-string comparison only — no legacy status-string normalization) and `_is_legacy_event(e)` (`agent is None`) as two separate helpers in `tools/agent-monitoring/generate_retro.py`, per the plan's explicit instruction not to merge the two legacy-schema discriminators.
2. Applied `_resolve_status` to `done_count`, `gate_fails`, `gate_counter`, and the `tier_done` loop inside `generate()`.
3. Added a `tier_scoped` counter (incremented when `_resolve_status(r) == "EPIC_SCOPED"`) and a new `Scoped` column in the Tier Distribution table; DONE-rate denominator is now `n - scoped`, generic across all tier labels (no hardcoded `"epic"` check).
4. Split Summary Quality into `Empty summary (current schema)` (computed only over events where `agent` is set) and `Legacy-format records (summary field not applicable)` (count of `agent is None` events). `long_summaries` (`Truncated (>200 chars)`) was left completely untouched — still computed over ALL events, unfiltered.
5. Applied the same `_resolve_status` fallback to `_update_index()`'s independent `done`/`fails` computation (lines formerly 252-253).
6. Updated `docs/guides/agent_monitoring.md`'s Report Sections table (Tier Distribution row now explains the Scoped-column exclusion and the 44%→79% correction; Summary Quality row now explains the current-schema/legacy split) and added a sentence to the Validation section noting `generate_retro.py` now shares the same `final_status`/`status` fallback pattern as `validate.py`. Ran `make knowledge-index-update` afterward since a `docs/` file changed (1 file re-embedded, 9 chunks).

No deviations from plan.md — no "Deviations" section was needed.

**Real regeneration performed** (not just a dry-run diff): ran `python3 tools/agent-monitoring/generate_retro.py --all` and `python3 tools/agent-monitoring/generate_retro.py --week 2026-W27` against live data. Measured results (at implement time: 481 total runs, 1965 total events — grown slightly since Plan's 481/1965 snapshot, consistent with the append-only-log drift the plan explicitly anticipated):
- Run Summary "Completed (DONE)": 403/481 = 83% (was 342/480 = 71% pre-fix).
- Gate failures: 58 (was 119 pre-fix); `gate_counter` breakdown now shows real legacy status labels (`success: 16, completed: 12, None: 10, complete: 8, done: 5, ...`) instead of collapsing them into `None`.
- Tier Distribution `epic` row: `| epic | 58 | 19 | 31 | 79% |` — matches plan's predicted 31/39 = 79.49% → floors to 79%. `hotfix`: `| hotfix | 62 | 0 | 60 | 96% |`. `standard`: `| standard | 338 | 0 | 296 | 87% |`. Only `epic` (19) and `epic_batch` (1) have non-zero `Scoped`.
- Summary Quality: `Empty summary (current schema) | 0`, `Legacy-format records (summary field not applicable) | 258`, `Truncated (>200 chars) | 46` — unchanged from the pre-fix committed value, confirming AC4. The `⚠` warning line does not render (current-schema empty count is 0).
- `agent-monitoring/retro/index.md`'s `2026-W27` row (`80 | 77 | 3`) matches `RETRO-2026-W27.md`'s own Run Summary (`77 (96%)` DONE, `3` gate failures, `80` total runs) — confirms Step 5's cross-artifact consistency requirement.

**Notes-section preservation**: regenerating both reports overwrote the human-written Notes sections from the prior retro-running session (the ones documenting the original, now-fixed findings). Per the task's explicit instruction, re-added equivalent Notes content to both `RETRO-ALL.md` and `RETRO-2026-W27.md` stating that this ticket corrected the counting, that the original raw findings are preserved in this ticket's stored artifacts, and reframing each report's numbered "what changed"/"what to watch" analysis around the corrected numbers — so the institutional-memory rule in `docs/guides/agent_monitoring.md`'s Retrospective Process ("Do not discard notes") is honored. Note: an intermediate verification pass during Test re-ran `generate_retro.py --all`/`--week`, which (correctly, per how the tool always works) reset the Notes sections to the placeholder a second time; they were re-added a second time with current, re-verified numbers before Verify ran — the final committed Notes reflect the last, correct regeneration, not an intermediate one.

**Disclosed, out-of-scope finding**: independent test-phase verification found `_update_index()`'s "ALL" row in `agent-monitoring/retro/index.md` is permanently hardcoded to `0 | 0 | 0` — `_update_index()` buckets runs by `iso_week(start_ts)` and looks up `runs_by_week.get("ALL", [])`, but no run's ISO week is ever literally the string `"ALL"`, so the lookup always misses regardless of real data. This bug **predates this ticket** (confirmed: the underlying grouping logic this ticket touched was only the `done`/`fails` fallback computation inside the per-row loop, not the `runs_by_week` lookup key itself) and is not fixed here — this ticket's Scope only covers `generate()`'s and `_update_index()`'s DONE/gate-fail *counting* logic, not this separate indexing-key mismatch. Worth a small follow-up ticket, not actioned in this one.

## Test Summary
No pytest test harness exists for `tools/agent-monitoring/*.py` (confirmed by `test_plan.md`, matching the established convention for this tool family — same precedent as the sibling `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` ticket). Verification was via direct CLI execution + inspection, matching `test_plan.md`'s prescribed method:
- `python3 -c "import ast; ast.parse(...)"` — confirmed no syntax errors after all edits.
- `python3 tools/agent-monitoring/generate_retro.py --all` — ran clean, regenerated `RETRO-ALL.md`; all AC-mapped numbers verified by direct inspection (see Implementation Notes above): DONE 403/481 (83%), epic tier 31/39 (79%) with Scoped=19, Summary Quality split (0 current / 258 legacy / 46 truncated unchanged).
- `python3 tools/agent-monitoring/generate_retro.py --week 2026-W27` — ran clean, regenerated `RETRO-2026-W27.md` and (via `main()`) `_update_index()`; cross-checked `index.md`'s `2026-W27` row against the report's own Run Summary — numbers agree (77 DONE / 3 gate failures / 80 runs in both).
- Confirmed no other tier's `Scoped` column is non-zero except `epic` (19) and `epic_batch` (1), matching plan.md's Step 3 Verify prediction.
- Confirmed the empty-summary `⚠` warning line does not render in either regenerated report (current-schema count is 0 in both).
- Manually re-read the edited `docs/guides/agent_monitoring.md` Report Sections/Validation rows against the actual Step 2-5 code for accuracy (docs-only change, no command to run per plan.md's own Step 6 Verify).

## Files Changed
- `tools/agent-monitoring/generate_retro.py` — added `_resolve_status`/`_is_legacy_event` helpers; applied fallback to `done_count`/`gate_fails`/`gate_counter`/`tier_done`/`_update_index()`; added `tier_scoped` + Scoped column to Tier Distribution; split Summary Quality into current-schema/legacy buckets.
- `docs/guides/agent_monitoring.md` — updated Tier Distribution and Summary Quality rows in the Report Sections table; added a sentence to the Validation section.
- `agent-monitoring/retro/RETRO-ALL.md` — regenerated with corrected metrics; Notes section rewritten to document the fix and point to stored artifacts for historical findings.
- `agent-monitoring/retro/RETRO-2026-W27.md` — regenerated with corrected metrics; Notes section rewritten to document the fix and point to stored artifacts for historical findings.
- `agent-monitoring/retro/index.md` — regenerated (auto-updated by `_update_index()`, no manual edit).

## Completion Summary
Fixed three counting bugs in `tools/agent-monitoring/generate_retro.py`, not just the two originally scoped: the empty-summary false alarm (100% legacy-data noise, now correctly split into "current schema: 0" vs. "legacy: 258"), the epic-tier DONE-rate miscalculation (`EPIC_SCOPED` no longer counted as failure, corrected to 79% via a new `Scoped` column), and a third, investigation-discovered issue — every DONE-classifying computation in the file (`done_count`, `gate_fails`, `tier_done`, `_update_index()`) lacked the `final_status`-or-legacy-`status` fallback already established in `validate.py`/`retro_nudge_hook.py`, without which the epic-tier fix's own 79% target was mathematically unreachable (only 67%). Both retro reports regenerated for real against live data with numbers verified to match plan predictions exactly; institutional-memory Notes sections re-added twice (once after implementation, once after an intermediate Test-phase regeneration reset them again) so the fix itself is documented, not just applied silently. One genuinely pre-existing, unrelated bug was found and explicitly disclosed rather than silently fixed or ignored: `index.md`'s "ALL" row is permanently hardcoded to `0|0|0` due to an indexing-key mismatch in `_update_index()`, a separate issue from the DONE-counting logic this ticket touched.
