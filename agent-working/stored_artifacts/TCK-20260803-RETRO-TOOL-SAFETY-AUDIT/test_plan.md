---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-RETRO-TOOL-SAFETY-AUDIT
artifact_type: test_plan
tags: [agent-monitoring, retro]
---

# Test Plan — TCK-20260803-RETRO-TOOL-SAFETY-AUDIT

## Regression Surface

Existing tests that must keep passing (all unit-level; there is no arena-combat or integration
surface for this ticket — it is agent-orchestration tooling, not simulation code):

- unit:
  - `tests/tools/test_generate_retro.py` — full file (98 existing tests as of this investigation,
    including `TestComputeRetrievalMetrics`, the shadow-baseline-comparison tests, the
    phase/agent-case-fold tests, and `test_function_is_read_only_no_write_call_or_file_open_in_
    write_mode`-style guards). Any new `generate(...)` signature change (adding a `tools`
    parameter) must not break existing call sites in this file that invoke `generate(runs, events,
    label)` without a `tools` argument.
  - `tests/tools/test_retrieval_baseline_metrics.py` (if present) — confirms
    `retrieval_baseline_metrics.py`'s existing `load_all_sources()`/`DEFAULT_TOOLS_FILE` imports
    from `generate_retro.py` are untouched by this ticket's changes (this ticket must not rename or
    change the signature of anything `retrieval_baseline_metrics.py` imports:
    `_load_runs_and_events`, `load_jsonl`, `DEFAULT_TOOLS_FILE`, `_resolve_status`, `_is_gate_fail`).
  - `tests/tools/test_build_index.py` — confirms `build_index.py`'s import of
    `generate_retro._resolve_status` still resolves; this ticket must not touch `_resolve_status`.
  - `tests/tools/test_agent_ops_dashboard_stats.py` — confirms `compute_retro_metrics()`'s
    documented output-key contract (consumed by the dashboard API) is unchanged; this ticket adds a
    net-new top-level key only if the new function's output is folded into `compute_retro_metrics`'s
    return dict (Plan's call) — if so, this suite is regression surface; if the new function stays
    fully separate (called directly from `generate()`, mirroring `compute_retrieval_metrics`'s own
    separateness from `compute_retro_metrics`), this suite is unaffected either way and should still
    be run to confirm zero incidental impact.
- No integration or arena-combat tests apply — this ticket touches no `src/` simulation code.

## New Tests Required

Per Acceptance Criteria, mirroring `TestComputeRetrievalMetrics`'s fixture-based structure
(`tests/tools/test_generate_retro.py:1049+`) and `TestComputeShadowBaselineComparison`-style
provenance partitioning:

1. **`test_search_before_grep_compliance_true_when_search_docs_precedes_grep`**
   - Category: unit
   - Verifies: a synthetic fixture with an Investigate-phase `(run_id, seq)` whose `tools.jsonl`
     rows are ordered `[mcp__knowledge-search__search_docs, Grep]` reports 100% compliance for
     that pair.
   - Location: `tests/tools/test_generate_retro.py` (new test class, e.g.
     `TestComputeToolSafetyMetrics` or similar, per Plan's chosen function name).

2. **`test_search_before_grep_compliance_true_when_graphify_bash_call_precedes_grep`**
   - Category: unit
   - Verifies: a `Bash` tool row with `input_summary` starting with `"graphify"` satisfies the
     hard rule exactly like `mcp__knowledge-search__search_docs` does — the ticket's own Scope
     text names both as compliant orderings, and they must be tested as genuinely distinct code
     paths, not assumed equivalent by construction.
   - Location: same file.

3. **`test_search_before_grep_compliance_false_when_grep_tool_precedes_search_docs`**
   - Category: unit
   - Verifies: an ordering violation (`Grep` tool call before any `search_docs`/`graphify` call)
     within an Investigate-phase `(run_id, seq)` is correctly flagged as non-compliant — a
     synthetic fixture, since real `tools.jsonl` data is currently 100% compliant and cannot alone
     prove the check can detect a violation (per AC5's explicit requirement).
   - Location: same file.

4. **`test_search_before_grep_compliance_false_when_bash_grep_precedes_search_docs`**
   - Category: unit
   - Verifies: the same violation shape as #3, but via a `Bash` tool call whose `input_summary`
     contains `"grep"` (not the `Grep` tool itself) — the ticket's Scope explicitly names both
     detection paths ("first `Grep` tool call or Bash call containing `grep` in its
     `input_summary`"), so both must be independently tested, not just one as a stand-in for both.
   - Location: same file.

5. **`test_search_before_grep_compliance_rate_aggregated_across_multiple_investigate_pairs`**
   - Category: unit
   - Verifies: with 2+ Investigate-phase `(run_id, seq)` pairs (mix of compliant/violating), the
     aggregated compliance rate for the period is computed correctly (e.g. 1 compliant + 1
     violating → 50%), not just a per-pair boolean.
   - Location: same file.

6. **`test_search_before_grep_ignores_non_investigate_phase_tool_calls`**
   - Category: unit
   - Verifies: a `Grep`-before-`search_docs` ordering that occurs during a *non*-Investigate phase
     (e.g. `Implement`) is not counted toward the compliance rate at all — the check is explicitly
     scoped to Investigate-phase `(run_id, seq)` pairs only, cross-referenced against
     `events.jsonl`'s `phase` field.

7. **`test_parity_write_safety_zero_violations_on_clean_fixture`**
   - Category: unit
   - Verifies: a fixture with zero `Edit`/`Write` calls targeting `docs/parity_ledger/*.yaml` and
     every `parity_index.py build` Bash invocation targeting a scratch/tmp path (e.g.
     `/tmp/pi_smoke2/parity.db`) reports zero violations of both kinds — the "clean" contrast case
     AC5 requires alongside each violation-detecting test.
   - Location: same file.

8. **`test_parity_write_safety_detects_edit_targeting_parity_ledger_yaml`**
   - Category: unit
   - Verifies: a synthetic, fabricated `Edit` tool call with `input_summary` naming
     `docs/parity_ledger/combat_movement.yaml` (the ticket's own named example fixture) is
     correctly flagged as a violation and counted — do not rely solely on the real, currently-clean
     corpus (AC5's explicit "not just confirm today's clean data stays clean" requirement).
   - Location: same file.

9. **`test_parity_write_safety_detects_build_targeting_real_repo_path`**
   - Category: unit
   - Verifies: a synthetic `Bash` call whose `input_summary` is a `parity_index.py build`
     invocation targeting the real repo's `parity-index/` location (no `--db-path` override, or an
     explicit `--db-path parity-index/parity.db`) is flagged, while the same command targeting a
     `/tmp/...` path is not.
   - Location: same file.

10. **`test_tool_safety_function_never_crashes_on_malformed_rows`**
    - Category: unit (architecture-guard-adjacent — graceful-degradation contract)
    - Verifies: rows missing `input_summary`, missing `seq` (`None`), tool-call rows with no
      matching `phase`/`events.jsonl` cross-reference, and negative `seq` (shadow-packet
      convention) are all skipped gracefully rather than raising — mirrors
      `_is_legacy_event`/`_resolve_status`'s existing graceful-skip discipline. AC2's explicit
      requirement.
    - Location: same file.

11. **`test_tool_safety_function_is_pure_no_file_io`**
    - Category: architecture guard
    - Verifies: via `inspect.getsource()` (mirroring
      `test_function_is_read_only_no_write_call_or_file_open_in_write_mode` at
      `tests/tools/test_generate_retro.py:1136`), the new function contains no `write_lines(`,
      `write_line(`, `"w")`/`'w')`, `"a")`/`'a')`, `EVENTS_FILE`, `RUNS_FILE`, `DEFAULT_TOOLS_FILE`,
      `load_jsonl`, or `DEFAULT_DB_PATH` literal — proves it takes already-loaded data and performs
      no I/O of its own, matching the ticket's own Scope text ("no file I/O of its own").
    - Location: same file.

12. **`test_new_section_rendered_in_generate_output_when_investigate_tool_data_present`**
    - Category: unit (rendering)
    - Verifies: `generate(runs, events, label, tools=...)` (or however Plan threads the new
      parameter) includes the new Markdown section (a distinct `##` heading) when at least one
      real Investigate-phase tool-call record is present.

13. **`test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data`**
    - Category: unit (rendering)
    - Verifies: with zero Investigate-phase tools.jsonl data in the period, the new section is
      entirely absent from `generate()`'s output (no heading, no empty table) — matching the
      "Shadow vs. Baseline Retrieval Comparison" section's render-gating convention exactly. AC3's
      explicit requirement.

14. **`test_generate_retro_real_corpus_matches_hand_verified_findings`** (or equivalent,
    run manually per AC5 rather than as a hard-asserting pytest test against a moving real corpus —
    Plan should decide whether this is a pytest test with a loose/documented tolerance, or a
    documented manual verification step, since asserting exact literal numbers against the live,
    ever-growing `agent-monitoring/*.jsonl` corpus in a committed test would break on every future
    run. Recommendation: keep the exact-number check as a manual `--all` run documented in the
    ticket's own Test Summary, not a brittle pytest assertion against real data.)
    - Category: integration (manual verification, not committed to the automated suite)
    - Verifies: AC5 — running `python3 tools/agent-monitoring/generate_retro.py --all` against
      this repo's real data produces a new section whose numbers match the ticket's own
      hand-verified findings (100% search-before-grep compliance across the 7 real Investigate
      phases, 0 `docs/parity_ledger/*.yaml` write violations across the 4 parity runs) for the
      equivalent window.

## Scoped Pytest Commands

```bash
# Primary regression + new-test surface
pytest tests/tools/test_generate_retro.py -v

# Confirm no incidental breakage to modules that import from generate_retro.py
pytest tests/tools/test_build_index.py -v
pytest tests/tools/test_agent_ops_dashboard_stats.py -v

# If a tests/tools/test_retrieval_baseline_metrics.py file exists, include it too — confirms
# retrieval_baseline_metrics.py's imports from generate_retro.py still resolve:
pytest tests/tools/test_retrieval_baseline_metrics.py -v 2>/dev/null || true
```

Never: `pytest tests/`. This ticket's entire surface is `tools/agent-monitoring/` and its direct
test/doc dependents — no `src/`, no `tests/unit/`, `tests/integration/`, or arena-combat suites
are touched.

## Anti-Drift Test Guards

- **`test_tool_safety_function_is_pure_no_file_io`** (#11 above) — catches any future edit that
  quietly adds a `load_jsonl`/file-open call inside the compute function itself, which would break
  the module's established "compute functions are I/O-free, loading happens in the caller" contract
  (already enforced for `compute_retrieval_metrics` at `tests/tools/test_generate_retro.py:1136`).
- **`test_new_section_omitted_not_rendered_empty_when_no_investigate_tool_data`** (#13) — catches
  scope-creep into rendering an empty/placeholder table, which every other conditionally-gated
  section in this file (Reason Codes, Tag Breakdown, Outliers, Retrieval Quality, Shadow vs.
  Baseline) deliberately avoids.
- A test asserting **`compute_retrieval_metrics`'s and `compute_shadow_baseline_comparison`'s
  existing behavior/signatures are byte-unchanged** — e.g. re-running
  `test_compute_retrieval_metrics_does_not_reliteral_cache_or_authority_constants` and the shadow
  comparison suite as part of the regression run (not a new test — already covered by running the
  full `test_generate_retro.py` file) — guards against this ticket's new function accidentally
  reusing/mutating shared module-level state (e.g. a shared `Counter`/`defaultdict` import) in a
  way that leaks between functions.
- A test confirming **`SEARCH_TOOL_NAMES` in `retrieval_baseline_metrics.py` is untouched** (e.g.
  asserting its literal frozenset value, or simply re-running that module's own existing tests if
  present) — guards against the Anti-Drift Hazard identified in investigation.md: this ticket's
  new search-before-grep tool-identification logic must not be implemented by importing or
  mutating that unrelated constant.
- A test confirming **the new function/section never appears wired into
  `.claude/workflows/implement-ticket.js`** — not a pytest test per se (that file isn't Python),
  but Verify/Finalize should grep-confirm no `phase(...)` gating call references the new section's
  name, guarding against the ticket's explicit "never a blocking gate" Out-of-Scope boundary being
  silently crossed in a later, unrelated change.
