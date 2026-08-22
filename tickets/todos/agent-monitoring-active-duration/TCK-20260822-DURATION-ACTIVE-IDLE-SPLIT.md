---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT
phase: open
date: 2026-08-22
tags: [agent-monitoring, data-quality, documentation]
---

# TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT

## Title
Compute active/idle duration split for Slow Runs and Duration outliers reporting

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
runs.jsonl's duration_s and generate_retro.py's Slow Runs / Duration outliers sections currently report naive wall-clock duration with no awareness of idle gaps between phase transitions, which distorts what counts as a "slow" run. This ticket adds a single shared tools/agent-monitoring/duration_utils.py that computes active_duration_s and idle_gap_s at read time from a run's events.jsonl rows (ordered strictly by timestamp, never seq, since seq resets across pause/resume sessions), and wires both Slow Runs and Duration outliers to render the split alongside raw duration_s. Real corpus inspection this session found the gap distribution is heavier-tailed than assumed (p50=205s, p75=457s, p90=19min, p95=43.5min, p99=413.5min across 5960 gaps), and that today's top-ranked Slow Runs rows are actually dominated by a run-start-to-first-event gap rather than a mid-run inter-event gap as originally assumed -- so the ticket must make an explicit, stated scoping decision about whether duration_utils.py treats start_ts/end_ts as timeline endpoints or only measures strict inter-event gaps, rather than deriving it as settled fact. This ticket also absorbs the doc-update scope originally filed separately as C3, since C3's content was verbatim-lifted from the same idea doc's own table and added nothing beyond this ticket's own natural doc-update work (schema.md disclosure of the naive-duration limitation and a rendered disclaimer in generate_retro.py's output).

## Scope
- Create tools/agent-monitoring/duration_utils.py as the single shared pure computation (active_duration_s, idle_gap_s, largest-gap phase boundary), ordering events strictly by ts.
- Choose and explicitly document a pause threshold, seeded by this session's real gap-distribution data (p90=19min/p95=43.5min as the data-backed starting candidate range), noting it as a judgment call, not derived law.
- Make an explicit scoping decision, stated in the ticket, on whether start_ts/end_ts run boundaries count toward idle_gap_s or only strict inter-event gaps do -- given today's top Slow Runs rows are dominated by start-to-first-event gaps.
- Wire generate_retro.py's Slow Runs section (around L1107-1146) and Duration outliers section, plus their markdown render (L1669-1704), to import duration_utils.py and display active_duration_s/idle_gap_s alongside raw duration_s.
- Explicitly address the retrieval_baseline_metrics.py trip-wire test (test_baseline_report_would_prefer_gap_aware_view_if_available): either update build_duration_section to consume the new shared view, or explicitly declare that consumer out of scope with the now-red canary documented as expected/tracked.
- Handle events.jsonl rows with missing/non-string ts by skipping them explicitly, not crashing.
- Update docs/agent-monitoring/schema.md's "### What is not recorded" subsection with a new bullet disclosing duration_s's naive-wall-clock limitation, in the same voice as the existing Token-counts bullet, cross-referencing active_duration_s/idle_gap_s by name.
- Add a visible note in generate_retro.py's rendered Slow Runs/Duration outliers sections distinguishing active vs idle time for any run whose reported duration is dominated by an idle gap, matching the existing conditional-disclaimer style used for the outlier-ratio caveat.
- Add/extend tests: duration_utils.py unit tests (including a seq-collision case), generate_retro.py rendering tests, and whatever retrieval_baseline_metrics.py change (or explicit deferral) is chosen.

## Out of Scope
- Full re-ranking of the Slow Runs table by active_duration_s instead of raw duration_s -- investigation recommends additive/flagging as the safer default; re-ranking changes the historical meaning of "slow" across all past reports and is deferred as a future decision.
- Rewriting existing historical agent-monitoring/retro/RETRO-*.md reports.
- Any write-path mutation of runs.jsonl or events.jsonl -- duration_utils.py is a pure read-time computation only, per the append-only/audited-correction constraint.
- Dashboard-side changes (models.py, api.ts, StatsView.tsx) -- those belong to the sibling dashboard ticket, sequenced behind this one.

