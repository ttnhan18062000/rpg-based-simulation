---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-RETRO-METRIC-ACCURACY
artifact_type: plan
tags: [agent-monitoring, retro, data-quality, schema-fallback]
---

# Implementation Plan — TCK-20260705-RETRO-METRIC-ACCURACY

## Summary

Fix three bugs in `tools/agent-monitoring/generate_retro.py`, all sharing one root cause (two schema generations, no explicit version field): (1) split the empty-summary count into current-schema vs. legacy-format buckets so the "check agent prompts" warning stops firing on 258 pre-normalization `events.jsonl` records that never had a `summary` field; (2) exclude `EPIC_SCOPED` runs from the Tier Distribution DONE-rate denominator via a new `Scoped` column; (3) — **added to scope, per investigation's Finding 3, confirmed by direct measurement below** — apply the precedented `final_status or status` fallback (already used in `retro_nudge_hook.py:49` and `validate.py`) to every DONE/gate-fail computation in the file (`done_count`, `gate_fails`/`gate_counter`, `tier_done`, and `_update_index()`'s independent `done`/`fails`), because AC3's own target of 79% (31/39) is mathematically unreachable without it (Finding 2 alone yields 67%, confirmed against live `runs.jsonl`). Two separate, non-merged helper functions are introduced (`_resolve_status` for `runs.jsonl`, `_is_legacy_event` for `events.jsonl`) — the two legacy-schema concepts are different fields in different files and must not share one predicate. The truncated-summary (`long_summaries`) computation is explicitly **not** touched by the schema-scoping fix, preserving its currently-committed value of 46 (verified directly against `RETRO-ALL.md`), not 38.

## Steps

### Step 1 — Add two schema-discriminator helpers

- **Files:** `tools/agent-monitoring/generate_retro.py`
- **Change:** After `fmt_pct` (currently ends at line 50) and before `def generate(...)` (currently line 53), add:
  ```python
  def _resolve_status(r):
      """Fallback-aware run status for runs.jsonl. Current schema writes
      final_status; legacy (pre-normalization) records write only status.
      Mirrors the precedented pattern in retro_nudge_hook.py:49 and
      validate.py (post TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP).
      Only bridges the field-presence gap — does NOT normalize legacy
      status-string spellings (e.g. "success", "done", "complete") to
      "DONE"; those remain distinct, literal values by design."""
      return r.get("final_status") or r.get("status")


  def _is_legacy_event(e):
      """events.jsonl legacy-schema discriminator: agent is None on
      pre-normalization records (free-text `event` field, no `summary`).
      Distinct from _resolve_status's runs.jsonl discriminator — different
      field, different file. Do not merge these two predicates."""
      return e.get("agent") is None
  ```
- **Do NOT touch:** `load_jsonl`, `iso_week`, `week_range`, `current_week`, `fmt_pct` bodies.
- **Verify:** `python3 tools/agent-monitoring/generate_retro.py --all` runs without error and produces **byte-identical** output to the pre-change baseline (helpers added but not yet called anywhere) — confirms no syntax error and no behavior change yet. Capture this baseline file (`diff` target for later steps).

### Step 2 — Apply `_resolve_status` to `generate()`'s DONE/gate-fail computations

- **Files:** `tools/agent-monitoring/generate_retro.py`
- **Change:** Inside `generate()`:
  - Line 59: `done_count = sum(1 for r in runs if r.get("final_status") == "DONE")` → `done_count = sum(1 for r in runs if _resolve_status(r) == "DONE")`
  - Line 60: `gate_fails = [r for r in runs if r.get("final_status") not in (...)]` → same tuple, condition on `_resolve_status(r)`
  - Line 70: `gate_counter = Counter(r.get("final_status") for r in gate_fails)` → `gate_counter = Counter(_resolve_status(r) for r in gate_fails)` (so a legacy run whose real status is e.g. `GATE_FAIL`/`STOPPED_BY_USER` is labeled correctly instead of showing as `None` in the breakdown — the same data gate_fails now filters on)
  - Lines 74-77 (`tier_done` loop): condition `r.get("final_status") == "DONE"` → `_resolve_status(r) == "DONE"`
