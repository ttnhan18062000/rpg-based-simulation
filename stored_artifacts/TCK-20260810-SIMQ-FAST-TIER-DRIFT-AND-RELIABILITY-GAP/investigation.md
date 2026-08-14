---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP
phase: investigate
date: 2026-08-10
tags: [simulation-quality, calibration, corpus]
---

# Investigation — TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP

## Finding (1): 12 real REGRESS pillars on 6 previously-unverified worlds

Re-ran `tools/evaluate_simq.py` (fast-tier only, correctly scoped post
`TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK`) — reproduced the identical 12-item REGRESS
list found while verifying that ticket's own fix:

| run_key | pillar(s) |
|---|---|
| crowded_frontier_seed42_200t | COMBAT C→A |
| crowded_frontier_seed456_200t | COMBAT C→A |
| frontier_marches_seed42_200t | COMBAT C→A |
| generated_frontier_3_42_seed42_200t | COMBAT C→A |
| generated_frontier_3_42_seed123_200t | PROGRESSION C→A |
| generated_frontier_3_42_seed456_200t | COMBAT C→A, PROGRESSION C→A |
| simq_scale_stress_seed42_seed42_200t | COMBAT C→A |
| lifecycle_full_coverage_world_seed42_200t | FACTION C→S, ECONOMY C→A, PROGRESSION C→A, SOCIAL C→S |

`quest_dense_frontier` (all 3 seeds) is NOT in this list — a prior draft of the ticket text
mistakenly flagged it as needing re-check; confirmed no REGRESS on any `quest_dense_frontier`
key (its own `test_grade_within_anchor_band` pytest failures are all pre-existing
`[known tick_budget]` noise, unrelated).

**Cause confirmed for all 6 worlds** (not assumed): inspected each world's own
`data/worlds/{name}/resolved/compile_context.json` (or `{name}_seed42/` for
`simq_scale_stress`, whose world directory name differs from its calibration profile prefix) —
every one contains real `legacy_roles` entries mapping monster-archetype role IDs
(raider/leader/predator_hunter/sentinel/alpha) to `MONSTER(=2)`, confirming each was genuinely
affected by SUB-384 and simply never re-run since that fix. Same established pattern as
`TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION`.

**Fixed**: recalibrated all 12 fields in `grade_anchors.json` to their live post-fix values.
Corpus-wide `--dry-run` diff confirms 0 regressions afterward (720 pillars checked).

## Finding (2): FAST-tier watchdog-throttle non-determinism — first confirmed instances

The 2026-08-07 D06 F6 audit's own 18-key/3-trial SLOW-tier (1000t/2000t) reliability sweep
(`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`) found all 18 stable. The FAST tier (<=500t) was
never subjected to the same check. Sampled 6 FAST-tier scenarios, 2-4 independent re-runs each
(identical seed/code):

| run_key | pillar | result |
|---|---|---|
| dungeon_crawl_seed42_500t | (all) | stable, 2/2 identical |
| highland_traverse_seed42_200t | (all) | stable, 2/2 identical |
| hero_guild_routing_seed42_500t | COGNITION | stable within tolerance (212 vs 213 events, <1%) |
| hero_guild_routing_seed456_500t | COGNITION, ECONOMY | stable, 3/3 identical (this was ordinary stale drift, not instability — recalibrated normally, see Finding 1's methodology) |
| simq_routing_test_seed42_500t | PROGRESSION | **unstable**: event_count 10/11/11/10 across 4 runs |
| simq_routing_test_seed42_500t | COGNITION | **unstable**: event_count 194/196/194/193 across 4 runs |
| simq_routing_test_seed123_500t | PROGRESSION | **unstable**: event_count 28/24 across 2 runs |
| simq_routing_test_seed123_500t | COGNITION | stable, 2/2 identical (52 events both) |
| simq_routing_test_seed456_500t | (both) | stable, 2/2 identical (lightly sampled) |
| urban_political_seed456_500t | ECONOMY | **unstable**: event_count 14/17/14 across 3 runs |
| urban_political_seed456_500t | PROGRESSION | **unstable**: event_count 17/19/17 across 3 runs |

**Root cause directly checked, not assumed**: captured full stdout/stderr of a
`simq_routing_test_seed42_500t` re-run — confirmed real `WatchdogTrip` alerts firing repeatedly
starting at tick ~25 (D06 F6's own mechanism, `kernel.py`'s tick-budget watchdog). Watchdog trips
are also confirmed present in the STABLE scenarios (`dungeon_crawl_seed42_500t`,
`urban_political_seed42_500t` from an earlier same-day reproducibility check) — so mere presence
of the watchdog mechanism does not predict instability.

**Pattern identified**: every confirmed-unstable (run_key, pillar) pair has a low absolute event
count for that pillar (10-30 events). A pillar with few real events is disproportionately
sensitive to the watchdog occasionally dropping 1-2 of them near a tick boundary — the same
mechanism, but only visible when the sample size is small enough that a couple of dropped/kept
events swing the normalized score past the tolerance band. Confirmed NOT isolated to one world
or flag family: affects both `simq_routing_test` (`ENABLE_ADVENTURE_ROUTING=ON`) and
`urban_political` (a different world, no special flag).

## Recommendation

Not a code defect — `kernel.py`'s watchdog is documented, intentional behavior
(`docs/engine/kernel.md` "Emergency Throttling"), same scope guard already established by D06 F6
and `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`. Picking a single anchor
value for an unstable (run_key, pillar) pair would just drift again on the next re-run,
regardless of which value is chosen — not a real fix. Classified via 6 new entries in
`tests/simulation_quality/fixtures/score_ceilings.json` under a new `ceiling_kind: "watchdog_variance"`
(the existing `tools/simq_ceiling.py` provenance mechanism already supports free-text
`ceiling_kind` values sourced from this JSON fixture — no code change needed), each citing the
real reproducibility evidence gathered above. This makes future drift on these specific pairs
read as known, understood noise in `test_grade_regression.py`'s own failure output, exactly
matching the existing `tick_budget`/`flag_gated` convention.

A full FAST-tier sweep matching D06 F6's own 18-key/3-trial SLOW-tier methodology was not
performed — descoped to this representative 6-scenario sample per the ticket's own Acceptance
Criteria allowance. More FAST-tier keys may show the same instability; not claimed to be
exhaustive.
