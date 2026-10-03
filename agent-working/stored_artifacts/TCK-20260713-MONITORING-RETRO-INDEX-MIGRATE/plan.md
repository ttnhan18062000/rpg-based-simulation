---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE
artifact_type: plan
tags: [agent-monitoring, data-quality, schema]
---

# Implementation Plan — TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE

## Summary

This plan migrates `generate_retro.py`'s **data-loading layer only** — `main()`'s two
`load_jsonl(RUNS_FILE)`/`load_jsonl(EVENTS_FILE)` calls and `_update_index()`'s own duplicate
`load_jsonl(RUNS_FILE)` read — from direct JSONL scans to the derived SQLite index
(`agent-monitoring-index/monitoring.db`, built by the out-of-scope `build_index.py`), with a
build-on-demand fallback that degrades to the original `load_jsonl()` scan if the index is
missing and cannot be built, so the index never becomes a hard gating dependency.

**AC1's literal wording ("removed... from generate_retro.py") is reinterpreted, following the
exact precedent set by the sibling `TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE` ticket's plan
for its own identical AC3 conflict.** `build_index.py` imports `_resolve_status` directly
(`from generate_retro import _resolve_status`, build_index.py:39) and is out of scope to edit, so
`_resolve_status()`'s definition cannot be deleted. Separately, `compute_retro_metrics()`'s 10
internal call sites of the three helpers are exercised by ~15+ existing tests that inject plain
dicts directly (never through the index) — rewriting those call sites to read a pre-injected index
key would break AC4's "tests continue to pass unmodified." **Resolution: `_resolve_status()`,
`_is_legacy_event()`, and `_is_gate_fail()` all keep their current definitions AND all 10 of their
call sites inside `compute_retro_metrics()` completely untouched (zero behavior change there).**
"Removed... and replaced by reads against the... index" is satisfied at the layer that actually
reads `runs.jsonl`/`events.jsonl` from disk — `main()` and `_update_index()` — which is where the
ticket's real DRY payoff (one physical read of the corpus, not a second linear scan per retro
invocation) actually lives. This must be stated explicitly here, not silently narrowed — see
Acceptance Criteria Map.

**`_is_legacy_event()`/`_is_gate_fail()` are kept, unchanged, alongside `_resolve_status()`** —
confirmed to have no external importers, so they *could* be inlined, but since their call sites
inside `compute_retro_metrics()` must stay untouched regardless (same constraint as
`_resolve_status`), removing them would only add churn (rewriting 4 call sites to inline
expressions) with no scope benefit tied to any AC. Not worth the risk.

**`_update_index()`'s 2 call sites and its own `load_jsonl(RUNS_FILE)` read are folded into this
migration** (recommended in investigation.md Risk #3, same reasoning the VALIDATE-INDEX-MIGRATE
ticket used to fold in `compute_multi_invocation_collision_report`): it duplicates the exact
normalization/load pattern this ticket exists to consolidate. Rather than giving `_update_index()`
its own second index read, its signature changes to accept the already-loaded `all_runs` list from
`main()` — eliminating a redundant physical read entirely, not just moving it from JSONL to SQL.

