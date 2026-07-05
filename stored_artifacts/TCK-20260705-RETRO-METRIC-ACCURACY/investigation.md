---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-RETRO-METRIC-ACCURACY
artifact_type: investigation
tags: [agent-monitoring, retro, data-quality, schema-fallback]
---

# Investigation — TCK-20260705-RETRO-METRIC-ACCURACY

## Current Behavior (file:line)

All three findings live in `tools/agent-monitoring/generate_retro.py`. Confirmed by direct read of the current file (261 lines total).

### Finding 1 — empty-summary false alarm (events.jsonl legacy format)

- `generate()` line 85: `empty_summaries = sum(1 for e in events if not e.get("summary", "").strip())` — counts over **all** events, no schema-generation filter.
- Line 158-166: renders `| Empty summary | {empty_summaries} |` and, if `empty_summaries > 0`, an unconditional `_⚠ {empty_summaries} empty summaries — check agent prompts for `summary` field._` warning.
- Direct measurement against the live `agent-monitoring/events.jsonl` (1965 events as of this investigation, grown since the ticket was filed against a smaller snapshot):
  - `agent` is `None` on 258 records; of those, 239 carry a legacy `event` field (`ticket_finalized`, `ticket_complete`, `epic_completed`, `ticket_done`, `implementation_complete`, etc. — 100+ distinct free-text values, none of them the current `phase`/`agent`/`status`/`summary` schema).
  - **All 246 empty-summary events are `agent: None` records.** 0 of 1707 current-schema events (`agent` set) have an empty summary.
  - 38 current-schema events truncate past 200 chars (`long_summaries` at line 86, current schema subset) — a real, separate, live finding, distinct from the false alarm and explicitly preserved per ticket Scope.
- Root cause: `events.jsonl` has no explicit schema-version field. The de facto discriminator already used elsewhere in the codebase is `agent is not None` (current schema) vs `agent is None` + presence of a legacy `event` key (pre-normalization). `generate_retro.py` never applies this discriminator to `empty_summaries`.

### Finding 2 — epic DONE-rate excludes nothing (Tier Distribution)

