---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC
artifact_type: test_plan
tags: [agent-monitoring, observability]
---

# Test Plan — TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC

## Regression Surface

All existing tests in `tests/tools/test_retrieval_baseline_metrics.py` must keep passing, with one
explicit modification required (see below).

**Unit (per-section, inline-dict, no file I/O):**
- `test_baseline_report_context_tokens_marked_unavailable`
- `test_baseline_report_search_count_is_marked_or_derived_never_silent`
- `test_baseline_report_search_count_derivation_matches_stated_fields`
- `test_baseline_report_flags_duration_as_pause_contaminated_when_no_gap_aware_view_exists`
- `test_baseline_report_would_prefer_gap_aware_view_if_available`
- `test_baseline_report_gate_outcome_uses_final_status_and_reason_code_only`
- `test_baseline_report_review_rework_proxy_requires_multi_record_same_run_id`
- `test_baseline_report_review_rework_proxy_ignores_reason_code_alone`

**Reuse-not-reimplement AST guards (must stay green — the new function must not violate them):**
- `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader` — walks the module AST for
  banned `.read_text()`/`.read_bytes()`/`.readlines()` calls and a banned `sqlite3` import. The new
  section function must take `tools: list` as a parameter exactly like `build_search_count_section`
  does — it must never open `agent-monitoring/tools.jsonl` itself.
- `test_baseline_report_reuses_classify_provenance_not_reimplemented`
- `test_baseline_report_tool_never_imports_writer_module` — also asserts no `open(path, "w"/"a")`
  call anywhere in the module; the new function must not add one.

**Integration (real corpus, zero-mutation, must remain a *real* `agent-monitoring/` check — never a
`tmp_path` copy, per this test file's own docstring rationale):**
- `test_baseline_report_tool_causes_zero_diff_on_real_corpus` — `git status --porcelain --
  agent-monitoring/` pre/post snapshot around `load_all_sources()` + `build_baseline_report(...)`.
  The new section reads `tools` (already loaded, already in memory) and must not add any write path.
- `test_baseline_report_cli_runs_against_real_corpus_and_prints_json` — **must be edited as part of
  this ticket's implementation**, not left as-is. It currently asserts the exact key set:
  ```python
  assert set(report.keys()) == {
      "ticket_id", "generated_note", "context_tokens", "search_count", "duration",
      "gate_outcome", "review_rework", "legacy_schema_notes",
  }
  ```
  Wiring the new section into `build_baseline_report()` will make this line fail unless the new
  key (e.g. `"raw_investigation_count"`) is added to this literal set. This is flagged here as a
  required **modification of an existing test**, not scope creep — it is the direct, mechanical
  consequence of AC1 ("wired into the assembled report output"), and leaving it unedited would be a
  silent regression of this test's own precision (exactly the kind of thing this repo's tests are
  built to catch).

## New Tests Required

All new tests live in `tests/tools/test_retrieval_baseline_metrics.py`, alongside the existing
`# --- AC2 — follow-up-search-count ... ---` section, in a new comment-delimited block (mirroring
the file's existing `# --- ACn — ... ---` banner convention, e.g. a new
`# --- AC-NEW — raw-investigation (Read) count, derived proxy for grep-equivalent effort ---`
banner) immediately after the AC2 block.

