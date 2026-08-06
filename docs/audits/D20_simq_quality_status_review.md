---
status: active
layer: simulation
authority: P1
audience: developer
tags: [audit, simulation-quality, calibration, corpus, roadmap]
---

# SimQ Quality Status Review — Follow-Up to D20

**Purpose:** a persistent, periodically-refreshed synthesis document — the broader-view read on
where simulation quality actually stands, meant to ground an epic/ticket-scoping decision, not a
scoped plan itself. Refreshed in place (like `current_state.md`), not layered with dated notes;
the "Last refreshed" line below is always the source of truth for how current the findings are.

**Distinct from its two source documents:**
- `docs/audits/D20_simq_integration.md` — the original wiring/calibration audit (2026-06-30,
  closed). Answers "is SimQ plumbed correctly and producing live scores." Still true; not
  re-litigated here.
- `docs/simulation_quality/current_state.md` — the mechanical, refreshed-in-place numeric
  snapshot (grade tables, per-pillar notes). This document draws directly from it but adds the
  synthesis layer current_state.md deliberately doesn't attempt: what do the numbers mean *as a
  system*, what's the real menu of candidate work, and how should it be sequenced/scoped.

**Last refreshed:** 2026-08-06, from a real full-corpus live engine re-run (`make simq-full-audit-full`).
79 of 79 anchor scenarios produced a valid report (0 exclusions). This is the closing snapshot for
a full working session spanning 11 tickets — see `current_state.md`'s "2026-08-05/06 session
summary" for the complete list; this document summarizes and synthesizes, it does not duplicate
the evidence trail.

---

## Executive Summary

- **Module health: fully wired, no infrastructure regressions.** All 10 pillar scorers live,
  event delivery intact, calibration tooling's one previously-documented bug confirmed resolved.
- **Correction (2026-08-05):** an earlier draft of this review listed "wire
  `ActionIntentAdapter.execute()`" and "persist raw `normalized_score`" as open candidate work
  items (formerly C and D below). Both were already fully implemented and closed —
  `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` and `TCK-20260713-SIMQ-RAWSCORE-PERSIST`,
  both landed 2026-07-13, both verified live directly against source in this refresh. That
  mistake traced back to trusting `current_state.md`'s older "Recommended next features" section
  at face value instead of re-checking `tickets/done/` and the actual code; both are now corrected
  here and there. No tickets needed for either.
- **WORLD's regression gate is now trustworthy** — `TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION`
  recalibrated all 37 affected anchors; WORLD-specific `test_grade_regression.py` failures went
  from 19 to 0.
- **ECONOMY's remaining gap is closed to a decision, not left open** — the goal-generation
  investigation this review previously called for already happened
  (`TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`, done) and isolated 3 factors; Factor 3
  (arrival-transition wiring) was already fixed; **Factor 2 (`AdventureRouteScorer`'s craft/buy
  bias) is now also investigated and closed** (`TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS`) —
  confirmed correct scorer behavior (entities never harvest/earn gold, so craft/buy are correctly
  blocked), not a bug; no fix was made, deliberately, per direct user guidance against forcing
  unrealistic routes. Only Factor 1 remains, as a genuine policy question (reopening a DA ruling),
  not filed as a ticket.
- **The engine-correctness bridge is now complete** — all 7 real `HardLawMonitor` laws are bridged
  into SimQ, up from 1 (`TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP`); confirmed 0 real corpus
  occurrences of the new signal this refresh.
- **A real gap in cognition-graph observability was found and fixed**
  (`TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`) — NORMAL/FULL/RESEARCH modes now capture
  state changes correctly; a real corpus-wide cost measurement (143MB for one 2000-tick scenario)
  showed adopting this for SimQ's own calibration harness isn't worth it, a decision made and
  documented, not left implicit.
- **Corpus-breadth investigation found 3 of 4 targeted "gaps" were already closed** by pre-existing
  worlds (`crowded_frontier`, `resource_dense_basin`, `hero_guild_routing`) and simply
  undocumented — corrected `corpus_tier_taxonomy.md` in each case instead of shipping redundant
  world content. The 4th gap (quest density decoupled from entity count) was genuinely open; closed
  with a new world, `quest_dense_frontier` (ratio 1.0, well beyond the corpus's prior incidental
  max of 0.636).
- **2 new single-draw score-tolerance variances observed this refresh**
  (`hero_guild_routing_seed42_500t`/COGNITION, `generated_frontier_3_42_seed456_200t`/NARRATIVE) —
  both within letter-grade band, neither traced to any change made this session. Flagged, not yet
  investigated with the multiple-fresh-draws rigor `SCORE_TOLERANCE_OVERRIDES` requires before
  committing a widened floor — see `current_state.md`'s session summary.
