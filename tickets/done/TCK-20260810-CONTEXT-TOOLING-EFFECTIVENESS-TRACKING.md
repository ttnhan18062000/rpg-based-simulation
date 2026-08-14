---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING
phase: done
date: 2026-08-10
tags: [agent-monitoring, observability, process-improvement]
---

# TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING

## Title
Track, on a recurring cadence, whether context-search (`search_docs`/`graphify`) and parity-index
sqlite queries actually reduce raw investigation effort

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
User asked to track whether context-search tooling and parity sqlite queries "improve the
working" (e.g. reduce grep/raw-investigation calls). `TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC`
already answered the measurement-design question: this environment records no distinct `Grep` tool
name (grep-equivalent work runs through the catch-all `Bash` tool, which
`retrieval_baseline_metrics.py`'s existing `SEARCH_TOOL_NAMES` design deliberately excludes from
search-tool counting as non-distinguishable). It built `raw_investigation_count` (`Read`-call count,
the precise proxy) and a corpus-wide `read_to_search_ratio` in
`tools/agent-monitoring/retrieval_baseline_metrics.py` — real numbers, last observed
`raw_investigation_count.total = 18594`, `search_count.total = 1924`, `read_to_search_ratio = 9.66`.
That ticket explicitly scoped OUT wiring the metric into the recurring weekly retro
(`generate_retro.py`), calling it "a separate, recurring-cadence tool" — so today it only exists as
a manual one-off run, with no trend visibility and no correlation to actual compliance behavior.

Separately, `tools/parity_index.py`'s `entry`/`impact`/`health` sqlite read path (reviewed GO in
`docs/ai/parity_readpath_gate_a_decision.md`) has **zero real call sites** anywhere — nothing
tracks its usage because nothing calls it yet.

## Scope
- **Investigate (mandatory before Plan):** read `retrieval_baseline_metrics.py`'s current section
  structure (`build_search_count_section`, `build_raw_investigation_count_section`) and
  `generate_retro.py`'s existing report-assembly pattern (`compute_tool_safety_metrics`'s
  `search_before_grep` section is the closest existing precedent: per-`(run_id, seq)` compliance
  keyed off real `events.jsonl` phase data) before designing anything new.
- Wire `raw_investigation_count`/`search_count`/`read_to_search_ratio` (or an equivalent computed
  directly in `generate_retro.py`, reusing rather than duplicating `retrieval_baseline_metrics.py`'s
  logic) into the recurring report, trended report-over-report (comparable across `RETRO-<week>.md`
  runs, the way `Gate Failure Breakdown`/`Agent Status Distribution` already are).
- Add a genuine correlation section: for each Investigate-phase `(run_id, seq)` pair already
  computed by `compute_tool_safety_metrics`'s `per_pair_compliance`, compute that pair's own
  `Read`-call count, then report compliant-pair vs. non-compliant-pair `Read`-count
  median/average — real evidence for or against "does search-before-grep compliance actually
  reduce raw investigation effort," not an assumed causal story.
- Add a `parity_index.py` read-path call-count section (`entry`/`impact`/`health` invocations),
  following the exact same "never a silent/fabricated number" convention as the existing sections
  — today this must explicitly report 0 real call sites with a derivation string stating why
  (nothing wired in yet), not omit the section or fake a value. Design it so it activates
  automatically once `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` or any future ticket adds a
  real call site — do not hardcode a "not implemented" bypass that would need a second ticket to
  remove.
- Update `docs/agent-monitoring/README.md` and/or `docs/agent-monitoring/schema.md` describing the
  new section(s).

## Out of Scope
- Any change to `retrieval_baseline_metrics.py`'s existing `SEARCH_TOOL_NAMES` design or
  Bash-exclusion rationale — reused, not revisited.
- Wiring `parity_index.py`'s read path into any actual workflow call site — that is
  `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`'s adjacent-but-separate concern (write safety) or
  a future, separately-scoped Phase-3 ticket (read-path wiring) per Gate A's own boundary; this
  ticket only tracks call counts once/if such a site exists.
- Backfilling a correlation number for historical weeks predating this ticket's own code landing —
  the correlation section reports from real data going forward, not a fabricated retroactive claim.

## Acceptance Criteria
- [x] A real `generate_retro.py` run against the current corpus produces the new trended
      search/read-investigation section with real, non-fabricated numbers.
- [x] The compliant-vs-non-compliant `Read`-count correlation section produces a real number from
      real `(run_id, seq)` pairs already in the corpus (the 65 Investigate pairs / 27 non-compliant
      ones identified during this ticket's originating audit are available as a real first data
      point).
