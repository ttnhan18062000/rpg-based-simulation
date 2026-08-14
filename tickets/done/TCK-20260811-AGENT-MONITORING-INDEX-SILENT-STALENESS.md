---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS
phase: done
date: 2026-08-11
tags: [observability]
---

# TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS

## Title
`generate_retro.py`'s derived SQLite index degrades silently when stale (present but outdated),
under-reporting retro numbers with no warning

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Found while running `/agent-monitoring-retro` at the end of a long session
(2026-08-10/11, `RETRO-2026-W33.md`). `tools/agent-monitoring/generate_retro.py`'s
`_load_runs_and_events()` reads from `agent-monitoring-index/monitoring.db` (built by
`tools/agent-monitoring/build_index.py`) instead of scanning `agent-monitoring/runs.jsonl`/
`events.jsonl` directly, and only rebuilds the index on demand if the DB file is **missing**
(`if not DEFAULT_DB_PATH.exists(): ... build_index.build(...)`) — never if it's merely stale.

In this session, the index was last built at `2026-08-10T14:15+07`, before the first ticket of a
5-ticket batch even closed. The retro run at `2026-08-10T19:15+07` (~5 hours later, `runs.jsonl`
mtime `2026-08-11T02:14+07` local) silently used the stale index and reported **7 runs / 41
events** for the week — a 61% under-count versus the real, correct **18 runs / 123 events**
confirmed after a manual rebuild. Every gate-failure entry, most DONE tickets, and both
`architecture_violation`/`documentation_accuracy` reason codes from that session's work were
invisible in the first (stale-index) report. No warning, error, or staleness indicator was printed
— the report looked complete and plausible.

This is a real risk for anyone trusting `/agent-monitoring-retro`'s numbers at face value, per this
skill's own stated purpose ("Before trusting the numbers, cross-check integrity" — currently the
only documented mitigation is `make agent-monitoring-validate`, which does NOT check index
freshness, only cross-file consistency of the JSONL sources themselves).

## Scope
- Add a staleness check to `_load_runs_and_events()` (`tools/agent-monitoring/generate_retro.py`):
  compare `DEFAULT_DB_PATH`'s mtime against `RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_TOOLS_FILE`'s mtimes;
  if any source file is newer than the index, rebuild before reading (same code path already used
  for the missing-index case) rather than silently reading stale data
- Alternatively/additionally: have `record_run.py`/`record_events.py` touch or invalidate the index
  file on every write, so the index is never more than one retro-run stale regardless of what reads
  it
- Whichever mechanism is chosen, it must not become a hard gating dependency (same constraint the
  existing code comment already states for the missing-index case) — a rebuild failure should
  degrade to the direct JSONL scan fallback that already exists, not raise
- Add a regression test: write a JSONL row, confirm a stale (pre-existing, older) index file gets
  rebuilt before the row is reflected in retro output

## Out of Scope
- `make agent-monitoring-validate`'s own cross-file consistency checks — unrelated, already working
  correctly (confirmed this session: it flagged real, pre-existing, unrelated June-2026 tickets
  missing `working_log.csv` entries, nothing caused by index staleness)