1. **`test_baseline_report_raw_investigation_count_is_marked_or_derived_never_silent`**
   - Category: unit
   - Verifies: mirrors `test_baseline_report_search_count_is_marked_or_derived_never_silent` exactly
     — calling `build_raw_investigation_count_section([])` returns a dict where `section["total"]`
     is an `int` (`0` for empty input, never `None`/absent), and `section["derivation"]` is a
     non-empty string containing the literal substrings `"tool"` and `"Read"` (mirroring the
     original's `assert "tool" in section["derivation"]` / `assert "SEARCH_TOOL_NAMES" in
     section["derivation"]` pattern, adapted to this section's own filter literal). Additionally
     asserts the derivation string contains `"Grep"` or `"Bash"` (whichever literal word the
     implementation uses) to confirm the non-distinguishability rationale is actually present, not
     just alluded to — this is the AC2-equivalent requirement from the ticket ("The section's
     `derivation` field explicitly explains the Read-as-proxy choice and the Grep/Bash
     non-distinguishability reason").
   - Location: `tests/tools/test_retrieval_baseline_metrics.py`

2. **`test_baseline_report_raw_investigation_count_derivation_matches_stated_fields`**
   - Category: unit
   - Verifies: mirrors `test_baseline_report_search_count_derivation_matches_stated_fields` exactly
     — a fixed inline list of `tools` records covering: multiple `Read` records under the same
     `run_id` (must sum correctly in `per_run`), a `Read` record with `run_id: None` (must land under
     the literal `"unattributed"` key, not `None` — reusing the exact same null-key-avoidance
     convention `build_search_count_section` already established), and non-`Read` records (`Bash`,
     `Edit`, `Write`, `mcp__knowledge-search__search_docs`) that must **not** be counted. Asserts
     `section["total"]` and `section["per_run"]` match hand-computed expected values exactly (no
     off-by-one, no double-counting). Example fixture, structurally mirroring the existing
     `search_count`-derivation test's fixture:
     ```python
     tools = [
         {"run_id": "TCK-A", "tool": "Read"},
         {"run_id": "TCK-A", "tool": "Read"},
         {"run_id": "TCK-A", "tool": "Bash"},
         {"run_id": "TCK-B", "tool": "Read"},
         {"run_id": "TCK-B", "tool": "Edit"},
         {"run_id": None, "tool": "Read"},
         {"run_id": "TCK-B", "tool": "mcp__knowledge-search__search_docs"},
     ]
     section = build_raw_investigation_count_section(tools)
     assert section["total"] == 4
     assert section["per_run"] == {"TCK-A": 2, "TCK-B": 1, "unattributed": 1}
     ```
   - Location: `tests/tools/test_retrieval_baseline_metrics.py`

3. **`test_baseline_report_raw_investigation_count_wired_into_report`**
   - Category: integration (inline-dict, no file I/O — mirrors the AC1 `context_tokens` wiring style
     rather than requiring the real corpus)
   - Verifies: `build_baseline_report(runs, events, tools)` includes the new key (e.g.
     `"raw_investigation_count"`) in its returned dict, and that value equals
     `build_raw_investigation_count_section(tools)` called directly on the same `tools` input — i.e.
     the report assembly actually calls the new function rather than silently omitting it or
     computing something different inline. This directly targets AC1 ("wired into the assembled
     report output"), which none of the other new tests independently confirm (they test the section
     function in isolation, not its presence in the assembled report).
   - Location: `tests/tools/test_retrieval_baseline_metrics.py`

4. **`test_baseline_report_raw_investigation_count_ratio_never_silent_if_present`**
   - Category: unit
   - Verifies: whichever design the Plan phase settles on for the optional
     `read_to_search_ratio` field (per investigation.md's Risk #2 — corpus-wide only, per-run with an
     explicit skip-on-zero-search marker, or omitted entirely with a stated reason) must not silently
     produce `ZeroDivisionError`, `None`-as-a-hidden-zero, or a `KeyError` for a `run_id` present in
     one section's `per_run` but absent from the other's. If the field is present, this test asserts
     it is either a finite computed number or an explicit marker string per run/corpus (never a raw
     Python exception, never a bare `0`/`null` standing in for "not computed"). If the field is
     absent by design, this test instead asserts the section's `derivation` string states the reason
     for omission (mirroring `build_context_tokens_section`'s "reason"/"citation" precedent). This
     test's exact shape is intentionally contingent on the Plan-phase decision flagged in
     investigation.md — write it against whatever shape plan.md actually specifies, not a guessed
     shape.
   - Location: `tests/tools/test_retrieval_baseline_metrics.py`

5. **`test_baseline_report_raw_investigation_count_plausible_on_real_corpus`**
   - Category: integration (real corpus, zero-mutation-safe read — companion to, but not a
     duplicate of, `test_baseline_report_tool_causes_zero_diff_on_real_corpus`)
   - Verifies: directly targets the ticket's AC4 ("Running the script against real
     `agent-monitoring/tools.jsonl` produces a non-trivial, plausible Read count, order of magnitude
     consistent with the ~18,567 total observed during investigation"). Calls `load_all_sources()`
     then `build_raw_investigation_count_section(tools)` (or reads the value back out of
     `build_baseline_report(...)`) against the real corpus and asserts:
     - `section["total"]` is an `int` greater than some conservative floor (e.g. `> 1000`, well below
       the ~18,567 figure to tolerate corpus growth/shrinkage between investigation time and test-run
       time — per investigation.md's own Risk #5 precedent from the original baseline ticket:
       "any specific counts cited... should be treated as illustrative, re-measured at implementation
       time, not hardcoded").
     - `section["total"] >= sum(section["per_run"].values())` is exactly equal (internal consistency
       — no double-counting/undercounting between the aggregate and the breakdown), matching the
       same style of self-consistency the `search_count` real-corpus citations in
       `docs/ai/default_packet_scenarios_decision.md` implicitly rely on.
     - Does not assert git-porcelain zero-diff itself (that is already covered by the existing
       `test_baseline_report_tool_causes_zero_diff_on_real_corpus`, which will exercise the new
       section too once it's wired into `build_baseline_report`) — avoids duplicating that test's
       responsibility.
   - Location: `tests/tools/test_retrieval_baseline_metrics.py`

## Scoped Pytest Commands

```bash
# Primary scoped regression run for this ticket's affected module:
pytest tests/tools/test_retrieval_baseline_metrics.py -v

# Sibling agent-monitoring tooling tests, to catch any accidental cross-module import/behavior
# regression in generate_retro.py/legacy_reader.py/manifest.py (read-only reuse — must stay
# unmodified, per Anti-Drift Hazards):
pytest tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_agent_monitoring_manifest.py -v

# If retrieval_events.py / generate_retro.py's own test suite exists and is touched indirectly
# (only if the Plan phase's ratio-field decision ends up importing anything new from those
# modules — not expected, but scoped here defensively):
pytest tests/tools/ -k "monitoring or retrieval or retro" -v
```

Never `pytest tests/` (repo-wide) — this ticket's change is confined to one script and one test
file; scope stays at `tests/tools/`.

## Anti-Drift Test Guards

- **`test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`** (existing, unmodified) —
  continues to guard against the new function adding a second/fourth data-loading path; failing this
  test would mean the new section bypassed the already-loaded `tools` parameter.
- **`test_baseline_report_tool_never_imports_writer_module`** (existing, unmodified) — continues to
  guard against any accidental write-path addition; a Read-count feature has zero legitimate reason
  to ever open a file for writing, so this test failing would indicate real scope creep.
- **`test_baseline_report_search_count_derivation_matches_stated_fields`** (existing, unmodified) —
  its literal assertion `SEARCH_TOOL_NAMES == {"mcp__knowledge-search__search_docs", "ToolSearch",
  "WebSearch"}` is the direct guard against this ticket accidentally touching `SEARCH_TOOL_NAMES`
  (explicitly Out of Scope) while adding the new Read-based section — if this ticket's diff ever
  causes this assertion to fail, that is a scope violation, not an acceptable side effect.
  New test #2 above (`..._derivation_matches_stated_fields` for the Read section) is the direct
  structural sibling guarding the new filter (`tool == "Read"` only, no widening to
  `Edit`/`Write`/other tools) the same way.
- **New test #3 above (`..._wired_into_report`)** is itself an anti-drift guard against a subtle
  failure mode: a correct, well-tested `build_raw_investigation_count_section()` that is never
  actually called from `build_baseline_report()` — i.e. AC2/AC3 (section logic + tests) satisfied
  while AC1 (wiring) silently is not. Without this test, unit tests #1/#2 could all pass while the
  real report output never includes the new section.
- **Existing `test_baseline_report_cli_runs_against_real_corpus_and_prints_json`, once edited** to
  include the new key in its exact-set assertion, becomes itself an anti-drift guard against a
  *fifth* future section being added without updating this same set — the test's existing "exact set,
  not subset" design (`==`, not `<=`) is deliberate and should be preserved, not loosened to a
  subset check, when this ticket edits it.