- [x] The `parity_index.py` call-count section exists, explicitly reports 0/N call sites today with
      a derivation string explaining why, and requires no further code change to start reporting
      real numbers once a call site exists.
- [x] Every new section has a `"derivation"` (or equivalent) string, matching the existing
      never-silent convention used by `search_count`/`raw_investigation_count`.
- [x] New tests mirror the existing `test_retrieval_baseline_metrics.py`/`generate_retro.py` test
      patterns (never-silent, derivation-matches-fields, real-corpus zero-diff where applicable).
- [x] `docs/agent-monitoring/README.md`/`schema.md` updated.

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC (DONE; predecessor metric, this ticket wires it
  into the recurring cadence that ticket explicitly deferred)
- TCK-20260804-EXPANSION-RATE-WIRING (DONE; sibling wiring precedent, same user request thread)
- TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP (sibling; this ticket's correlation section is
  how that fix's real-world effect becomes visible)
- TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL (sibling; potential future source of real
  `parity_index.py` call sites this ticket's section is built to pick up automatically)
- TCK-20260731-PARITY-READPATH-GATE (DONE; source of the `entry`/`impact`/`health` read path)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (backlog; broader retrieval epic, not a duplicate)

## Related Docs
- `docs/agent-monitoring/README.md`
- `docs/agent-monitoring/schema.md`
- `docs/ai/parity_readpath_gate_a_decision.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC/`

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py`
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `tools/parity_index.py`
- `tests/tools/test_generate_retro.py`
- `tests/tools/test_retrieval_baseline_metrics.py`

## Assumptions / Open Questions
- Whether the correlation section belongs in `generate_retro.py` directly (reusing
  `compute_tool_safety_metrics`'s already-computed `per_pair_compliance`) or as a new function in
  `retrieval_baseline_metrics.py` that `generate_retro.py` then calls — not decided here; Investigate
  should follow whichever file already owns the relevant per-pair data without duplicating a second
  loader, matching this codebase's existing anti-duplication test precedent (e.g.
  `test_baseline_report_tool_reuses_load_data_pattern_not_a_fourth_loader`).

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING/plan.md`'s
8 steps, no deviations from the plan's substance (one clarified rendering detail noted below):

1. Relocated `SEARCH_TOOL_NAMES`, `build_search_count_section(tools)`, and
   `build_raw_investigation_count_section(tools)` verbatim from `retrieval_baseline_metrics.py`
   into `generate_retro.py` (placed beside the other `_is_*`/predicate helpers, after
   `_is_unsafe_parity_build_call`). `retrieval_baseline_metrics.py` now re-imports all three names
   from its existing `from generate_retro import (...)` statement — zero new import edges, no
   cycle. Module docstring updated to list the three relocated names.
2. Added `compute_search_investigation_trend(tools)` (thin wrapper calling the two relocated
   functions by name, no independent filtering loop) and wired a new
   `## Search & Investigation Effort` section into `generate()`, placed after `## Shadow vs.
   Baseline Retrieval Comparison` and before `## Tool Safety Audit`, gated on
   `search_count.total + raw_investigation_count.total > 0` (omitted, not rendered empty, on the
   frozen fixture — confirmed unaffected).
3. Extended `_update_index(all_runs, all_tools=None)` — additive optional parameter. Added a
   `Search Calls` / `Read Calls` column pair to `index.md`, computed per week by filtering
   `all_tools` to that week's `run_id` set (mirroring `main()`'s existing per-period filter
   pattern) and calling the same two relocated section functions — no new counting logic.
   `main()`'s call site updated to `_update_index(all_runs, all_tools)`. Replaced
   `test_update_index_call_sites_migrated_or_explicitly_documented_as_out_of_scope` with
   `test_update_index_signature_change_is_deliberate_and_documented`, which re-asserts the
   no-direct-jsonl-read guarantee and pins the new two-parameter signature explicitly.
4. Added `read_count_correlation` as a new top-level key on `compute_tool_safety_metrics`'s return
   dict (sibling to `search_before_grep`/`parity_write_safety`, per the plan's literal spec — not
   nested inside `search_before_grep`), computed by reusing `pair_tool_rows`/`per_pair_compliance`
   (already built earlier in the same function) — no second scan of `tools`. Empty groups report
   `None` for median/average, never a fabricated `0` or a `statistics.median([])` crash. Rendered
   as a third subsection, `### Read-Count Correlation (Search-Before-Grep Compliance)`, appended
   after `### Parity Ledger Write-Safety`, inside the same `if sbg["investigate_pair_count"]:`
   gate — no new gate.
5. Added `_PARITY_INDEX_READPATH_RE` (path-anchored: `(?:^|/)parity_index\.py\s+
   (entry|impact|health)\b`), `_is_parity_index_readpath_call(tool_row)`, and
   `compute_parity_index_readpath_call_count(tools)` (returns `count`, `bash_rows_scanned`,
   `examples`, `derivation`). Verified against all four real corpus-observed false-positive shapes
   (`--help`, `git log --`, `pytest -k`, `sed`) and three synthetic true-positive shapes
   (`entry`/`impact`/`health`) directly via a smoke script before writing the pytest tests. Wired a
   new `## Parity Index Read-Path Usage` section into `generate()`, placed after `## Tool Safety
   Audit` and before `## Notes` — deliberately **always rendered** (not gated), per the plan's
   explicit exception to the conditional-render convention, since "0 today" is itself the
   reportable finding. This required updating the frozen `_FIXED_CORPUS_EXPECTED_REPORT` literal in
   `test_generate_retro.py` to include the new always-on section's exact text (both frozen-output
   tests that assert against it were otherwise correctly unaffected by the `> 0`-gated Step 2
   section, which the fixture's zero-tools call correctly omits) — a necessary, disclosed
   consequence of Step 5's own explicit "always render" design choice, not a silent test-editing
   workaround.
6. Updated `docs/agent-monitoring/README.md` (new dated note under "Baseline Metrics Snapshot"
   distinguishing shared numbers from the still-distinct cadences), `docs/agent-monitoring/
   schema.md` (new "Detecting a specific script's subcommand in `Bash` rows" subsection under
   `tools.jsonl` describing the path-anchored-regex convention), and `docs/guides/
   agent_monitoring.md`'s Report Sections table (extended the existing Tool Safety Audit row with
   the Read-Count Correlation subsection's meaning, plus two new rows for Search & Investigation
   Effort and Parity Index Read-Path Usage).
