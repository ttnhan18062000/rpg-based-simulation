---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-MONITORING-RUNID-JOIN
artifact_type: plan
tags: [agent-monitoring, data-quality, root-cause, run-id, legacy-schema]
---

# Implementation Plan — TCK-20260705-MONITORING-RUNID-JOIN

**RE-PLAN (2026-07-05).** This revises the prior plan.md, which architecture review rejected: its core numeric claim ("126 -> ~6" after the dedup fix) was wrong. The corrected investigation.md (systematic, not illustrative) has now been independently verified three times — by architecture review, by the main session directly, and by this corrected investigation pass — converging on **126 -> 107**: only **16** `run_id`s are genuinely dedup-resolved (Class A: a same-`run_id` legacy record with no `end_ts` alongside a genuinely-complete sibling record), and **107** `run_id`s are true residual with no `end_ts` anywhere under that `run_id`. The investigation additionally found, exhaustively (not sampled), that **107/107 (100%) of the residual represent genuinely completed work** recorded under a missing or differently-named completion field — not real crashes. This re-plan keeps Step 2 (`implement-epic.js` hardening) essentially unchanged and revises Steps 1, 3, and 4 to (a) state the true numbers and (b) make an explicit, evidence-based decision on whether `validate.py` should also recognize the 107's legacy completion-field variants as "not crashed."

## Summary

Investigation found the ticket's "21 crashed / 5 zero-event" framing is stale (real count at investigation time: 126 incomplete-run warnings; 5 zero-event errors, unchanged). Of the 126, only 16 `run_id`s are dedup-resolvable (a legacy no-`end_ts` line coexists with a genuinely-complete sibling line for the same `run_id`) — dedup-by-`run_id` takes the count from **126 to 107**, not to ~6. The remaining 107 are single-`run_id` residual with no `end_ts` record at all, and the investigation's exhaustive cross-check (98/107 direct `tickets/done/` file match, the other 9 `FOLDER-*`/`EPIC-*`/maintenance wrappers individually read and confirmed via an explicit terminal-status field plus independently-DONE child tickets) found **zero genuine crashes or abandoned work** among them — the 107 are real completed work recorded under at least five distinct historical schema generations that never wrote (or wrote under a different name than) `end_ts`.

This plan: (1) fixes `validate.py`'s incomplete-run check in two parts — dedup-by-`run_id` (resolves the true 16 Class A cases, the ticket's literal "run_id/event join" remit) **and**, as a deliberate additional decision justified by the 107/107 evidence, recognition of the known legacy completion-field variants found across the 107 (closing the loop on genuinely-done historical work rather than leaving it as a permanent unexplained warning); (2) adds a verification gate to `implement-epic.js`'s batch write (the one confirmed live, currently-reproducible gap — Pattern 3); (3) documents the confirmed-historical patterns, the recognized legacy-field allowlist, and a manual-write convention in `docs/agent-monitoring/schema.md`; (4) corrects the ticket's own AC1/Request Summary framing from "21+5" to the true "126+5," classified per investigation.md's Classes A/B/C/D. All open questions are decided below with cited evidence — none are deferred.

**Resolutions of investigation's open questions:**

1. **`validate.py` dedup-by-`run_id` fix is IN SCOPE, and resolves 16 of 126 (126 -> 107), not ~120.** The sibling ticket `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` explicitly routed "run_id/event join logic" to *this* ticket (`stored_artifacts/TCK-20260705-RETRO-METRIC-ACCURACY/plan.md:153`). This ticket's title is literally "run_id/event join." The true dedup-eligible set is the 16 Class A `run_id`s (investigation.md, corrected classification) — verified three separate times (architecture review twice, main session once) at exactly 107 residual. Do not re-cite "~6" or "~120" — both are superseded, wrong figures from an earlier, non-systematic pass.

