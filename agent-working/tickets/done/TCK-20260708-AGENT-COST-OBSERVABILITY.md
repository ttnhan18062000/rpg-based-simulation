---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-AGENT-COST-OBSERVABILITY
phase: done
date: 2026-07-08
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260708-AGENT-COST-OBSERVABILITY

## Title
Agent spend proxy — Tier 1 `cost_proxy_score` from existing tools.jsonl data, surfaced as spend-by-phase/spend-by-agent in the retro report

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implements Tier 1 (and optionally Tier 2) of `docs/plans/agent_infrastructure/idea_agent_cost_observability.md`. Real token/cost data is platform-blocked (`agent()` doesn't forward `input_tokens`/`output_tokens` to workflow scripts), but `tools.jsonl` already has `duration_ms` per tool call joined to `events.jsonl` by `run_id`+`seq` — enough to compute a comparable, monotonic (not dollar-denominated) proxy score today. This closes the audit's Recommendation #2 and the only remaining unaddressed observability gap from the 2026-07-03 audit.

## Scope
- Compute `cost_proxy_score` per event in `writeMonitoring` from existing `tools.jsonl` data: weighted sum of Bash `duration_ms`, nested `Agent`-tool spawn count, and Read/Edit/Write/MultiEdit call count (formula per idea doc)
- Add the field as an addition to `events.jsonl`'s schema, documented in `docs/agent-monitoring/schema.md` as an explicit proxy (not disguised as real usage data) — `agent-monitoring/README.md`'s "What It Does NOT Capture" section keeps token counts listed as still-not-captured
- Add a spend-by-phase / spend-by-agent breakdown section to `make agent-monitoring-retro`'s generated report
- (Stretch, only if Tier 1 lands cleanly) Tier 2: optional `self_reported_scope` field on an agent's structured return, same trust ceiling as the existing free-text `summary` field

## Out of Scope
- Tier 3 (real token/cost telemetry) — platform-blocked, no action possible from this repo alone
- Any model-routing policy decision — this ticket only produces the evidence base; routing is a separate, later decision
- Backfilling `cost_proxy_score` onto historical events — only new writes gain the field

## Acceptance Criteria
- `writeMonitoring` computes and writes `cost_proxy_score` for every new event
- `docs/agent-monitoring/schema.md` documents the field's formula and explicitly labels it a proxy
- `make agent-monitoring-retro`'s report includes a spend-by-phase and spend-by-agent breakdown table
- If Tier 2 is attempted: `self_reported_scope` is optional, does not break existing callers that omit it
- Tests cover: proxy score computation against a fixture `tools.jsonl`, retro report breakdown generation against fixture events

## Related Tickets
Parent: TCK-20260708-AGENT-INFRA-HARDENING-EPIC. Depends on (vocabulary must be clean before phase-breakdown is meaningful): TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT. References `verified_by` field from (done): TCK-20260705-GATE-DET-DONE-CHECKER et al. **Concurrent file-overlap notice**: `TCK-20260708-RETRO-TAG-BREAKDOWN` (`tickets/todos/tag-vision-followups/`, may be implemented concurrently in a different session) also adds a new report section to `generate_retro.py`'s `generate()` and may touch `tests/tools/test_generate_retro.py`. No design overlap (different breakdown axes), but whichever lands second should rebase its section-insertion point against the other's diff.

## Related Docs
docs/plans/agent_infrastructure/idea_agent_cost_observability.md, docs/agent-monitoring/schema.md, docs/agent-monitoring/README.md, docs/guides/agent_monitoring.md

## Related Stored Artifacts
none yet

## Related Code Areas
.claude/workflows/implement-ticket.js (writeMonitoring), tools/agent-monitoring/generate_retro.py

## Assumptions / Open Questions
- Assumes a unitless proxy score is actionable without a per-model $/call constant — Investigate phase should size this against real retro use cases before committing to the full formula, per the idea doc's own Open Question.
- Weights (`w_bash`, `w_agent`, `w_edit`) are placeholders in the idea doc — Plan phase must pick concrete starting values and note they're calibratable, not load-bearing precision.

## Implementation Notes

Implemented Steps 1-5 of `staging_artifacts/TCK-20260708-AGENT-COST-OBSERVABILITY/plan.md` exactly
as specified; Step 6 (Tier 2 `self_reported_scope`) was deferred (see below).

- **Step 1**: Created `tools/agent-monitoring/cost_proxy.py` — pure `compute_cost_proxy_score(tool_rows)`
  function with `W_BASH=0.001`, `W_AGENT=50`, `W_EDIT=1` module constants, no file I/O, no other
  imports. Matches the plan's formula verbatim (Bash duration_ms sum, Agent spawn count, edit-tool
  call count).