- **Do NOT touch:** `durations`/`avg_dur` (lines 62-64), `agent_counts`/`avg_agents` (66-67), `tier_counts` (line 73 — stays a raw per-tier run count, untouched), `agent_stats` (80-82). Do NOT extend `_resolve_status` comparisons to match lowercase/alternate spellings (`"success"`, `"done"`, `"complete"`, `"completed"`) — confirmed present in live data (16/12/8/5 occurrences respectively) but out of scope; the precedent is a literal `== "DONE"` fallback only, not a status-vocabulary normalization.
- **Verify:** Run `python3 tools/agent-monitoring/generate_retro.py --all`. Against live `agent-monitoring/runs.jsonl` (481 runs total, measured directly during Plan):
  - Run Summary "Completed (DONE)" goes from `343 (71%)` → `403 (83%)`.
  - "Gate failures" goes from `119` → `58`.
  - `gate_counter` breakdown now includes `success: 16, completed: 12, None: 10, complete: 8, done: 5, DOD_BLOCKED: 2, INPROGRESS: 1, NEEDS_HUMAN_INPUT: 1, GATE_FAIL: 1, ALL_SCOPED: 1, STOPPED_BY_USER: 1` (confirms the mislabeled-as-`None` legacy DONE runs are gone from the breakdown, and other legacy statuses now render their real value instead of `None`).

### Step 3 — Tier Distribution: exclude `EPIC_SCOPED` from the DONE-rate denominator via a new `Scoped` column

- **Files:** `tools/agent-monitoring/generate_retro.py`
- **Change:**
  - Add a `tier_scoped = defaultdict(int)` counter alongside `tier_done`, incremented when `_resolve_status(r) == "EPIC_SCOPED"`, keyed the same way as `tier_done` (`r.get("tier", "unknown")`).
  - Change the Tier Distribution table header (line 132) from `| Tier | Count | DONE count | DONE rate |` to `| Tier | Count | Scoped | DONE count | DONE rate |`.
  - Change the row-rendering loop (lines 134-137):
    ```python
    for tier in sorted(tier_counts):
        n = tier_counts[tier]
        scoped = tier_scoped[tier]
        d = tier_done[tier]
        denom = n - scoped
        lines.append(f"| {tier} | {n} | {scoped} | {d} | {fmt_pct(d, denom)} |")
    ```
  - This is generic across all tier labels (no hardcoded `"epic"` check) — applies uniformly to `epic`, `epic-batch`, `epic_batch`, `hotfix`, `standard`, `unknown`, etc. Tiers with zero `EPIC_SCOPED` runs get `scoped == 0` and `denom == n`, so their rate is unchanged in formula (though the underlying `DONE count` itself changes per Step 2's fallback fix — that is expected, in-scope, and not a Step 3 side effect).
- **Do NOT touch:** `tier_counts` itself (still the raw per-tier total, unchanged, remains the `Count` column).
- **Verify:** Run `python3 tools/agent-monitoring/generate_retro.py --all`. Confirm the rendered `epic` row reads `| epic | 58 | 19 | 31 | 79% |` (measured directly: 31/(58-19) = 31/39 = 79.49%, `fmt_pct`'s integer floor renders `79%`, matching AC3's literal target). Confirm no other tier's `Scoped` column is non-zero except `epic_batch` (1 run, `scoped=1`) — spot-checked directly via `Counter(r.get("tier") for r in runs if _resolve_status(r)=="EPIC_SCOPED")`. Confirm `hotfix` reads `| hotfix | 62 | 0 | 60 | 96% |` and `standard` reads `| standard | 338 | 0 | 296 | 87% |` (both driven purely by Step 2's fallback, `Scoped` column correctly 0).

### Step 4 — Summary Quality: split empty-summary count into current-schema vs. legacy bucket; leave truncation untouched

- **Files:** `tools/agent-monitoring/generate_retro.py`
- **Change:**
  - Line 85: replace
    ```python
    empty_summaries = sum(1 for e in events if not e.get("summary", "").strip())
    ```
    with
    ```python
    legacy_events = [e for e in events if _is_legacy_event(e)]
    current_events = [e for e in events if not _is_legacy_event(e)]
    empty_summaries_current = sum(1 for e in current_events if not e.get("summary", "").strip())
    legacy_event_count = len(legacy_events)
    ```
  - Line 86 (`long_summaries`): **leave completely unchanged** — `long_summaries = sum(1 for e in events if len(e.get("summary", "")) > 200)`, still computed over ALL events (current + legacy), no schema filter. See Anti-Drift Notes for why this is a deliberate, evidence-backed decision, not an oversight.
  - Lines 160-166 (table + warning): replace
    ```python
    lines.append(f"| Empty summary | {empty_summaries} |")
    lines.append(f"| Truncated (>200 chars) | {long_summaries} |")
    if empty_summaries > 0:
        ...
        lines.append(f"_⚠ {empty_summaries} empty summaries — check agent prompts for `summary` field._")
    ```
    with
    ```python
    lines.append(f"| Empty summary (current schema) | {empty_summaries_current} |")
    lines.append(f"| Legacy-format records (summary field not applicable) | {legacy_event_count} |")
    lines.append(f"| Truncated (>200 chars) | {long_summaries} |")
    if empty_summaries_current > 0:
        lines.append("")
        lines.append(f"_⚠ {empty_summaries_current} empty summaries (current schema) — check agent prompts for `summary` field._")
    ```
