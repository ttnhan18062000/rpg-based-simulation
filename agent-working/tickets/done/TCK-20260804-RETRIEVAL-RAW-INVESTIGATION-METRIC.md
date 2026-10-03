---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC
phase: done
date: 2026-08-04
tags: [agent-monitoring, observability]
---

# TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC

## Title
Add a raw-investigation (Read) call-count metric to retrieval_baseline_metrics.py

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
User asked what metric would show that the context-search tooling (`search_docs` / `graphify`) actually reduces raw investigation effort ("much less effort than pure grep"). Investigation of `agent-monitoring/tools.jsonl` found this environment has no distinct `Grep` tool name recorded at all — grep-equivalent work runs through the catch-all `Bash` tool, which `retrieval_baseline_metrics.py`'s existing `SEARCH_TOOL_NAMES` design already deliberately excludes from search-tool counting (comment: "Bash is excluded even though some Bash calls have search-flavored input_summary text, since that is not distinguishable by tool name alone"). A literal Grep-call-count metric is therefore not buildable without violating that existing precision precedent. `Read` (18,567 occurrences in the corpus — the single most common non-Bash tool) is a distinct, precisely-recorded tool whose usage rises when semantic search fails to surface the right doc/code and the agent has to open files directly to look — making it the correct proxy for "raw investigation effort" in this codebase.

## Scope
- Add `build_raw_investigation_count_section(tools)` to `tools/agent-monitoring/retrieval_baseline_metrics.py`, following the exact structural precedent of `build_search_count_section()`: per-run `defaultdict(int)` grouping keyed by `run_id` (or literal `"unattributed"`), a `total`, and a mandatory `"derivation"` string.
- The derivation string must explicitly state: (a) it counts `tool == "Read"` events, (b) why `Grep` is not counted (no such distinct tool name exists in this environment; grep-equivalent calls run via `Bash`, which is excluded per the same non-distinguishability rationale as `SEARCH_TOOL_NAMES`), (c) this is a proxy for raw investigation effort, not a literal grep-call count.
- Wire the new section into the report-assembly function (`build_report()` or equivalent) alongside the existing `search_count` section.
- Add a derived ratio field (e.g. `read_to_search_ratio` per run, or corpus-wide) only if it can be computed without silent assumptions — otherwise state explicitly in the derivation why it's omitted.
- Add tests in `tests/tools/test_retrieval_baseline_metrics.py` mirroring the existing `test_baseline_report_search_count_is_marked_or_derived_never_silent()` / `test_baseline_report_search_count_derivation_matches_stated_fields()` pattern for the new section.
- Update `docs/agent-monitoring/README.md` (or wherever `retrieval_baseline_metrics.py`'s output shape is documented) to describe the new section.

## Out of Scope
- Wiring this metric into `generate_retro.py`'s recurring weekly retro (that script is a separate, recurring-cadence tool; `retrieval_baseline_metrics.py` is the one-off baseline script — this ticket only touches the latter, matching its existing scope boundary).
- Any change to `SEARCH_TOOL_NAMES` itself or the Bash-exclusion rationale — that precedent is being followed, not revisited.
- The `expansion_rate` wiring fix (tracked separately as a sibling ticket, TCK-20260804-EXPANSION-RATE-WIRING).
- Adding a distinct `Grep` tool to the harness itself — out of this repo's control, not a code change this ticket can make.

## Acceptance Criteria
- [ ] `build_raw_investigation_count_section()` exists, follows the `build_search_count_section()` structural pattern, and is wired into the assembled report output.
- [ ] The section's `derivation` field explicitly explains the Read-as-proxy choice and the Grep/Bash non-distinguishability reason, matching the existing "never a fabricated or silent number" convention.
- [ ] New tests pass, mirroring the existing never-silent / derivation-matches-fields test pattern for the new section.
- [ ] Running the script against real `agent-monitoring/tools.jsonl` produces a non-trivial, plausible Read count (order of magnitude consistent with the ~18,567 total observed during investigation).
- [ ] Relevant docs updated to describe the new section's meaning and limits.

## Related Tickets
- TCK-20260728-RETRIEVAL-BASELINE-METRICS (original script)
- TCK-20260804-EXPANSION-RATE-WIRING (sibling ticket, same user request)
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC (backlog; broader context-retrieval epic this metric supports evaluating)

## Related Docs
- `docs/agent-monitoring/schema.md`
- `docs/agent-monitoring/README.md` (if it documents baseline-metrics output)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260728-RETRIEVAL-BASELINE-METRICS/`

## Related Code Areas
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `tests/tools/test_retrieval_baseline_metrics.py`

## Assumptions / Open Questions
None — the Read-as-proxy design decision was made directly from existing codebase precedent (the `SEARCH_TOOL_NAMES` Bash-exclusion rationale), not left open.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC/plan.md`
(APPROVED architecture review), following its Decisions 1 and 2 verbatim:

- Added `build_raw_investigation_count_section(tools)` to
  `tools/agent-monitoring/retrieval_baseline_metrics.py`, inserted between
  `build_legacy_schema_notes` (unchanged, `:157-167`) and `build_baseline_report` (now
  `:213-224`, shifted). The new function is at `:170-210`. Filters strictly to
  `record.get("tool") == "Read"` (no new `READ_TOOL_NAMES` constant), reuses the
  `run_id or "unattributed"` null-key convention verbatim from `build_search_count_section`.
  Returns `{"derivation": <str>, "per_run": <dict>, "total": <int>, "read_to_search_ratio": <float
  or literal "undefined: ..." string>}`. `read_to_search_ratio` is computed corpus-wide only (never
  per-run) by calling `build_search_count_section(tools)["total"]` internally — function
  composition on the already-loaded `tools` list, not a new/second loader.
- Wired into `build_baseline_report()`'s literal dict as `"raw_investigation_count"`, immediately
  after `"search_count"`.
- Fixed `test_baseline_report_cli_runs_against_real_corpus_and_prints_json`'s exact key-set
  assertion to include `"raw_investigation_count"`, keeping the `==` (not `<=`) comparison per
  plan.md's explicit instruction.
- Added `build_raw_investigation_count_section` to the test module's import block (alphabetically
  ordered, matching existing style).