7. Amended `INFRA-292` and `INFRA-315` in `docs/parity_ledger/infrastructure.yaml` in place via
   `tools/parity_ledger_writer.py::write_entry()` (the sibling ticket's newly-landed required write
   path) — appended a dated addendum clause to each entry's `v2_evidence`, `status`/`priority`
   unchanged, no renumbering. Followed with the separate, visible
   `python3 tools/parity_index.py build` Bash call per that tool's own documented usage
   instructions (the in-process `build()` call inside `write_entry()` is invisible to
   `_is_parity_index_build_call`'s literal-Bash-command detector). **Noted side effect, verified
   safe:** `write_entry()`'s `yaml.safe_dump(entries, sort_keys=False)` re-serializes the entire
   2014-entry ledger file on every call, producing a large line-level diff from PyYAML's default
   dumper choosing different block-scalar/quoting/unicode-escaping style than the file's original
   authoring style. Verified via a direct before/after YAML-parse comparison
   (`yaml.safe_load` on `git show HEAD:...` vs. the working file) that the *only* two entries with
   changed semantic content are `INFRA-292` and `INFRA-315`; every other entry (including
   `INFRA-331`, pre-existing/uncommitted from the sibling `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-
   TOOL` ticket that ran earlier in this session) is byte-for-byte identical in parsed content, only
   its YAML surface syntax differs. This is an inherent characteristic of the now-mandated write
   path, not something introduced by this ticket's logic — flagged here since it wasn't anticipated
   in plan.md's Step 7 and produces a much larger `git diff` than the two-entry semantic change.
8. Added 17 new tests to `tests/tools/test_generate_retro.py` covering Steps 2-5 plus the two
   AC4/AC5 cross-cutting derivation/no-file-IO guards (table-driven and AST-based respectively).
   Full scoped regression run clean: `test_generate_retro.py` + `test_retrieval_baseline_metrics.py`
   (137/137), `test_parity_index.py` + `test_parity_ledger_writer.py` (47/47), plus
   `test_parity_ledger_schema.py`/`test_parity_ledger_scan.py` (52/52 combined with the above two).
   `test_gate_a_readpath_review.py` has 3 failed/7 errored tests from missing
   `gate_a_corpus.json`/`gate_a_results.json` fixture files — confirmed pre-existing and unrelated
   (documented by the sibling `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` ticket's own
   Implementation Notes, not touched by this ticket's diff). Real `--all` corpus run of
   `generate_retro.py` completed cleanly (1030 runs, 6172 events, 106585 tools rows), producing all
   three new sections with real numbers: Search Calls 2327, Read Calls 22567 total corpus-wide;
   Read-Count Correlation compliant-group median 12.0 (n=138) vs. non-compliant-group median 9.0
   (n=79); Parity Index Read-Path Usage 0/62053 Bash rows scanned. `agent-monitoring/retro/
   RETRO-ALL.md` and `index.md` are left as the durable, committed tooling output per CLAUDE.md
   (not `data/runs/`/`reports/release_proof/`-class throwaway data).

## Test Summary
137/137 pass in `tests/tools/test_generate_retro.py` (119, +17 new) and
`tests/tools/test_retrieval_baseline_metrics.py` (25, all pre-existing, unchanged). 47/47 pass in
`tests/tools/test_parity_index.py` + `tests/tools/test_parity_ledger_writer.py` (confirms no
accidental edit to the untouched-by-this-ticket `parity_index.py` and no cross-contamination of the
sibling ticket's write path). Real `--all` corpus run of `generate_retro.py` completed with no
crash, producing all three new sections/columns with real, non-fabricated numbers (see
Implementation Notes Step 8 for the exact figures). Scoped commands run:
```
.venv/bin/python3 -m pytest tests/tools/test_generate_retro.py tests/tools/test_retrieval_baseline_metrics.py -v
.venv/bin/python3 -m pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_writer.py -v
.venv/bin/python3 tools/agent-monitoring/generate_retro.py --all
```

## Files Changed
- `tools/agent-monitoring/generate_retro.py` (relocated `SEARCH_TOOL_NAMES`/
  `build_search_count_section`/`build_raw_investigation_count_section`; added `import re`,
  `_PARITY_INDEX_READPATH_RE`, `_is_parity_index_readpath_call`,
  `compute_parity_index_readpath_call_count`, `compute_search_investigation_trend`; extended
  `compute_tool_safety_metrics` with `read_count_correlation`; extended `generate()` with three
  new/extended sections; extended `_update_index` signature + `index.md` columns; updated `main()`
  call site)
- `tools/agent-monitoring/retrieval_baseline_metrics.py` (removed the two relocated function
  bodies; extended the `from generate_retro import (...)` statement; updated module docstring)
- `tests/tools/test_generate_retro.py` (updated imports; replaced the `_update_index`
  signature-pin test; updated `_FIXED_CORPUS_EXPECTED_REPORT` for the new always-on section; added
  17 new tests)
- `docs/agent-monitoring/README.md`
- `docs/agent-monitoring/schema.md`
- `docs/guides/agent_monitoring.md`
- `docs/parity_ledger/infrastructure.yaml` (INFRA-292/INFRA-315 `v2_evidence` amended in place via
  `tools/parity_ledger_writer.py::write_entry()`; full-file YAML re-serialization is a side effect
  of that tool, verified semantically no-op for all other entries — see Implementation Notes Step 7)
- `agent-monitoring/retro/RETRO-ALL.md`, `agent-monitoring/retro/index.md` (regenerated durable
  tooling output from the real `--all` corpus run)

(`agent-monitoring-index/monitoring.db` was also rebuilt by `write_entry()`'s in-process
`parity_index.build()` call and the explicit `python3 tools/parity_index.py build` call, but that
path is gitignored — not a tracked file, listed here for completeness only, not as a repo change.)

## Completion Summary
Wired three new, evidence-backed sections into `generate_retro.py`'s recurring weekly retro report
and index: a trended `## Search & Investigation Effort` section (reusing, not duplicating,
`retrieval_baseline_metrics.py`'s search/raw-investigation logic, relocated into `generate_retro.py`
to resolve a real circular-import constraint) with new `Search Calls`/`Read Calls` trend columns on
`agent-monitoring/retro/index.md`; a `### Read-Count Correlation` subsection inside `## Tool Safety
Audit` reporting real compliant-vs-non-compliant median/average `Read`-call counts per
Investigate-phase pair; and an always-rendered `## Parity Index Read-Path Usage` section honestly
reporting 0 real `entry`/`impact`/`health` call sites today via a path-anchored regex detector
designed to auto-activate once a real call site lands. All sections carry a `derivation` string and
were verified against the real corpus (`--all` run, 1030 runs / 6172 events / 106585 tools rows,
zero crashes, real non-fabricated numbers). `docs/agent-monitoring/README.md`, `schema.md`, and
`docs/guides/agent_monitoring.md`'s Report Sections table were updated, and `INFRA-292`/`INFRA-315`
were amended in place via the newly-landed `parity_ledger_writer.py` write path.