- Line 73: `tier_counts = Counter(r.get("tier", "unknown") for r in runs)` — denominator per tier, includes every run regardless of `final_status`.
- Lines 74-77: `tier_done` increments only when `r.get("final_status") == "DONE"` — numerator.
- Lines 130-137 render `| {tier} | {n} | {d} | {fmt_pct(d, n)} |` — `EPIC_SCOPED` (a correct terminal state per `implement-ticket.js`'s epic tier, which scopes only and does no implementation) sits in the denominator `n` as a non-DONE run, diluting the rate.
- Direct measurement against `agent-monitoring/runs.jsonl` (58 `tier=="epic"` runs currently):
  - `final_status == "DONE"` only: **26**
  - `final_status in {"EPIC_SCOPED"}` (fallback-aware): **19**
  - Current report: 26/58 = 44%.
  - Ticket's proposed fix (exclude `EPIC_SCOPED` from denominator, still using `final_status`-only for DONE): 26/(58-19) = 26/39 = **67%**.

### Finding 3 — NEWLY CONFIRMED — missing `status` fallback pervades every DONE computation in this file

Verified directly by reading the current file and cross-checking against `agent-monitoring/runs.jsonl`. This is **not** in the ticket's original Scope but is real, live, and traceable to the exact same root cause the sibling ticket `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` already fixed in `validate.py`.

- `runs.jsonl` has two schema generations for the same "did this run complete" concept: current schema writes `final_status`; legacy-format runs (pre-`record_run.py` normalization, or written by an older version of it) write only `status` and leave `final_status` absent/`None`. This is documented at `docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md` (`workflow: null` / legacy field drift, same family of issue) and was the exact premise of `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`.
- The already-established, precedented fix pattern in this codebase: `tools/agent-monitoring/retro_nudge_hook.py:49` — `status = record.get("final_status") or record.get("status")` — and `tools/agent-monitoring/validate.py` line 82 (post-fix) — `status = run.get("final_status") or run.get("status")`.
- `generate_retro.py` was **never updated** to match this pattern anywhere DONE/status is computed. Confirmed four call sites, all reading `final_status` in isolation:
  - Line 59: `done_count = sum(1 for r in runs if r.get("final_status") == "DONE")` — feeds the top-level "Completed (DONE)" metric in Run Summary.
  - Line 60: `gate_fails = [r for r in runs if r.get("final_status") not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS")]` — feeds Gate Failure Breakdown; a legacy run with `status: "DONE"` but `final_status: None` is misclassified as a gate failure here (its `final_status` is `None`, which is "not in" the tuple), inflating gate-failure counts and misattributing legacy DONE runs as failures.
  - Lines 74-77 (`tier_done`): same `final_status`-only check, feeds Tier Distribution's DONE count per tier.
  - Line 253 (`_update_index()`): `done = sum(1 for r in week_runs if r.get("final_status") == "DONE")` — feeds `agent-monitoring/retro/index.md`'s per-week DONE column.
  - Line 254 (`_update_index()`, same function): `fails = sum(1 for r in week_runs if r.get("final_status") not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS"))` — same gate-fail misclassification bug replicated into the index.
- **Direct measurement confirming the compounded fix**, run against live `agent-monitoring/runs.jsonl` (58 epic-tier runs):
  ```
  final_status-only DONE:            26
  final_status-or-status DONE:       31   (+5, exactly matching the task's claim)
  EPIC_SCOPED (fallback-aware):      19
  non-scoped denominator:            39   (58 - 19)
  TRUE epic health:  31/39 = 79.49% ≈ 79%
  ```
  This matches the ticket's stated target of "approximately 79% (31/39)" in its own Acceptance Criteria — meaning **AC3 as currently worded is only satisfiable if Finding 3's fallback fix is also applied**. Fixing only the EPIC_SCOPED-exclusion (Finding 2) without the fallback yields 67% (26/39), not the 79% the ticket's own AC3 already commits to. The ticket's AC3 target number is unreachable without also fixing Finding 3.
  - Full `(final_status, status)` pair distribution for the 58 epic runs: `{('DONE', None): 26, ('EPIC_SCOPED', None): 19, (None, 'DONE'): 5, (None, None): 2, ('INPROGRESS', None): 1, (None, 'success'): 1, ('GATE_FAIL', None): 1, ('ALL_SCOPED', None): 1, ('DOD_BLOCKED', None): 1, ('STOPPED_BY_USER', None): 1}` — confirms the 5 fallback-recovered DONE runs are genuinely `final_status: None, status: "DONE"` legacy records, not a counting artifact. Also note one record has `status: "success"` (not `"DONE"`) under `final_status: None` — correctly stays out of both DONE counts under a straightforward `final_status or status == "DONE"` predicate, and one has both fields `None` (correctly falls to `"unknown"`/excluded).

## Mechanics/Engine Constraints

None — this is tooling (`tools/agent-monitoring/`), not simulation mechanics. No `docs/mechanics/` or `docs/engine/` chapter governs retro-report generation. No parity ledger entry applies (confirmed: `docs/parity_ledger/` only covers `substrate`, `combat_movement`, `strategic_cognition`, `town_resource`, `progression`, `social_narrative`, `world_dynamics`, `infrastructure` — none of which model agent-monitoring self-report tooling).

## Parity Ledger Overlap

None. This ticket does not touch simulation logic, so no `docs/parity_ledger/*.yaml` entry needs a status/evidence update.

## Prior Work

- `TCK-20260607-MON-RETRO` (`tickets/done/`, `stored_artifacts/TCK-20260607-MON-RETRO/`): original implementation of `generate_retro.py`, `validate.py`, `query.py`. Predates the legacy-schema drift entirely (schema was presumably clean/small at that point) — no schema-fallback handling was ever built in from the start.
- `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` (DONE, `tickets/done/TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP.md`): sibling ticket, same session, same root cause as Finding 3 above, but scoped to `validate.py` line 82 only. Its Implementation Notes explicitly state the fix mirrors `retro_nudge_hook.py:49`'s pattern and explicitly calls out `generate_retro.py` as a "reference — already has legacy-field-fallback handling to mirror" in its Related Code Areas — **this statement is incorrect/stale as applied to `done_count`/`tier_done`/`gate_fails`/`_update_index()`**: `generate_retro.py` has the fallback pattern in its own code only for other fields (see `week_range`/`iso_week` timestamp handling, and no `status` fallback anywhere) — it has NOT applied the `final_status or status` pattern to any of the four DONE/gate-fail computations enumerated in Finding 3. This is worth flagging as a documentation inaccuracy in the sibling ticket's already-closed Completion Summary, not something to fix retroactively, but relevant context for why this gap survived a sibling audit.
- `TCK-20260705-MONITORING-RUNID-JOIN` (referenced as sibling, distinct root cause — run_id/event join mismatches; not directly relevant to this ticket's metric-accuracy scope).
- `docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md`: the broader idea doc that documents the legacy-schema drift phenomenon (98/466 runs with `workflow: null` as of 2026-07-04) motivating both the validate.py fix and this ticket. Confirms this is a known, recurring, and NOT ticket-specific pattern — it is the third sibling instance of the same underlying schema-drift issue in this session's investigation lineage.

## Risks and Open Questions

1. **Scope expansion recommendation: YES, add Finding 3 to this ticket's Scope.** Rationale:
   - It is the exact same root cause as `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` (missing `final_status`/`status` fallback), already precedented and already accepted as a valid, narrow, mechanical fix in this same session.
   - The ticket's own AC3 ("approximately 79% (31/39)") is **only achievable if Finding 3 is fixed alongside Finding 2** — fixing Finding 2 alone caps the achievable rate at 67% (26/39). Leaving Finding 3 out means this ticket cannot satisfy its own stated Acceptance Criteria as written, i.e. the "fixed" report would still be wrong relative to the ticket's own target.
   - It affects `done_count` (Run Summary), `gate_fails`/`gate_counter` (Gate Failure Breakdown — currently misclassifying legacy DONE runs as gate failures), `tier_done` (Tier Distribution, all tiers not just epic), and `_update_index()`'s per-week `done`/`fails` columns (`agent-monitoring/retro/index.md`) — i.e. every DONE-derived number in every section of the report and the index, not just the two originally named.
   - If this repo's own hard rule ("Do not leave changes untested or untraceable" / consistency across sibling fixes in the same investigation lineage) is taken seriously, shipping a "metric accuracy" ticket that fixes 2 of 3 known accuracy bugs in the same file, in the same investigation session, with the third already precedented and measured, would be an inconsistent outcome.
2. **Naming collision risk**: this ticket already uses the term "legacy schema" for Finding 1 (events.jsonl's `agent`-null / free-text `event` field records). Finding 3's legacy/current split is a **different field, different file** (runs.jsonl's `final_status` vs `status`). The investigation and eventual Plan/Implementation must not conflate these two distinct legacy-schema concepts under one shared predicate — they are different data-quality issues in different files with different discriminating fields (`agent is None` for events.jsonl vs. `final_status is None` for runs.jsonl). A single shared `is_legacy_schema_record()` helper (raised as an open question in the ticket's own Assumptions section) would need to be schema/file-aware, or two separate small helpers (`is_legacy_event(e)`, `resolve_run_status(r)`) are more honest than one shared function pretending both files drifted identically.
3. **Whether a shared helper belongs in a common module**: the ticket's own Assumptions section raises this. Given `retro_nudge_hook.py`, `validate.py`, and (pending) `generate_retro.py` all now need the same `final_status or status` fallback for runs.jsonl, a small shared function (e.g. in a new `tools/agent-monitoring/_common.py` or similar) would eliminate a third independent reimplementation — worth deciding at Plan time, but not required for correctness (three call sites already exist with the pattern inlined, precedent tolerates duplication in this tool family so far).
4. **`fmt_pct` uses integer floor division** (`100 * n // total`) — 31/39 floors to 79% (not 79.5% rounding to 80%), consistent with the ticket's stated target of "approximately 79%". No change needed here, but worth confirming the fixed report literally renders "79%" and not "80%" during Verify.
5. **Data drift between ticket-filing time and investigation time**: the ticket's own numbers (246 empty summaries, 258 agent-null, 239 legacy-event-field, 38 truncated, 58 epic runs/26 DONE) were re-measured directly during this investigation and match exactly (including the newly-confirmed 31/39 for Finding 3), except total event/run counts have grown slightly since filing (more runs/events have landed) — this is expected for an append-only log under active development and does not change any of the three findings' validity.

## Anti-Drift Hazards

- Do not silently exclude the 258 `agent: None` legacy events from `empty_summaries` — the ticket's Scope explicitly requires a separate, clearly-labeled bucket, not silent suppression (this is the "false alarm" fix, not a "delete the data" fix).
- Do not touch the 38 genuine truncated-summary count/display — must remain exactly as-is per ticket Scope and AC4.
- Do not change `EPIC_SCOPED`'s meaning or remove it from the report — it must move to a separate denominator/column, not disappear.
- Do not apply the Finding 3 `status` fallback to fields unrelated to DONE/status classification (e.g. `duration_s`, `agent_count` at lines 62-67 are unaffected and correctly typed already — no legacy-field ambiguity exists there).
- Do not conflate the events.jsonl legacy-schema discriminator (Finding 1: `agent is None`) with the runs.jsonl legacy-schema discriminator (Finding 3: `final_status is None`) into one shared predicate without accounting for the fact that they gate different fields in different files.
- `_update_index()` (lines 235-256) is a separate function from `generate()` and has its OWN independent `done`/`fails` computation (lines 252-253) that duplicates the logic in `generate()` lines 59-60/74-77 rather than calling into shared helpers — any fix must be applied in **both** places or the main report and the index will silently disagree with each other after the fix (a new consistency bug if only one is patched).
