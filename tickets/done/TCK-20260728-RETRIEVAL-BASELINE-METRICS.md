---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-BASELINE-METRICS
phase: done
date: 2026-07-28
tags: [observability]
---

# TCK-20260728-RETRIEVAL-BASELINE-METRICS

## Title
Baseline Measurement of Current Retrieval and Context-Loading Behavior

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Before any mandatory workflow changes, collect a baseline measurement period over current retrieval/context-loading behavior. Record only available, safe metadata and never synthesize unknowns; capture scenario-specific ranges for context tokens, follow-up search count, phase duration, test/gate outcome, and review rework. This produces measurement artifacts only — no workflow change.

## Scope
- Build a read-only aggregation tool/report over existing agent-monitoring/runs.jsonl, events.jsonl, tools.jsonl data
- Report context-tokens dimension explicitly marked 'unavailable' (not zero/omitted), citing docs/agent-monitoring/schema.md's platform block
- Report follow-up-search-count marked 'not_yet_instrumented' or derived only from existing tool_call_count data with the derivation cited
- Report phase-duration using a gap-aware/active-duration view if available, or visibly flag raw duration_s as pause-contaminated (never presented as clean)
- Report test/gate outcome and review-rework derived only from existing fields (final_status, reason_code, Review/Architecture-Verify status transitions), documented as a derived proxy, not fabricated
- Handle >=5-6 legacy schema generations via the existing LEGACY_COMPLETION_FIELDS pattern (legacy_reader.py), not reimplemented

