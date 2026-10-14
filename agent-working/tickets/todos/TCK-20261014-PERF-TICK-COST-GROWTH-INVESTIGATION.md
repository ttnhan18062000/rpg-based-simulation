---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION
phase: open
date: 2026-10-14
tags: [performance, benchmarking, regression]
---

# TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION

## Title
Find where the tick cost grew since May: per-phase and per-call-site attribution on the scenarios that leave NORMAL under the canonical contract

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
PERF-M2-T08 (#591) re-ran the baselines under the canonical variants and found two things.
- **The tick cost has grown a lot.** `idle_100_local` went from 1.0 ms (May) to 36-62 ms, and `strategic_100_local` from 13 ms to 496 ms. The tick now runs about 30 phases, with cooperation (30-260 ms), advancement (40-100 ms in corpus worlds), resolution_overhead (35-100 ms) and combat_engagement (28-43 ms) on top.
- **Six records leave NORMAL deterministically under the canonical contract,** so they cannot be baselines: `strategic_100_*`, `mixed_200_*`, `simq_corpus_frontier_extended`, `simq_corpus_frontier_marches`.

The owner chose option **(ii), investigate first** (2026-10-14, via lead-planner). Find out where the cost is and whether it is legitimate work. A larger-budget canonical profile (option i) comes only if the cost turns out to be legitimate. rpg owns the fixes in `src/` (#593 asks rpg for a lane contact and timing relative to M0). This ticket is the **measurement side only**: attribution, evidence and a ranked hand-off. It changes no `src/` outside `src/perf/`.

## Scope
1. **Fixed work, so profiles compare.** Profile under fixed budgets (audit_mode / pinned NORMAL, the outcome contract in the PERF-D1 ruling on #585, approved by the owner 2026-10-14) as well as under the canonical variant. A shift in governor mode must not change what work is being compared. Record which contract each profile used.
2. **Scenarios:**
   - `strategic_100`, `mixed_200` (140 entities in the state; note the naming mismatch);
   - `simq_corpus_frontier_extended`, `simq_corpus_frontier_marches`;
   - `idle_100` (the smallest, the floor-cost reference);
   - `combat_10` plus the movement[5000] case from `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`. First establish whether that ticket's 3.2-16 s/tick and T08's 28-43 ms measure the same scenario and scale.
3. **Tools:** use `tools/perf/profile_tick.py` (py-spy, per-phase context) and `tools/perf/profile_diff.py`. Extend `profile_tick.py` to corpus worlds by reusing `tools/perf/rerun_baselines.py`'s loader (lands with #591). Do not write a third loader.
4. **Then-vs-now:** where a pre-growth commit still builds, profile the same scenario at that commit (May baseline era, and `c84352465` / `132bf09ca` for the combat step) with `profile_diff.py`. If an old commit no longer runs, say so. Do not reconstruct it.
5. **Fold in the held cost tickets** as hypotheses to confirm or refute with call-site evidence:
   - `TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED`: is `fingerprint()` called outside audit mode at `kernel.py:664` (REFINED_UPDATE whenever `replay_allowed`) or `:1096`, and what is its share?
   - `TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED`: is any trace-write cost on the tick thread, or only on the `QueueDrainWorker`? If none is on the tick thread, close it as not-a-tick-cost.
   - `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`: the `is_hostile_compat` → `project_relation` share. The fix stays with rpg Lane B.
   Close or update each one from this ticket's evidence.
6. **Memory:** attribute the peak RSS of `frontier_extended` (1703 MB) and `frontier_marches` (1568 MB) on a profile that declares 512 MB, using `tools/perf/profile_memory.py` or memray. Report whether anything checks a profile's declared memory, and propose a check if not (perf-owned).
7. **Output:** `docs/performance/tick_cost_growth.md`, containing:
   - the per-scenario phase table;
   - the top call sites with their share and the evidence (folded-stack excerpts);
   - for each hotspot, whether it is legitimate work (and why) or waste;
   - a ranked hand-off list for rpg with the file, function and expected saving;
   - the inputs for the (i) decision: what budget the legitimate work needs.

## Out of Scope
- Any fix in `src/` outside `src/perf/` (rpg owns the fixes, through #593).
- Changing a canonical profile's budget (option i: an owner decision, after this ticket).
- Re-recording baselines (the follow-up `TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES`).
- The PERF-D1 default flip itself (rpg plans it; perf reviews the measurement side).

## Acceptance Criteria
- AC1: Every scenario in Scope 2 has a profile under fixed budgets and one under canonical. Each profile records its host, CPU, loadavg, main sha and contract.
- AC2: The phase share of every phase above 5% of the tick is attributed to named call sites, with folded-stack evidence.
- AC3: Each of the three folded-in tickets is closed or updated with evidence (closes are checked by perf-planner).
- AC4: The movement[5000] vs combat_10 discrepancy is resolved: either the same scenario with an explained difference, or different scenarios, stated.
- AC5: `tick_cost_growth.md` exists with a ranked rpg hand-off list, and lead-planner can post it to #593.
- AC6: The RSS-over-profile finding is attributed, and a declared-memory check is proposed or filed.
- AC7: Resource rule followed: heavy local runs go one at a time in the foreground under `systemd-run --user --scope -p MemoryMax=... -p MemorySwapMax=0`, and lead-planner is told before any run expected to exceed about 3 GB. py-spy's own overhead is noted.

## Related Tickets
- TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (#591): the source finding
- TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED, TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED, TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP (folded in)
- TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED (closed; its A/B per-phase table is the starting evidence)
- TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES (re-records once the cost is understood)
- Issues #593 (rpg lane and timing), #585 (PERF-D1), #558 (triage)

## Related Docs
- docs/performance/baseline_invalidation_ledger.md (T08 rows), docs/performance/phase_inventory.md, docs/performance/hash_callsite_inventory.md
- docs/engine/performance_contract.md section 3.1 (a non-NORMAL run is not a baseline)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS/ (evidence.md, investigation.md: mode counts and per-phase top costs)

## Related Code Areas
- tools/perf/profile_tick.py, profile_diff.py, profile_memory.py, rerun_baselines.py
- src/perf/scenarios.py (read-only here)
- hot paths named by the folded-in tickets (read-only here): src/core/state.py::fingerprint, src/engine/kernel.py, src/observability/cognition/decision_trace_writer.py, src/domains/combat_engagement/phase.py, src/domains/cooperation/

## Assumptions / Open Questions
- A1: Fixed-budget (pinned NORMAL) runs are possible from `tools/perf` without a `src/` change, through audit_mode or the PinnedNormalGovernor test helper. If neither is reachable from tools, stop and report. Do not edit `src/`.
- Q1 (rpg, via #593): which lane receives the hand-off, and is there an M0 freeze window that bounds when fixes can land?

## Implementation Notes
(to be filled)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(to be filled)
