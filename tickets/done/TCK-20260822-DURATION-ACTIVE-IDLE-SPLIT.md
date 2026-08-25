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
DONE

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
- [x] tools/agent-monitoring/duration_utils.py exists, exporting a pure function taking a run's start_ts/end_ts plus its events.jsonl rows (sorted by ts, not seq) and returning active_duration_s + idle_gap_s (per chosen pause threshold) that sum to the run's total wall-clock span, plus which phase boundary the largest gap fell at.
- [x] generate_retro.py's Slow Runs and Duration outliers sections both import and call that single shared function, rendering active_duration_s/idle_gap_s alongside raw duration_s in both tables.
- [x] Running updated retro generation against real corpus data reproduces the documented finding for TCK-20260710-SIMQ-DEPTH-SOCIAL (idle_gap_s captures the ~590.6 min Investigate->Plan gap, active_duration_s materially smaller than raw 828 min duration_s).
- [x] Given events with a seq collision, duration_utils.py still produces a correct non-negative split because it orders strictly by ts.
- [x] test_baseline_report_would_prefer_gap_aware_view_if_available is explicitly addressed -- either retrieval_baseline_metrics.build_duration_section is updated to consume the new shared view, or the ticket explicitly declares that consumer out of scope and documents the now-red canary as expected/tracked.
- [x] docs/agent-monitoring/schema.md's "### What is not recorded" subsection (not the unrelated "## Known Limitations" H2) gains a new bullet disclosing duration_s's naive-wall-clock limitation, in the same voice as the existing Token-counts bullet, cross-referencing the new active/idle fields by name.
- [x] generate_retro.py's rendered Slow Runs/Duration outliers sections carry a visible note distinguishing active vs idle time for any run whose reported duration is dominated by an idle gap, matching the existing conditional-disclaimer style already used for the outlier-ratio caveat.
- [x] Existing historical agent-monitoring/retro/RETRO-*.md reports are explicitly NOT rewritten by this ticket.

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
Two open judgment calls resolved and documented (see staging_artifacts/.../investigation.md for
full reasoning):
1. **Pause threshold = 1800s (30 min)** — reuses generate_retro.py's own existing Slow Runs
   absolute threshold verbatim, for conceptual consistency; falls inside the ticket's own p90-p95
   data-backed range.
2. **start_ts/end_ts ARE included as timeline boundaries**, not just strict inter-event gaps —
   forced by the module's own active+idle==total invariant, which a boundary-adjacent gap would
   otherwise silently vanish from. `active_duration_s` is defined as the complement of
   `idle_gap_s` within the known total span (not independently re-summed), so the invariant holds
   by construction regardless of data messiness.

Verified by hand against the real corpus before trusting the unit test: `TCK-20260710-SIMQ-DEPTH-SOCIAL`'s
10 events broken into individual gaps confirm exactly 4 gaps (Plan 590.58min, Architecture-Verify
80.75min, Parity 36.1min, Finalize 105.85min) sum to the computed `idle_gap_s` (813.28min), and
the remaining 5 small gaps sum to `active_duration_s` (15.53min) — matches AC3 exactly.

Corrected one inaccuracy in ticket 2's own text while investigating the shared-shape coupling: it
claims `SlowRunEntry(**r)`-style unpacking "breaks outright" on new keys — empirically false, since
`src/api/agent_ops_dashboard/models.py`'s Pydantic models declare no `extra="forbid"`, so Pydantic's
default `extra="ignore"` silently drops unrecognized kwargs rather than raising.
`tests/tools/test_agent_ops_dashboard_stats.py` (17/17) already confirmed no regression before
ticket 2 begins. Flagged for ticket 2's own Investigate phase to re-verify and correct, not
silently trusted from the original ticket text.

The retired trip-wire test (`test_baseline_report_would_prefer_gap_aware_view_if_available`) is
replaced, not deleted — a real positive assertion now confirms `build_duration_section` actually
imports and calls the shared `duration_utils.compute_active_idle_split`, mirroring this repo's own
established precedent for retiring served-their-purpose trip-wire guards.

## Test Summary
- `pytest tests/tools/test_duration_utils.py -q` → 13 passed (new file).
- `pytest tests/tools/test_generate_retro.py -q` → 160 passed (156 pre-existing + 4 new).
- `pytest tests/tools/test_retrieval_baseline_metrics.py -q` → 18 passed (16 pre-existing,
  unmodified + 2 rewritten for the new real-computation shape).
- Broader surface: `pytest tests/tools/test_duration_utils.py tests/tools/test_generate_retro.py
  tests/tools/test_retrieval_baseline_metrics.py tests/docs/ -q` → 236 passed, 1 skipped,
  1 xfailed (pre-existing, unrelated).
- `pytest tests/tools/test_agent_ops_dashboard_stats.py -q` → 17 passed (confirms the sibling
  dashboard ticket's own consumer is not broken by this ticket's additive shape change, ahead of
  that ticket even starting).

## Files Changed
- `tools/agent-monitoring/duration_utils.py` (new) — shared pure active/idle computation.
- `tools/agent-monitoring/generate_retro.py` — imports and wires `compute_active_idle_split` into
  `compute_retro_metrics()`'s Slow Runs/Duration outliers construction and their Markdown
  rendering (new columns + conditional idle-dominated disclaimer).
- `tools/agent-monitoring/retrieval_baseline_metrics.py` — `build_duration_section(runs, events)`
  now computes a real per-row split instead of an unconditional static flag; caller updated.
- `docs/agent-monitoring/schema.md` — new "What is not recorded" bullet on `duration_s`'s
  naive-wall-clock limitation.
- `tests/tools/test_duration_utils.py` (new) — 13 unit tests.
- `tests/tools/test_generate_retro.py` — 4 new rendering tests.
- `tests/tools/test_retrieval_baseline_metrics.py` — 1 test rewritten for the real shape, the
  trip-wire test retired and replaced with a real positive assertion.
- `docs/parity_ledger/infrastructure.yaml` — new entry `INFRA-394` (renumbered from `INFRA-392`
  after merging `origin/main` independently landed an unrelated entry already claiming that id).

## Completion Summary
Added `tools/agent-monitoring/duration_utils.py` as the single shared, pure, read-time
active/idle duration computation, resolving both judgment calls the ticket flagged as open
(pause threshold, start/end-boundary treatment) with documented reasoning. Wired additively into
`generate_retro.py`'s Slow Runs and Duration outliers sections and into
`retrieval_baseline_metrics.py`'s one-off snapshot, retiring that module's trip-wire test with a
real positive replacement. Real-corpus reproduction for `TCK-20260710-SIMQ-DEPTH-SOCIAL` confirmed
exact by hand before trusting the automated test. No write-path mutation of `runs.jsonl`/
`events.jsonl`; no historical `RETRO-*.md` rewritten; no dashboard file touched (sibling ticket 2's
scope) — confirmed via `git status --short` matching the ticket's own scope exactly. Ticket 2's
own claim about the dashboard coupling being an outright break was checked and found overstated;
corrected here rather than carried forward silently.