2. **Whether to ALSO recognize the 107 residual's legacy completion-field variants as "not crashed" — DECIDED YES (Option a), evidence-based.** The investigation's Class C section is unambiguous and was checked exhaustively, not sampled: **107/107 (100%)** of the true residual are genuinely completed work — 98/107 have a direct `tickets/done/*.md` file match, and the other 9 (`FOLDER-*`/`EPIC-*`/one maintenance record) each carry an explicit terminal-status field in their own JSON (`status:"DONE"`, `final_status:"DONE"`, or `status:"EPIC_SCOPED"` with `gate_failures` showing a deliberate, successful mid-batch stop) plus independently-DONE child tickets. Zero abandoned or genuinely incomplete work was found anywhere in the 107. Leaving `validate.py` warning "CRASHED?" on 107 known-good historical runs, when the completion evidence is sitting right there in the record under a different field name, does not serve this ticket's purpose ("harden against run_id/event join mismatches") — it just relocates the same false-positive problem from "duplicate-record" shape to "single-record, differently-named field" shape, which is the same class of legacy-schema tolerance the sibling ticket already established as acceptable practice (dedup by `run_id` and the `status = final_status or status` fallback both being precedents for "read the intent, not just the exact current field name"). Concretely: **Step 1 will extend `validate.py`'s completion check to treat a run as complete if it has `end_ts` OR any of the investigation's catalogued legacy completion signals**: `finished_at`, `completed_at`, `ts_end` (the `ts_start`/`ts_end`/`result`/`agent` shape), or `final_status`/`status` whose value is in an enumerated closed terminal-value set (see Step 1 code — built by reading every distinct value actually present in the data, excluding `INPROGRESS`, the one genuinely non-terminal value found). **`final_status` is NOT treated as complete on mere truthiness** — an earlier draft of this design did that and architecture review correctly caught it as value-blind (real counterexample: `TCK-20260618-AUDIT-EPIC`'s sibling record has `final_status:"INPROGRESS"`). This is a bounded, explicit, enumerated allowlist (auditable, not a heuristic "does it look complete" guess) grounded directly in the investigation's field-shape catalogue plus a direct enumeration of real data values — not a general fuzzy match. **Forward-safety**: current-schema runs always write `final_status` and `end_ts` together in the same record from the same `writeMonitoring`/batch-write call (confirmed in investigation.md's reading of `implement-ticket.js` and `implement-epic.js`); a genuine future crash writes neither. Manual/ad hoc writes (a confirmed live, ongoing pattern — Pattern 2, `AUDIT-D01-D02-D09-UPDATE`) are the one category this can't fully rule out by code structure alone, which is exactly why `final_status` is bounded to enumerated values rather than trusted on presence. **Expected outcome, now fully verified against the corrected, bounded allowlist**: applying the corrected `_record_is_complete()` (dedup + the 11-value enumerated terminal set) to the real data yields exactly **1** residual: `TCK-20260623-TYPE-CHECKER`. Its record carries a 6th, previously-uncatalogued legacy shape (`"outcome": "success"`, `"phase": "implement"`, no `end_ts`/`final_status`/`status` field at all) — confirmed genuinely complete via a direct `tickets/done/TCK-20260623-TYPE-CHECKER.md` match. Per this plan's own stated policy (do not expand the allowlist speculatively for a single record), `outcome` is **not** added to `LEGACY_COMPLETION_FIELDS` — this one residual is accepted and individually documented in Step 3 as a named, confirmed-complete exception, not chased into the code. Step 1's Verify section still requires **empirically re-running the check** to confirm this exact result (126 → 107 → 1) holds at implementation time — a small drift is possible if new runs have landed since this plan was written, but the shape of the outcome (dedup + allowlist resolving all but one already-identified, already-verified case) should not change.

3. **`implement-epic.js` hardening remains IN SCOPE and highest-value, unchanged from the prior plan.** It is the only pattern confirmed reproducible by current code (investigation.md Pattern 3). Fix must stay advisory/non-fatal per the hard rule "monitoring write failure must never fail the workflow" — implemented as an added verification+retry instruction inside the existing single `agent()` prompt, not a new blocking step.