- **Do NOT touch:** `long_summaries`'s computation or its table row — must remain sourced from ALL events, unfiltered.
- **Verify:** Run `python3 tools/agent-monitoring/generate_retro.py --all`. Confirm Summary Quality table reads:
  ```
  | Empty summary (current schema) | 0 |
  | Legacy-format records (summary field not applicable) | 258 |
  | Truncated (>200 chars) | 46 |
  ```
  (measured directly: 1965 total events, 258 with `agent is None`, 1707 with `agent` set, 0 of the 1707 have an empty summary, 246 of the 258 legacy records do — all inside the legacy bucket, none inside "current schema"). Confirm the `⚠` warning line does **not** render (since `empty_summaries_current == 0`). Confirm `Truncated (>200 chars)` is unchanged at **46**, not 38 — this is the exact value already committed in `agent-monitoring/retro/RETRO-ALL.md` line 91 and consistent with `RETRO-2026-W27.md` line 68 (`8`, also an all-events count) — grep both files to confirm before/after diff shows zero change to this one line.

### Step 5 — Apply the same `_resolve_status` fallback inside `_update_index()`

- **Files:** `tools/agent-monitoring/generate_retro.py`
- **Change:** In `_update_index()` (lines 235-256), lines 252-253:
  ```python
  done = sum(1 for r in week_runs if r.get("final_status") == "DONE")
  fails = sum(1 for r in week_runs if r.get("final_status") not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS"))
  ```
  → 
  ```python
  done = sum(1 for r in week_runs if _resolve_status(r) == "DONE")
  fails = sum(1 for r in week_runs if _resolve_status(r) not in ("DONE", "EPIC_SCOPED", "IN_PROGRESS"))
  ```
  `_update_index()` is a separate function with its own independent load of `runs.jsonl` and its own `done`/`fails` computation (confirmed by direct read — it does not call `generate()` or share any variable with it); it must be fixed here explicitly or it will silently diverge from the main report's now-corrected numbers. No new shared module across files is introduced (that would be cross-tool scope beyond this ticket's Related Code Areas, which name only `generate_retro.py`) — both call sites within this one file now go through the same in-file `_resolve_status` helper, which is sufficient to remove the duplication risk this ticket is scoped to fix.
- **Do NOT touch:** the rest of `_update_index()` (file globbing, index table header/row format, `iso_week` grouping).
- **Verify:** Run `python3 tools/agent-monitoring/generate_retro.py --week 2026-W27` (or re-run `--all`, which also calls `_update_index()` via `main()`) and inspect `agent-monitoring/retro/index.md`. For the `2026-W27` row, confirm its `DONE`/`Gate failures` numbers match what `RETRO-2026-W27.md`'s own Run Summary shows for `done_count`/`len(gate_fails)` after Steps 2 applies — i.e. the two artifacts must agree with each other post-fix, not just individually look plausible.

### Step 6 — Document both corrected semantics in the guide

- **Files:** `docs/guides/agent_monitoring.md`
- **Change:** In the "Report Sections" table (lines 57-64):
  - Update the **Tier Distribution** row: `Are hotfix tickets actually taking a fast path? High hotfix gate-fail rate = wrong tier.` → append: `A tier's DONE rate is computed excluding EPIC\_SCOPED runs (shown in a separate Scoped column) — EPIC\_SCOPED is a correct terminal state for scope-only epics, not a failure, and inflating the denominator with it previously understated epic tier health (44% vs. the real 79%).`
  - Update the **Summary Quality** row: `Any empty summaries → fix agent prompt. Truncation frequent → responses too verbose.` → `Empty-summary count is scoped to current-schema events only (agent field set); pre-normalization legacy events (agent is null) never had a summary field and are reported separately as "Legacy-format records," not as a prompt-quality issue. Truncation count still covers all events (current + legacy).`
  - Also add one sentence near the existing "Validation" section's note about `validate.py`'s `final_status`/`status` tolerance (line 81-83), stating `generate_retro.py` now applies the same fallback for its DONE/gate-fail counts (Run Summary, Gate Failure Breakdown, Tier Distribution, and the retro index) — so a reader doesn't assume only `validate.py` handles legacy records.