- **Step 2**: Widened `writeMonitoring`'s Step 2 Python one-liner in
  `.claude/workflows/implement-ticket.js` (now inside `pushEvent`'s surrounding prompt template,
  around lines 202-231) to build `rows_by_seq` alongside the existing `counts` `Counter` in the same
  single pass over `agent-monitoring/tools.jsonl`, then compute `scores` via
  `cost_proxy.compute_cost_proxy_score` (imported via `sys.path.insert(0, 'tools/agent-monitoring')`).
  Result saved as `TOOL_STATS` (`{"counts": ..., "scores": ...}`) instead of the old bare
  `TOOL_COUNTS`. Step 3's instructions now also set `cost_proxy_score` per event from
  `TOOL_STATS["scores"][str(event.seq)]`, defaulting to `0.0` if absent. No second read of
  `tools.jsonl` was added. Verified with `node --check` (syntax OK) and by extracting the embedded
  Python snippet and running it standalone against a fake run_id (returns `{"counts": {}, "scores": {}}`
  for no matches, confirming no crash on the empty case).
- **Step 3**: Added `test_cost_proxy_score_field_written_to_events_jsonl` to
  `tests/tools/test_record_events.py` as a new standalone module-level test (not nested inside
  `TestVocabularyWarning`, to keep that class scoped to vocabulary-warning behavior only). Proves
  `record_events.py` persists the additive `cost_proxy_score` field with zero changes to that
  script's source. `record_events.py` itself was not touched.
- **Step 4**: Documented `cost_proxy_score` in `docs/agent-monitoring/schema.md` (new Fields-table
  row after `reason_code`, plus a new `### cost_proxy_score — proxy formula and interpretation`
  subsection covering the formula, current weights, the count-not-sum-Agent-duration rationale, and
  both known limitations called out in the plan). Added one bullet to
  `docs/agent-monitoring/README.md`'s "What It Captures" section; "What It Does NOT Capture" was not
  touched (token counts remain listed there).
- **Step 5**: Added a `## Spend Proxy — By Phase` / `## Spend Proxy — By Agent` breakdown to
  `tools/agent-monitoring/generate_retro.py`'s `generate()`, inserted immediately after `## Agent
  Status Distribution`'s closing `lines.append("")` and before `## Summary Quality`, using a
  filter-then-aggregate pattern (`scored_events = [e for e in events if e.get("cost_proxy_score") is
  not None]`) that excludes events missing the field rather than coercing to 0. Section is omitted
  entirely when `scored_events` is empty. Added 4 new tests to `tests/tools/test_generate_retro.py`:
  basic by-phase aggregation, basic by-agent aggregation, empty/all-missing-field omission, and a
  placement test confirming section ordering (`Tag Breakdown — Subsystem/Topic` <
  `Tag Breakdown — Process/Skill-signal` < `Agent Status Distribution` < `Spend Proxy — By Phase` <
  `Spend Proxy — By Agent` < `Summary Quality`) with all 11 pre-existing tests in that file passing
  unmodified.
