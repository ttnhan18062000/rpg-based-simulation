---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-SIDECAR-ATTRIBUTION-GAP
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-SIDECAR-ATTRIBUTION-GAP

## Title
23.7% of tool rows carry neither `run_id` nor phase, and `cost_proxy_score` is recorded on only 30.5% of events — every spend table is computed on a fraction of real volume

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Measured over the 2026-09-01 → 2026-09-15 window:

| Signal | Value |
|---|---|
| tool rows in window | 50,696 |
| rows with **no `run_id`** | 12,033 (23.7%) |
| rows with **no phase** | 12,033 (23.7%) |
| rows missing **both** | 12,033 (23.7%) |
| events in window | 1,897 |
| events with a nonzero `cost_proxy_score` | 579 (30.5%) |

The identical counts are not a coincidence — it is the *same* set of rows missing both fields,
landing in a single `<MISSING>` bucket that is by far the largest "run" in the corpus.

**Cause is known and already documented**: `.claude/current_run` is a single shared sidecar file
across all concurrent sessions
(`project_sidecar_cross_session_contamination`, confirmed live 2026-08-24). With several sessions
running simultaneously all week — as happened throughout 2026-09-11→15 — rows written while the
sidecar is absent, stale, or owned by another session cannot be attributed.

**Consequence:** `RETRO-LAST14D.md`'s Spend-Proxy-by-Phase and Spend-Proxy-by-Agent tables are a
*ranking*, not a measure of spend. They cannot answer "what does a ticket cost", which is the
question the cost proxy was built to answer
(`TCK-20260708-AGENT-COST-OBSERVABILITY`). This is also the largest single lever in the epic: fixing
it makes several other reports trustworthy rather than indicative.

## Scope
- Determine why the rows lose attribution: sidecar absent, sidecar owned by another session,
  hook firing outside a run, or interactive (non-workflow) tool calls that legitimately have no run.
  The last case is important — a large share may be *correctly* unattributed, and if so the metric
  should exclude them rather than count them as loss.
- Decide whether per-session sidecar isolation is feasible (a per-session path, a lock, or an
  identifier carried on the hook's own environment) versus accepting a documented floor.
- Make the reports honest either way: if a share of volume is unattributable by design, the spend
  tables should say what they cover rather than presenting a total.

## Out of Scope
- Retroactively attributing historical rows.
- `tool_call_count` disagreeing with actual row counts — that is
  `TCK-20260915-TOOL-CALL-COUNT-MISMATCH`, which may share this cause but must be confirmed, not
  assumed.

## Acceptance Criteria
- [ ] The unattributed rows are classified into "legitimately has no run" versus "lost attribution
      that should have been recorded", with counts for each.
- [ ] A disposition is recorded for the second category: fix, or accept with a documented floor.
- [ ] `generate_retro.py`'s spend sections state their coverage (e.g. "computed over N% of tool
      rows") rather than presenting an unqualified total.
- [ ] Any detector ratchets from the measured baseline; it must not assert zero.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-TOOL-CALL-COUNT-MISMATCH` — probable shared cause
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done) — introduced `cost_proxy_score`
- `TCK-20260911-COST-PROXY-EPIC-TICKETS-RUN-CONFIRMATION` (blocked by design — needs a real
  `implement-epic` run, which must not be triggered artificially)

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/agent-monitoring/schema.md`
- `docs/guides/agent_monitoring.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.claude/current_run` (the shared sidecar)
- `.claude/settings.json` (the `PostToolUse` hook that writes `tools.jsonl`)
- `tools/agent-monitoring/record_events.py` (`compute_tool_stats`)
- `tools/agent-monitoring/generate_retro.py` (spend sections)

## Assumptions / Open Questions
- **A meaningful share of the 12,033 may be correct.** Interactive tool calls outside any workflow
  run have no run to belong to. Do not treat the whole figure as loss before classifying it — that
  would overstate the defect.
- Whether a per-session sidecar is achievable given that the hook has no session identifier is the
  real design question.

## Implementation Notes
Derive from the JSONL shards directly. `monitoring.db` was last built 2026-09-13 and
`generate_retro.py` itself warns about and falls back from a stale index.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