## Acceptance Criteria
- [ ] tools/agent-monitoring/duration_utils.py exists, exporting a pure function taking a run's start_ts/end_ts plus its events.jsonl rows (sorted by ts, not seq) and returning active_duration_s + idle_gap_s (per chosen pause threshold) that sum to the run's total wall-clock span, plus which phase boundary the largest gap fell at.
- [ ] generate_retro.py's Slow Runs and Duration outliers sections both import and call that single shared function, rendering active_duration_s/idle_gap_s alongside raw duration_s in both tables.
- [ ] Running updated retro generation against real corpus data reproduces the documented finding for TCK-20260710-SIMQ-DEPTH-SOCIAL (idle_gap_s captures the ~590.6 min Investigate->Plan gap, active_duration_s materially smaller than raw 828 min duration_s).
- [ ] Given events with a seq collision, duration_utils.py still produces a correct non-negative split because it orders strictly by ts.
- [ ] test_baseline_report_would_prefer_gap_aware_view_if_available is explicitly addressed -- either retrieval_baseline_metrics.build_duration_section is updated to consume the new shared view, or the ticket explicitly declares that consumer out of scope and documents the now-red canary as expected/tracked.
- [ ] docs/agent-monitoring/schema.md's "### What is not recorded" subsection (not the unrelated "## Known Limitations" H2) gains a new bullet disclosing duration_s's naive-wall-clock limitation, in the same voice as the existing Token-counts bullet, cross-referencing the new active/idle fields by name.
- [ ] generate_retro.py's rendered Slow Runs/Duration outliers sections carry a visible note distinguishing active vs idle time for any run whose reported duration is dominated by an idle gap, matching the existing conditional-disclaimer style already used for the outlier-ratio caveat.
- [ ] Existing historical agent-monitoring/retro/RETRO-*.md reports are explicitly NOT rewritten by this ticket.

## Related Tickets
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC
- TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
- TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG
- TCK-20260810-MONITORING-NEGATIVE-DURATION-BULK-CLEANUP
- TCK-20260822-DASHBOARD-DURATION-GAP-AWARE

## Related Docs
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/retrieval_baseline_metrics.py
- docs/agent-monitoring/schema.md
- docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md
- agent-monitoring/runs.jsonl
- agent-monitoring/events.jsonl
- expected: tools/agent-monitoring/duration_utils.py

## Assumptions / Open Questions
- No single "obviously correct" pause threshold exists in the data; 30-60 min (~p90-p95) is a reasonable data-backed starting candidate but remains a judgment call, not derived law.
- Whether duration_utils.py treats start_ts/end_ts as timeline endpoints or only strict inter-event gaps materially changes idle attribution for the highest-ranked Slow Runs rows and needs an explicit scoping decision during planning.
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC has two runs.jsonl records for the same run_id with conflicting start_ts (one plausible, one a suspicious 00:00:00Z placeholder) -- affects that row's ranking regardless of chosen approach.
- TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG's run shows 6 perfectly-equal 3994s gaps between consecutive events, a suspicious evenly-spaced pattern possibly indicating fabricated/interpolated timestamps; duration_utils.py cannot and is not expected to distinguish real pauses from this.
- 66 events.jsonl rows in the current corpus have missing/non-string ts and must be skipped/handled explicitly, not crashed on.
- Implementing duration_utils.py will flip the retrieval_baseline_metrics.py trip-wire test red by design; this must be resolved in-ticket per its own acceptance criterion.
- The idea doc's own open question (flag high-idle runs vs. fully re-rank Slow Runs by active_duration_s) remains unresolved beyond this ticket's additive/flagging choice.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
