---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE
artifact_type: test_plan
tags: [agent-monitoring, data-quality, schema]
---

# Test Plan — TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE

## Regression Surface

All must pass **unmodified** (AC4) — none of these files are to be edited by this ticket except
where explicitly noted:

**Unit — `tests/tools/test_generate_retro.py`** (35 tests, full file, confirmed by direct read).
Every test drives `compute_retro_metrics()`/`generate()` via hand-built dicts, not through the
index — these are the tests that make investigation.md's Risk #1 concrete. Notable subsets:
- Reason-code / tag-breakdown / tier-distribution / spend-proxy / outlier tests — all depend on
  `_resolve_status`/`_is_gate_fail`'s current call-site behavior inside `compute_retro_metrics()`.
- `test_tag_breakdown_subsystem_topic_section_renders_when_tags_resolve` — explicitly the
  regression guard for `_resolve_status`'s `status`-without-`final_status` fallback path (a
  legacy-shaped record), named in its own comment as guarding against reintroducing
  `TCK-20260705-RETRO-METRIC-ACCURACY`'s bug. This is the single highest-value pre-existing test
  to re-run and eyeball after any change to `_resolve_status`'s call sites.
- `test_generate_retro_days_flag_does_not_raise_on_legacy_start_ts` — monkeypatches
  `generate_retro.RUNS_FILE`/`EVENTS_FILE`/`RETRO_DIR` and calls `generate_retro.main()` directly.
  **This test will break if `main()`'s data-loading path changes without preserving a
  monkeypatch-compatible seam** — if `main()` moves to `open_index()`/index-loading helpers, this
  test needs either an equivalent `DEFAULT_DB_PATH` monkeypatch point or an explicit update (see
  New Tests Required — this is the one pre-existing test most likely to need a compatible seam,
  not necessarily a content change).