- **Step 6 (Tier 2, `self_reported_scope`) — DEFERRED.** Steps 1-5 landed cleanly and all tests pass,
  but Tier 2 was explicitly optional/stretch per the ticket's own framing ("not required for this
  ticket's Definition of Done"). Wiring an optional self-reported field through `pushEvent` would
  require touching every phase's agent-prompt call site across `implement-ticket.js` to have agents
  actually populate it, which is a materially larger and separately-reviewable change than the
  Tier 1 scope covered here. Deferring keeps this ticket's diff focused and auditable; a follow-up
  ticket can pick up Tier 2 independently if the retro data from Tier 1 motivates it.

Test results: `tests/tools/test_cost_proxy.py` (3 passed), `tests/tools/test_record_events.py`
(16 passed, 1 new), `tests/tools/test_generate_retro.py` (15 passed, 4 new), plus a combined run
alongside `test_record_run.py`, `test_validate_agent_monitoring.py`, `test_tag_report.py` (61 passed
total) — all via `.venv/bin/python3 -m pytest` per the investigation's noted requirement (system
`/usr/bin/python3` lacks `pydantic` and can't collect `tests/conftest.py`).

No `src/` file was touched. No `docs/parity_ledger/*.yaml` file was touched. `record_events.py`'s
`REQUIRED` set, `record_run.py`, `vocabulary.py`, and both already-landed Tag Breakdown blocks in
`generate_retro.py` were left untouched, per the plan's Scope Guards.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_cost_proxy.py tests/tools/test_record_events.py tests/tools/test_generate_retro.py tests/tools/test_record_run.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_tag_report.py -v` — 61 passed, 0 failed. New coverage: `test_cost_proxy.py` (3 tests — formula correctness, null-duration handling, empty-group), `test_record_events.py` (+1 — additive field pass-through with zero source changes), `test_generate_retro.py` (+4 — by-phase aggregation, by-agent aggregation, missing-field-excluded-not-zeroed, section-placement non-disturbance of the Tag Breakdown sections). No coverage gaps (docs-only changes have no executable surface).

## Files Changed
- `tools/agent-monitoring/cost_proxy.py` (new)
- `tests/tools/test_cost_proxy.py` (new)
- `.claude/workflows/implement-ticket.js`
- `tests/tools/test_record_events.py`
- `docs/agent-monitoring/schema.md`
- `docs/agent-monitoring/README.md`
- `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_generate_retro.py`

## Completion Summary
Implemented Tier 1 of the cost-observability idea doc: `cost_proxy_score`, a monotonic unitless proxy computed from existing `tools.jsonl` data (weighted Bash `duration_ms` + Agent-spawn count + edit-tool-call count, weights `W_BASH=0.001`/`W_AGENT=50`/`W_EDIT=1`), is now computed in `writeMonitoring`'s existing single pass over `tools.jsonl` and written additively to `events.jsonl` with zero changes to `record_events.py`. The field is documented in `docs/agent-monitoring/schema.md` as an explicit non-dollar proxy, and `make agent-monitoring-retro`'s report now includes spend-by-phase and spend-by-agent breakdown tables that exclude (never zero-coerce) events lacking the field. All 4 acceptance criteria for Tier 1 are met; 61 tests pass with no regressions in the surrounding agent-monitoring test surface (including the concurrently-landed `TCK-20260708-RETRO-TAG-BREAKDOWN` Tag Breakdown sections, confirmed undisturbed).

Tier 2 (`self_reported_scope`) was deferred, not ticketed as a follow-up: the ticket's own Scope framed it as "stretch, only if Tier 1 lands cleanly," and there is no concrete retro use case yet demanding it — per this repo's Uncertainty Rule, a vague future benefit doesn't warrant opening a ticket today. It remains available as a natural pickup for whoever next revisits `docs/plans/agent_infrastructure/idea_agent_cost_observability.md` once Tier 1's spend-by-phase/by-agent data has actually been used in a retro and either does or doesn't motivate self-reported scope.
