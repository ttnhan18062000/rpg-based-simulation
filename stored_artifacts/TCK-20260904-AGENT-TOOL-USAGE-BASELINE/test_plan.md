---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-AGENT-TOOL-USAGE-BASELINE
artifact_type: test_plan
tags: [agent-monitoring, ai, governance]
---

# Test Plan — TCK-20260904-AGENT-TOOL-USAGE-BASELINE

## Regression Surface

This ticket adds one new read-only script and its own test file; it does not modify any existing
production module, so the regression surface is "prove nothing else broke," not "re-verify
existing behavior changed correctly."

**Unit / existing agent-monitoring tooling (must keep passing unmodified):**
- `tests/tools/test_record_events.py` — `record_events.py`'s own event-schema validation and
  warn-only phase/agent vocabulary check; this ticket's script must not import or monkeypatch
  anything `record_events.py` depends on.
- `tests/tools/test_validate_agent_monitoring.py` — single-source-of-truth guard for
  `vocabulary.py`; confirms this ticket does not duplicate `WORKFLOW_AGENTS`/`WORKFLOW_AGENT_PREFIXES`
  elsewhere.
- `tests/tools/test_retrieval_baseline_metrics.py` — the direct sibling precedent this ticket's
  script should structurally mirror (same `load_data_glob` reuse, same read-only-guard pattern);
  must still pass unmodified, proving this ticket didn't accidentally touch shared helpers in
  `validate.py`/`generate_retro.py`.
- `tests/tools/test_agent_monitoring_manifest.py`, `tests/tools/test_migrate_monitoring_data.py`,
  `tests/tools/test_monitoring_writer.py`, `tests/tools/test_monitoring_writer_single_source.py` —
  cover the shard write path/migration this ticket's script must never touch.

**Integration (real corpus, not fixtures):**
- The new script's own real-corpus run (see below) is itself the integration check — there is no
  existing integration suite for "per-agent tool usage" to regress against, since no such tool
  existed before this ticket.

**Arena-combat:** not applicable — this ticket touches no `src/` simulation code.

## New Tests Required