**Build-on-demand fallback**: `generate_retro.py` gains a new `_load_runs_and_events()` function.
If `DEFAULT_DB_PATH` (a new module constant, `Path("agent-monitoring-index/monitoring.db")`,
mirroring `build_index.py`/`query.py`/`validate.py`'s own independently-defined copies of the same
literal — this repo's established convention, not a new shared-constant module) does not exist, it
calls `build_index.build()` programmatically to build it on the spot, then reads from it. If that
build fails for any reason (corrupt source JSONL, permissions, etc.), it prints a non-fatal warning
and falls back to the original `load_jsonl(RUNS_FILE)`/`load_jsonl(EVENTS_FILE)` scan — the most
literal reading of the ticket's Scope ("must never become a hard gating dependency"). The
`import build_index` statement is **deferred inside the function**, not placed at module top level
alongside the file's other imports: `build_index.py` itself does `from generate_retro import
_resolve_status` at ITS module top level, so an eager top-level `import build_index` in
`generate_retro.py` — evaluated before `_resolve_status` is defined at line 88 — would raise
`ImportError` on the very first `python3 generate_retro.py` invocation. The deferred/lazy import is
the standard, safe fix and is called out explicitly in Step 2 below.

## Steps

### Step 1 — Add direct predicate-level tests for the three helpers (no production code change)
**Files:** `tests/tools/test_generate_retro.py`
**Change:** Add to the existing `from generate_retro import compute_retro_metrics, generate,
_record_since_cutoff` line (line 17) the three additional names: `_resolve_status`,
`_is_legacy_event`, `_is_gate_fail`. Then add these new test functions (exact names per
test_plan.md, so a future contributor recognizes them as the intended coverage, not incidental):
- `test_resolve_status_prefers_final_status_over_status` — `_resolve_status({"final_status":
  "DONE", "status": "old"}) == "DONE"`.
- `test_resolve_status_falls_back_to_status_when_final_status_absent` — `_resolve_status({"status":
  "complete"}) == "complete"` (literal spelling preserved, NOT normalized to `"DONE"`).
- `test_resolve_status_returns_none_when_both_absent` — `_resolve_status({}) is None`.
- `test_is_legacy_event_true_when_agent_missing` / `test_is_legacy_event_false_when_agent_present`.
- `test_is_gate_fail_true_for_non_terminal_status` /
  `test_is_gate_fail_false_for_done_epic_scoped_in_progress` — cover all 3 terminal values
  (`"DONE"`, `"EPIC_SCOPED"`, `"IN_PROGRESS"`) individually, not just one.
- `test_resolve_status_function_still_importable_from_generate_retro` — `from generate_retro
  import _resolve_status` succeeds and is callable (guards against a future edit literally deleting
  it, since `build_index.py` depends on this import).
- `test_gate_fail_tuple_literal_unchanged` — pins `("DONE", "EPIC_SCOPED", "IN_PROGRESS")` as the
  exact tuple `_is_gate_fail()` compares against.
**Do NOT touch:** `generate_retro.py` itself in this step — pure test addition, proves the three
helpers' current behavior is captured before any surrounding code changes.
**Verify:** `pytest tests/tools/test_generate_retro.py -v` — all new tests pass, all 35 pre-existing
tests still pass.

### Step 2 — Add the index-backed loader function to generate_retro.py
**Files:** `tools/agent-monitoring/generate_retro.py`
**Change:**
1. Add `import sqlite3` to the top-of-file stdlib imports (alongside `argparse`, `json`,
   `statistics`, `sys`).
2. Add two new module constants directly below `RETRO_DIR = Path("agent-monitoring/retro")`
   (line 38): `DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")` and
   `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")`.
3. Add a new function `_load_runs_and_events()` (placed near `load_jsonl()`, e.g. directly after
   it): reads `DEFAULT_DB_PATH` (bare global-name lookup, so it stays monkeypatch-compatible from
   outside via `monkeypatch.setattr(generate_retro, "DEFAULT_DB_PATH", ...)`, exactly like
   `RUNS_FILE`/`EVENTS_FILE`/`RETRO_DIR` already are). If the path does not exist, lazily `import
   build_index` and `from types import SimpleNamespace` **inside this function body**, then call
   `build_index.build(SimpleNamespace(runs_file=str(RUNS_FILE), events_file=str(EVENTS_FILE),
   tools_file=str(DEFAULT_TOOLS_FILE), db_path=str(DEFAULT_DB_PATH)))` — passing the SAME full set
   of file paths `build_index.py`'s own CLI defaults use, so an on-demand build produces the exact
   same shape of index a `make agent-monitoring-index` run would (not a stripped-down
   runs/events-only index that would silently diverge for other consumers like `query.py`). Then
   open a read-only `sqlite3.connect()`, `SELECT raw_json FROM runs ORDER BY id` /
   `SELECT raw_json FROM events ORDER BY id`, `json.loads()` each `raw_json` value back to a plain
   dict (mirroring `validate.py`'s `load_runs_from_index()`/`load_events_from_index()` shape
   exactly — field-identical dicts, no injected key like `query.py`'s `_resolved_status`), close
   the connection, and return `(all_runs, all_events)`. Wrap the whole body in `try/except
   Exception`: on any failure, print `WARNING: agent-monitoring index unavailable ({exc}); falling
   back to direct JSONL scan of {RUNS_FILE}/{EVENTS_FILE}` to stderr and return
   `(load_jsonl(RUNS_FILE), load_jsonl(EVENTS_FILE))`.
**Do NOT touch:** `_resolve_status()`, `_is_legacy_event()`, `_is_gate_fail()`,
`compute_retro_metrics()`, `generate()`, `load_jsonl()`'s own body, `main()`, `_update_index()` —
this step only adds a new, not-yet-called function.
**Verify:** New unit test (added in Step 6) exercising `_load_runs_and_events()` directly with a
`tmp_path`-monkeypatched `DEFAULT_DB_PATH`/`RUNS_FILE`/`EVENTS_FILE`. Confirm `python3 -c "import
generate_retro"` still succeeds with no `ImportError` (proves the lazy-import placement avoids the
circular-import hazard).

### Step 3 — Wire main() to use the new loader
**Files:** `tools/agent-monitoring/generate_retro.py`
**Change:** In `main()`, replace the two lines
```python
all_runs = load_jsonl(RUNS_FILE)
all_events = load_jsonl(EVENTS_FILE)
```
(currently lines 751-752) with:
```python
all_runs, all_events = _load_runs_and_events()
```
No other line in `main()` changes — the `--all`/`--days`/`--week` filtering logic below this point
already operates on `all_runs`/`all_events` and needs no modification.
**Do NOT touch:** the filtering branches (`if args.all: ... elif args.days: ... else: ...`),
`generate(runs, events, label, week_str)` call, or the report-writing lines.
**Verify:** `test_main_loads_via_index_not_direct_jsonl_scan` (Step 7) — a source-text or
call-tracking assertion that `main()` no longer calls `load_jsonl(RUNS_FILE)`/`load_jsonl
(EVENTS_FILE)` directly.

### Step 4 — Fold _update_index()'s data loading into the migration
**Files:** `tools/agent-monitoring/generate_retro.py`
**Change:** Change `_update_index()`'s signature from `def _update_index():` to `def
_update_index(all_runs):`. Delete its internal `all_runs = load_jsonl(RUNS_FILE)` line (currently
line 796) entirely — it now uses the `all_runs` parameter directly for the
`runs_by_week`/`week_runs`/`done`/`fails` computation that follows (lines 797-808 unchanged
otherwise). Update `main()`'s call site from `_update_index()` to `_update_index(all_runs)` (using
the `all_runs` list `main()` already holds from Step 3 — no second read of any kind, JSONL or
index).
**Do NOT touch:** the rest of `_update_index()`'s body — `retro_files` globbing, the `iso_week`
grouping logic, the `_resolve_status()`/gate-fail-tuple comparisons at lines 807-808 (these stay
calling `_resolve_status()` exactly as before, same as `compute_retro_metrics()`'s call sites — no
special-casing needed since they now just read from the parameter instead of a fresh disk scan).
**Verify:** `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope` (Step
7) — asserts `_update_index()` no longer contains a `load_jsonl(RUNS_FILE)` call and that its
`_resolve_status` call sites still produce identical DONE/gate-fail counts against a fixed fixture.

### Step 5 — Add a module-level autouse fixture that isolates every test in the file
**Files:** `tests/tools/test_generate_retro.py`
**Change:** Add a local `@pytest.fixture(autouse=True)` near the top of the file (directly below
the existing imports, before the first test function — no new `conftest.py`) that monkeypatches
`generate_retro.DEFAULT_DB_PATH` to a `tmp_path`-based location for **every** test in the file
automatically:
```python
@pytest.fixture(autouse=True)
def _isolate_monitoring_index(monkeypatch, tmp_path):
    monkeypatch.setattr(generate_retro, "DEFAULT_DB_PATH", tmp_path / "monitoring.db")
```
Because `tmp_path` is function-scoped (a fresh temp dir per test) and this fixture is `autouse=True`,
it runs before every test in `tests/tools/test_generate_retro.py` without any test needing to
reference it by name — including `test_generate_retro_days_flag_does_not_raise_on_legacy_start_ts`
(currently line 691) and every new test added in Steps 6-7.
**Why this is necessary:** without it, any test that calls `generate_retro.main()` (or otherwise
reaches Step 2's `_load_runs_and_events()`) would evaluate `DEFAULT_DB_PATH` against its real
default (`agent-monitoring-index/monitoring.db`, relative to the real repo root) — silently reading
the **real** production index instead of a test's fake fixture (masking the test's actual intent
without failing it), or worse, if the real index doesn't exist at test-run time, **building a real
`agent-monitoring-index/monitoring.db` in the actual repo tree containing only test fixture
records**, corrupting durable state for every other consumer (`query.py`, `validate.py`) — a direct
violation of CLAUDE.md's Hard Rule "Do not mutate durable state outside authoritative flows." The
autouse fixture closes this hole for the whole file at once, by construction, rather than relying on
each test author to remember an individual monkeypatch line.
**Why this is strictly better than a per-test monkeypatch line (architecture review finding):**
(a) it satisfies AC4's "tests continue to pass unmodified" **literally** — zero existing test bodies
change, so no exception to AC4 needs to be invoked at all; (b) it protects every future test added to
the file, including the new tests Steps 6-7 are about to add, against the same durable-state-leak
class by construction, not by each test remembering to add the monkeypatch line individually;
(c) it remains a single-file, in-scope change (`tests/tools/test_generate_retro.py` only).
**Do NOT touch:** any existing test function's body, assertions, or fixture arguments — this step
adds exactly one new fixture function and modifies no other line in the file.
**Verify:** `pytest tests/tools/test_generate_retro.py -v` — full file green, including
`test_generate_retro_days_flag_does_not_raise_on_legacy_start_ts` unmodified — and confirm (by
inspection, not a committed artifact) that no file appears under the real repo's
`agent-monitoring-index/` as a side effect of running the full test file.

### Step 6 — Add build-on-demand / fallback / no-hard-exit tests
**Files:** `tests/tools/test_generate_retro.py`
**Change:** Add:
- `test_generate_retro_builds_index_on_demand_when_missing` — monkeypatch `RUNS_FILE`,
  `EVENTS_FILE`, `DEFAULT_DB_PATH` (and `DEFAULT_TOOLS_FILE` if convenient) to `tmp_path` locations,
  with `DEFAULT_DB_PATH` pointing at a file that does not yet exist; call `_load_runs_and_events()`
  directly; assert the db file now exists at that path afterward and the returned `(runs, events)`
  match the fixture content written to `RUNS_FILE`/`EVENTS_FILE`.
- `test_generate_retro_produces_clear_error_message_if_build_on_demand_disabled_or_fails` —
  monkeypatch `build_index.build` (via `monkeypatch.setattr(build_index, "build", <raiser>)`, lazy
  import already means `build_index` is importable at test time too) to raise; call
  `_load_runs_and_events()`; assert it does **not** raise, prints a warning to stderr (capsys), and
  returns the same result `load_jsonl(RUNS_FILE)`/`load_jsonl(EVENTS_FILE)` would have returned
  directly against the fixture files.
- `test_no_sys_exit_1_on_missing_index_in_generate_retro` — negative-space guard: run
  `_load_runs_and_events()` (or `main()`) against a missing/unbuildable index and assert no
  `SystemExit` is raised — the direct opposite of `query.py`/`validate.py`'s `open_index()`
  precedent, catching a future editor "fixing" this intentional divergence back toward
  sibling-pattern conformity.
- `test_generate_retro_never_writes_to_agent_monitoring_index_db` — architecture guard: read
  `generate_retro.py`'s source text and assert no `INSERT`/`UPDATE`/`.execute("INSERT` string
  appears in the file (the only legitimate write path is the delegated `build_index.build()` call);
  the module's own `sqlite3.connect()` usage in `_load_runs_and_events()` must only ever `SELECT`.
**Do NOT touch:** `_load_runs_and_events()`'s implementation itself in this step — tests only.
**Verify:** `pytest tests/tools/test_generate_retro.py -v` — all four new tests pass.

### Step 7 — Add migration-completeness and output-parity architecture guards
**Files:** `tests/tools/test_generate_retro.py`
**Change:** Add:
- `test_main_loads_via_index_not_direct_jsonl_scan` — source-text guard mirroring
  `test_build_index_never_touches_write_path_modules`'s shape: assert `main()`'s source (via
  `inspect.getsource(generate_retro.main)`) no longer contains a literal `load_jsonl(RUNS_FILE)` or
  `load_jsonl(EVENTS_FILE)` call.
- `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope` — asserts
  `inspect.getsource(generate_retro._update_index)` contains no `load_jsonl(RUNS_FILE)` call and
  that `_update_index`'s signature takes an `all_runs` parameter (via `inspect.signature`).
- `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` — the direct
  AC2 proof. Build a small fixed `runs`/`events` fixture (2-3 records covering a DONE run, a
  gate-fail run, and a legacy-shaped `status`-only run), call `generate(runs, events,
  "fixed-label")`, and assert the output equals a frozen string constant hand-copied into the test
  file (not sourced from git history, per the `QUERY-INDEX-MIGRATE` convention). Since
  `compute_retro_metrics()`/`generate()` are untouched by this migration, this should trivially
  pass — its value is pinning the guarantee explicitly.
- `test_normalize_phase_agent_and_flag_outliers_untouched` — source-text or behavioral guard
  confirming `_normalize_phase`, `_normalize_agent`, `_canonicalize`, `_flag_outliers` are
  byte-identical to their pre-migration form (a future editor migrating `_resolve_status` might be
  tempted to "also clean up" these adjacent functions — this guard catches that scope creep).
**Do NOT touch:** any file outside `tests/tools/test_generate_retro.py`.
**Verify:** `pytest tests/tools/test_generate_retro.py -v` — full file green, including all tests
added in Steps 1, 5, 6, 7.

### Step 8 — Full regression pass
**Files:** none (verification only)
**Change:** Run the Scoped Pytest Commands from test_plan.md:
```
pytest tests/tools/test_generate_retro.py tests/tools/test_build_index.py -v
pytest tests/tools/test_validate_agent_monitoring.py -v
pytest tests/tools/test_query.py -v
pytest tests/tools/test_agent_ops_dashboard_stats.py -v  # only if it exists and imports compute_retro_metrics
```
Explicitly re-run (not modify)
`tests/tools/test_build_index.py::TestNormalizationParity::test_resolved_status_matches_generate_retro_resolve_status`
to confirm `_resolve_status()`'s behavior has not silently diverged from what `build_index.py`
assumes. Confirm `git diff --stat` touches only `tools/agent-monitoring/generate_retro.py` and
`tests/tools/test_generate_retro.py` — no edits to `build_index.py`, `query.py`, `validate.py`, or
any doc.
**Do NOT touch:** run this as a read-only verification step; if anything fails, return to the
relevant earlier step rather than patching ad hoc here.
**Verify:** All listed pytest commands exit 0.

## Scope Guards

- Do not edit `tools/agent-monitoring/build_index.py` — out of scope (sibling ticket
  TCK-20260713-MONITORING-SQLITE-INDEX's responsibility). `_resolve_status`'s import from it must
  keep working unmodified.
- Do not edit `tools/agent-monitoring/query.py` or `tools/agent-monitoring/validate.py` — separate
  sibling tickets already migrated these; both are out of scope here.
- Do not delete or change the definitions of `_resolve_status()`, `_is_legacy_event()`, or
  `_is_gate_fail()` — keep all three, unchanged, alongside their current call sites inside
  `compute_retro_metrics()` (10 sites) and `_update_index()` (2 sites, migrated only in the sense
  that the data feeding them now comes from a parameter instead of a fresh disk read — the call
  sites themselves, `_resolve_status(r)`/`_is_gate_fail(r)`, are textually identical before and
  after).
- Do not change `compute_retro_metrics()`'s or `generate()`'s signature or body in any way.
- Do not touch `_normalize_phase`, `_normalize_agent`, `_canonicalize`, `_flag_outliers` — a
  separate, already-shipped normalization concern (INFRA-283/284), no index column support, not
  named in this ticket's Scope.
- Do not write to `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, or
  `agent-monitoring/tools.jsonl` — read-only source of truth throughout.
- Do not write to `agent-monitoring-index/monitoring.db` via any path other than the delegated
  `build_index.build()` call — no bespoke `INSERT`/`UPDATE`/`sqlite3.connect(...)` write logic
  inside `generate_retro.py`.
- Do not introduce a hard `sys.exit(1)`-on-missing-index pattern copied from `query.py`/
  `validate.py` — this ticket's Scope explicitly requires the opposite, a deliberate divergence.
- Do not extract `_resolve_status()` (or any of the three helpers) into a new shared module to
  "properly" resolve the cross-import — investigation.md explicitly names this as a materially
  larger, unrequested architectural change; not in scope.
- Do not modify `docs/agent-monitoring/schema.md` or any other doc — confirmed neither sibling
  migration (query.py/validate.py) added index-loading documentation there either; no new
  precedent to establish in this ticket.
- Do not add a `--db-path` CLI flag to `generate_retro.py`'s `argparse` parser — not requested by
  the ticket's Scope/AC, and `query.py`/`validate.py`'s CLI-flag pattern is exactly the
  hard-dependency precedent this ticket diverges from; the build-on-demand path is automatic, not
  operator-invoked.

## Dependency Map

- Step 1 — independent, can run first or in parallel with Step 2.
- Step 2 — independent (adds a new, not-yet-called function).
- Step 3 — depends on Step 2 (`_load_runs_and_events()` must exist).
- Step 4 — depends on Steps 2 and 3 (uses the `all_runs` variable Step 3 introduces in `main()`).
- Step 5 — depends on Step 2 only (`DEFAULT_DB_PATH` must exist as a module attribute on
  `generate_retro` before the fixture can monkeypatch it); independent of Steps 3-4. Positioned
  before Steps 6-7 in execution order because those steps add new tests to the same file that this
  fixture protects by construction.
- Step 6 — depends on Step 2 (`_load_runs_and_events()` must exist to test directly); independent
  of Steps 3-5.
- Step 7 — depends on Steps 2-4 (asserts the migration landed in `main()`/`_update_index()`).
- Step 8 — depends on all prior steps; final gate.

Recommended execution order: 1, 2, 3, 4, 5, 6, 7, 8 (matches numbering — no reordering needed).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — helpers "removed... and replaced by reads against the index" (**reinterpreted**: `_resolve_status`/`_is_legacy_event`/`_is_gate_fail` definitions and their 10 `compute_retro_metrics()` call sites stay; the data-**loading** layer in `main()`/`_update_index()` is what migrates to index reads) | Steps 2, 3, 4 | `test_main_loads_via_index_not_direct_jsonl_scan`, `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope`, `test_resolve_status_function_still_importable_from_generate_retro` |
| AC2 — byte-identical report output before/after, proving non-normalizing behavior is preserved | Steps 2, 3, 4 (no change to `compute_retro_metrics()`/`generate()` bodies) | `test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus`, re-run of `test_build_index.py::TestNormalizationParity::test_resolved_status_matches_generate_retro_resolve_status` |
| AC3 — "all 6 call sites... migrated together, not partially" (**corrected**: actual count is 12 call sites across `compute_retro_metrics()` [10, intentionally untouched] and `_update_index()` [2, migrated]; the migration unit that lands together is the 2 data-loading sites in `main()` + `_update_index()`, landed in one coherent change across Steps 2-4) | Steps 2, 3, 4 | `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope` |
| AC4 — existing tests pass unmodified + new predicate-level tests added (**satisfied literally**: Step 5 adds a module-level `autouse=True` pytest fixture that monkeypatches `DEFAULT_DB_PATH` for every test in the file automatically — zero existing test bodies are edited, so no exception to "unmodified" is invoked) | Steps 1, 5, 6, 7 | Full `pytest tests/tools/test_generate_retro.py -v` run (Step 8) |
| Scope — "safe fallback (build-on-demand, or a clear error)... must never become a hard gating dependency" | Step 2 (loader), Step 6 (tests) | `test_generate_retro_builds_index_on_demand_when_missing`, `test_generate_retro_produces_clear_error_message_if_build_on_demand_disabled_or_fails`, `test_no_sys_exit_1_on_missing_index_in_generate_retro` |

## Scope Reconciliation — provider/execution_id cross-reference (WRITER-UNIFICATION)

This ticket's own `Related Tickets` section states: "TCK-20260721-MONITORING-WRITER-UNIFICATION
(BLOCKS this ticket... this ticket's provider/execution_id-aware read migration depends on that
ticket's additive writer schema fields existing first)." The done
`TCK-20260721-MONITORING-WRITER-UNIFICATION` ticket similarly states that `generate_retro.py`'s
migration to provider/execution_id-aware reads is "owned by...
TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE." This plan.md previously had zero mentions of
`provider` or `execution_id` anywhere, leaving that cross-reference's implication unaddressed. This
section reconciles it explicitly.

**This cross-reference is a cross-batch DEPENDENCY annotation, not a Scope/Acceptance-Criteria
amendment.** It exists to confirm this ticket was safe to *start* only once WRITER-UNIFICATION had
shipped its additive `provider`/`execution_id` fields into the raw JSONL records — it is not an
instruction for this plan to add new provider/execution_id grouping, filtering, or labeling to
`generate_retro.py`'s report output. That reporting capability is explicitly **OUT OF SCOPE** for
this ticket:

- No AC in this ticket's own `Acceptance Criteria` section mentions `provider` or `execution_id`.
- This ticket's own `Scope` section asks only for removing/migrating the three legacy-shape
  helpers' (`_resolve_status`/`_is_legacy_event`/`_is_gate_fail`) call sites — not for new report
  dimensions.

**The data-loading migration in this plan is provider/execution_id-SAFE, but not
provider/execution_id-AWARE, and this plan does not close that gap.** `build_index.py`'s
`CREATE TABLE` schema has no `provider`/`execution_id`/`ticket_id` SQL columns — those fields exist
only as additive fields inside each raw JSONL record, preserved verbatim in the index's `raw_json`
column (per WRITER-UNIFICATION), not as queryable SQL columns today. Step 2's
`_load_runs_and_events()` reads `raw_json` and `json.loads()`s it back into a field-identical dict —
every key present in a newer record, including `provider`/`execution_id` if WRITER-UNIFICATION
populated them, survives the round trip untouched and undropped; the data-loading migration does not
silently destroy or corrupt those fields when present. However, `compute_retro_metrics()` and
`generate()`'s report rendering (the weekly/`--all` report logic) never grouped, filtered, or
labeled by `provider`/`execution_id` before this migration, and — per the Scope Guards above, which
keep `compute_retro_metrics()`/`generate()` untouched — this plan does not add that capability
either.

**If provider/execution_id-aware reporting is wanted, it needs its own future ticket.** This plan
recommends that follow-up but does not scope it in here — implementers should not interpret this
section as authorization to add provider/execution_id grouping/filtering/labeling logic as part of
any step above.

## Anti-Drift Notes

- **The provider/execution_id `Related Tickets` cross-reference to WRITER-UNIFICATION is a
  dependency annotation only** — see the "Scope Reconciliation" section above. Do not add
  provider/execution_id grouping, filtering, or labeling to `compute_retro_metrics()`/`generate()`
  as part of this ticket; that is out of scope and belongs in a future ticket if wanted.
- **AC1 and AC3 are both explicitly reinterpreted in this plan**, following the exact precedent of
  the sibling `TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE` plan's resolution of its own
  identical conflict. This is stated here and in the Summary/Acceptance Criteria Map — not applied
  silently. If the main session disagrees with this reinterpretation, the blocking architectural
  fact (`build_index.py`'s live import of `_resolve_status`, out of scope to edit) must be resolved
  first — either by bringing `build_index.py` into scope or accepting the reinterpretation.
- **AC4 is satisfied literally, not via an invoked exception** (Step 5) — a single module-level
  `@pytest.fixture(autouse=True)` in `tests/tools/test_generate_retro.py` monkeypatches
  `DEFAULT_DB_PATH` to a `tmp_path` location for every test in the file automatically. No existing
  test body is modified, so "tests continue to pass unmodified" holds literally; this also protects
  every test added in Steps 6-7 against the same durable-state-leak class (CLAUDE.md Hard Rule:
  "do not mutate durable state outside authoritative flows") by construction, not by each test
  remembering an individual monkeypatch line. Do not expand this into per-test monkeypatch lines or
  a new `conftest.py` — the fixture lives in the one file, once.
- **`_is_legacy_event()`/`_is_gate_fail()` are intentionally kept, not removed** — no external
  importers means removal is *possible*, not *valuable*; their call sites can't move regardless
  (same constraint as `_resolve_status`), so removing them buys nothing and adds unrequested churn.
- **The on-demand build must pass the full `runs_file`/`events_file`/`tools_file`/`db_path`
  argument set to `build_index.build()`**, not a runs/events-only partial call — an incomplete
  on-demand-built index would silently diverge in shape from what `make agent-monitoring-index`
  produces, corrupting `query.py`/`validate.py`'s later reads of the same db file.
- **The `import build_index` inside `_load_runs_and_events()` must stay a deferred/lazy import**,
  never hoisted to module top level — `build_index.py`'s own top-level `from generate_retro import
  _resolve_status` creates the opposite-direction edge; an eager top-level import in
  `generate_retro.py` would raise `ImportError` on ordinary invocation, since `_resolve_status`
  isn't defined yet at the point Python would need to resolve it.
- **Once built, the on-demand index is not proactively rebuilt on every subsequent invocation** —
  build-on-demand fires only when `DEFAULT_DB_PATH` is missing, matching the ticket's literal "if
  the index has not been built yet" framing. This means a stale index (source JSONL grew since the
  last build) is read as-is until someone runs `make agent-monitoring-index` again — an accepted,
  pre-existing tradeoff already present for `query.py`/`validate.py`'s consumers, not a new problem
  this ticket introduces.
- **Do not normalize legacy status-string spellings** anywhere in this migration — automatically
  preserved by construction since `_resolve_status()`'s body is untouched and the index's
  `resolved_status` column is built from the exact same function (import, not reimplementation).
- **`_update_index()` is not named in the ticket's own Scope text** but is explicitly folded in
  here per investigation.md Risk #3's recommended resolution — flagged so a reviewer checking the
  ticket's literal wording against the diff isn't surprised to see `_update_index()` touched.