## Out of Scope
- Does NOT build the ContextPacket/retrieval-event schema described in later Sequenced Future Epic phases
- Does NOT depend on or require docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md being implemented first — this ticket proceeds with an explicit raw-duration-contamination caveat if that idea has not been picked up
- No mutation of agent-monitoring/*.jsonl — strictly read-only, matching tools/agent-monitoring/manifest.py precedent
- No new mandatory workflow gate or change to how runs/events are recorded

## Acceptance Criteria
- [ ] Baseline report explicitly marks context-tokens as 'unavailable' (not zero/omitted), citing schema.md's platform block
- [ ] Follow-up-search-count is marked 'not_yet_instrumented' or derived only from existing tool_call_count data with cited computation
- [ ] Phase-duration uses a gap-aware active-duration view OR visibly flags raw duration_s as pause-contaminated, never presented as clean
- [ ] Test/gate outcome and review-rework are derived only from existing fields (final_status, reason_code, Review/Architecture-Verify status transitions), documented as derived proxy not fabricated
- [ ] Tool/report performs zero mutation of agent-monitoring/*.jsonl (read-only, matches manifest.py precedent)

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC

## Related Docs
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/validate.py
- tools/agent-monitoring/manifest.py
- tools/agent-monitoring/legacy_reader.py
- tools/agent-monitoring/vocabulary.py
- tools/agent-monitoring/cost_proxy.py
- agent-monitoring/runs.jsonl
- agent-monitoring/events.jsonl
- agent-monitoring/tools.jsonl

## Assumptions / Open Questions
- No scenario taxonomy exists yet to bucket runs (small bugfix vs ticket implementation vs review vs architecture) — new classification work may be needed within this ticket
- Dependency-ordering resolved as: proceed now with an explicit raw-duration caveat rather than waiting on idea_agent_monitoring_active_duration.md being implemented
- tool_call_count/cost_proxy_score are only computed for the implement-ticket workflow today; create-tickets/implement-epic workflows have no sidecar data for these fields

## Implementation Notes
Implemented `tools/agent-monitoring/retrieval_baseline_metrics.py`, a strictly read-only baseline
report over `agent-monitoring/{runs,events,tools}.jsonl`, following `staging_artifacts/.../plan.md`'s
12 steps:

- `load_all_sources()` composes `generate_retro.py`'s `_load_runs_and_events()` (index-with-JSONL-
  fallback) and `load_jsonl(DEFAULT_TOOLS_FILE)` — no fourth loader, no direct `sqlite3.connect()`.
- `build_context_tokens_section()` — AC1: literal `"unavailable"` status, citing
  `docs/agent-monitoring/schema.md`'s "What is not recorded" section.
- `build_search_count_section(tools)` — AC2: `SEARCH_TOOL_NAMES` literal-`tool`-field filter
  (`mcp__knowledge-search__search_docs`, `ToolSearch`, `WebSearch`), grouped per-`run_id` plus a
  corpus-wide total, with the AC-wording-tension derivation string cited verbatim in the output
  (Option B over Option A, per plan.md's resolved judgment call).
- `build_duration_section(runs)` — AC3: every duration-bearing row unconditionally carries
  `"flag": "pause-contaminated"` — no gap-aware branch, since `duration_utils.py` does not exist.
- `build_gate_outcome_section(runs)` — AC4: status breakdown / gate-fail count / terminal-success
  count via imported `_resolve_status`/`_is_gate_fail`, with a literal "derived proxy ... not
  fabricated" disclosure.
- `build_review_rework_section(runs)` — AC4: cross-run proxy grouping `runs.jsonl` by `run_id`
  (mirroring `validate.py`'s `runs_grouped_by_id` pattern), sorted by `start_ts`, flagging a
  `run_id` as reworked only if an earlier `NEEDS_CHANGES`/`BLOCKED` record is followed
  chronologically by a `DONE` record for the same `run_id`. `reason_code` plays no role.
- `build_legacy_schema_notes(runs, events, tools)` — tallies non-empty `classify_provenance()`
  labels per source (imported from `legacy_reader.py`, never reimplemented).
- `build_baseline_report(...)` assembles all sections; `main()` mirrors `manifest.py`'s CLI shape
  (stdout by default, optional `--output` guarded by imported `_assert_safe_output_path`).

**Two small technical fixes beyond the plan's literal snippets** (see Deviations in plan.md):
`build_search_count_section`'s `per_run` grouping key falls back to the literal string
`"unattributed"` when `record.get("run_id")` is `None` (real `tools.jsonl` has "interactive_null"
records issued outside any workflow run), and `build_gate_outcome_section`'s status breakdown key
falls back to `"MISSING_STATUS"` when `_resolve_status(r)` is `None` (a handful of real
`shape6_type_checker_exception` `runs.jsonl` records have neither `final_status` nor `status`).
Both were required because `json.dumps(..., sort_keys=True)` raises `TypeError` comparing `None`
to `str` when sorting dict keys — discovered by running the CLI against the real corpus, not a
synthetic fixture. Total counts are unaffected; only the grouping-key label changed.

Added the parity ledger entry `INFRA-292` in `docs/parity_ledger/infrastructure.yaml` (next free
ID after `INFRA-291`), following the more recent/numerous `INFRA-281`-`INFRA-291` agent-tooling
precedent per plan.md Step 12's resolved judgment call, rather than
`TCK-20260721-BASELINE-MONITORING-MANIFEST`'s own "no entry needed" conclusion.

## Test Summary
New file `tests/tools/test_retrieval_baseline_metrics.py` — 13 tests, all passing:
reuse-not-reimplement guards (load-data pattern, `classify_provenance`, no-writer-import),
AC1-AC5 marker/derivation/proxy tests, the forward-looking `duration_utils.py`-absence expiry
guard, and a dirty-tree-aware zero-mutation integration test + CLI smoke test against the real
corpus. Full regression surface from `test_plan.md` re-run and green: `test_agent_monitoring_
legacy_reader.py`, `test_agent_monitoring_manifest.py`, `test_validate_agent_monitoring.py`,
`test_cost_proxy.py`, `test_generate_retro.py`, `test_monitoring_writer.py`,
`test_monitoring_writer_single_source.py`, `test_monitoring_writer_lockfile_candidate.py`,
`tests/agent_replay/test_no_mutation_snapshot.py` — 138 passed, 0 failed, none modified.
`git status --porcelain -- agent-monitoring/` confirmed identical before/after the new tool's
real-corpus run (pre-existing dirty state from unrelated in-flight tickets, unchanged by this
tool).

## Files Changed
- `tools/agent-monitoring/retrieval_baseline_metrics.py` (new)
- `tests/tools/test_retrieval_baseline_metrics.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (added INFRA-292)

## Completion Summary
Built a new, strictly read-only baseline-metrics report over `agent-monitoring/*.jsonl`
satisfying all 5 acceptance criteria: context-tokens explicitly `"unavailable"` (cited),
follow-up-search-count derived from `tools.jsonl`'s literal `tool` field (cited derivation),
phase-duration always flagged `"pause-contaminated"` (no gap-aware view exists), gate-outcome and
review-rework both computed only from existing `runs.jsonl` fields via imported
`generate_retro.py` helpers and disclosed as "derived proxy, not fabricated", and zero mutation of
`agent-monitoring/*.jsonl` proven by a real-corpus integration test. All logic reuses existing
functions (`_load_runs_and_events`, `load_jsonl`, `_resolve_status`, `_is_gate_fail`,
`classify_provenance`, `_assert_safe_output_path`) — no reimplementation, no modification to any
of `generate_retro.py`/`validate.py`/`manifest.py`/`legacy_reader.py`/`vocabulary.py`/
`cost_proxy.py`. Parity ledger entry `INFRA-292` added. Ready to move to `tickets/done/`.
