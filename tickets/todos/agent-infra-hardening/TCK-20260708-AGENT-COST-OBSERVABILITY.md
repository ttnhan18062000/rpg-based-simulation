---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-AGENT-COST-OBSERVABILITY
phase: open
date: 2026-07-08
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260708-AGENT-COST-OBSERVABILITY

## Title
Agent spend proxy — Tier 1 `cost_proxy_score` from existing tools.jsonl data, surfaced as spend-by-phase/spend-by-agent in the retro report

## Status
OPEN

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
(fill during Plan/Implement)

## Test Summary
(fill during Test)

## Files Changed
(fill during Implement)

## Completion Summary
(pending)