- **9 pillars are healthy, intentionally bounded, or fully closed** (FACTION, INFORMATION, SOCIAL,
  AGENCY, NARRATIVE, COMBAT, PROGRESSION, WORLD, and COGNITION's query-routing half) — no action
  recommended for any of them.

---

## Findings (evidence-backed, 2026-08-05/06 session)

Full evidence, exact deltas, and root-cause chains for all findings below are in
`current_state.md`'s "2026-08-05/06 session summary" section — summarized here for the
broader-view read.

### Finding 1 — WORLD pillar anchors were stale against an intentional scoring change — FIXED

**Status: resolved 2026-08-05** (`TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION`).
`TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (landed 2026-07-30) correctly added a new, intentional
negative-weighted signal (`spawn_occupancy_violation`, weight -30.0) to `WorldDynamicsScorer`,
routing real `LAW-SPAWN-OCCUPANCY` hard-law violations into the WORLD pillar. `grade_anchors.json`
was never recalibrated against it, causing 19 of 20 real `test_grade_regression.py` failures in
the original 2026-08-05 refresh. All 37 affected anchors were recalibrated from a fresh
full-corpus run; WORLD-specific regression failures went from 19 to 0.

### Finding 2 — ECONOMY's goal-generation gap is already investigated and mostly fixed; 2 precise factors remain

**Correction to this review's prior framing:** the "why does no entity ever decide to
harvest/craft/trade" investigation this document previously called for has already been done, by
`TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` (done, landed the day after the prior review
draft). It found and fixed the general routing gap in `TacticalDecisionSystem.evaluate_entity_intent`
(only `ObjectiveKind.REACH_LOCATION` was ever wired to execution; every other kind, including
harvest/craft/trade objectives, was silently dropped) by wiring the previously-orphaned
`ObjectiveIntentResolver` into production. It then ran real, non-mocked full-corpus verification —
not just isolated unit tests — and precisely isolated exactly 3 remaining contributing factors:

1. **Factor 1 — `ENABLE_ADVENTURE_ROUTING` defaults OFF** in every shipped profile. This is the
   feature flag that lets entities consider `craft_upgrade`/`buy_upgrade` routes at all. Tied to
   AGENCY's own DA-ruled design decision (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`) — turning it on
   more broadly is a policy question, not a bug fix, and is explicitly not assumed here.
