---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261022-PERF-EVENT-RECORDER-AND-EVENT-CONSTRUCTION-REMEASURE
phase: done
date: 2026-10-22
tags: [performance, observability, benchmarking]
---

# TCK-20261022-PERF-EVENT-RECORDER-AND-EVENT-CONSTRUCTION-REMEASURE

## Title
Re-measure H3 (EventRecorder eviction) and H4 (pydantic construction of engine-made events) after #645, then close or hand a fix to rpg

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`docs/performance/tick_cost_growth.md` §3 ranked two observability costs as waste:

- **H3**: `EventRecorder.record` scanned the whole full buffer per event to pick an eviction victim: 42.5 % of
  all samples in the late corpus profile.
- **H4**: pydantic `__init__` on events the engine itself produced, plus `event_shapers.py`: 2 to 14 %
  (`strategic_100`).

Both were profiled before #645 (2026-10-19). #645 replaced the full scan with per-severity counts and
introduced the typed event catalog. The decision on #593 (comment 6338326690, user-approved on #715) is to
re-measure first at P3. Fix H3 only if it is still above about 2 % of the tick, otherwise close it. The same
rule applies to H4. Every §3 share is PROVISIONAL: one loaded 6-vCPU VM and py-spy shares.

This ticket is measurement only. Any fix is rpg's (`src/**`) and is filed by rpg-planner from this ticket's
numbers.

## Scope
- Profile on `main` at or after #645, with `tools/perf/profile_tick.py` and the §3 method, so the before and
  after numbers compare:
  - **H3:** `--world frontier_extended --warmup 600 --ticks 40 --contract pinned`. 600 warmup ticks fill
    the 5000-event buffer; §7 item 6 says early ticks hide H3.
  - **H4:** `--scenario strategic --entities 100 --warmup 10 --ticks 40 --contract pinned`.
  - `py-spy` sampler at the §3 rate, 3 runs per workload, run serially.
- Report the inclusive share of `EventRecorder.record`, including the eviction path, and of
  `pydantic/main.py __init__` reached from engine-made events, plus `event_shapers.py`. Give the median and
  range over the 3 runs, the host load per run and the commit.
- Name the post-#645 eviction code path by file:line. Confirm from the folded stacks that the O(buffer) scan
  is gone, or show where it remains.
- Append a dated "Re-measure after #645" note to `tick_cost_growth.md` §3 under the H3 and H4 rows. Keep the
  original numbers and mark them as pre-#645.
- Verdict per item: **CLOSE** (≤ 2 % of the tick) or **FIX** (> 2 %, with the call site and the share). Post
  it on #593 for rpg-planner.

## Out of Scope
- Any `src/**` change, including the deque/ring-buffer fix and `model_construct` (rpg's, after v1).
- Baselines or tripwire references: nothing here is promoted.
- H1, H2 and H5 (rpg / Lane B), and T3 `no_replay` (ruled on #593, implemented by rpg or testing).
- Replay-on cost (measured by `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`).

## Acceptance Criteria
- [x] 3 runs × 2 workloads on main at or after #645, taken in a lead-granted quiet slot (loadavg1 < 1.5,
      ≥ 2.5 GB available, `systemd-run` MemoryMax=3G / MemorySwapMax=0, one at a time, foreground). The
      load is recorded per run.
- [x] H3 and H4 inclusive shares reported as median and range, with commit, host and contract. Labelled
      PROVISIONAL (shares, single host).
- [x] The post-#645 eviction path is cited by file:line, with folded-stack evidence for or against a
      remaining O(buffer) step.
- [x] `tick_cost_growth.md` §3 has the dated re-measure note. The pre-#645 numbers are kept and labelled.
- [x] A CLOSE or FIX verdict per item is posted on #593 with the numbers. A FIX verdict names the call site
      for rpg.
- [x] Profiles stay under `reports/perf/tick_cost_remeasure/` (git-ignored) and are summarised in the
      ticket. Run data is cleaned by run id.

## Related Tickets
- `TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION` (#597): the source of H3 and H4.
- #645: per-severity eviction counts and the typed event catalog.
- `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`: the method precedent for a single-question profile.

## Related Docs
- `docs/performance/tick_cost_growth.md` §3, §7 item 6, §8.
- `docs/plans/architecture/faster_feature_testing_draft_tickets.md` (H3/H4 drafts, #719).
- `docs/engine/performance_contract.md` (claims language).

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION/`

## Related Code Areas
- `src/observability/event_recorder.py` (read only)
- `src/observability/event_shapers.py` (read only)
- `tools/perf/profile_tick.py`

## Assumptions / Open Questions
- The profiles may run in a branch during the v1 freeze. Only the doc note merges, and it touches no `src/`.
- 2 % is the decision's threshold. It applies to the median share. If the range straddles 2 %, report
  FIX-BORDERLINE and leave the call to rpg-planner.

## Implementation Notes
Six serial runs (H3 x3, H4 x3) at commit `3b5c7b473` (main `81b387aa8`, contains #645), each started at loadavg1 below 1.5 with at least 3.6 GB available, under `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`. No timeout or OOM. Inclusive shares of kept py-spy samples, runs 1 / 2 / 3:
- H3 `EventRecorder.record` on `frontier_extended`: 0.69 / 0.76 / 0.56 %, median 0.69 % (was 42.5 %). **CLOSE.**
- H4 on `strategic_100`: `event_shapers.py` 0.97 / 1.59 / 1.18 %, median 1.18 %; pydantic `__init__` under the event path 0.44 / 0.71 / 0.65 %, median 0.65 %. **CLOSE.**
- Observation: `frontier_extended` `event_shapers.py` is 2.41 / 4.84 / 3.74 %, median 3.74 %, with only 0.75 % pydantic `__init__`; not a `model_construct` target, left to rpg-planner.
Eviction path and the full table are in `docs/performance/tick_cost_growth.md` section 3, "Re-measure after #645". Raw folded stacks stay in the git-ignored `reports/perf/tick_cost_remeasure/`. The verdict posts on #593 through perf-planner.

## Test Summary
Measurement only; no code changed, so no tests. Frontmatter validated by the closure checks.

## Files Changed
- `docs/performance/tick_cost_growth.md` (dated re-measure note under section 3)
- this ticket

## Completion Summary
H3 and H4 both CLOSE by the 2 % rule; evidence in the doc note.