- **Do NOT touch:** any other section of the guide (How to Generate, Querying Raw Data, Retrospective Process, Makefile Targets, Schema Reference).
- **Verify:** Re-read the edited table/section for accuracy against the actual Step 2-5 code; no command to run (docs-only change). Since this file is under `docs/`, run `make knowledge-index-update` after this step per the project's doc-change rule.

## Scope Guards

- Finding 3 (the `final_status`/`status` fallback across `done_count`, `gate_fails`/`gate_counter`, `tier_done`, and `_update_index()`) **is in scope** for this ticket. Rationale: it is the identical root cause and precedented fix pattern already shipped in `retro_nudge_hook.py:49` and `validate.py` (via `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`), and AC3's own stated target (79%, 31/39) is provably unreachable without it — Finding 2 alone caps the rate at 67% (26/39), confirmed by direct computation against live `runs.jsonl`.
- The events.jsonl legacy discriminator (`agent is None`, Finding 1 / `_is_legacy_event`) and the runs.jsonl legacy discriminator (`final_status is None`, Finding 3 / `_resolve_status`) are **kept as two separate helper functions**, never merged into one shared predicate — they gate different fields in different files.
- `long_summaries` (truncated-summary count) is **not** touched by the current-schema scoping applied to `empty_summaries`. This is a deliberate, evidence-backed decision: the already-committed `agent-monitoring/retro/RETRO-ALL.md` (line 91) and `RETRO-2026-W27.md` (line 68) both show the all-events count (46 and 8 respectively), not the current-schema-only count (38 for all-time). Scoping `long_summaries` to current-schema-only would silently regress AC4 ("unchanged") from 46 to 38 in the very report this ticket's own Related Docs section names as its baseline.
- Do not normalize legacy status-string variants (`"success"`, `"done"`, `"complete"`, `"completed"` — all confirmed present in live `runs.jsonl` via direct measurement) to `"DONE"`. The precedented fallback pattern bridges only the `final_status`-vs-`status` field-presence gap via exact-string comparison to `"DONE"`; it does not redefine what counts as "done." These records correctly continue to appear in `gate_fails`/`gate_counter` post-fix. This is a known, pre-existing data-vocabulary inconsistency, out of this ticket's scope.
- Do not touch `validate.py`, `record_run.py`, `record_events.py`, or the run_id/event join logic — tracked in sibling tickets `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` (done) and `TCK-20260705-MONITORING-RUNID-JOIN`.
- Do not regenerate/commit new `RETRO-ALL.md`/`RETRO-2026-W27.md` output as part of this ticket's required scope (per ticket's Out of Scope) — the Verify steps above run the tool locally to confirm correctness, but committing the regenerated reports is a natural, separate follow-up action, not a blocking AC.
- No new pytest tests are introduced, per `test_plan.md`'s established no-test-harness convention for `tools/agent-monitoring/*.py`; verification is direct CLI execution + diff, consistent with the sibling `VALIDATE-SCHEMA-GAP` ticket's precedent.

## Dependency Map

- Step 1 (helpers) is a prerequisite for Steps 2, 3, 4, 5 — all of them call `_resolve_status` and/or `_is_legacy_event`.
- Step 2 (done_count/gate_fails/gate_counter/tier_done fallback) must land before Step 3 (Tier Distribution rendering) — Step 3's `denom = n - scoped` and rate column depend on `tier_done` already being fallback-aware from Step 2, otherwise the DONE numerator and EPIC_SCOPED-exclusion denominator would be computed on inconsistent bases.
- Step 4 (Summary Quality) is independent of Steps 2/3 — different section, different data (`events`, not `runs`) — but shares Step 1's helpers.
- Step 5 (`_update_index()`) depends on Step 1 only, but should be verified *after* Step 2, since its Verify step diffs its output against `generate()`'s now-corrected `done_count`/`gate_fails` for consistency.
- Step 6 (docs) should be last — it documents the final, verified behavior of Steps 2-5.