- **Test name:** `test_output_has_exactly_16_agent_rows_plus_unattributed`
  **Category:** unit
  **Verifies:** the script's output contains exactly one row per current `.claude/agents/*.md`
  filename (derived by globbing at test time, never a hardcoded list-of-16 in the test itself — the
  test must fail loudly if a 17th agent file is added and the script wasn't updated to notice it)
  plus exactly one `unattributed` row. Covers AC1.
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_agent_row_present_with_zero_count_for_agents_with_no_real_rows`
  **Category:** unit
  **Verifies:** an agent with zero matching rows in a synthetic fixture still gets an explicit row
  with `count == 0`, not omission — regression guard for the real finding that 6 of 16 registered
  agents currently have zero real rows (`concern-investigator`, `mechanics-auditor`,
  `simulation-analyst`, `spec-document-reviewer`, `world-debugger`, `world-render-reviewer`). Covers
  AC1's "not hardcoded or stale" requirement together with the zero-count case.
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_null_and_non_matching_agent_values_bucket_to_unattributed`
  **Category:** unit
  **Verifies:** synthetic rows with `agent: null`, `agent: "finalizer"`, `agent: "claude"`,
  `agent: "orchestrator"`, and `agent: "some-typo"` all land in the single `unattributed` bucket,
  never silently dropped and never misassigned to a real agent row. Covers AC1's explicit
  "unattributed" bucketing requirement.
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_glob_matches_all_dated_week_shards_and_unknown_week`
  **Category:** unit
  **Verifies:** the script's glob (or its reuse of `load_data_glob`) matches every
  `agent-monitoring/data/*/tools.jsonl` file, including the `unknown-week` fallback shard — using a
  `tmp_path`-constructed fixture with several `YYYY-Www` folders plus an `unknown-week` folder, not
  the real corpus (keeps this test deterministic and fast). Covers AC2's glob-correctness
  requirement.
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_reuses_load_data_glob_not_a_fourth_loader`
  **Category:** architecture guard
  **Verifies:** the script imports and calls `validate.py`'s `load_data_glob` (or an equivalent
  already-shared helper) rather than reimplementing its own glob+parse loop — mirrors
  `test_retrieval_baseline_metrics.py::test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`'s
  exact style (introspect the module's source or call graph, not just its output). Covers the
  Anti-Drift Hazard against a duplicate loader.
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_sum_of_per_agent_counts_matches_wc_l_sanity_check_on_real_corpus`
  **Category:** integration
  **Verifies:** running the script against the real `agent-monitoring/data/` corpus, the sum of
  every row's count (16 agent rows + unattributed) equals the total line count across all real
  `agent-monitoring/data/*/tools.jsonl` shards (computed independently in the test via a plain
  `sum(len(open(f).readlines()) for f in glob(...))` or equivalent, not by re-calling the script's
  own internal counting logic — must be an independent re-derivation, not a tautology). Covers AC2's
  sanity-check requirement directly.
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_every_nonzero_tool_entry_has_a_labeled_truncated_example`
  **Category:** unit
  **Verifies:** for every (agent, tool-name) entry with count > 0, the output includes a
  non-empty example string sourced from a real row's `input_summary`, explicitly labeled as
  truncated/summarized (e.g. a `truncated: true` field or an inline marker) — never a fabricated or
  synthesized example. Covers AC3. (If the planner resolves the AC3 granularity question in favor of
  "one example per distinct tool name globally" instead of "per (agent, tool)", this test's
  assertion granularity should be updated to match — see investigation.md's Risks section.)
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_example_is_verbatim_substring_of_a_real_row_not_paraphrased`
  **Category:** unit
  **Verifies:** each reported example string is independently found as a substring of some real
  fixture row's actual `input_summary` value — guards against a plausible-looking but fabricated
  example slipping through. Covers AC3's "truthfully-labeled" requirement.
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_script_is_read_only_against_real_agent_monitoring_data`
  **Category:** architecture guard
  **Verifies:** `git status --porcelain -- agent-monitoring/` is identical before and after running
  the script against the real corpus (directly mirrors
  `test_retrieval_baseline_metrics.py::test_baseline_report_tool_causes_zero_diff_on_real_corpus`'s
  `_porcelain_snapshot()` pattern) — this is the literal test AC4 requires ("shard file bytes
  unchanged before vs. after running the script").
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

- **Test name:** `test_cli_runs_against_real_corpus_and_prints_valid_json_or_table`
  **Category:** integration
  **Verifies:** invoking the script as a subprocess against the real repo root exits 0 and produces
  well-formed output (JSON or a parseable table) covering the real 16-agent + unattributed rows —
  smoke-tests the full path end to end, mirroring
  `test_retrieval_baseline_metrics.py::test_baseline_report_cli_runs_against_real_corpus_and_prints_json`.
  **Where:** `tests/tools/test_agent_tool_usage_baseline.py`

## Scoped Pytest Commands

```bash
# This ticket's new test file (primary):
pytest tests/tools/test_agent_tool_usage_baseline.py -v

# Regression surface — existing agent-monitoring tooling tests, scoped to the domain:
pytest tests/tools/test_record_events.py tests/tools/test_validate_agent_monitoring.py \
  tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_agent_monitoring_manifest.py \
  tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py \
  tests/tools/test_migrate_monitoring_data.py -v

# Full agent-monitoring-adjacent tools directory as a final scoped sweep (never the bare
# `pytest tests/` invocation):
pytest tests/tools/ -k "monitoring or agent_tool_usage or retrieval_baseline" -v
```

## Anti-Drift Test Guards

- **`test_output_has_exactly_16_agent_rows_plus_unattributed`** derives its expected agent set from
  a live glob of `.claude/agents/*.md` at test time, not a hardcoded list — so it fails loudly (not
  silently passes stale) the moment a 17th agent file is added without the script being updated to
  notice it.
- **`test_reuses_load_data_glob_not_a_fourth_loader`** guards against the exact kind of
  loader-reimplementation drift already documented as a real precedent risk in
  `test_retrieval_baseline_metrics.py` for the sibling script.
- **`test_null_and_non_matching_agent_values_bucket_to_unattributed`** guards against the
  script silently dropping rows (undercounting the wc -l sanity check) or misattributing a
  pseudo-agent/orchestrator literal to a real agent's row — either failure mode would corrupt the
  evidence M3 depends on without being visually obvious in a quick eyeball of the output table.
  Includes both a documented-legitimate pseudo-agent value (`finalizer`) and an
  undocumented/anomalous one (`orchestrator`, per investigation.md's Risks section) to prove the
  bucketing logic doesn't special-case only the values `vocabulary.py` already knows about.
  **Note:** this test's real-corpus counterpart (`test_sum_of_per_agent_counts_matches_wc_l_sanity_check_on_real_corpus`)
  is the one that would actually catch a regression here in practice — the unit test with synthetic
  fixtures verifies the logic directly and independently.
- **`test_example_is_verbatim_substring_of_a_real_row_not_paraphrased`** guards against a
  plausible-but-fabricated "representative example" — since this table is the evidence base for a
  future least-privilege scoping decision, a fabricated example is worse than a missing one.
- **`test_script_is_read_only_against_real_agent_monitoring_data`** is the direct enforcement of
  this project's Durable State Rule for this ticket: the script must never mutate
  `agent-monitoring/data/`, and this test proves it against the real corpus, not a mocked
  filesystem.
