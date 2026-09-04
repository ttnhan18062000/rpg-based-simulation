---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY
artifact_type: test_plan
tags: [agent-monitoring, observability, data-quality, schema]
---

# Test Plan — TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY

## Regression Surface

This ticket adds a new, additive script/module and its own new test file — it does not modify any
existing consumer script, so the regression surface is "prove nothing existing broke," not "prove
existing behavior changed."

**Unit (must keep passing unmodified):**
- `tests/tools/test_validate_agent_monitoring.py` — `compute_drift_report`,
  `compute_tool_count_drift_report`, `compute_multi_invocation_collision_report` and the
  SQLite-index-backed `main()` path must be untouched by this ticket (Out of Scope: "Any change to
  the 3 per-line record schemas"; this ticket does not modify `validate.py` at all unless the
  implementer chooses the "new function in `validate.py`" placement option — if so, this file's
  existing tests must still pass unmodified).
- `tests/tools/test_migrate_monitoring_data.py` — the loader/bucketing primitives this ticket's new
  loader is modeled on (`bucket_lines_by_week_multi_field`, `relocate_tools_shards`,
  `write_week_bucket`, `verify_migration`) must remain untouched; this ticket only reads the
  `agent-monitoring/data/` layout `migrate_monitoring_data.py` produces, never writes to it.
- `tests/tools/test_agent_monitoring_manifest.py` — `manifest.py`'s own read-only scan is unrelated
  and unaffected.
- `tests/tools/test_agent_monitoring_legacy_reader.py` — `legacy_reader.py`'s provenance
  classification is unrelated and unaffected.

**Integration:**
- Any test exercising `record_events.py::compute_tool_stats()` (if such a test exists elsewhere,
  e.g. within a broader `record_events` test file) must remain passing — this ticket reuses the same
  glob pattern by reference/precedent, not by importing/modifying that function.

**Arena-combat:** not applicable — this ticket touches only `tools/agent-monitoring/` and
`tests/tools/`, no `src/` combat code.

## New Tests Required

