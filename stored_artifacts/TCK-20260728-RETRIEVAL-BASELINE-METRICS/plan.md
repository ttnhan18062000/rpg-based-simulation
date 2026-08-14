---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-BASELINE-METRICS
artifact_type: plan
tags: [agent-monitoring, observability]
---

# Implementation Plan — TCK-20260728-RETRIEVAL-BASELINE-METRICS

## Summary

Build one new, strictly read-only module, `tools/agent-monitoring/retrieval_baseline_metrics.py`,
that computes the 5 baseline metrics this ticket requires (context-tokens, follow-up-search-count,
phase-duration, test/gate outcome, review-rework) purely by importing and composing existing
functions from `generate_retro.py` (`_load_runs_and_events`, `load_jsonl`, `_resolve_status`,
`_is_gate_fail`), `legacy_reader.py` (`classify_provenance`), and `manifest.py`
(`_assert_safe_output_path`) — never reimplementing any of their logic and never modifying any of
those files. Each metric is its own small, independently-testable function; a final assembly step
composes them into one JSON report printed to stdout by default (mirroring `manifest.py`'s CLI
shape exactly), with a `--output` flag guarded the same way `manifest.py` guards its own output path
(which transitively also blocks `agent-monitoring/retro/`, since that is a subdirectory of
`agent-monitoring/`). Every metric's output carries an explicit, literal marker/citation string per
its AC — never a silently-omitted or silently-coerced value. This plan resolves all 4 open judgment
calls the investigation flagged (parity ledger entry: yes, new P2 entry; search-count derivation:
literal `tool` field filtering, not the coarser `tool_call_count` aggregate; review-rework rule:
precise cross-run `NEEDS_CHANGES`/`BLOCKED` → later `DONE` transition; output location: stdout by
default, never under `agent-monitoring/`) as documented implementation decisions below, with
rationale, rather than leaving them open.

## Steps

### Step 1 — Module skeleton and reused data loading
**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py` (new)
**Change:** Create the module with the same `sys.path.insert(0, str(Path(__file__).resolve().parent))`
wiring `manifest.py` uses. Import, read-only:
- `_load_runs_and_events` from `generate_retro.py` — the index-with-JSONL-fallback loader for
  `runs`/`events`; never call `sqlite3.connect()` directly in this module.
- `load_jsonl`, `DEFAULT_TOOLS_FILE` from `generate_retro.py` — for `tools.jsonl`.
- `_resolve_status`, `_is_gate_fail` from `generate_retro.py`.
- `classify_provenance` from `legacy_reader.py`.
- `_assert_safe_output_path` from `manifest.py`.

Add `load_all_sources() -> tuple[list, list, list]`:
```python
def load_all_sources():
    runs, events = _load_runs_and_events()
    tools = load_jsonl(DEFAULT_TOOLS_FILE)
    return runs, events, tools
```
**Decision (resolves investigation Risk #4's loading half):** `generate_retro.py` has no
index-with-fallback wrapper for `tools.jsonl` (only `validate.py`'s `load_tools_from_index` +
`open_index`, and `open_index` hard-fails with `sys.exit(1)` when the index is missing — exactly
the "hard gating dependency" `generate_retro.py`'s own docstring says a report must never have).
Reusing `open_index` verbatim would violate that invariant, so `tools.jsonl` is loaded via the
plain `load_jsonl(DEFAULT_TOOLS_FILE)` scan instead — still 100% reuse of an existing function, not
a new loader, and it degrades the same way (empty list) `load_jsonl` already does if the file is
missing.
**Do NOT touch:** `generate_retro.py`, `validate.py`, `manifest.py`, `legacy_reader.py`,
`vocabulary.py`, `cost_proxy.py` — import only, zero edits to any of them.
**Verify:** `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`

### Step 2 — AC1: context-tokens marked 'unavailable'
**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`
**Change:** Add `build_context_tokens_section() -> dict` returning a literal:
```python
{
    "status": "unavailable",
    "reason": "Real token/context-size telemetry is platform-blocked and is not recorded "
              "anywhere in agent-monitoring/*.jsonl.",
    "citation": "docs/agent-monitoring/schema.md — 'What is not recorded' section",
}
```
The literal string `"unavailable"` must appear verbatim as the `status` value — never `0`, never
`null`, never an omitted key.
**Do NOT touch:** do not attempt to estimate/approximate a token count from any proxy (e.g.
`cost_proxy_score`) — that would contradict AC1's "not synthesized" requirement.
**Verify:** `test_baseline_report_context_tokens_marked_unavailable`