- Added the 5 new tests from test_plan.md verbatim, in a new `# --- AC-NEW ---` banner block placed
  immediately after the AC2 (`search_count`) block, before the AC3 (`duration`) banner.
- Updated `docs/parity_ledger/infrastructure.yaml`'s `INFRA-292` `text` (appended the extension
  note) and `v2_evidence` (re-derived real post-edit line numbers by reading the file, not
  guessing) — see Deviations below for one correction beyond plan.md's literal Step 6 text.
- Added the "Baseline Metrics Snapshot (one-off)" subsection to
  `docs/agent-monitoring/README.md`, placed after the `cost_proxy_score` calibration paragraph and
  before `## Navigation`, exactly as plan.md's Step 7 content specifies.

**Deviation from plan.md (documented in plan.md's new "Deviations" section):** Decision 2 asserted
"no other function's citation shifts" beyond the `:157-180` split, but `INFRA-292`'s pre-existing
`:183-196 (def main() ...)` citation also sits after the insertion point and therefore also shifted
(now `:227-240`, with the `_assert_safe_output_path` call at `:237` instead of `:193`). Corrected
this citation too in Step 6, since leaving it stale would contradict the ticket's own
accuracy purpose. No other citation (`:21-29`, `:50-53`, `:56-88`, `:91-154`) was touched.

## Test Summary
Ran `.venv/bin/python3 -m pytest tests/tools/test_retrieval_baseline_metrics.py -v` — **18 passed**,
0 failed (13 pre-existing + 5 new). All 3 pre-existing AST reuse guards
(`..._reuses_load_data_pattern_not_a_fourth_loader`, `..._reuses_classify_provenance_not_reimplemented`,
`..._tool_never_imports_writer_module`) stayed green unmodified. The real-corpus zero-diff test
(`test_baseline_report_tool_causes_zero_diff_on_real_corpus`) passed, confirming the new section
adds no write path.

Also ran `python3 tools/agent-monitoring/retrieval_baseline_metrics.py` directly against the real
corpus: produced valid JSON with 9 top-level keys including `raw_investigation_count`. Real values
observed: `raw_investigation_count.total = 18594` (Read calls), `search_count.total = 1924`,
`read_to_search_ratio = 9.6642` — same order of magnitude as the ~18,567 figure cited during
investigation (corpus grew slightly since then, consistent with expectations; no hardcoded exact
value was ever asserted in tests, per plan.md's Anti-Drift Notes).

## Files Changed
- `tools/agent-monitoring/retrieval_baseline_metrics.py` — added `build_raw_investigation_count_section`, wired into `build_baseline_report`
- `tests/tools/test_retrieval_baseline_metrics.py` — import added, exact-key-set assertion fixed, 5 new tests added
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-292` `text` and `v2_evidence` updated with re-derived line ranges
- `docs/agent-monitoring/README.md` — new "Baseline Metrics Snapshot (one-off)" subsection added
- `staging_artifacts/TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC/plan.md` — Deviations section appended

## Completion Summary
Added `build_raw_investigation_count_section()` to `tools/agent-monitoring/retrieval_baseline_metrics.py`
as the Read-call-count proxy metric for raw investigation effort, resolving the user's original
question ("what metric would show search tooling reduces grep-style effort") after investigation
found this environment records no distinct `Grep` tool name at all — grep-equivalent work runs via
the catch-all `Bash` tool, which the file's pre-existing `SEARCH_TOOL_NAMES` design already excludes
from search-tool counting for the same non-distinguishability reason. Read (18,594+ occurrences) is
the precise, distinctly-recorded proxy instead. Ships with a corpus-wide `read_to_search_ratio`
(explicitly `"undefined: ..."` rather than fabricated/zero when `search_count.total` is 0), wired
into the report alongside `search_count`, with 5 new tests (18/18 total passing) and the one
pre-existing test asserting an exact report key-set updated accordingly. `docs/parity_ledger/
infrastructure.yaml`'s `INFRA-292` and `docs/agent-monitoring/README.md` both updated and
independently re-verified across three separate passes (Architecture-Verify, Parity, Verify) with
zero drift found. Full standard-tier pipeline: Investigate → Plan → Review (APPROVED) → Implement →
Architecture-Verify (APPROVED) → Document-Update (no additional staleness found) → Test (18/18) →
Parity (accurate, no changes) → Verify (READY TO CLOSE, all 13 DoD conditions PASS).