## Acceptance Criteria Map

| AC | Steps | Verified by |
|---|---|---|
| AC1: empty-summary count computed over current-schema events only; legacy records reported in a separate, clearly-labeled category | Step 1, Step 4 | Step 4 Verify: table shows `Empty summary (current schema) | 0` and `Legacy-format records (summary field not applicable) | 258` as distinct rows |
| AC2: re-running `--all` shows ~0 empty summaries under "current schema", ~246 legacy records reported separately and labeled not-applicable | Step 4 | Step 4 Verify: exact measured values (0 current, 258 legacy bucket containing the 246 empty ones) |
| AC3: epic tier DONE-rate excludes `EPIC_SCOPED`, shows ~79% (31/39) | Step 2, Step 3 | Step 3 Verify: rendered row `| epic | 58 | 19 | 31 | 79% |` |
| AC4: truncated-summary (>200 char) count unchanged | Step 4 (explicit non-change) | Step 4 Verify: diff shows `Truncated (>200 chars) | 46` before and after, matching already-committed `RETRO-ALL.md` |
| AC5: `docs/guides/agent_monitoring.md` Report Sections table documents both corrected semantics | Step 6 | Step 6 Verify: manual re-read of edited rows against Steps 2-5's actual behavior |
| (Added) Finding 3 fallback consistently applied across `done_count`, `gate_fails`/`gate_counter`, `tier_done`, `_update_index()` | Steps 2, 3, 5 | Step 2 Verify (Run Summary/Gate Breakdown numbers), Step 3 Verify (Tier Distribution per-tier numbers), Step 5 Verify (index.md agreement with main report) |

## Anti-Drift Notes

- The two legacy-schema discriminators are structurally different and must stay in two functions (`_resolve_status` for `runs.jsonl`'s `final_status`/`status`; `_is_legacy_event` for `events.jsonl`'s `agent`). A future refactor that tries to unify them into one "is this record legacy?" helper would be factually wrong — they gate different fields in different files with different value spaces.
- `long_summaries` must remain computed over ALL events (current + legacy), unconditionally, matching the exact pre-existing line 86 logic untouched. This was confirmed against the actual committed `RETRO-ALL.md` (46) and `RETRO-2026-W27.md` (8) — both are all-events counts, not current-schema-only (which would read 38 all-time). Do not "fix" this into scoped-only as a misguided consistency pass with `empty_summaries`.
- `_update_index()` independently re-implements the `done`/`fails` counting rather than calling into `generate()` — this plan fixes both call sites in-file via the shared `_resolve_status` helper rather than trying to make `_update_index()` call `generate()` or share more state; that refactor is out of scope and unnecessary for correctness.
- Gate breakdown labels will start showing previously-hidden legacy status values (`success`, `completed`, `complete`, `done` lowercase, etc.) once `gate_counter` uses `_resolve_status`. This is expected and correct (the same data was previously misclassified as `None`), not a new bug — do not attempt to collapse or reinterpret these into `"DONE"` during implementation.
- Numbers in this plan's Verify steps (481 total runs, 403/58 done/gate-fail split, 1965 total events, 258 legacy events, 46/38 truncation split, etc.) were measured directly against the live `agent-monitoring/runs.jsonl`/`events.jsonl` during Plan on 2026-07-05; the append-only logs will keep growing, so exact counts at Verify/Implement time may drift slightly upward — the *ratios and qualitative direction* (epic ≈79%, current-schema empty ≈0, truncation unchanged at whatever the pre-fix run showed) are the actual acceptance bar, not the literal integers frozen here.

## Unresolved Questions

None. All four open questions raised in `investigation.md`'s Risks and Open Questions section were resolved above with direct evidence:
1. Finding 3 is in scope (AC3 unreachable otherwise; identical precedent already shipped twice).
2. The two legacy-schema discriminators stay separate (`_resolve_status` vs. `_is_legacy_event`).
3. The truncated-summary count must stay at the all-events value — confirmed directly by reading the committed `RETRO-ALL.md` (46) and `RETRO-2026-W27.md` (8), not 38.
4. `_update_index()` has its own independent computation (confirmed by direct code read, lines 235-256) and is fixed in-file via the same shared `_resolve_status` helper as `generate()`, not by making one call the other.