### Step 3 — AC2: follow-up-search-count, derived from tools.jsonl's literal `tool` field
**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`
**Change:** Add a module-level constant:
```python
SEARCH_TOOL_NAMES = frozenset({
    "mcp__knowledge-search__search_docs",
    "ToolSearch",
    "WebSearch",
})
```
(These are the literal `tool` values confirmed present in the real corpus by investigation.md's
direct scan; `mcp__knowledge-search__search_health` is deliberately excluded — it is a health-check
call, not a follow-up search, and `Bash` is excluded even though some `Bash` calls have
search-flavored `input_summary` text, since that is not distinguishable by tool name alone and this
metric must stay precise, not inflated.)

Add `build_search_count_section(tools: list) -> dict`: for each record, count matches where
`record.get("tool") in SEARCH_TOOL_NAMES`, grouped by `run_id`, plus a corpus-wide total. Return:
```python
{
    "derivation": "Derived from tools.jsonl's literal `tool` field, filtered to "
                  "SEARCH_TOOL_NAMES = {mcp__knowledge-search__search_docs, ToolSearch, "
                  "WebSearch}. This is a finer-grained derivation than the ticket AC's literal "
                  "'tool_call_count' wording — tool_call_count is a coarse per-event total-tool "
                  "-activity aggregate on events.jsonl records, and does not distinguish a search "
                  "call from any other tool call. This report uses the more precise, still-100%"
                  "-existing-data derivation because it actually answers 'how many follow-up "
                  "searches happened', per this ticket's plan.md Step 3.",
    "per_run": {...},
    "total": N,
}
```
**Decision (resolves investigation Risk #2):** Option B (literal `tool`-name filtering) is chosen
over Option A (the coarser `tool_call_count` aggregate). The `derivation` string above must be
present verbatim in the report output so a reviewer diffing against the AC text can see the
AC-wording tension was deliberately resolved, not silently reinterpreted.
**Do NOT touch:** do not add `Skill`/`graphify`-invocation counting — investigation.md did not
confirm those are distinguishable by literal `tool` name at the required precision; do not fold in
`mcp__knowledge-search__search_health`.
**Verify:** `test_baseline_report_search_count_is_marked_or_derived_never_silent`,
`test_baseline_report_search_count_derivation_matches_stated_fields`

### Step 4 — AC3: phase-duration, flagged pause-contaminated (no gap-aware branch)
**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`
**Change:** Add `build_duration_section(runs: list) -> dict`. For each run with a truthy
`duration_s`, emit a row:
```python
{
    "run_id": r.get("run_id"),
    "duration_s": r["duration_s"],
    "flag": "pause-contaminated",
    "note": "raw duration_s includes session-pause/idle gaps; a gap-aware active-duration view "
            "does not exist in this repo today (tools/agent-monitoring/duration_utils.py is "
            "absent) — see docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md",
}
```
Every duration-bearing row must carry the literal `"pause-contaminated"` flag — never an unqualified
`duration_s` value anywhere in the report.
**Decision (resolves investigation Risk #6 / the ticket's own Out-of-Scope note):** Do NOT write any
`if duration_utils exists: use gap-aware view` branch in production code. `duration_utils.py`
does not exist (confirmed by investigation.md's directory listing), and approximating gap-awareness
with an ad hoc heuristic (e.g. "largest inter-event gap is idle time") would half-implement the
sibling idea doc this ticket is explicitly scoped not to depend on. Always emit the
pause-contaminated flag; there is no conditional branch to write.
**Do NOT touch:** do not create `duration_utils.py`; do not add any gap-detection heuristic.
**Verify:** `test_baseline_report_flags_duration_as_pause_contaminated_when_no_gap_aware_view_exists`

### Step 5 — AC3: forward-looking expiry guard (test-only, no production change)
**Files:** `tests/tools/test_retrieval_baseline_metrics.py` (new)
**Change:** Add a test that asserts, via `importlib.util.find_spec("duration_utils")`, that the
module does not exist today (searched relative to `tools/agent-monitoring/`, e.g. by checking
`(Path(__file__).resolve().parent.parent.parent / "tools" / "agent-monitoring" /
"duration_utils.py").exists() is False`, or an equivalent `find_spec`-based check). This is a pure
test addition — no production code changes in this step. Its purpose: once
`idea_agent_monitoring_active_duration.md` is implemented and `duration_utils.py` is created, this
test starts failing loudly, forcing someone to update Step 4's always-flag behavior rather than
letting the caveat silently go stale.
**Do NOT touch:** production module code (Step 4's function already exists; this step only adds a
test).
**Verify:** `test_baseline_report_would_prefer_gap_aware_view_if_available`

### Step 6 — AC4: test/gate outcome, from existing fields only
**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`
**Change:** Add `build_gate_outcome_section(runs: list) -> dict` using the imported
`_resolve_status`/`_is_gate_fail` (Step 1) — do not re-derive status resolution or gate-fail
classification inline. Compute a `Counter` of resolved statuses across `runs` and a gate-fail vs.
terminal-success split. Return:
```python
{
    "status_breakdown": {...},   # Counter(_resolve_status(r) for r in runs)
    "gate_fail_count": N,        # count where _is_gate_fail(r) is True
    "terminal_success_count": M,
    "disclosure": "derived proxy from runs.jsonl's final_status/status fields via "
                  "generate_retro.py's _resolve_status/_is_gate_fail — not fabricated",
}
```
The literal `"derived proxy"` / `"not fabricated"` phrasing must appear verbatim.
**Do NOT touch:** do not reimplement `_resolve_status`/`_is_gate_fail` inline — import and call them.
**Verify:** `test_baseline_report_gate_outcome_uses_final_status_and_reason_code_only`

### Step 7 — AC4: review-rework, precise cross-run proxy
**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`
**Change:** Add a module constant:
```python
# Deliberately narrower than generate_retro.py's _is_gate_fail — that predicate also covers
# TESTS_FAILED/DOD_BLOCKED (Test/Verify-phase gate fails), which are not "review rework".
# Scoped to exactly the two statuses investigation.md confirmed (via a direct grep of
# .claude/workflows/implement-ticket.js) terminate a run at the Review phase (line ~550) or the
# post-Implement Architecture-Verify phase (line ~742).
REWORK_TRIGGER_STATUSES = frozenset({"NEEDS_CHANGES", "BLOCKED"})
```
Add `build_review_rework_section(runs: list) -> dict`:
1. Group `runs` by `run_id` (mirror `validate.py`'s `runs_grouped_by_id` pattern: a
   `defaultdict(list)` keyed by `run.get("run_id", f"?:{i}")`).
2. Within each group of 2+ records, sort by `start_ts`.
3. Flag the `run_id` as **reworked** if there exists an earlier record `e` with
   `_resolve_status(e) in REWORK_TRIGGER_STATUSES` and a chronologically later record `l` (same
   group) with `_resolve_status(l) == "DONE"`.
4. A `run_id` with only a single terminal non-`DONE` record and no later record is **not** flagged
   (distinguishes "failed and abandoned" from "failed and reworked", per test_plan.md's explicit
   test for this).
5. `reason_code`/`reason_code_breakdown` must play **no role** in this determination.

Return:
```python
{
    "reworked_run_ids": [...],
    "count": N,
    "rule": "A run_id is flagged as review-rework if 2+ runs.jsonl records share that run_id, an "
            "earlier record's resolved status is NEEDS_CHANGES or BLOCKED (the Review/"
            "Architecture-Verify gate-failure statuses), and a chronologically later record for "
            "the same run_id resolves to DONE.",
    "disclosure": "derived proxy from cross-run final_status transitions grouped by run_id — not "
                  "fabricated; reason_code/reason_code_breakdown is not used as a rework signal",
}
```
**Do NOT touch:** do not use `reason_code_breakdown` as the signal (named anti-drift hazard); do not
widen `REWORK_TRIGGER_STATUSES` to include `TESTS_FAILED`/`DOD_BLOCKED` — those are Test/Verify-phase
outcomes, not Review/Architecture-Verify, and folding them in would blur the metric's precise label.
**Verify:** `test_baseline_report_review_rework_proxy_requires_multi_record_same_run_id`,
`test_baseline_report_review_rework_proxy_ignores_reason_code_alone`

### Step 8 — Legacy-schema handling via classify_provenance (ticket's explicit scope line)
**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`
**Change:** Add `build_legacy_schema_notes(runs: list, events: list, tools: list) -> dict` that
calls the imported `classify_provenance(record, source)` per record (source = `"runs"`/`"events"`/
`"tools"` respectively) and tallies non-empty label counts per source, e.g.:
```python
{
    "runs_legacy_count": N, "events_legacy_count": M, "tools_legacy_count": K,
    "note": "counts records whose shape matches one of legacy_reader.py's documented legacy "
            "schema generations (classify_provenance) — informational, not blocking",
}
```
This directly satisfies the ticket's Scope line "Handle >=5-6 legacy schema generations via the
existing LEGACY_COMPLETION_FIELDS pattern (legacy_reader.py), not reimplemented."
**Do NOT touch:** do not write a second `if`/`elif` shape-classification chain inline — every shape
check must go through the imported `classify_provenance`.
**Verify:** `test_baseline_report_reuses_classify_provenance_not_reimplemented`

### Step 9 — Assemble report + CLI entrypoint + output-path safety
**Files:** `tools/agent-monitoring/retrieval_baseline_metrics.py`
**Change:** Add `build_baseline_report(runs, events, tools) -> dict` composing Steps 2-8's section
functions plus a top-level `{"ticket_id": "TCK-20260728-RETRIEVAL-BASELINE-METRICS", "generated_note":
"one-off baseline snapshot — not the recurring weekly retro cadence"}`. Add `main()` with
`argparse`, mirroring `manifest.py`'s CLI shape:
- `--output` (optional `Path`, default `None`).
- Default behavior: `runs, events, tools = load_all_sources(); report = build_baseline_report(...);
  output = json.dumps(report, indent=2, sort_keys=True) + "\n"`; write to `sys.stdout` always.
- If `--output` given: call the imported `_assert_safe_output_path(args.output)` (from `manifest.py`)
  **before** writing — this refuses any path under `agent-monitoring/`, which transitively also
  blocks `agent-monitoring/retro/` since it is a subdirectory of `agent-monitoring/`.
- No file write happens by default — stdout is the only default sink.

**Decision (resolves investigation Risk #4's output-location half):** No new
`agent-monitoring/retro/`-adjacent directory is created. This is a one-off/periodic snapshot tool,
architecturally distinct from `generate_retro.py`'s weekly-cadence `RETRO-*.md` family; conflating
the two would pollute `generate_retro.py`'s own `_update_index()` rebuild. Reusing
`manifest.py`'s exact `_assert_safe_output_path` guard (rather than writing a new one) means any
future `--output` misuse is caught the same way `manifest.py`'s own is already tested.
**Do NOT touch:** do not add a `--week`/`--days`/cadence flag; do not write into
`agent-monitoring/retro/` or any `agent-monitoring/` subpath, ever; do not import or call anything
from `writer.py`, `record_run.py`, `record_events.py`, or `post_tool_hook.py`.
**Verify:** `test_baseline_report_tool_never_imports_writer_module`

### Step 10 — Zero-mutation integration test
**Files:** `tests/tools/test_retrieval_baseline_metrics.py`
**Change:** Add a dirty-tree-aware pre/post snapshot test mirroring
`tests/agent_replay/test_no_mutation_snapshot.py` and
`test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff`:
snapshot `git status --porcelain -- agent-monitoring/` (or a SHA-256 content-hash fallback if the
tree is already dirty) before and after invoking `main()`/`build_baseline_report` against the real,
live `agent-monitoring/runs.jsonl`, `events.jsonl`, `tools.jsonl`. Assert no diff.
**Do NOT touch:** do not mock the corpus for this specific test — it must run against the real files
(matching the sibling precedent's own real-corpus invariant test).
**Verify:** `test_baseline_report_tool_causes_zero_diff_on_real_corpus`

### Step 11 — Full regression pass
**Files:** none (verification-only step)
**Change:** Run the scoped pytest commands from `test_plan.md`'s "Scoped Pytest Commands" section:
the new module's own test file, plus the full existing regression surface
(`test_agent_monitoring_legacy_reader.py`, `test_agent_monitoring_manifest.py`,
`test_validate_agent_monitoring.py`, `test_cost_proxy.py`, `test_generate_retro.py`), plus the
adjacent writer/consent-boundary tests, plus `tests/agent_replay/test_no_mutation_snapshot.py`. All
must pass unmodified. Do not run `pytest tests/` in full.
**Do NOT touch:** do not edit any test file listed as "Regression Surface" in test_plan.md — they
must pass as-is, proving this ticket's reuse didn't change their behavior.
**Verify:** every test named in test_plan.md's "Scoped Pytest Commands" section, green.

### Step 12 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Add one new entry, `id` = the next free `INFRA-NNN` sequential number after `INFRA-291`
(confirm the actual next-free number at implementation time — do not hardcode `INFRA-292` if the
ledger has since grown), with:
- `text`: "New read-only baseline-metrics reporting tool over agent-monitoring/*.jsonl
  (context-tokens, follow-up-search-count, phase-duration, gate-outcome, review-rework) —
  TCK-20260728-RETRIEVAL-BASELINE-METRICS"
- `status: verified`
- `priority: P2`
- `v2_evidence`: `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `test_path`: `tests/tools/test_retrieval_baseline_metrics.py`
**Decision (resolves investigation Risk #1):** Follow the more recent, more numerous precedent
(`INFRA-281` through `INFRA-291`, all agent-tooling infrastructure entries) rather than
`TCK-20260721-BASELINE-MONITORING-MANIFEST`'s own "no entry needed" conclusion. This is a judgment
call between two real, conflicting pieces of prior practice in this repo — recorded here explicitly,
not silently picked, per investigation.md's own flag.
**Do NOT touch:** do not change the `status` of any existing `INFRA-*` entry.
**Verify:** no pytest test — verified by `done-checker`'s ledger-presence/frontmatter checks, not a
unit test.

## Scope Guards

- Do not modify `generate_retro.py`, `validate.py`, `manifest.py`, `legacy_reader.py`,
  `vocabulary.py`, or `cost_proxy.py` — read/import only, in every step.
- Do not write to `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, or
  `agent-monitoring/tools.jsonl` anywhere in this module or its tests (except the pre-existing,
  unrelated monitoring-write path this ticket's own workflow run uses, which is out of this plan's
  scope).
- Do not write into `agent-monitoring/retro/` — that is `generate_retro.py`'s own weekly-cadence
  output space.
- Do not create `tools/agent-monitoring/duration_utils.py` or any gap-detection heuristic — Step 4
  always emits the pause-contaminated flag; no conditional gap-aware branch is written.
- Do not use `reason_code`/`reason_code_breakdown` as a review-rework signal (Step 7).
- Do not widen `REWORK_TRIGGER_STATUSES` beyond `{"NEEDS_CHANGES", "BLOCKED"}` (Step 7).
- Do not add a `--week`/`--days`/cadence CLI flag, and do not call anything from `writer.py`,
  `record_run.py`, `record_events.py`, or `post_tool_hook.py` (Step 9).
- Do not build the ContextPacket/retrieval-event schema described in later Sequenced Future Epic
  phases of the context-efficient-retrieval idea doc — out of scope per the ticket.
- Do not change the `status` of any existing `docs/parity_ledger/infrastructure.yaml` entry (Step 12
  only adds a new one).
- Do not run `pytest tests/` in full — stay scoped to `tests/tools/` plus the one zero-mutation
  precedent file in `tests/agent_replay/`.

## Dependency Map

- Step 1 is a prerequisite for every other step (imports/data-loading foundation).
- Steps 2, 3, 4, 6, 7, 8 are independent of each other — each adds one self-contained section
  function and can be implemented/verified in any order once Step 1 lands.
- Step 5 depends conceptually on Step 4 (same duration topic) but is a test-only addition and does
  not require Step 4's code to change.
- Step 9 depends on Steps 2, 3, 4, 6, 7, 8 (assembles all section functions) and Step 1 (data
  loading + `_assert_safe_output_path` import).
- Step 10 depends on Step 9 (needs `main()`/`build_baseline_report` to exist to invoke).
- Step 11 depends on all of Steps 1-10 being complete.
- Step 12 depends on Step 11 passing (parity entries are added once the behavior is implemented and
  verified, not before).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — context-tokens marked 'unavailable', citing schema.md | Step 2 | `test_baseline_report_context_tokens_marked_unavailable` |
| AC2 — follow-up-search-count marked 'not_yet_instrumented' or derived with cited computation | Step 3 | `test_baseline_report_search_count_is_marked_or_derived_never_silent`, `test_baseline_report_search_count_derivation_matches_stated_fields` |
| AC3 — phase-duration gap-aware or visibly flagged pause-contaminated | Steps 4, 5 | `test_baseline_report_flags_duration_as_pause_contaminated_when_no_gap_aware_view_exists`, `test_baseline_report_would_prefer_gap_aware_view_if_available` |
| AC4 — test/gate outcome and review-rework derived only from existing fields, documented as proxy | Steps 6, 7, 8 | `test_baseline_report_gate_outcome_uses_final_status_and_reason_code_only`, `test_baseline_report_review_rework_proxy_requires_multi_record_same_run_id`, `test_baseline_report_review_rework_proxy_ignores_reason_code_alone` |
| AC5 — zero mutation of agent-monitoring/*.jsonl | Steps 9, 10 | `test_baseline_report_tool_causes_zero_diff_on_real_corpus`, `test_baseline_report_tool_never_imports_writer_module` |
| (Reuse-not-reimplement, ticket Scope line) | Steps 1, 8 | `test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`, `test_baseline_report_reuses_classify_provenance_not_reimplemented` |

## Anti-Drift Notes

- **Reuse discipline is the primary risk.** Every section function in Steps 2-8 must call an
  imported function (`_resolve_status`, `_is_gate_fail`, `classify_provenance`,
  `_load_runs_and_events`, `load_jsonl`, `_assert_safe_output_path`) rather than re-deriving
  equivalent logic inline — the reuse-guard tests are `ast`/source-text checks specifically because
  output-equality tests would miss a silent reimplementation that happens to match today's numbers
  but drifts the next time, e.g., a 7th legacy shape is added to `classify_provenance`.
- **The duration caveat has a deliberately-designed expiry (Step 5).** Do not "fix" that test by
  making it pass forever (e.g. by stubbing `duration_utils` into existence) — its entire purpose is
  to fail loudly once the sibling idea doc is actually implemented, so a human notices this report
  needs updating.
- **Review-rework must never be derived from `reason_code_breakdown` alone.** This is the single
  most likely silent-scope-creep failure mode per investigation.md — `reason_code` explains *why* a
  single gate failed, not *whether* the ticket was later resubmitted and passed. Step 7's
  `REWORK_TRIGGER_STATUSES` + cross-run grouping is the only sanctioned derivation.
- **Every AC's marker/citation string must appear verbatim in the report output**, not just as an
  internal code comment — a reviewer diffing against the AC text needs to find `"unavailable"`,
  the search-count derivation citation, `"pause-contaminated"`, and `"derived proxy... not
  fabricated"` literally in what the tool prints.
- **This ticket's own tests must themselves remain read-only** (Step 10) — no test may assert
  correctness by writing then re-reading a mutated fixture file under `agent-monitoring/`.
- **Corpus counts are illustrative only.** Any specific line-count or `tool` distribution numbers
  cited during implementation (e.g. from investigation.md's measured snapshot) will have grown by
  the time this ticket runs — tests must not hardcode today's corpus size as an expected value in
  the real-corpus zero-mutation test; only the diff (before vs. after) matters, not an absolute count.

## Deviations

Two small technical fixes were required beyond this plan's literal code snippets, both discovered
by running the CLI against the real corpus (not caught by synthetic-fixture unit tests, since the
synthetic fixtures used clean `run_id`/`final_status` values):

1. **Step 3 (`build_search_count_section`)**: the plan's snippet groups `per_run` by the literal
   `record.get("run_id")`. The real `tools.jsonl` corpus contains "interactive" tool-call records
   (`legacy_reader.py`'s `classify_provenance` calls these `interactive_null` — both `run_id` and
   `seq` are `None`, meaning the call happened outside any workflow run). Using `None` directly as
   a dict key makes `json.dumps(..., sort_keys=True)` raise `TypeError: '<' not supported between
   instances of 'NoneType' and 'str'` when it tries to sort the `per_run` dict's keys alongside
   real string `run_id`s. Fix: group under the literal string `"unattributed"` instead of `None`
   when `record.get("run_id")` is falsy. The corpus-wide `total` count is unaffected — only the
   per-run grouping key for these interactive calls changed.
2. **Step 6 (`build_gate_outcome_section`)**: the plan's snippet builds `status_breakdown` via
   `Counter(_resolve_status(r) for r in runs)`. A handful of real `runs.jsonl` records match
   `legacy_reader.py`'s `shape6_type_checker_exception` shape (has `outcome`, but neither
   `final_status` nor `status`), so `_resolve_status(r)` returns `None` for them — same
   `sort_keys=True` `TypeError` as above. Fix: `Counter(_resolve_status(r) or "MISSING_STATUS" for
   r in runs)`. This does not change `gate_fail_count`/`terminal_success_count` (both still call
   `_is_gate_fail`/`_resolve_status` directly, unaffected by the label substitution) — only the
   `status_breakdown` dict's key for these records changed from `None` to a literal, JSON-safe
   string.

Neither fix reimplements any imported function's logic (`_resolve_status`/`_is_gate_fail`/
`classify_provenance` are still called exactly as specified) — both are purely about choosing a
JSON-serializable grouping-key label for an edge case the plan's snippets didn't anticipate.
No other step deviated from this plan.
