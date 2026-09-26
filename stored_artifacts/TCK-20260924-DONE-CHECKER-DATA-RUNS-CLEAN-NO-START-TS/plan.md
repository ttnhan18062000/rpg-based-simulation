---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS
artifact_type: plan
tags: [workflows, process-improvement, agent-monitoring]
---

# Plan — TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS

## Design decision (Open Question 2, settled with the consumer list as evidence)

New status value: **`INDETERMINATE`** — distinct from the existing `NA` (which means "not
applicable for this tier," a different semantic) and from `PASS`/`FAIL`. Safe because every real
consumer (`_render_results`, `classify_checklist_failure`, the pipeline's LLM done-checker agent)
only branches on the literal string `"FAIL"` — see investigation.md's consumer list. This is the
**smaller, safer, and more honest** change relative to the ticket's own tentatively-suggested
alternative ("a PASS with an explicit evidence string") — a genuinely unmeasured condition must
never read as `PASS`, which risks being cited as "a clean bill of health" exactly as the ticket's
own Open Question flagged.

## `check_data_runs_clean` signature and resolution order

```python
def check_data_runs_clean(
    start_ts: str | None,
    ticket_id: str | None = None,
    runs_dir: Path = Path("data/runs"),
    proof_dir: Path = Path("reports/release_proof"),
    data_root: Path = Path("agent-monitoring/data"),
) -> tuple[str, str]:
```

`start_ts` stays the first positional parameter (AC4: unchanged existing behavior for every caller
that already passes one, including a garbage string — that path is untouched, still flows straight
into `_find_flagged_data_run_files`'s existing fail-closed branch). `ticket_id` is new, optional,
keyword-friendly.

Resolution order:
1. If `start_ts` is given (truthy) — **unchanged**, whether it parses or not.
2. Else, if `ticket_id` is given — look up this ticket's own run record via the already-shared
   `_jsonl_rows_for_run_id_across_weeks(data_root, "runs.jsonl", ticket_id)` (reused, not
   reimplemented — the exact function `check_monitoring_write_recorded` already uses for the same
   `run_id == ticket_id` shape). If a row with a `start_ts` field is found, use it, with the
   reliability caveat embedded in the evidence string per investigation.md.
3. Else (no `start_ts`, no resolvable run record) — return `("INDETERMINATE", "...")`, never `FAIL`.

`run_static_precheck(ticket_id, tier, start_ts)` — already has `ticket_id` in scope — passes it
through: `check_data_runs_clean(start_ts, ticket_id)`.

## Test changes

- Correct `test_data_runs_clean_unparsable_start_ts_flags_any_file`'s name and body: it tests an
  *absent* `start_ts` with no `ticket_id` context, which now resolves to `INDETERMINATE`, not
  `FAIL`. Renamed to `test_data_runs_clean_absent_start_ts_no_ticket_context_is_indeterminate`.
- New test: an explicit, present-but-garbage `start_ts` string (not `None`) still flags every file
  — `FAIL` — proving AC4/the pipeline fail-closed rule survives untouched (no existing test actually
  covered this exact case with a real non-None garbage string before).
- New test: `ticket_id` given, `start_ts` omitted, a scratch `runs.jsonl` row with a real `start_ts`
  for that `run_id` — resolves and behaves like an explicit `start_ts` would (both `PASS` and `FAIL`
  sub-cases), and the evidence string names the fallback source.
- New test: `ticket_id` given but no matching run record exists for it — falls through to
  `INDETERMINATE`, same as no `ticket_id` at all.
- All 5 existing real-`start_ts` tests (`test_data_runs_clean_empty_dirs_passes`, etc.) and every
  `clean_data_runs_early`/shared-walk test — run unchanged, expected byte-identical (AC4/AC5;
  `clean_data_runs_early` itself is not touched at all, per Out of Scope).

## Verification

Full `tests/gate_checks`-adjacent scope: `tests/tools/test_done_checker_static.py` plus a broader
`tests/tools/` regression pass, since this file's functions are imported by
`implement-ticket.js`-adjacent test coverage elsewhere.
