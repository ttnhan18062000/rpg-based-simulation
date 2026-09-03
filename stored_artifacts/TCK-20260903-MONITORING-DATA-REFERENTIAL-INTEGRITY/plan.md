---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY
artifact_type: plan
tags: [agent-monitoring, observability, data-quality, schema]
---

# Implementation Plan — TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY

## Summary

Build a new, standalone, read-only script — `tools/agent-monitoring/verify_referential_integrity.py`
— that automates the 2 documented FK relationships in `docs/agent-monitoring/schema.md`
(`events.run_id → runs.run_id` at schema.md:141/172; `tools.(run_id, seq) → events.(run_id, seq)` at
schema.md:370/407-408): a multi-week-aware loader (`load_all_weeks()`, modeled on the 3 already-landed
glob-over-all-weeks precedents — `record_events.py::compute_tool_stats()` lines 34-74,
`migrate_monitoring_data.py`, and schema.md's own Join Example lines 472-502), two independent
existence-check functions (one per FK), and a structured, dual-purpose report (a small dataclass with
a `.to_text()` renderer mirroring `validate.py`'s `compute_tool_count_drift_report()` string
convention, lines 151-194) exposing both counts and capped concrete-example lists. The tool is
additive only — it never gates, never writes, and never touches the SQLite index
(`agent-monitoring-index/monitoring.db`) or `build_index.py`, both confirmed stale against the new
`agent-monitoring/data/<week>/` layout by investigation.md. It is invocable both as a CLI script and
as an importable library function, so a future consumer (dashboard, gate, manual audit) can call
`compute_referential_integrity_report()` directly without shelling out. 11 new tests land in
`tests/tools/test_verify_referential_integrity.py`, the tool is run once against the real corpus with
its output captured in the ticket's Test Summary/Implementation Notes, and a new "Referential
Integrity" entry is added to `docs/agent-monitoring/schema.md`'s existing Known Limitations section.

## Ratified Decisions (per orchestrator's request)

**Decision on item 8 (script vs. library function vs. both): standalone script, exposing both.**
`tools/agent-monitoring/verify_referential_integrity.py` is a new file, not a new function added to
`validate.py`. Rationale:
- `validate.py`'s only read path is the stale SQLite index (`open_index()`/`load_runs_from_index()`
  etc., `validate.py:33-55`, wired from `main()` at `validate.py:258-262`) — reusing that file would
  either require also patching its index-dependent `main()` (out of scope: this ticket must not
  depend on `build_index.py`, confirmed stale, per investigation.md's Current Behavior section) or
  bolting an entirely separate multi-week loader onto a module whose own `load_jsonl()` (lines
  223-240) already targets a different, retired directory shape (`agent-monitoring/tools/tools-*.jsonl`,
  not `agent-monitoring/data/<week>/*.jsonl`).
- Keeping `validate.py` byte-for-byte untouched trivially satisfies test_plan.md's regression
  requirement that `tests/tools/test_validate_agent_monitoring.py` "must be untouched by this ticket"
  without relying on the file's own conditional escape clause.
- The ticket's own Related Code Areas section lists `verify_referential_integrity.py` as the expected
  new filename.
- Both a CLI (`main()`/`build_parser()`, argparse convention matching `validate.py:243-253`) and a
  plain importable function (`compute_referential_integrity_report(data_dir: Path = DEFAULT_DATA_DIR)
  -> ReferentialIntegrityReport`) are exposed from the same module — the function does the real work,
  `main()` is a thin wrapper that calls it and prints `.to_text()`. This satisfies investigation's
  named future consumer (`done_checker_static.py` or a future CI gate calling it as a library
  function) without wiring either in now — no import of this module appears anywhere outside its own
  test file in this ticket's diff.

**Decision on item 4 (report vs. crash vs. gate on real-corpus violations): report unconditionally,
never crash, never hard-fail on volume alone.** Rationale, directly following investigation.md's Risk
#1 recommendation:
- The real corpus already has ~17,274 Check-2 orphans (12.7% of 135,804 checked rows) and 18 Check-1
  orphans, and investigation.md's own analysis attributes the large majority to already-documented,
  explicitly-not-backfilled historical corruption (`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-
  COLLISION`, `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`) plus one confirmed-but-unroot-caused
  anomaly (`TCK-20260902-MONITORING-SHARD-MIGRATION`). A default hard-fail exit code on volume alone
  would immediately and permanently "fail" every future invocation, training operators to ignore the
  tool's exit status entirely — the same failure mode `compute_drift_report()` /
  `compute_tool_count_drift_report()` / `compute_multi_invocation_collision_report()` already avoid by
  design (`validate.py`'s own docstrings state "never gates anything, purely additive reporting" at
  lines 92-93 and 159-163).
- `main()` therefore always exits 0 after printing the report (matching the 3 existing report
  functions' contract), never `sys.exit(1)` on violation count. This mirrors `validate.py`'s own
  `errors`/`warnings` split, except this tool has no `errors` category at all — every finding is
  reported, none is gating.
- No `--strict`/exit-code-on-violation flag is added in this ticket. Out of Scope explicitly excludes
  "wiring this into `done_checker_static.py`/CI... unless the real-corpus run finds it needs to" —
  adding a strict/gate-flavored flag now would be scope-creep toward exactly that wiring decision
  without the deliberate record the ticket requires. If a future ticket wires this into a gate, that
  ticket adds the flag then, with its own explicit decision record.
- Tests never assert the real corpus is clean (`test_real_corpus_smoke_run` asserts successful
  execution + well-formed report only); a separate clean synthetic fixture test
  (`test_same_week_only_join_baseline`) asserts `zero` violations so a real regression stays
  catchable — this matches test_plan.md's Anti-Drift Test Guards section verbatim.

## Steps

### Step 1 — Script skeleton + multi-week loader
**Files:** `tools/agent-monitoring/verify_referential_integrity.py` (new)
**Change:** Create the new module with:
- `DEFAULT_DATA_DIR = Path("agent-monitoring/data")` module constant.
- `load_all_weeks(data_dir: Path, source: str) -> list[tuple[dict, str]]` — globs
  `sorted(data_dir.glob(f"*/{source}.jsonl"))` (the exact pattern confirmed at
  `record_events.py:65`, reused by reference per investigation's Anti-Drift Hazards, "do not build a
  4th independent loader"), reads each file line-by-line, `json.loads()` each non-empty line inside a
  `try/except json.JSONDecodeError` that prints a `WARNING: {path}:{i}: invalid JSON — {e}` to stderr
  and skips the line (matching `validate.py::load_jsonl()`'s tolerance convention, lines 223-240,
  reused as a style precedent, not imported — that function's directory-glob branch targets the
  retired `tools-*.jsonl` shard shape and is not reusable as-is per investigation.md). Returns a list
  of `(record_dict, week_folder_name)` tuples — the week-folder tag travels with each record from here
  on so every downstream violation example can cite it, satisfying Scope's "concrete examples:
  `run_id`/`seq`/week-folder of each orphan" requirement. `source` is one of `"runs"`, `"events"`,
  `"tools"` — the three physical filenames confirmed present under every `agent-monitoring/data/<week>/`
  folder by schema.md's own directory-layout description (lines 143-153, 374-385) and directly
  observed via `ls agent-monitoring/data/2026-W36/` during investigation.
- This loader makes no assumption about which week folder a `run_id`'s records land in — it reads
  every folder unconditionally, satisfying the ticket's core correctness requirement (never resolve a
  run's week before searching).
- Concurrent-writer note (Fact-Verification requirement #2): the same `agent-monitoring/data/<week>/
  {runs,events,tools}.jsonl` files this loader reads are actively appended to by `record_run.py`,
  `record_events.py`, and `post_tool_hook.py` (via the shared `writer.py::write_line()` O_CREAT|O_EXCL
  lock protocol, documented at schema.md:419) during any concurrently-running session — this loader
  takes no lock and does not need one, because it only ever reads complete, already-flushed lines
  (`write_line()` writes one full line per call under its own lock; a reader can at worst see a
  file with N lines partway through a write of line N+1, which `splitlines()` simply does not yet
  include — it cannot observe a torn/partial line, since the writer never mutates already-written
  bytes). The `json.JSONDecodeError` tolerance above is defense-in-depth for pre-existing malformed
  historical rows (the same posture `load_jsonl()` already takes), not primarily a concurrency
  safeguard.
**Do NOT touch:** `validate.py`, `record_events.py`, `record_run.py`, `migrate_monitoring_data.py`,
`build_index.py`, `manifest.py`, `legacy_reader.py`, `writer.py` — all read-only precedent/reference,
none imported or modified.
**Verify:** No standalone test yet (loader is exercised end-to-end by every test in Step 5); its
directory-inclusion behavior is directly verified by `test_unknown_week_folder_included_in_join`
once Steps 2-4 land.

### Step 2 — Check 1: `events.run_id → runs.run_id`
**Files:** `tools/agent-monitoring/verify_referential_integrity.py`
**Change:** Add `check_events_to_runs(runs: list[tuple[dict, str]], events: list[tuple[dict, str]]) ->
tuple[int, list[dict]]`:
- Build `valid_run_ids = {r.get("run_id") for r, _ in runs if r.get("run_id")}` — a plain `set`
  (per anti-drift note below).
- For each `(e, week)` in `events`: `run_id = e.get("run_id")`. Skip (do not count as checked) if
  `run_id is None` (defensive — schema.md:172 documents `events.run_id` as non-nullable ("No"), but
  the loader must not crash on a malformed historical row) or if `run_id.startswith("RETRIEVAL-EVENT-")`
  (the documented exception, schema.md lines 353-364: these `run_id`s "have no matching `runs.jsonl`
  row" by design). Otherwise increment `checked` and, if `run_id not in valid_run_ids`, append
  `{"run_id": run_id, "seq": e.get("seq"), "week_folder": week}` to the violation list.
- Return `(checked, violations)`.
- **Do not resolve a `run_id`'s own week before searching** — `valid_run_ids` is built from the full,
  all-weeks `runs` list passed in, never filtered to one folder. This is the single correctness
  property `test_cross_week_run_id_not_flagged` exists to catch.
- Duplicate-key note: `runs.jsonl` has 145-adjacent legacy-duplicate precedent for `(run_id, seq)` in
  `events.jsonl` (investigation.md's `(run_id, seq)` Global Uniqueness section) — `valid_run_ids` here
  is keyed by `run_id` alone (existence check, not uniqueness check), so a duplicate `runs.jsonl` row
  for the same `run_id` (investigation confirmed 8 such cases) has no effect on this check either way;
  no special handling needed.
**Do NOT touch:** Check 2's function (Step 3) — keep the two checks in fully independent functions,
each testable in isolation.
**Verify:** `test_orphan_event_no_matching_run_anywhere_is_flagged`,
`test_retrieval_event_run_id_excluded_from_check`, `test_cross_week_run_id_not_flagged`.

### Step 3 — Check 2: `tools.(run_id, seq) → events.(run_id, seq)`
**Files:** `tools/agent-monitoring/verify_referential_integrity.py`
**Change:** Add `check_tools_to_events(events: list[tuple[dict, str]], tools: list[tuple[dict, str]]) ->
tuple[int, list[dict]]`:
- Build `valid_keys: set[tuple] = set()`; for each `(e, _)` in `events`, if `e.get("run_id") is not
  None and e.get("seq") is not None`, add `(e["run_id"], e["seq"])` to the set. **Must be a `set`
  populated by iterating every event row, never a `dict` comprehension that overwrites on key
  collision** — investigation.md confirmed 145 distinct `(run_id, seq)` keys have more than one real
  `events.jsonl` row (e.g. `('TCK-20260606-DOCSITE-SCHEMA', 1)`); a `dict(...)`-style construction
  would silently keep only the last-seen row per key depending on glob/file ordering, and this is an
  existence check (does at least one event exist at this key), so a `set` is both correct and
  sufficient — no need to retain the duplicate rows themselves.
- For each `(t, week)` in `tools`: `run_id = t.get("run_id")`; `seq = t.get("seq")`. Skip (not
  counted as checked) if `run_id is None` (documented exception, schema.md:407 — "tool call occurred
  outside an active workflow run") or if `seq is None` (schema.md:408 — sidecar not yet written) or if
  `seq <= 0` (documented exception, schema.md:173/338-340 — negative-`seq` shadow rows from the
  `context-packet-wrapper` mechanism, deliberately disjoint from the monotonic `seq >= 1` range).
  Otherwise increment `checked` and, if `(run_id, seq) not in valid_keys`, append `{"run_id": run_id,
  "seq": seq, "week_folder": week}` to the violation list.
- Return `(checked, violations)`.
- Same cross-week correctness property as Step 2: `valid_keys` is built from the full, all-weeks
  `events` list — never scoped to one folder before searching.
**Do NOT touch:** `compute_tool_count_drift_report()` in `validate.py` (lines 151-194) — investigation
confirmed this is a distinct, pre-existing count-mismatch check, not an existence/FK check, and this
ticket's function is additive, not a replacement. Do not modify or call into it.
**Verify:** `test_orphan_tools_row_no_matching_event_anywhere_is_flagged`,
`test_null_run_id_tools_row_excluded_from_check`,
`test_negative_and_zero_seq_tools_rows_excluded_from_check`,
`test_duplicate_event_key_does_not_break_lookup`.

### Step 4 — Structured report, `.to_text()` rendering, and CLI entry point
**Files:** `tools/agent-monitoring/verify_referential_integrity.py`
**Change:**
- Add a small `@dataclass ReferentialIntegrityReport` with fields: `events_checked: int`,
  `events_violations: list[dict]`, `tools_checked: int`, `tools_violations: list[dict]`. Add a
  `.to_text(self, sample_size: int = 20) -> str` method that renders a string mirroring
  `compute_tool_count_drift_report()`'s exact convention (`validate.py:184-194`: a `"--- ... Report
  ---"` header, explicit checked/violation counts as their own lines, then `"Sample ..."` + up to
  `sample_size` capped concrete examples formatted as `f"  {run_id} seq={seq} (week={week_folder})"`,
  plus a `"... and N more"` trailer if truncated) — for both checks, clearly labeled ("Check 1:
  events.run_id -> runs.run_id" / "Check 2: tools.(run_id, seq) -> events.(run_id, seq)"). Document in
  the dataclass's own docstring: (a) the checked-count excludes every documented exception (never
  inflates the denominator with `RETRIEVAL-EVENT-*` events, `run_id: null` tools rows, or `seq <= 0`
  tools rows — directly satisfying `test_null_run_id_tools_row_excluded_from_check`'s requirement that
  the 26.2%-of-corpus null-`run_id` population never inflates "checked"), and (b) this report format
  itself (field names + `.to_text()` shape) is the documented contract for AC #4's "future consumer...
  to parse it" — a future dashboard/gate reads `report.events_violations` / `report.tools_violations`
  directly (structured), a human reads `report.to_text()` (rendered).
- Add `compute_referential_integrity_report(data_dir: Path = DEFAULT_DATA_DIR) ->
  ReferentialIntegrityReport`: calls `load_all_weeks(data_dir, "runs")` /
  `load_all_weeks(data_dir, "events")` / `load_all_weeks(data_dir, "tools")`, then
  `check_events_to_runs()` / `check_tools_to_events()`, and assembles the dataclass. This is the
  library-callable entry point (Decision on item 8 above).
- Add `build_parser()` (argparse, `--data-dir` optional override defaulting to
  `str(DEFAULT_DATA_DIR)`, mirroring `validate.py:243-248`'s `--db-path` convention) and `main(argv=None)`
  that parses args, calls `compute_referential_integrity_report(Path(args.data_dir))`, prints
  `report.to_text()`, and always exits 0 (Decision on item 4 above — no `sys.exit(1)` on violation
  volume; this tool has no `errors` category, only reported findings). Add the standard
  `if __name__ == "__main__": main()` footer.
**Do NOT touch:** Do not add a `--strict` or exit-code-on-violation flag in this step or ticket (see
Decision on item 4).
**Verify:** `test_report_output_matches_validate_py_style`, `test_same_week_only_join_baseline`,
`test_unknown_week_folder_included_in_join`.

### Step 5 — New test suite
**Files:** `tests/tools/test_verify_referential_integrity.py` (new)
**Change:** Add all 11 tests specified by test_plan.md, using `tmp_path` fixtures to build small
multi-week `<tmp>/data/<week>/{runs,events,tools}.jsonl` trees (never the real
`agent-monitoring/data/` directory for the unit/integration tests — matching
`test_migrate_monitoring_data.py`'s own precedent) and calling
`compute_referential_integrity_report(data_dir=tmp_path / "data")` directly (never shelling out to
`main()`, except optionally for one CLI-smoke assertion if the implementer wants it — not required by
test_plan.md):

1. `test_same_week_only_join_baseline` — one `run_id` with consistent `runs`/`events`/`tools` rows
   all in one week folder; assert `events_violations == []` and `tools_violations == []`.
2. `test_cross_week_run_id_not_flagged` — `<tmp>/data/2026-W10/runs.jsonl` holds the run record;
   `<tmp>/data/2026-W11/events.jsonl` + `<tmp>/data/2026-W11/tools.jsonl` hold that same `run_id`'s
   events/tools (modeled directly on the real corpus's confirmed
   `TCK-20260820-EPIC-WORLD-RENDERING-CORE`-style W34/W35 split, investigation.md's Real Corpus
   Characteristics section). Assert zero violations from both checks. This is the test that must fail
   for any same-week-scoped implementation.
3. `test_orphan_tools_row_no_matching_event_anywhere_is_flagged` — a `tools` row at `(run_id, seq)`
   with no matching `events` row in any week folder; assert it appears in `tools_violations` with the
   correct `run_id`/`seq`/`week_folder`.
4. `test_orphan_event_no_matching_run_anywhere_is_flagged` — an `events` row (ordinary `TCK-*`
   `run_id`) with no matching `runs` row in any week folder; assert it appears in `events_violations`.
5. `test_retrieval_event_run_id_excluded_from_check` — synthetic `events` row with `run_id =
   "RETRIEVAL-EVENT-some-slug"` and no matching `runs` row; assert **not** flagged and not counted in
   `events_checked`.
6. `test_null_run_id_tools_row_excluded_from_check` — synthetic `tools` row with `run_id: null`;
   assert not flagged and not counted in `tools_checked`.
7. `test_negative_and_zero_seq_tools_rows_excluded_from_check` — synthetic `tools` rows with `seq: -1`
   and `seq: 0`; assert neither is flagged nor counted in `tools_checked`.
8. `test_duplicate_event_key_does_not_break_lookup` — two distinct `events` rows sharing one
   `(run_id, seq)` key, plus one `tools` row at that same key; assert the `tools` row is **not**
   flagged (correctly matched despite the duplicate).
9. `test_unknown_week_folder_included_in_join` — a `runs` row under `<tmp>/data/unknown-week/
   runs.jsonl` and a matching `events` row under a real ISO-week folder (and vice versa in a second
   case); assert neither is flagged — `unknown-week` participates in the glob exactly like any
   `YYYY-Www` folder.
10. `test_report_output_matches_validate_py_style` — assert `report.to_text()` contains explicit
    violation counts (both checks) and, when violations exist, a bounded/capped sample list — not just
    a boolean.
11. `test_real_corpus_smoke_run` — call `compute_referential_integrity_report()` with no override
    (real `Path("agent-monitoring/data")` default) or an explicit path to the repo's real data
    directory; assert it runs to completion without exception and returns a well-formed
    `ReferentialIntegrityReport` (non-negative counts, list-typed violation fields). **Do not** assert
    `events_violations == []` or `tools_violations == []` — investigation.md documents ~17,274 real
    Check-2 orphans and 18 real Check-1 orphans existing in the corpus today; asserting zero would be
    false on its face per test_plan.md's Anti-Drift Test Guards.

Mark test 11 in a way consistent with this repo's existing real-corpus-smoke convention if one exists
in `tests/tools/` (check `test_migrate_monitoring_data.py`/`test_agent_monitoring_manifest.py` for a
`@pytest.mark.slow`-style precedent before inventing a new marker); otherwise leave unmarked — it does
not touch the network or take non-trivial time (glob + JSON parse over ~193K rows is well within
normal pytest run time).
**Do NOT touch:** `tests/tools/test_validate_agent_monitoring.py`,
`tests/tools/test_migrate_monitoring_data.py`, `tests/tools/test_agent_monitoring_manifest.py`,
`tests/tools/test_agent_monitoring_legacy_reader.py` — all remain unmodified per test_plan.md's
Regression Surface.
**Verify:** `pytest tests/tools/test_verify_referential_integrity.py -v` — all 11 pass. Then the
regression re-check: `pytest tests/tools/test_validate_agent_monitoring.py
tests/tools/test_migrate_monitoring_data.py tests/tools/test_agent_monitoring_manifest.py
tests/tools/test_agent_monitoring_legacy_reader.py -v` — all still pass, unmodified.

### Step 6 — Run against the real corpus; capture and triage findings
**Files:** `tickets/inprogress/TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY.md` (Implementation
Notes, Test Summary sections only)
**Change:** Run `python3 tools/agent-monitoring/verify_referential_integrity.py` (or the equivalent
`compute_referential_integrity_report()` call) against the real `agent-monitoring/data/` tree. Paste
the resulting `.to_text()` output (or a faithful summary of it) into the ticket's Test Summary
section. In Implementation Notes, explicitly triage the findings per the ticket's own Scope
requirement ("if it finds real violations, they must be reported and explicitly triaged... never
silently suppressed"):
- Cross-reference the actual output's counts against investigation.md's figures (~18 Check-1
  orphans, ~17,274/135,804 Check-2 orphans) — note any material difference (the finished tool's own
  run may find slightly different numbers than investigation's one-off scratchpad script if the
  corpus has grown between investigation and implementation).
- State explicitly: the bulk of Check-2 volume is accepted-as-known-legacy-noise, attributable to
  the already-documented, explicitly-not-backfilled `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-
  COLLISION` / `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` fixes.
- Flag `TCK-20260902-MONITORING-SHARD-MIGRATION`'s complete `events`/`runs.jsonl` absence (229 real
  tool rows, zero matching events/runs anywhere) as the one finding that is **not** explained by
  already-known historical corruption and may warrant its own follow-up investigation ticket — do not
  open that ticket as part of this one (Out of Scope: "Repairing any orphan this check finds"), just
  record the flag.
- Do not attempt to fix, backfill, or otherwise resolve any orphan found.
**Do NOT touch:** Any data file under `agent-monitoring/data/` — this step only reads and records
findings in the ticket, never writes to the monitoring corpus itself.
**Verify:** `test_real_corpus_smoke_run` (Step 5) already proves the tool runs cleanly; this step's
own verification is manual — the ticket's Test Summary/Implementation Notes sections are filled in
with real, non-fabricated numbers from an actual run.

### Step 7 — `docs/agent-monitoring/schema.md` Known Limitations entry
**Files:** `docs/agent-monitoring/schema.md`
**Change:** Add a new subsection to the existing "## Known Limitations" section (after the existing
"### Manual/ad hoc run_id convention" subsection, before "### Full evidence", matching that section's
existing pattern of one subsection per finding-class plus a trailing evidence pointer — confirmed
structure at schema.md lines 506-533), titled `### Referential Integrity Verification`. Content
template (fill in `<N1>`/`<N2>`/`<PCT>` with the real Step 6 numbers, do not leave placeholders in the
committed doc):
```
`tools/agent-monitoring/verify_referential_integrity.py` (TCK-20260903-MONITORING-DATA-REFERENTIAL-
INTEGRITY) automates the 2 FK relationships documented above (`events.run_id -> runs.run_id`;
`tools.(run_id, seq) -> events.(run_id, seq)`), reading the union of every `agent-monitoring/data/
<week>/` folder (never scoped to one week) so a legitimate cross-week-boundary run is never
false-flagged. It excludes the 3 documented exceptions: `RETRIEVAL-EVENT-<slug>` run_ids (no
matching runs.jsonl row by design), `tools.jsonl` rows with `run_id: null` (outside an active
workflow run), and `seq <= 0` shadow rows (context-packet-wrapper mechanism).

A real-corpus run on <DATE> found <N1> Check-1 orphans (events with no matching run) and <N2>/<TOTAL>
(<PCT>%) Check-2 orphans (tool-call rows with no matching event). The large majority of Check-2 volume
is attributed to already-documented, explicitly-not-backfilled historical corruption
(TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION, TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE). One
notable exception is not explained by either fix: TCK-20260902-MONITORING-SHARD-MIGRATION has zero
events.jsonl/runs.jsonl rows anywhere despite real, dated tools.jsonl activity — flagged for possible
follow-up investigation, not resolved here. As with the other Known Limitations above, no orphan is
backfilled or repaired retroactively (append-only precedent) — this tool verifies and reports only.

Full evidence: `stored_artifacts/TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY/investigation.md`.
```
Also run `make knowledge-index-update` after this edit lands, per this repo's After Work rule ("If
any files under `docs/` were created or modified: run `make knowledge-index-update`").
**Do NOT touch:** Any other section of `schema.md` (the FK-contract prose at lines 141/172/370/
407-408, the Join Example at lines 470-502, the other 2 existing Known Limitations subsections) —
this step only appends one new subsection in the established slot.
**Verify:** Manual review — the new subsection reads correctly in context, cites real (not
placeholder) numbers matching Step 6's Test Summary, and `make knowledge-index-update` completes
without error.

## Scope Guards

- Do not build a general-purpose/SQL-style referential-integrity engine — exactly these 2 FK checks,
  nothing else (ticket's Out of Scope, epic's own boundary).
- Do not wire this tool into `done_checker_static.py` as a new blocking DoD gate, or into any CI
  workflow, in this ticket. No `--strict` flag, no `sys.exit(1)` on violation volume.
- Do not repair, backfill, or otherwise fix any orphan/violation this tool finds — report and triage
  only (Steps 6-7 record findings; they never mutate `agent-monitoring/data/`).
- Do not change any of the 3 per-line record schemas (`runs.jsonl`/`events.jsonl`/`tools.jsonl` field
  shapes) — this ticket is a new reader, not a schema change.
- Do not touch `validate.py`, `build_index.py`, `manifest.py`, `legacy_reader.py`,
  `migrate_monitoring_data.py`, `record_events.py`, `record_run.py`, `writer.py`,
  `tools/agent_replay_codex/` — all either read-only precedent or another child ticket's active,
  concurrent scope (children 3/4/5 of the same epic).
- Do not depend on `agent-monitoring-index/monitoring.db` or `build_index.py` anywhere in the new
  script — confirmed stale against the current layout.
- Do not filter `unknown-week` out of the glob, and do not resolve a `run_id`'s "home week" before
  searching for its matching rows anywhere in the implementation, including as a fast-path
  optimization with a fallback.
- Do not touch `docs/parity_ledger/*.yaml` or `docs/mechanics/*.md` — investigation and this ticket's
  own predecessor (`TCK-20260705-MONITORING-RUNID-JOIN`) both independently concluded
  `agent-monitoring/` tooling is infrastructure, not a tracked simulation subsystem.
- Do not add a new tag to `registries/tag_registry.jsonl` or a new layer to
  `registries/layer_registry.jsonl` — this ticket reuses the parent ticket's existing, already-valid
  `layer: observability` and `tags: [agent-monitoring, observability, data-quality, schema]`.

## Dependency Map

- Step 1 (loader) is a prerequisite for Steps 2, 3, and 4 — both check functions and the report
  assembly call it.
- Steps 2 and 3 are independent of each other (separate functions, separate FK relationships) and can
  be implemented/tested in either order, but both must land before Step 4 (report assembly calls
  both).
- Step 4 depends on Steps 1-3.
- Step 5 (test suite) depends on Steps 1-4 being complete (tests import and call the finished module's
  public functions).
- Step 6 (real-corpus run) depends on Step 5 passing (the tool must be verified correct on synthetic
  fixtures before its real-corpus output is trusted enough to write into the ticket record).
- Step 7 (docs) depends on Step 6 (the doc entry cites Step 6's real numbers — writing it first would
  require placeholder numbers, explicitly disallowed above).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| All 5 Scope test scenarios (a-e) pass, each a testable assertion | Steps 2, 3, 4 | `test_same_week_only_join_baseline`, `test_orphan_tools_row_no_matching_event_anywhere_is_flagged`, `test_orphan_event_no_matching_run_anywhere_is_flagged`, `test_retrieval_event_run_id_excluded_from_check`, `test_null_run_id_tools_row_excluded_from_check`, `test_negative_and_zero_seq_tools_rows_excluded_from_check` |
| Explicit cross-week-join test passes | Steps 1, 2 | `test_cross_week_run_id_not_flagged` |
| Tool runs successfully against the real post-migration corpus; output captured in Test Summary | Steps 4, 5, 6 | `test_real_corpus_smoke_run` + manual Step 6 record |
| Report format documented well enough for a future consumer to parse | Step 4 | `test_report_output_matches_validate_py_style` |

## Anti-Drift Notes

- **The cross-week test is the highest-priority correctness guard in this plan.** A same-week-scoped
  implementation (resolving a `run_id`'s week from its `runs.jsonl` row, then only scanning that one
  folder's `events`/`tools`) would pass every other test trivially and only `test_cross_week_run_id_
  not_flagged` would catch it. Steps 1-3 are written explicitly to build `valid_run_ids`/`valid_keys`
  from the full all-weeks list, never a per-folder subset — do not "optimize" this into a per-week
  lookup with a fallback scan during implementation.
- **`unknown-week` is a real, currently-populated folder, not a special case to filter out.** The
  loader (Step 1) must not apply any ISO-week-shaped regex filter to directory names.
- **The 145 real duplicate-`(run_id, seq)`-event-key rows are a measured, not hypothetical, real-corpus
  finding** (investigation.md) — Step 3's `valid_keys` must be built as a `set` populated by iterating
  every row, never a `dict` comprehension that silently drops a colliding key depending on file/glob
  ordering.
- **Do not assert the real corpus is clean in `test_real_corpus_smoke_run`.** ~17,274 real Check-2
  orphans and 18 real Check-1 orphans exist today; the smoke test proves the tool runs and reports
  correctly, not that the data is pristine.
- **Root-causing why `TCK-20260902-MONITORING-SHARD-MIGRATION`'s events/runs rows are completely
  missing is out of scope for this ticket.** Step 6 flags it in Implementation Notes; it is not
  investigated further here, and no fix/backfill is attempted.
- **The 26.2%-of-corpus `run_id: null` `tools.jsonl` population must never inflate `tools_checked`.**
  Step 3's skip-before-increment ordering (check exclusions first, only then increment `checked`) is
  load-bearing for `test_null_run_id_tools_row_excluded_from_check` and for any future consumer that
  computes a violation rate from `tools_violations / tools_checked`.
- **This tool never gates.** No exit-code-on-violation behavior is added in this ticket (Decision on
  item 4) — resist the temptation to add a `--strict` flag "while we're in here"; that is a separate,
  deliberate future decision per the ticket's own Out of Scope.
