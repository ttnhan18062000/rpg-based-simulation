---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKING-LOG-BACKFILL
artifact_type: test_plan
tags: [agent-monitoring, data-quality, working-log, csv-parsing]
---

# Test Plan — TCK-20260705-WORKING-LOG-BACKFILL

## Regression Surface

This ticket, as investigated, results in **zero writes** to `tickets/working_log.csv` (see
`investigation.md` — all 62 flagged run_ids already have a row, either malformed-column-order or under a
duplicate/suffixed run_id key). The regression surface is therefore about proving the *absence* of change
and the *correctness* of the exclusion reasoning, not about validating new CSV rows.

Directly affected / must-not-regress:
- `tickets/working_log.csv` — must end with the exact same 945 lines (944 data rows + header) it has today,
  byte-for-byte, if the Plan phase adopts the "zero backfill, document as residual" recommendation.
- `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl` — append-only; AC4 requires an empty diff.
- `python3 tools/agent-monitoring/validate.py` exit code / warning count — expected to be **unchanged**
  after this ticket (62 "no working_log entry" warnings persist as a documented residual, not eliminated),
  since no code or data fix that would change the count is in scope.
- No other ticket's `tickets/done/` file, `stored_artifacts/`, or `docs/` content should be touched — this
  ticket only reads those as evidence.

## New Tests Required (per AC)

Given the "zero backfill" outcome, no new `pytest` unit tests are warranted — there is no new code path.
The verification burden is procedural/evidentiary, already captured in `investigation.md`'s table. If the
Plan phase instead chooses to spin off a `validate.py` parser-fix follow-up ticket (recommended, but out of
this ticket's scope), that follow-up ticket would need:

- A unit test asserting `validate.py`'s working-log cross-check correctly recognizes a malformed
  (ticket-id-in-column-1) row as satisfying the presence check for its ticket_id.
- A unit test asserting the cross-check consults a run record's own `ticket_id` field (when present and
  distinct from `run_id`) before falling back to treating `run_id` itself as the ticket_id.
- A regression fixture combining both legacy shapes plus a genuine well-formed row and a genuinely-missing
  row, asserting only the genuinely-missing one is still flagged.

None of the above tests belong to *this* ticket per its own scope ("Any change to `validate.py` itself" is
out of scope) — listed here only so the recommended follow-up ticket doesn't have to re-derive them.

Per this ticket's actual (zero-write) AC set://
- **AC1** ("every flagged run_id is either given a row or explicitly excluded with a documented reason") —
  verified by the presence of the full 62-row disposition table in `investigation.md`; no automated test
  applies, this is a documentation completeness check (manual review: all 62 rows present, each with a
  specific reason, none left as "unknown").
- **AC2** ("re-running validate.py shows zero, or a documented justified residual, warnings") — verified by
  re-running `python3 tools/agent-monitoring/validate.py` after finalize and confirming the same 62
  "no working_log entry" warnings appear, cross-checked against the investigation table (every warning
  line corresponds to a table row marked "exclude"). Zero is not achievable without an out-of-scope
  `validate.py` change; the residual must be explicitly called out as justified in the ticket's Completion
  Summary, per AC2's own "or a documented, justified residual" clause.
- **AC3** ("every added row is individually verified...no blind bulk-append") — trivially satisfied: zero
  rows added, so there is nothing un-verified to have bulk-appended.
- **AC4** (`runs.jsonl`/`events.jsonl` zero diff) — see Scoped Pytest Commands below (not a pytest check,
  a git diff check).

## Scoped Pytest Commands

No `tools/agent-monitoring/*.py` pytest suite exists (documented pre-existing gap, confirmed by the sibling
`TCK-20260705-MONITORING-RUNID-JOIN` ticket's own Test Summary — "No pytest suite exists for
`tools/agent-monitoring/*.py`... not introduced by this ticket"). This ticket does not introduce one either,
consistent with that precedent (no code changes are in scope). Verification is via direct CLI invocation:

```bash
# 1. Confirm the flagged set is unchanged from investigation time (before any finalize action):
python3 tools/agent-monitoring/validate.py 2>&1 | grep -c "no working_log entry"
# expected: 62 (or a small, explainable delta if concurrent session work landed more monitoring records)

# 2. Confirm the append-only invariant (run before AND after any finalize step):
git diff --stat agent-monitoring/runs.jsonl agent-monitoring/events.jsonl
# expected: empty output both times

# 3. Confirm working_log.csv is untouched (if the Plan phase adopts the zero-write recommendation):
git diff --stat tickets/working_log.csv
# expected: empty output

# 4. Spot-check 3 of the disposition-table rows against tickets/done/ content (already performed during
#    investigation; re-run to confirm no drift before finalize):
git show HEAD:tickets/working_log.csv | grep -n "^TCK-20260610-ARCHETYPE-DEFAULT-PATH,"
git show HEAD:tickets/working_log.csv | grep -n "^TCK-20260619-E53Cb-SIEGE-MODEL,"
git show HEAD:tickets/working_log.csv | grep -n "^TCK-20260623-FIX-ARENA,"
```

If the Plan phase instead scopes a `validate.py` follow-up ticket, its scoped commands would be:
```bash
python3 -m pytest tests/unit/tools/test_agent_monitoring_validate.py -v   # (does not exist yet — new file)
python3 tools/agent-monitoring/validate.py   # before/after warning-count diff
```

## Anti-Drift Test Guards

- **Guard against silent bulk-append**: before finalize, re-run the `grep -c` "already-logged" check from
  `investigation.md` (base ticket_id string match, both wellformed-column and malformed-column-1 forms) for
  every one of the 62 run_ids one more time immediately before writing anything, in case concurrent session
  work has genuinely closed a new ticket in the interim that coincidentally shares a prefix — do not rely
  solely on the investigation-time snapshot if there is any time gap before implementation.
- **Guard against touching `runs.jsonl`/`events.jsonl`**: `git diff --stat` on both files must be empty at
  both start and end of the finalize step — this is a hard AC (AC4), not advisory.
- **Guard against rewriting the 39 malformed rows**: `git diff --stat tickets/working_log.csv` should show
  **zero** changed/removed lines (only additions, if any are ultimately deemed warranted) — a `-` line in
  the diff for any pre-existing row is a scope violation of this ticket's "append, not rewrite" mandate.
- **Guard against re-introducing the "62 vs prior-cited number" drift bug**: any Plan/Implement-phase
  restatement of the flagged count must come from a fresh `validate.py` run at that phase's own time, not
  copied from this investigation's snapshot, per the ticket's own explicit instruction ("do not trust any
  previously-cited number").