All new tests live in a new file, `tests/tools/test_verify_referential_integrity.py` (or
`test_validate_agent_monitoring.py`-adjacent if the implementer places the checks as new functions
in `validate.py` — file placement follows whichever module placement decision the implementer
documents per the ticket's own Assumptions/Open Questions). Mirrors
`tests/tools/test_migrate_monitoring_data.py`'s structure: synthetic-fixture unit tests first, then
an integration test against a small hand-built multi-week directory tree (never the real
`agent-monitoring/` directory directly — matching that file's own explicit precedent), then one
opt-in/marked real-corpus smoke test.

Per acceptance criteria — one entry per required new test:

- **`test_same_week_only_join_baseline`**
  Category: unit
  Verifies: a `run_id` whose `runs`/`events`/`tools` rows all live in the same single week folder,
  with a fully consistent chain (every event has a matching run, every tool row has a matching
  event) produces **zero** violations from both checks. Baseline correctness (Scope scenario a).
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_cross_week_run_id_not_flagged`** (the ticket's own explicitly-called-out key risk test)
  Category: integration (real multi-directory fixture via `tmp_path`)
  Verifies: build a `tmp_path` fixture with `<data_dir>/2026-W10/runs.jsonl` containing the run
  record, and `<data_dir>/2026-W11/events.jsonl` + `<data_dir>/2026-W11/tools.jsonl` containing that
  same `run_id`'s events/tools (mirroring the real corpus's own confirmed pattern, e.g.
  `TCK-20260820-EPIC-WORLD-RENDERING-CORE`'s runs.jsonl-in-W34-events-in-W35 shape found in the real
  corpus during investigation). Assert **zero** violations. A same-week-only implementation (one that
  resolves a run's week before searching, or that only scans the week folder the tool itself is
  invoked against) must fail this test — this is the test the ticket's AC calls out as the one that
  must distinguish a correct implementation from a subtly-wrong one.
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_orphan_tools_row_no_matching_event_anywhere_is_flagged`**
  Category: unit
  Verifies: a `tools` row with a non-null `run_id`, `seq >= 1`, whose `(run_id, seq)` has no matching
  row in `events` in *any* week folder (not just the same week) is reported as a violation, with the
  violating `run_id`/`seq`/week-folder captured in the report's concrete-examples list (per Scope's
  "structured report... concrete examples: `run_id`/`seq`/week-folder of each orphan"). Scope
  scenario c.
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_orphan_event_no_matching_run_anywhere_is_flagged`**
  Category: unit
  Verifies: an `events` row (non-`RETRIEVAL-EVENT-*` `run_id`) with no matching `runs` row in any
  week folder is reported as a violation, with `run_id`/week-folder captured. Scope scenario d.
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_retrieval_event_run_id_excluded_from_check`**
  Category: unit
  Verifies: an `events` row whose `run_id` starts with `RETRIEVAL-EVENT-` and has no matching `runs`
  row is **not** reported — the documented exception (schema.md lines 353-364). Scope scenario e
  (part 1). Since the real corpus has 0 live examples today (see investigation.md), this must be a
  synthetic fixture.
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_null_run_id_tools_row_excluded_from_check`**
  Category: unit
  Verifies: a `tools` row with `run_id: null` is excluded from the `tools → events` check entirely
  (never counted as checked, never flagged) — the documented exception (schema.md line 407). Given
  26.2% of the real corpus's `tools.jsonl` rows have `run_id: null`, this must not just "not be
  flagged" but must not inflate the reported "checked" denominator either. Scope scenario e (part 2).
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_negative_and_zero_seq_tools_rows_excluded_from_check`**
  Category: unit
  Verifies: `tools` rows with `seq <= 0` (both a negative shadow-row `seq` and a literal `seq: 0`)
  are excluded from the `tools → events` check — the documented exception (schema.md lines 145, 310,
  338-340). Synthetic fixture (0 live examples in the real corpus today, per investigation.md). Scope
  scenario e (part 3).
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_duplicate_event_key_does_not_break_lookup`**
  Category: unit (anti-drift / regression-prone-path guard, derived from a real corpus finding)
  Verifies: when 2 distinct `events` rows share the same `(run_id, seq)` key (confirmed real pattern
  in the corpus — 145 such keys found during investigation, e.g. a legacy-schema duplicate alongside
  a current-schema record for the same identity), a `tools` row at that key is still correctly
  matched (not spuriously flagged) — guards against a `dict` comprehension that would silently drop
  one of the colliding event rows and, depending on which one survives, potentially miss the match.
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_unknown_week_folder_included_in_join`**
  Category: unit / architecture guard
  Verifies: a run/event/tool row placed under `<data_dir>/unknown-week/<source>.jsonl` participates
  in the join exactly like any ISO-week folder — an event in `unknown-week` matching a run in a real
  ISO week is not flagged, and vice versa. Guards against an implementation that filters directory
  names against an ISO-week regex (`\d{4}-W\d{2}`) and silently excludes `unknown-week`.
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_report_output_matches_validate_py_style`**
  Category: unit
  Verifies: the report is a structured object/string documented well enough to be machine- or
  human-parsed (AC #4) — assert the report contains explicit violation counts and a bounded sample
  of concrete examples (mirroring `compute_tool_count_drift_report`'s
  `"Mismatches (recorded != actual tools.jsonl row count): {len(mismatches)}"` +
  `"Sample mismatches..."` capped-list convention), not just a pass/fail boolean.
  Location: `tests/tools/test_verify_referential_integrity.py`.

- **`test_real_corpus_smoke_run`** (integration, real data)
  Category: integration
  Verifies: the finished script runs successfully (no crash, no exception) against the real
  `agent-monitoring/data/` tree and produces a report — this is the AC #2 requirement ("runs
  successfully against the real post-migration corpus"). Given the real corpus currently produces
  ~17K Check-2 violations and 18 Check-1 violations (see investigation.md), this test must assert
  successful *execution* and a well-formed report, not zero violations — do not write this test to
  assert `violation_count == 0`, since that would be true today only by accident of not having run it
  yet, and would make the test itself lie about what "passing" means once real (expected, historical,
  triaged) violations exist. If the implementer decides the tool should also expose a `--strict`/exit-
  code-on-violation mode for future gate wiring, that mode should be tested separately from this
  smoke test, which validates the report-generation path only.
  Location: `tests/tools/test_verify_referential_integrity.py`.

## Scoped Pytest Commands

```
pytest tests/tools/test_verify_referential_integrity.py -v
```

Regression re-check (confirm nothing in the adjacent monitoring-tooling test surface broke):

```
pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_migrate_monitoring_data.py tests/tools/test_agent_monitoring_manifest.py tests/tools/test_agent_monitoring_legacy_reader.py -v
```

Never `pytest tests/` — scoped to the `tools/agent-monitoring/` domain per this repo's Testing Rule.

## Anti-Drift Test Guards

- **The cross-week test (`test_cross_week_run_id_not_flagged`) is the single most important guard in
  this suite** — it is specifically designed to fail a same-week-scoped implementation even though
  such an implementation would pass every other test in this plan trivially. Do not let this test be
  weakened to a same-week fixture during implementation "for simplicity."
- **`test_duplicate_event_key_does_not_break_lookup`** guards against a subtle, real-corpus-observed
  failure mode (145 real duplicate `(run_id, seq)` event keys) that a naive `dict(...)` construction
  would silently mishandle — this is not a hypothetical edge case, it is measured from the live data.
- **`test_unknown_week_folder_included_in_join`** guards against an implementation that "cleans up"
  the glob by filtering to an ISO-week-shaped directory name regex, which would silently exclude a
  real, currently-populated fallback bucket and reintroduce exactly the kind of same-week/known-
  shape-only false positive this ticket exists to prevent.
- **`test_null_run_id_tools_row_excluded_from_check`** guards against the reported "checked" count
  being inflated by the 26.2%-of-corpus `run_id: null` population, which would make any future
  violation-rate percentage reported by the tool meaningless.
- **No test in this plan asserts the real corpus is clean.** A future regression in the write path
  (e.g. a reintroduced sidecar bug, or another `TCK-20260902-MONITORING-SHARD-MIGRATION`-style
  complete-events-loss incident) should be caught by a human reading the real-corpus report's
  violation *count* increasing over time, not by an automated test asserting zero — asserting zero
  today would be false on its face (investigation.md documents ~17K real, currently-existing
  violations) and asserting "no new violations since some baseline" is out of scope for this ticket
  (no baseline-snapshot mechanism exists yet; that would be new scope, not verification of this
  ticket's own deliverable).