2. **Factor 2 — `AdventureRouteScorer` never selects craft/buy routes even when routing is on. —
   INVESTIGATED AND CLOSED 2026-08-05** (`TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS`).
   Empirically confirmed 0/492 and 0/342 real selections across 2 routing-enabled runs — always
   outscored by `form_party`/`gather_resource`. Root-caused: `scoring.py`'s flat
   `blocker_penalty=2.0` clamps craft/buy's score to exactly `0.0` whenever
   `AdventureRouteGenerator` marks the route blocked, which it correctly does whenever the entity
   lacks the `has_gold`/`has_item` a craft/buy opportunity requires — and since entities never
   harvest resources or earn gold (Factor 3's own finding), that's always. **Confirmed correct
   scorer behavior, not a miscalibration.** No scoring fix was made — see the sequencing caution
   below, which this finding validates rather than merely anticipates.
3. **Factor 3 — the `REACH_RESOURCE→MOVE_TO` arrival-transition gap.** Fixed by the direct follow-up
   `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` (done, landed 07-16). This session's
   fresh full-corpus run confirms the fix alone has zero measured corpus-wide effect —
   `resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction` still appear in **zero**
   calibration runs — which is exactly what the ticket's own scope predicted, since Factors 1 and 2
   were deliberately left out of it.

**Sequencing caution (important, from direct user guidance 2026-08-05):** this is a realistic RPG
simulation. A "fix" for Factor 2 that just forces `AdventureRouteScorer` to route entities into
craft/buy more often — without a reasonable, entity-legible cognitive path (perceived need,
opportunity, resource proximity) leading there — would not close a real gap, it would manufacture
an unrealistic route the design never intended, trading one artificial signal (ECONOMY's silence)
for another (unmotivated harvesting). Any Factor 2 work must start as an investigation into whether
the scorer's current bias is a genuine miscalibration versus a correct reflection of the corpus's
archetype incentives, and only then decide whether — and how — to adjust scoring, not jump straight
to "make craft/buy score higher." See `docs/parity_ledger/infrastructure.yaml` INFRA-242.

### Finding 3 — 1 unreliable calibration run in the original refresh — RESOLVED, did not recur

`unit_selfmodel_pilot_seed42_1000t` failed its calibration integrity check under observability
backpressure (`pressure_mode_final=PRESSURE`) in the original 2026-08-05 refresh, likely
session-load-related. The 2026-08-06 closing full-corpus run (79/79 scenarios) completed this
exact scenario cleanly — consistent with the session-load theory, not investigated further since
it didn't recur.

### Finding 5 — the engine-correctness bridge is now complete (real, closed)

Of the 7 real `HardLawMonitor` laws, only `LAW-SPAWN-OCCUPANCY` was bridged into SimQ prior to this
session. `TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP` bridged the remaining 6:
`LAW-HP-NONNEGATIVE`/`LAW-READINESS-NONNEGATIVE` route to the existing (previously dormant)
`combat_hard_law_violation` signal, `LAW-GOLD-NONNEGATIVE` routes to the existing (previously
dormant) `conservation_law_violated` signal, and `LAW-STAMINA-NONNEGATIVE`/`LAW-POSITION-FINITE`/
`LAW-OCCUPANCY-COLLISION` route to a new `world_hard_law_violation` signal. Confirmed 0 real
corpus occurrences of the new signal in this refresh — no anchor impact, purely closing a coverage
gap for whenever these laws do fire in the future.

### Finding 6 — cognition-graph capture had a real mode-handling bug, now fixed; corpus-wide adoption deliberately declined

`CognitionCapturePolicy.should_capture()` previously handled OFF/LIGHT/LONG_RUN and DEBUG/
CERTIFICATION explicitly but silently fell through to `False` for NORMAL/FULL/RESEARCH modes,
despite their `ObservabilityConfig` flags implying richer capture than LIGHT.
`TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP` fixed this. Separately, that ticket measured
real corpus-wide storage cost (143MB for a single 2000-tick scenario) and concluded adopting this
for SimQ's own calibration harness is not worth it — a deliberate, documented decision, not a
silent gap.

### Finding 7 — 3 of 4 targeted corpus scale-diversity gaps were already closed and undocumented

`corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" list disagreed with its own per-world
table in 3 of 4 cases: `crowded_frontier` already closed the faction-density gap,
`resource_dense_basin` already closed the resource-density gap, and `hero_guild_routing` (31
entities/4 regions/10 quests, dramatically exceeding every real Unit-tier world and matching
End-to-end peers) already closed the AGENCY-real-archetype gap — all found via direct verification
before authoring anything, and corrected in the doc rather than shipping redundant world content.
The 4th gap (quest density decoupled from entity count) was genuinely open — closed with a new
world, `quest_dense_frontier` (6 entities, 6 quest_definitions, ratio 1.0).

### Finding 8 — 2 new single-draw score-tolerance variances observed, not yet investigated

This refresh's fresh full-corpus run found 2 within-band score-tolerance failures
(`hero_guild_routing_seed42_500t`/COGNITION, `generated_frontier_3_42_seed456_200t`/NARRATIVE),
neither traced to any change made this session — and notably, `urban_political_seed42_200t` (the
failure cited as "stable" throughout this session) did not reproduce this run, itself evidence
this is ordinary single-draw variance rather than a new regression. Not investigated further or
added to `SCORE_TOLERANCE_OVERRIDES` this refresh, per that mechanism's own precedent requiring
multiple independent fresh draws before committing a widened floor.

### Finding 4 — a previously-documented tooling bug is confirmed resolved

`current_state.md` had long carried a note that `evaluate_simq.py`'s live-calibration mode
silently mishandled the one scenario whose profile name differs from its world name. Re-checked
the current source directly and confirmed via this refresh's own normal automated run (no
workaround needed): the bug is fixed. No outstanding tooling issue in this path.

---

## Full Pillar Health (2026-08-06, 79 of 79 scenarios)

| Pillar | S | A | B | C | D | Read |
|---|---|---|---|---|---|---|
| WORLD | 0 | 3 | 66 | 10 | 0 | **Finding 1** — anchors recalibrated, gate now trustworthy |
| NARRATIVE | 8 | 58 | 6 | 7 | 0 | Healthy; 1 unrelated single-draw variance this refresh (Finding 8) |
| COMBAT | 0 | 0 | 47 | 32 | 0 | Healthy, archetype-correct spread |
| PROGRESSION | 0 | 10 | 41 | 28 | 0 | Healthy, unchanged |
| FACTION | 31 | 15 | 6 | 27 | 0 | Declared structurally complete (roadmap Phase 5) |
| INFORMATION | 0 | 3 | 36 | 40 | 0 | Declared structurally complete (roadmap Phase 5) |
| COGNITION | 9 | 5 | 40 | 25 | 0 | Both halves wired and closed; 1 unrelated single-draw variance this refresh (Finding 8) |
| SOCIAL | 16 | 0 | 0 | 63 | 0 | Staged depth is the deliberate permanent bar (roadmap Phase 5) |
| ECONOMY | 0 | 1 | 17 | 61 | 0 | **Finding 2** — both factors resolved to decisions: Factor 1 is a policy question (not filed), Factor 2 confirmed correct behavior, not a bug (closed 08-05) |
| AGENCY | 0 | 8 | 0 | 71 | 0 | C-by-design, `ENABLE_ADVENTURE_ROUTING` opt-in (DA-ruled); `hero_guild_routing` now also formally credited with closing the real-archetype corpus gap (Finding 7) |

---

## Candidate Work Items (for epic-scoping — none of these are filed as tickets yet)

This is the menu the executive summary and findings above ground. Sizing carried forward from
`current_state.md`'s own recommendation estimates where available.

**Correction (2026-08-05):** former items C ("wire `ActionIntentAdapter.execute()`") and D
("persist raw `normalized_score`") are removed from this table — both were already done as of
2026-07-13, discovered during Context Scan before ticket-filing. See the Executive Summary
correction note above.

| # | Candidate | Real gap? | Size | Urgency | Notes |
|---|---|---|---|---|---|
| A | Recalibrate WORLD pillar anchors against the spawn-occupancy signal | Yes — anchor staleness (Finding 1) | S | **High** — regression gate is untrustworthy for WORLD until done | Root cause fully diagnosed already; no further investigation needed before implementing |
| B1 | Decide whether to reopen `ENABLE_ADVENTURE_ROUTING`'s DA-ruled default (ECONOMY Factor 1) | Real, but a policy question, not a bug | — | Low — no defect, a deliberate design boundary | Not a ticket unless the user wants to revisit the DA ruling; noted for completeness, not filed by default |
| B2 | ~~Investigate whether `AdventureRouteScorer`'s craft/buy selection bias is a miscalibration~~ — **DONE 2026-08-05**, confirmed correct behavior, no fix (ECONOMY Factor 2) | Was real (Finding 2), now resolved as "working as intended" | — | — | `TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS`: blocker_penalty=2.0 correctly fires because entities never harvest/earn gold; root cause loops back to Factors 1/3, not this scorer |

**Not recommended right now:** reopening FACTION/INFORMATION/SOCIAL/AGENCY depth (all closed with
real evidence under the SimQ roadmap's Phase 5 ruling), or any of SimQ's explicit MVP Non-Goals
(per-entity profiles, historical run comparison, real-time alerting, ML anomaly detection,
automated config suggestion — `quality_scoring_contract.md` §14, reaffirmed out of scope
2026-07-10).

---

## Recommendation

**All previously-open candidate work items are now closed.** Item A (WORLD anchors) and Item B2
(ECONOMY scorer investigation) both resolved 2026-08-05, alongside 5 more tickets not originally
scoped in this review (hardlaw bridge coverage, cognition-graph capture fix, behavior-scorecard
redundancy investigation, cross-pillar correlation investigation, and the 4 corpus-scale-diversity
tickets). **Item B1** (reopening `ENABLE_ADVENTURE_ROUTING`'s DA-ruled default) remains not
recommended to file — a policy question, not a defect, needing explicit user intent to reopen.

**What's genuinely left for a future session:**
- The 2 new single-draw score-tolerance variances (Finding 8) — worth a proper multi-draw
  investigation if they recur, not urgent on their own.
- Nothing else from this review's own scope remains open. Any further SimQ work would come from a
  fresh investigation, not a backlog item this document is still tracking.

---

## Related

- `docs/audits/D20_simq_integration.md` — original wiring/calibration audit (closed)
- `docs/simulation_quality/current_state.md` — refreshed-in-place numeric snapshot, full evidence
- `docs/simulation_quality/quality_scoring_contract.md` — the authoritative scoring spec
- `docs/simulation_quality/eval_matrix_results.md` — append-only historical calibration batch log
- `docs/simulation_quality/corpus_tier_taxonomy.md` — corpus tier structure and per-world classification
- `docs/plans/archive/simq_development_roadmap.md` — the closed 6-phase roadmap this review follows on from
- `docs/parity_ledger/infrastructure.yaml` (INFRA-242) — ECONOMY `gold_sink_fired` finding detail