- Any change to `query.py`'s or `validate.py`'s own `open_index()` (which hard-fails on a missing
  index, unlike `generate_retro.py`'s soft-degrade) — different failure mode, not this ticket's scope

## Acceptance Criteria
- [x] `generate_retro.py` detects a stale-but-present index (any source JSONL newer than the DB
      file) and rebuilds before reading, not just when the DB file is missing. New
      `_index_is_stale(db_path)` helper checks `db_path.exists()` plus each of
      `RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_TOOLS_FILE`'s mtime against the index's mtime;
      `_load_runs_and_events()`'s rebuild condition changed from `if not DEFAULT_DB_PATH.exists()`
      to `if _index_is_stale(DEFAULT_DB_PATH)`.
- [x] Rebuild failure degrades to the existing direct-JSONL-scan fallback, does not raise. No
      change to the surrounding `try`/`except Exception` block — the staleness check only changes
      *when* a rebuild is attempted, not the existing fallback-on-failure behavior, confirmed by
      the pre-existing `test_generate_retro_produces_clear_error_message_if_build_on_demand_
      disabled_or_fails` and `test_no_sys_exit_1_on_missing_index_in_generate_retro` staying green
      unmodified.
- [x] New regression test confirms a stale index gets rebuilt and the retro output reflects a
      freshly-written record that predates the stale index but postdates the source JSONL write.
      `test_generate_retro_rebuilds_stale_index_not_just_missing_index` (builds the index from one
      row, appends a second row with a forced-later mtime, confirms the second load returns both
      rows) plus `test_index_is_stale_false_when_index_newer_than_all_sources` (negative case).
- [x] `docs/guides/agent_monitoring.md` (or wherever this skill's own doc lives) is updated to state
      staleness is now handled automatically, if the doc currently implies manual rebuild is
      needed. `docs/guides/agent_monitoring.md` itself only documents `query.py`'s manual-rebuild
      need (unaffected, out of scope, `query.py` still hard-fails on missing/stale). The actual
      staleness claims lived in `docs/agent-monitoring/schema.md` and `docs/agent-monitoring/
      README.md` (2 locations) — both corrected to say "missing or stale" instead of "missing"
      alone, plus a parity ledger addendum (INFRA-291).

## Related Tickets
None yet.

## Related Docs
- docs/guides/agent_monitoring.md (if it exists — confirm path at Implement time)
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py (`_load_runs_and_events()`)
- tools/agent-monitoring/build_index.py

## Assumptions / Open Questions
- Whether a periodic/hook-based touch-on-write approach (record_run.py/record_events.py
  invalidating the index) is preferable to a staleness-check-on-read approach in generate_retro.py,
  or both should coexist as defense in depth — not decided here, an Implement-time design call

## Implementation Notes

Added `_index_is_stale(db_path)` to `tools/agent-monitoring/generate_retro.py` (right before
`_load_runs_and_events()`): returns `True` if `db_path` doesn't exist, or if any of
`RUNS_FILE`/`EVENTS_FILE`/`DEFAULT_TOOLS_FILE` exists and has a newer `st_mtime` than the index.
Changed `_load_runs_and_events()`'s rebuild-trigger condition from the old
`if not DEFAULT_DB_PATH.exists():` to `if _index_is_stale(DEFAULT_DB_PATH):` — same rebuild call
(`build_index.build(...)` via `SimpleNamespace`), same surrounding `try`/`except Exception`
fallback-to-`load_jsonl()` block, unchanged. `build_index.build()` itself is already a
full-delete-and-recreate rebuild (`db_path.unlink()` then fresh schema + full re-ingest), not
incremental, so triggering it on staleness fully resolves the under-count — no partial-rebuild
risk to reason about.

Went with the "design assumption" from the ticket's own Assumptions section: staleness-check-on-
read in `generate_retro.py` only, not a touch-on-write hook in `record_run.py`/`record_events.py`.
Reasoning: a write-side invalidation hook would need to fire on every write across all monitoring
call sites (dozens, per this session's own experience hand-writing sidecars/events), is a second
mechanism to keep in sync with the read-side one, and the mtime-comparison approach already fully
solves the reported problem (a retro run always sees fresh data relative to whatever's on disk at
read time) without touching the write path at all. Not implemented as defense-in-depth per the
ticket's own "not decided here" framing — this single mechanism is sufficient and simpler.

Also checked every real consumer of `_load_runs_and_events()` beyond `generate_retro.py` itself
(`retrieval_baseline_metrics.py`, `security_gate_firing_check.py` both call it directly and now
transparently benefit from staleness detection too — no code change needed on their side, pure
behavior improvement) and found one more stale-claim citation: a source comment in
`tools/agent-monitoring/done_ticket_monitoring_coverage.py:62-68` explaining why that tool
bypasses the index — same correction applied as the README.md rationale (staleness gap fixed for
`generate_retro.py`'s path, but mtime-comparison still isn't true up-to-the-second freshness, so
the bypass design remains independently justified).

Doc audit: grepped the repo for every other place the old "missing-only" claim was documented,
since `docs/guides/agent_monitoring.md` (the doc named in the ticket's own Related Docs) turned
out not to be the actual source of the claim — it only discusses `query.py`'s manual-rebuild
need, which is correctly unchanged (out of scope, `query.py`'s `open_index()` still hard-fails,
per the ticket's own Out-of-Scope). Found and corrected 2 real citations:
- `docs/agent-monitoring/schema.md`'s "Derived SQLite Index" section ("builds the index on demand
  if missing" → "if missing or stale", with the ticket ID and rationale)
- `docs/agent-monitoring/README.md`: the Quick Start snippet's inline comment, plus the
  Done-Ticket Monitoring Coverage Audit section's design rationale for `done_ticket_monitoring_
  coverage.py` bypassing the index entirely — that rationale cited "only rebuilt when missing,
  not when stale" as the *reason* for the bypass; corrected to note the staleness gap is now
  fixed for `generate_retro.py`'s own path, while still noting mtime-comparison isn't true
  up-to-the-second freshness, so the bypass design remains independently justified (not claiming
  the audit tool's design is now obsolete — it wasn't touched, per this ticket's own scope, which
  names only `generate_retro.py`/`build_index.py`).

Also added an append-only addendum to `docs/parity_ledger/infrastructure.yaml`'s INFRA-291 (the
entry documenting `generate_retro.py`'s original index-migration behavior, including the old
missing-only rebuild condition) — following this session's established precedent (INFRA-237) of
appending dated addenda to `support_boundary` rather than rewriting `text`/`v2_evidence` in place.
`python3 tools/parity_index.py build` confirmed schema-valid post-edit (2013 entries, unchanged
count — an edit to an existing entry, not a new one).

## Test Summary

- `pytest tests/tools/test_generate_retro.py -v -m "not slow"` → 102 passed (2 new:
  `test_generate_retro_rebuilds_stale_index_not_just_missing_index`,
  `test_index_is_stale_false_when_index_newer_than_all_sources`; 100 pre-existing, all still
  green including the missing-index/fallback/no-sys-exit tests this ticket's change sits next to)
- `pytest tests/tools/test_generate_retro.py tests/tools/test_build_index.py tests/tools/
  test_done_ticket_monitoring_coverage.py tests/tools/test_security_gate_firing_check.py
  tests/tools/test_retrieval_baseline_metrics.py -q -m "not slow"` → 162 passed, 0 failed (full
  sweep across every real consumer of `_load_runs_and_events()` plus the comment-only file)
- `python3 tools/parity_index.py build` → schema-valid, 2013 entries (INFRA-291 addendum confirmed
  parseable and within schema)

## Files Changed

- `tools/agent-monitoring/generate_retro.py` — added `_index_is_stale()`, changed
  `_load_runs_and_events()`'s rebuild condition to check staleness, not just existence
- `tests/tools/test_generate_retro.py` — 2 new regression tests
- `docs/agent-monitoring/schema.md` — corrected "missing" → "missing or stale" claim
- `docs/agent-monitoring/README.md` — corrected 2 citations (Quick Start snippet,
  Done-Ticket Monitoring Coverage Audit rationale)
- `tools/agent-monitoring/done_ticket_monitoring_coverage.py` — corrected the same stale claim in
  a source comment (no behavior change)
- `docs/parity_ledger/infrastructure.yaml` — INFRA-291 addendum

## Completion Summary

Fixed the silent-staleness bug: `generate_retro.py`'s derived-index read path now rebuilds
whenever any source JSONL postdates the index's own mtime, not only when the index file is
entirely absent — closing the exact gap that under-counted a real session's retro numbers by 61%
with no warning. Chose read-side staleness detection over a write-side invalidation hook (simpler,
fully sufficient, no write-path touch needed). Corrected every doc citation of the old
missing-only behavior found via a full-repo grep (2 doc files, 1 parity ledger addendum) rather
than stopping at the ticket's own named doc, which turned out not to be the actual source of the
stale claim.