4. **Manual-write convention gets a doc note, not tooling — unchanged.** No single script exists to lint ad hoc/manual monitoring writes (the two confirmed instances — `run-E43B-*` and `HAZARD-NATIVE-IMMUNITY-REDESIGN` — are historical, pre-dating current workflows, and the one confirmed *current* direct-invocation record, `AUDIT-D01-D02-D09-UPDATE`, already uses a stable single run_id correctly). Building a lint for a pattern with no live occurrence would be speculative tooling — documented recommendation only.

**AC1 scope correction:** the ticket's AC1 says "classify each of the 21 crashed + 5 zero-event runs." Investigation.md already classifies all 126 + 5 currently-incomplete records (Classes A/B/C/D), not just the stale 21, with the corrected 16/107 split. Step 4 updates the ticket text to state the corrected counts and cite investigation.md's classification tables as the completing evidence — this is a factual correction (more historical records merged into `runs.jsonl` since the ticket was filed hours earlier, and this investigation's own first pass under-counted the residual before being corrected), not scope creep requiring new work.

## Steps

### Step 1 — Fix `validate.py`'s incomplete-run false positives (dedup by `run_id` + recognize legacy completion-field variants)

**Files:** `tools/agent-monitoring/validate.py`

**Change, part (a) — dedup by `run_id` (resolves the true 16 Class A cases, 126 -> 107):**
Replace the per-line incomplete-run scan (current lines ~56-58):
```python
# 1. Incomplete runs (start_ts but no end_ts)
for run in runs:
    if not run.get("end_ts"):
        warnings.append(f"Incomplete run (no end_ts — CRASHED?): {run.get('run_id', '?')}")
```
with an order-independent, group-by-`run_id` version: first group all raw records by `run_id`, then only warn for a `run_id` if **none** of its records satisfy the completion check (part (b) below) — and warn **at most once per `run_id`** even if multiple incomplete legacy lines share it (confirmed real case: `TCK-20260614-ARTIFACT-BUDGET-REG` has 2 records under one run_id, neither complete under the old `end_ts`-only check). Do not rely on "last record in file wins" — aggregate-then-check, not a last-write-wins dict swap, since file ordering is not a documented guarantee.

**Change, part (b) — recognize legacy completion-field variants (per decision #2 above, drives the 107 toward its true final floor):**
Define an explicit, closed allowlist (name it, e.g., `LEGACY_COMPLETION_FIELDS` / `LEGACY_TERMINAL_STATUS_VALUES`) and use it inside the same per-`run_id` completion check:
```python
LEGACY_COMPLETION_FIELDS = ("end_ts", "finished_at", "completed_at", "ts_end")
# The full union of distinct final_status AND status values actually observed in
# agent-monitoring/runs.jsonl (12 total), minus "INPROGRESS" (the one genuinely
# non-terminal value found) — enumerated by reading BOTH fields' value sets
# independently and unioning them, not inferred, so a future value this list has
# never seen is NOT silently treated as terminal.
LEGACY_TERMINAL_STATUS_VALUES = {
    "DONE", "done", "complete", "completed", "success",
    "EPIC_SCOPED", "ALL_SCOPED",
    "DOD_BLOCKED", "NEEDS_HUMAN_INPUT", "GATE_FAIL", "STOPPED_BY_USER",
}

def _record_is_complete(rec: dict) -> bool:
    if any(rec.get(f) for f in LEGACY_COMPLETION_FIELDS):
        return True
    if rec.get("final_status") in LEGACY_TERMINAL_STATUS_VALUES:
        return True
    if rec.get("status") in LEGACY_TERMINAL_STATUS_VALUES:
        return True
    return False
```
**Corrections from architecture review's second and third passes**: (1) the original design treated *any truthy* `final_status` as complete, which is value-blind — real data contains `final_status: "INPROGRESS"` (a genuinely non-terminal value; `runs.jsonl`'s `TCK-20260618-AUDIT-EPIC` sibling record), which that version would have silently miscounted as complete. `final_status` is now bounded to the same enumerated terminal-value treatment as `status`, not treated as complete-if-truthy. (2) The first enumeration attempt scanned `final_status`'s distinct values only and missed that `status` independently carries two more real, unambiguous terminal values (`"complete"`, `"completed"`) not present in `final_status`'s own value set — the true union across **both** fields is **12** distinct values, not 10; only `INPROGRESS` is non-terminal, giving **11** enumerated terminal values (see the corrected set above). The lesson, stated explicitly so it isn't repeated: when a check reads two field names as a fallback pair, enumerate real values from **both fields independently and union them** — do not enumerate one field and assume the other's value space is a subset. This was NOT assumed from `implement-ticket.js`'s documented status list, since a manual/ad hoc write (a confirmed live, ongoing pattern — see Pattern 2/`AUDIT-D01-D02-D09-UPDATE`) could in principle write a value this repo's JS workflows never produce.

A `run_id`'s group of records is complete if **any** record in the group is complete. This is a bounded, enumerated allowlist grounded in investigation.md's catalogued schema generations (the `started_at`/`finished_at`/`status`/`phases_completed` shape; the `final_status`-present-no-`end_ts` shape; the `ts_start`/`ts_end`/`result`/`agent` shape; the `completed_at`/`status` shape; the `FOLDER-*`/`EPIC-*` wrapper `status` values) plus a direct enumeration of every distinct status-like value in the real data — not a general "any field that looks like a timestamp/status" heuristic. Do not add fields or terminal values to these lists beyond what direct data evidence supports; if the post-implementation run (see Verify) finds a residual record with an as-yet-uncatalogued legacy field or status value, that is new evidence requiring its own individually-verified `tickets/done/` cross-check before being added — do not add speculatively, and never add a value that could plausibly mean "still running" (e.g. anything resembling `INPROGRESS`/`RUNNING`/`PENDING`).

**Do NOT touch:**
- The "no events" check (current lines ~61-64) — Out of Scope per ticket text, tracked separately, and explicitly must stay unchanged per test_plan.md's Anti-Drift Test Guards.
- The working_log cross-check (already fixed by the sibling ticket `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` at `validate.py:82`) — that fix's `status = final_status or status` fallback is a different check (working_log join) and is not to be merged with or duplicated by this allowlist.
- `record_run.py` / `record_events.py` themselves — not implicated by any of the 3 confirmed patterns.
- `runs.jsonl` / `events.jsonl` content — read-only, Out of Scope. This is a read-side check change only; no backfilling.

**Verify:**
```bash
python3 tools/agent-monitoring/validate.py > /tmp/validate_before.txt 2>&1   # capture BEFORE editing
grep -c "Incomplete run" /tmp/validate_before.txt   # expect 126

# ... apply part (a) only, dedup-by-run_id, temporarily without part (b) ...
python3 tools/agent-monitoring/validate.py > /tmp/validate_dedup_only.txt 2>&1
grep -c "Incomplete run" /tmp/validate_dedup_only.txt
# EXPECT EXACTLY 107 — this is the true, three-times-independently-verified number.
# Do NOT expect ~6 here; that figure was a wrong, uncorrected under-count from an
# earlier, non-systematic investigation pass and must not be cited again.
diff <(grep "Incomplete run" /tmp/validate_dedup_only.txt | sort) \
     <(printf '%s\n' <the 107 Class-C run_ids from investigation.md, sorted>)
# must be empty (exact match)

# ... apply part (b), the legacy completion-field allowlist ...
python3 tools/agent-monitoring/validate.py > /tmp/validate_after.txt 2>&1
grep -c "Incomplete run" /tmp/validate_after.txt
# EXPECT EXACTLY 1: TCK-20260623-TYPE-CHECKER (a 6th legacy shape, "outcome":"success",
# no end_ts/final_status/status field at all — confirmed complete via a direct
# tickets/done/TCK-20260623-TYPE-CHECKER.md match; not added to the allowlist per this
# plan's policy against speculative single-record expansion). Re-measure at
# implementation time in case new runs have landed since this plan was written — small
# drift is possible, but the fix should resolve all but this one already-verified case.
# Whatever count remains, enumerate it by run_id and, for each survivor, re-run the
# investigation's own tickets/done/ cross-check methodology (exact-match file lookup,
# else explicit terminal-status field read) to confirm it is genuinely still-open
# (a real, newly-discovered crash) rather than an as-yet-uncatalogued sixth legacy
# schema shape. Any such survivor must be either (i) a genuine crash — escalate, do not
# silently document away — or (ii) a new legacy shape — hand it to Step 3's doc with its
# own named field, not folded silently into the existing allowlist without evidence.

grep -c "no events" /tmp/validate_before.txt; grep -c "no events" /tmp/validate_after.txt
# must be IDENTICAL (5 both times) — this check is untouched
python3 tools/agent-monitoring/validate.py; echo "exit=$?"
# still exits 1 (the 5 "no events" are hard errors) — unchanged from before
```
Regression guard: construct a throwaway single-line `runs.jsonl` fixture (a copy, never the real file) with one record that has **none** of `end_ts`/`final_status`/`finished_at`/`completed_at`/`ts_end` and no `status` in `{"DONE","EPIC_SCOPED"}` — confirm the fix still flags it as CRASHED. This proves both the dedup and the allowlist do not silently swallow a genuine future crash. Also construct one fixture per allowlisted field in isolation (five+ tiny fixtures) confirming each is correctly recognized as complete — this is the closest thing to unit coverage this tool family has (no pytest harness exists; see test_plan.md's Regression Surface).

### Step 2 — Add a verification gate to `implement-epic.js`'s batch monitoring write (Pattern 3)

**Files:** `.claude/workflows/implement-epic.js` (the `agent(...)` call at lines ~231-247, `batchEvents`/`batchRunId` built at lines ~213-222)

**Change:** Insert a verification instruction between the existing Step 2 (write batch events) and Step 3 (write batch run record) inside the same prompt string — do not split into a second `agent()` call (that would double the agent-call cost for every epic batch and isn't necessary; the fix is a stronger instruction inside the existing single call). Add:
```
Step 2b — verify: after Step 2, run:
  grep -c "\"run_id\":\"${batchRunId}\"" agent-monitoring/events.jsonl
Confirm the count is >= ${batchEvents.length}. If it is lower, retry Step 2 once.
If still short after retry, proceed to Step 3 anyway (per the "do NOT raise" rule below)
but prefix the WARNING in Step 3's failure message with "EVENTS-MISSING: " so a future
retro run can distinguish this from an ordinary write failure.
```
Keep the existing "If any command fails, print WARNING... do NOT raise" contract as-is for the whole block — this is additive (a stronger self-check before the run-record write), not a new blocking/fatal condition. Matches the hard rule: monitoring write failure must never fail the workflow.

**Do NOT touch:**
- The main per-ticket loop above (lines ~190-210) or `implement-ticket.js`'s own `writeMonitoring` (a separate, already-correct single-agent-call pattern per investigation.md — not implicated in Pattern 3).
- `batchRunId` / `batchStatus` / `doneCount` computation logic — unrelated to the join gap.
- Folder cleanup logic below this block.

**Verify:** No live epic batch available to exercise end-to-end in this session (would require a real folder of un-implemented tickets — out of scope to fabricate one). Verify by code inspection:
```bash
grep -n "Step 2b\|EVENTS-MISSING\|batchEvents\|record_events.py\|record_run.py" .claude/workflows/implement-epic.js
```
Confirm the new Step 2b appears between the existing Step 2 and Step 3 text, references the correct `batchRunId` variable, and the "do NOT raise" contract still covers the full block. This is a prompt-text change, not executable code — there's no unit test surface beyond confirming the instruction is present and correctly ordered.

### Step 3 — Document known limitations, the completion-field allowlist, and the manual-write convention in `docs/agent-monitoring/schema.md`

**Files:** `docs/agent-monitoring/schema.md`

**Change:** Add a "Known Limitations" (or extend an existing one, if present after re-reading the file) subsection covering:
1. **Legacy schema generations without `end_ts`, and how `validate.py` now closes the gap.** At least five historical monitoring-write generations coexist with the current schema in `runs.jsonl`: (i) `started_at`/`finished_at`/`status`/`phases_completed`/`notes`; (ii) `final_status` present but `end_ts` key absent; (iii) `ts_start`/`ts_end`/`result`/`agent`; (iv) `completed_at`/`status`; (v) `FOLDER-*`/`EPIC-*` batch wrappers using a bare `status` field. As of this ticket, `validate.py` recognizes all of these as valid completion signals (not just the current schema's `end_ts`) — see the `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` allowlist in `tools/agent-monitoring/validate.py`. This was a deliberate decision: an exhaustive audit (not a sample) found **107/107** of the previously-residual "Incomplete run (CRASHED?)" warnings were genuinely completed work (98/107 via direct `tickets/done/` file match, the other 9 via explicit terminal-status fields plus independently-DONE child tickets) — zero genuine crashes or abandoned work was found. **Final residual after the fix: exactly 1** — `TCK-20260623-TYPE-CHECKER`, a 6th legacy shape (`"outcome":"success"`, `"phase":"implement"`, no `end_ts`/`final_status`/`status` field at all) confirmed genuinely complete via a direct `tickets/done/TCK-20260623-TYPE-CHECKER.md` match. Not added to the allowlist (single-record shape, not worth a speculative code addition) — accepted as a permanently-documented, individually-verified exception. Re-confirm this exact residual (or note any drift) at implementation time via Step 1's Verify. Do not "fix" any of this by backfilling `runs.jsonl` (Out of Scope, append-only precedent) — the fix lives entirely in `validate.py`'s read-side interpretation.
2. **The `run-{code}-{unix_ts}` run_id convention and ad hoc `-REDESIGN`-style suffixes** are pre-refactor/manual-session artifacts (confirmed via `.claude/workflows/implement-ticket.js:109`'s single-capture `tid` pattern, which cannot produce either shape) — not reproducible by current `.claude/workflows/*.js` code. If hand-writing monitoring records outside the JS workflows (e.g. an `audit-maintenance`-style direct invocation), always reuse the exact ticket ID as `run_id` verbatim — never invent a suffix or a synthesized `run-{code}-{timestamp}` ID; doing so breaks the events/run-record join for that record permanently.
3. A pointer: "Full classification evidence for the 2026-07-05 audit of 126 incomplete-run / 5 zero-event records (corrected: 16 true dedup-resolved, 107 true residual, 107/107 confirmed genuinely completed): `stored_artifacts/TCK-20260705-MONITORING-RUNID-JOIN/investigation.md`."

**Do NOT touch:** the schema field tables above the Known Limitations section (current schema definitions are correct and unrelated to this finding).

**Verify:**
```bash
grep -n "Known Limitations\|known-limitations" docs/agent-monitoring/schema.md
```
Confirm the new subsection exists, contains all 3 points above, and that point 1's residual count/run_id list matches whatever Step 1's Verify actually produced (not a number copied from this plan without re-checking).

### Step 4 — Correct the ticket's AC1/Request Summary framing and fill in closing sections

**Files:** `tickets/inprogress/TCK-20260705-MONITORING-RUNID-JOIN.md`

**Change:**
- Amend AC1 wording from "Each of the 21 crashed runs and 5 zero-event runs is classified" to reflect that the live count was 126 incomplete-run warnings + 5 zero-event runs at investigation time (not 21+5 — the ticket was scoped against a stale count; investigation.md's "21 vs 126" section explains why), and that all 126+5 are classified in `investigation.md`'s Classes A/B/C/D, with the corrected split: **16 true Class A (dedup-resolved) + 107 true Class C residual**, all 107 confirmed genuinely completed work.
- Fill `## Implementation Notes` with a summary of the 3 confirmed patterns (1: historical debris/pre-refactor `run-{code}-{ts}` IDs; 2: ad hoc manual `-REDESIGN` suffix, not a real rename; 3: live `implement-epic.js` batch-write gap, now hardened) and the corrected Class A/B/C/D classification outcome (16/107 split, 107/107 confirmed complete), plus the decision to extend `validate.py`'s completion check with the legacy-field allowlist rather than leave the 107 as an unexplained permanent residual.
- Fill `## Test Summary` with the actual before/after `validate.py` warning counts: **126 (before) -> 107 (after dedup-by-run_id alone) -> [actual post-allowlist count, filled in from Step 1's real Verify run, not assumed]**, and confirmation that the "no events" check (5) is unchanged.
- Fill `## Files Changed` with the 3 files touched (`tools/agent-monitoring/validate.py`, `.claude/workflows/implement-epic.js`, `docs/agent-monitoring/schema.md`) plus this ticket file.
- Fill `## Completion Summary`.
- Flip `## Status` to `DONE`, frontmatter `phase: closed` (or repo's equivalent closing convention — check a recently-closed sibling ticket's frontmatter for the exact field value used, e.g. `tickets/done/TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP.md`, and match it).

**Do NOT touch:** `## Scope` / `## Out of Scope` / `## Related Tickets` / `## Related Docs` sections — these remain accurate as originally written; only the AC1 framing and the closing sections need updates.

**Verify:** Re-read the ticket file after edits; confirm every `## Acceptance Criteria` checkbox item is either checked or explicitly explained as narrowed-with-justification (per this ticket's own AC5 wording, which already anticipates "or, if no live risk is found... the finding is documented"). Confirm no residual reference to "21", "~6", or "~120" remains anywhere in the ticket's closing sections — only the verified 126/107/16 figures and the actual final post-allowlist count.

## Scope Guards

- Do not backfill, edit, or reorder any line in `agent-monitoring/runs.jsonl` or `agent-monitoring/events.jsonl` — append-only, Out of Scope, matches the precedent set by both sibling tickets this session.
- Do not touch `validate.py`'s "no events" check or working_log cross-check — only the incomplete-run/`end_ts` check changes (dedup + legacy-field allowlist).
- Do not add fields to the legacy-completion allowlist beyond what investigation.md's evidence supports — if Step 1's Verify surfaces an uncatalogued shape, treat it as new evidence requiring its own `tickets/done/` cross-check, not a speculative addition.
- Do not add a pytest suite for `tools/agent-monitoring/*.py` — no harness exists repo-wide for this tool family (confirmed by both sibling tickets); that is a separate, explicitly-scoped future decision, not this ticket's job.
- Do not make the `implement-epic.js` batch-write verification gate a hard failure — must stay advisory per the hard rule "monitoring write failure must never fail the workflow."
- Do not build lint tooling for manual/direct monitoring-write sessions — documentation-only recommendation (open question 4's resolution).
- Do not touch `docs/parity_ledger/` or `docs/mechanics/` — not applicable (agent-monitoring is infrastructure, not simulation mechanics, per investigation.md).
- Do not cite "126 -> ~6" anywhere in code comments, docs, or the ticket — that figure is wrong and rejected by architecture review; the verified figures are 126 -> 107 (dedup only) and 107 -> [empirically confirmed count] (dedup + legacy-field allowlist).

## Dependency Map

- Step 1 (validate.py) is independent of Step 2 (implement-epic.js) and Step 3 (schema.md) — no shared code path, can be done in any order, but numbered 1→2→3 here because Step 1's before/after counts are referenced by Step 3's doc and Step 4's Test Summary text.
- Step 3 (schema.md doc) must follow Step 1 in practice (it documents Step 1's actual final residual count and run_id list — cannot be written accurately first, unlike the prior plan's assumption of a fixed "~6" figure).
- Step 4 (ticket closure) depends on Steps 1-3 being complete — it summarizes their outcomes and cannot be written accurately first.
- Finalize-phase actions (not separate numbered steps, handled by workflow convention): append `tickets/working_log.csv`, move `staging_artifacts/TCK-20260705-MONITORING-RUNID-JOIN/` → `stored_artifacts/`, stage `agent-monitoring/tools.jsonl`, write this run's own run/event monitoring records, run `graphify update .` only if `src/`/`tests/` changed (they are not, for this ticket — all changes are in `tools/`, `.claude/workflows/`, `docs/` — so `graphify update .` is NOT required), run `make knowledge-index-update` (IS required — `docs/agent-monitoring/schema.md` is modified in Step 3).

## Acceptance Criteria Map

| AC | Satisfied by | Evidence |
|---|---|---|
| AC1 — classify each of the 21 crashed + 5 zero-event runs | Already satisfied by investigation.md (Classes A/B/C/D, all 126+5, corrected 16/107 split); Step 4 corrects the ticket's own count framing to match | investigation.md "21 vs 126" section + corrected classification tables |
| AC2 — pattern 1 (timestamp race) root cause confirmed | Already satisfied by investigation.md "Pattern 1" section (historical debris, not reproducible by current code) | `implement-ticket.js:109` single-capture `tid`; `run-E43B/C/D/E-*` shape |
| AC3 — pattern 2 (rename mismatch) root cause confirmed | Already satisfied by investigation.md "Pattern 2" section (ad hoc manual `-REDESIGN` suffix, not a real rename) | `git log --follow` single-commit result; ticket's own "Reopened 2026-07-02" note |
| AC4 — 2026-06-23 cluster common cause | Already satisfied by investigation.md "Class B" section (single transitional schema generation, batch-merged, now folded into the 107 residual) | 16-record shared-shape table + `6e25d4f2` merge-commit hypothesis |
| AC5 — safeguard added or documented | Step 1 (validate.py dedup + legacy-field allowlist, closing the loop on the 107/107-confirmed-complete residual) + Step 2 (implement-epic.js verification gate, the one live risk) + Step 3 (schema.md known-limitations doc for whatever residual remains) | Verify commands in Steps 1-3 |

## Anti-Drift Notes

- Do not re-litigate whether Patterns 1/2 are "really" live risks — investigation.md already confirmed both are historical/pre-refactor debris with cited code evidence (`implement-ticket.js:109`, `git log --follow`). Re-deciding this during implementation would contradict already-verified evidence.
- Do not skip Step 1's dedup fix on the theory that "126 vs 107 is just a counting quirk" — the ticket's own title and the sibling ticket's explicit routing make the dedup fix squarely in scope; leaving `validate.py` unfixed defeats this ticket's purpose.
- Do not skip Step 1's legacy-field allowlist on the theory that "107 residual documented is good enough" — the investigation's own exhaustive 107/107-confirmed-complete finding is strong, specific evidence that this residual is closeable, and this ticket exists precisely to hardened the join logic, not just describe it. If, during implementation, new evidence emerges that the allowlist is riskier than assessed here (e.g., a genuine future crash could plausibly write one of these fields without truly completing), stop and re-flag rather than proceeding — but do not use that as a reason to skip the attempt outright given the current evidence.
- Do not turn Step 2's verification gate into a blocking/fatal check — re-read the hard rule before implementing: "Monitoring write failure must never fail the workflow."
- Do not conflate "the 107 residual, now resolved to exactly 1 by the legacy-field allowlist" with "the fix failure" — the single remaining survivor (`TCK-20260623-TYPE-CHECKER`, a 6th legacy shape) is already individually verified via `tickets/done/` and documented in Step 3; do not chase it into the code (no speculative allowlist expansion for one record) and do not assume the count is exactly 1 without re-measuring at implementation time.
- If Step 4's ticket-closure edit reveals the repo uses a different `phase:` value convention for closed tickets than assumed here, follow the sibling ticket's actual frontmatter (`tickets/done/TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP.md`) rather than guessing.
- **Never re-cite "126 -> ~6"** in any artifact, commit message, or doc produced during implementation of this ticket — it is a rejected, incorrect figure. The verified figures are 126 -> 107 (dedup alone) and 107 -> [the actual post-allowlist count, to be filled in during implementation].