**Integration/build — `tests/tools/test_build_index.py`** (full file). Not touched by this ticket,
but `TestNormalizationParity::test_resolved_status_matches_generate_retro_resolve_status` (line
184) is the direct proof that `resolved_status`'s SQL column and `_resolve_status()`'s Python
output can never diverge (import-based, not reimplementation) — re-run to confirm this ticket's
changes (if any land inside `generate_retro.py`'s `_resolve_status` definition itself, which they
should not per investigation.md Risk #1) don't silently break the import.

**Integration — `tests/tools/test_validate_agent_monitoring.py`, `tests/tools/test_query.py`** —
sibling consumers of the same index; not expected to be affected by this ticket at all (different
files, no shared state), but included in the regression surface since all three read the same
`agent-monitoring-index/monitoring.db`.

**Dashboard consumer — `tests/tools/test_agent_ops_dashboard_stats.py`** (if present) —
`src/api/agent_ops_dashboard/ingest.py` calls `generate_retro.compute_retro_metrics()` directly
(confirmed by investigation.md's Prior Work / INFRA-274 cross-reference). If `compute_retro_metrics()`'s
signature or behavior changes at all, this is the one downstream consumer outside `tools/` that
could regress silently — re-run explicitly even though it's not in `tools/agent-monitoring/`.

## New Tests Required

Per the ticket's Scope/AC and investigation.md's findings:

1. **`test_resolve_status_prefers_final_status_over_status`** — unit, direct predicate test.
   Verifies `_resolve_status({"final_status": "DONE", "status": "old"}) == "DONE"`.
   `tests/tools/test_generate_retro.py`.
2. **`test_resolve_status_falls_back_to_status_when_final_status_absent`** — unit. `_resolve_status({"status": "complete"}) == "complete"` — also asserts the literal, non-normalized
   spelling is preserved (does **not** become `"DONE"`), directly guarding `_resolve_status`'s
   documented non-normalizing contract. `tests/tools/test_generate_retro.py`.
3. **`test_resolve_status_returns_none_when_both_absent`** — unit. Covers
   `TCK-20260623-TYPE-CHECKER`-shaped records (no `final_status`/`status` at all) —
   `_resolve_status({}) is None`. `tests/tools/test_generate_retro.py`.
4. **`test_is_legacy_event_true_when_agent_missing`** / **`test_is_legacy_event_false_when_agent_present`**
   — unit, direct predicate tests. `tests/tools/test_generate_retro.py`.
5. **`test_is_gate_fail_true_for_non_terminal_status`** / **`test_is_gate_fail_false_for_done_epic_scoped_in_progress`**
   — unit, direct predicate tests covering all 3 non-gate-fail terminal values individually (not
   just one), since a future edit to the tuple literal at line 112 should be caught per-value.
   `tests/tools/test_generate_retro.py`.
6. **`test_generate_retro_builds_index_on_demand_when_missing`** — integration. Point
   `generate_retro`'s db-path constant (or equivalent monkeypatch seam, per whichever fallback
   design Plan selects — see investigation.md Risk #2) at a `tmp_path` location that does not
   exist; run the equivalent of `main()` or the new loading function; assert the index now exists
   at that path afterward and the report was still produced (not a hard failure). This is the
   direct AC test for "must never become a hard gating dependency."
7. **`test_generate_retro_produces_clear_error_message_if_build_on_demand_disabled_or_fails`** —
   integration, failure-mode. Simulate a build-on-demand failure (e.g. read-only target directory,
   or monkeypatch `build_index.build` to raise) and assert the resulting error is a clear,
   actionable message — never an unguarded traceback, and (per the ticket's "must never become a
   hard gating dependency" language) the process should not necessarily need to exit non-zero the
   same way `query.py`/`validate.py` do; confirm the exact exit-code contract against whatever
   Plan decides for Risk #2.
8. **`test_main_loads_via_index_not_direct_jsonl_scan`** — architecture guard, mirrors
   `test_build_index_never_touches_write_path_modules`'s source-text-assertion shape (or, if
   feasible, a call-count/mock-based assertion that `load_jsonl(RUNS_FILE)` is no longer invoked
   by `main()`). Verifies the migration actually happened, not just that behavior is unchanged.
   `tests/tools/test_generate_retro.py`.
9. **`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus`** — the
   direct AC2 byte-identical proof. Build a small fixed `runs`/`events` fixture, capture
   `generate(runs, events, "fixed-label")`'s output as a frozen string constant (or via a `git
   show`-free hand-copy, mirroring `QUERY-INDEX-MIGRATE`'s "frozen reference in the test file, not
   git history" convention), and assert the post-migration call produces byte-identical output.
   Given investigation.md Risk #1's recommended resolution (loader-only migration,
   `compute_retro_metrics()`'s body untouched), this should trivially pass — the value of this
   test is pinning that guarantee explicitly rather than relying on inference.
10. **`test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope`** —
    architecture guard tied directly to investigation.md Risk #3. Whichever way Plan resolves
    `_update_index()`'s inclusion, add a test that fails loudly if a future edit silently
    reintroduces a `load_jsonl(RUNS_FILE)` call inside `_update_index()` without updating this
    test — prevents the migration from becoming partial by accretion.
11. **`test_generate_retro_days_flag_still_works_against_index_backed_main`** — regression-shape
    replacement/extension for the existing `test_generate_retro_days_flag_does_not_raise_on_legacy_start_ts`
    if that test's monkeypatch seam changes (see Regression Surface above) — only needed if Plan's
    chosen fallback design breaks the existing monkeypatch points; otherwise the existing test
    already covers this.

## Scoped Pytest Commands

```
pytest tests/tools/test_generate_retro.py -v
pytest tests/tools/test_build_index.py -v
pytest tests/tools/test_validate_agent_monitoring.py -v
pytest tests/tools/test_query.py -v
pytest tests/tools/test_agent_ops_dashboard_stats.py -v  # only if it exists and imports compute_retro_metrics
```

Combined single scoped run for this ticket's actual diff surface:

```
pytest tests/tools/test_generate_retro.py tests/tools/test_build_index.py -v
```

**Never:** `pytest tests/` (full suite) — CLAUDE.md's Testing Rule and this repo's own convention
(every sibling ticket's test_plan.md scopes to `tests/tools/`) both apply.

## Anti-Drift Test Guards

- **`test_resolve_status_function_still_importable_from_generate_retro`** — guards against a
  future edit literally deleting `_resolve_status()`'s definition (investigation.md's central
  finding: `build_index.py` imports it directly). `from generate_retro import _resolve_status`
  must always succeed; assert it's callable and returns the documented non-normalizing behavior.
  Place in `tests/tools/test_generate_retro.py`, not `test_build_index.py`, so it's visible
  alongside the other direct-predicate tests this ticket adds.
- **`test_build_index_resolved_status_parity_still_passes`** — re-run (not modify)
  `tests/tools/test_build_index.py::TestNormalizationParity::test_resolved_status_matches_generate_retro_resolve_status`
  as part of this ticket's own verification pass — if this starts failing, `_resolve_status()`'s
  behavior diverged from what `build_index.py` assumes, which would be a silent cross-module
  regression this ticket must never introduce.
- **`test_generate_retro_never_writes_to_agent_monitoring_index_db`** — architecture guard. The
  index is a derived, read-only-by-convention artifact everywhere else in this subsystem
  (`build_index.py`'s own docstring: "never writes back"). If the build-on-demand fallback
  (Risk #2) is implemented, it necessarily *creates* the db file when missing — but assert
  `generate_retro.py` never opens the db in any write mode other than via a full delegated
  `build_index.build()` call (i.e., no direct `sqlite3.connect(...)` + `INSERT`/`UPDATE` inside
  `generate_retro.py` itself) — the only legitimate write path is the imported `build()` function,
  never a bespoke one.
- **`test_normalize_phase_agent_and_flag_outliers_untouched`** — source-text or behavioral guard
  confirming `_normalize_phase`, `_normalize_agent`, `_canonicalize`, `_flag_outliers` are
  unchanged by this ticket (investigation.md Anti-Drift Hazards) — a future editor migrating
  `_resolve_status` might be tempted to "also clean up" the adjacent normalization functions in
  the same file; this guard catches that scope creep.
- **`test_gate_fail_tuple_literal_unchanged`** — pins `("DONE", "EPIC_SCOPED", "IN_PROGRESS")` as
  the exact terminal-state set `_is_gate_fail()` (and `_update_index()`'s inline duplicate at line
  808, if migrated) compares against — catches an accidental widening/narrowing during the
  call-site rewrite.
- **`test_no_sys_exit_1_on_missing_index_in_generate_retro`** — the direct negative-space guard
  for this ticket's core divergence from `query.py`/`validate.py`'s precedent: asserts
  `generate_retro.py`'s missing-index path does *not* raise `SystemExit(1)` the way
  `query.open_index()`/`validate.open_index()` do — catches a future editor "fixing" this ticket's
  intentional inconsistency back toward sibling-pattern conformity.
