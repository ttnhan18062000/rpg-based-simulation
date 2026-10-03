---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-MONITORING-RUNID-JOIN
artifact_type: test_plan
tags: [agent-monitoring, data-quality, root-cause, run-id, legacy-schema]
---

# Test Plan — TCK-20260705-MONITORING-RUNID-JOIN

## Regression Surface

No automated test harness exists for `tools/agent-monitoring/*.py` anywhere in this repo (confirmed identically by sibling tickets `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` and `TCK-20260705-RETRO-METRIC-ACCURACY` — `record_run.py`, `record_events.py`, `validate.py`, `generate_retro.py`, `pre_tool_hook.py`, `post_tool_hook.py` all lack pytest coverage as a pre-existing, documented convention gap). This ticket does not introduce a new testing pattern unilaterally for the tool family. "Tests" for this ticket are verification queries/scripts run directly against `agent-monitoring/*.jsonl` and diffed before/after, matching the established precedent (`validate.py`'s sibling ticket: "warning count went from 54 to 62... confirmed via diff of the full warning list before/after").

The regression surface that matters:
- `agent-monitoring/runs.jsonl` / `events.jsonl` themselves must not be mutated (Out of Scope — append-only, historical debris left alone).
- If `validate.py` is touched (open question #1 in investigation.md), its two other checks (working_log cross-check, and the warning/error split) must not regress — re-run and diff against the current baseline captured below.
- If `implement-epic.js` is touched (Pattern 3 fix), the `implement-ticket.js` writeMonitoring pattern it's modeled on must not be disturbed, and a live batch run (or the closest feasible dry-run) must be exercised to confirm events + run record both land under `implement-epic`'s `workflow`.

## New Tests Required (per AC)

| AC | Evidence required | How to produce it |
|---|---|---|
| AC1 — classify each of the 21 crashed + 5 zero-event runs | Classification table (see investigation.md Classes A/B/C/D, **corrected 2026-07-05**) covering all 126 currently-incomplete + 5 zero-event runs, not just the stale "21". **Corrected, systematically-derived numbers**: 450 distinct run_ids; 343 resolved by dedup (of which only 16 have an actual incomplete-plus-complete sibling pair — true Class A); 107 true residual (no record anywhere has a truthy `end_ts` — full Class C, exhaustively checked against `tickets/done/`, not a 6-item sample). The prior in-progress pass's "~6 singles" figure was an under-count based on illustrative examples, not a systematic count — do not cite it. | Re-run the classification script (below) and diff its output against the corrected table in investigation.md — every run_id in the table must still resolve to the same verdict, and the totals must still be exactly 16 (Class A) + 107 (Class C) |
| AC2 — pattern 1 (timestamp race) root cause confirmed | Direct quote of `implement-ticket.js:109` (`tid` capture) + the `run-E43B-*` / `run-E43C/D/E-*` raw JSONL lines showing the older `run-{code}-{unix_ts}` + `ticket_id`-field shape, plus lowercase-phase/`agent:"implement-ticket"`-for-every-row events | Already captured via `grep -n "E43" agent-monitoring/runs.jsonl agent-monitoring/events.jsonl` — re-run to confirm no new similar pattern has appeared since |
| AC3 — pattern 2 (rename mismatch) root cause confirmed | `git log --follow --oneline -- tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY.md` (single commit, no rename) + ticket's own "Reopened 2026-07-02" Implementation Notes + `git log --all -S "HAZARD-NATIVE-IMMUNITY-REDESIGN"` (string never appears in a file path) | Already run — re-run both git commands to reconfirm no rename commit has since been added |
| AC4 — 2026-06-23 cluster common cause | The 16-record table (investigation.md Class B, now confirmed to be a labeled sub-cluster fully inside the 107 residual, not a separately-resolved bucket) showing identical schema shape (`final_status` present, `end_ts` key absent) and shared merge-commit provenance hypothesis | Re-run: `grep -n '"start_ts":"2026-06-23' agent-monitoring/runs.jsonl` and confirm all matches share the `final_status`-present/`end_ts`-absent shape, and that none of them appear in the 16-item Class-A resolved list |
| AC5 — safeguard added, or finding documented in `docs/agent-monitoring/schema.md` known-limitations | Depends on planner's decision between: (a) `validate.py` dedup-by-run_id fix, (b) `implement-epic.js` Pattern-3 hardening, (c) `docs/agent-monitoring/schema.md` known-limitations doc entry for the legacy-schema debris (Patterns 1/2 + Classes A/B/C), or some combination | See "Scoped verification commands" below per option |

## Scoped Pytest Commands

None — no pytest suite exists for this tool family (see Regression Surface). Do not create one unilaterally for this ticket; if a future ticket wants to establish a test harness for `tools/agent-monitoring/*.py`, that's a separate, explicitly-scoped decision (same precedent as both sibling tickets today).

## Verification Commands (in place of pytest)

Baseline capture (run before any change):
```bash
python3 tools/agent-monitoring/validate.py > /tmp/validate_before.txt 2>&1
grep -c "Incomplete run" /tmp/validate_before.txt   # expect 126
grep -c "no events" /tmp/validate_before.txt || true
```

If `validate.py` is modified (dedup-by-run_id for the `end_ts` check):
```bash
python3 tools/agent-monitoring/validate.py > /tmp/validate_after.txt 2>&1
diff /tmp/validate_before.txt /tmp/validate_after.txt
# Expect: "Incomplete run" warnings drop from 126 to exactly 107 (the true Class-C
# residual, corrected 2026-07-05 — NOT ~6; that figure was an uncorrected under-count
# from an earlier pass's illustrative-examples-only classification). Every run_id
# whose warning disappears (the 16 true Class-A run_ids) must have been shown in this
# ticket's classification table as having a same-run_id complete sibling record with a
# truthy end_ts. The 107 remaining warnings must exactly match the Class-C run_id list
# in investigation.md.
# Expect: the "no events" errors and "no working_log entry" warnings to be UNCHANGED
# (this ticket must not touch those checks).
```

If `implement-epic.js` is modified (Pattern 3 hardening):
```bash
# No live epic batch is available to run end-to-end in this session (would require a
# real folder of un-implemented tickets). Verify by code inspection instead:
grep -n "batchEvents\|record_events.py\|record_run.py" .claude/workflows/implement-epic.js
# Confirm the new code path either (a) verifies record_events.py's exit code / re-reads
# events.jsonl before calling record_run.py, or (b) fails loudly enough in the workflow
# log (not to the user — must remain non-fatal per the hard rule) that a future retro
# would catch a repeat of the FOLDER-tickets/todos/world-data/ shape immediately.
```

If the schema.md known-limitations route is chosen instead of a code change:
```bash
grep -n "known-limitations\|Known Limitations" docs/agent-monitoring/schema.md
# Confirm a new subsection documents: (1) legacy schema generations that lack `end_ts`
# despite genuine completion (Classes A/B/C), (2) the `run-{code}-{unix_ts}` id
# convention and ad hoc `-REDESIGN`-style suffixes as pre-refactor / manual-session
# artifacts not reproducible by current .claude/workflows/*.js, (3) a pointer to this
# ticket's stored_artifacts for the full classification evidence.
```

## Anti-Drift Test Guards

- Any fix must not "backfill" `runs.jsonl`/`events.jsonl` content — verify via `git diff --stat agent-monitoring/` showing zero changes to those two files (only `tools/`, `docs/`, or `.claude/workflows/` should change, plus the mandatory `agent-monitoring/tools.jsonl` self-update and this run's own new run/event records).
- If `validate.py`'s `end_ts` check is deduped by `run_id`, verify it does NOT silently swallow a **genuine** future crash: construct a synthetic single-line `runs.jsonl` fixture with one `IN_PROGRESS`/no-`end_ts` record and no sibling — confirm it still gets flagged. (Use a throwaway copy of the file, not the real `agent-monitoring/runs.jsonl` — the hard rule against mutating durable state outside authoritative flows applies to test fixtures too; never point a test run at the real file.)
- Confirm the fix (whichever is chosen) does not change `record_run.py`/`record_events.py`'s `REQUIRED` field validation — those are correctly strict already and are not implicated by any of the 3 patterns found here.
- Re-confirm after any change that `python3 tools/agent-monitoring/validate.py`'s exit code is UNCHANGED by this ticket's fix — it exits 1 both before and after (the 5 pre-existing "no events" errors are a hard `sys.exit(1)` condition per `validate.py:93-94`, untouched by this ticket's dedup/allowlist changes to the "Incomplete run" warning path). Do not expect exit 0; that would only happen if the unrelated "no events" errors were also resolved, which is Out of Scope.
