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

**Last refreshed:** 2026-08-05, from a real full-corpus live engine re-run (`make simq-full-audit-full`
— `data/calibration/` was empty going in, a fresh-checkout state). 75 of 76 anchor scenarios
produced a valid report. Full detail and raw evidence citations for every finding below live in
`current_state.md`'s own 2026-08-05 refresh section — this document summarizes and synthesizes,
it does not duplicate the evidence trail.

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
- **1 pillar's regression gate is currently untrustworthy** (WORLD) — not a quality problem, a
  measurement one: a real, intentional scoring addition landed without an anchor recalibration.
  Small, urgent fix.
- **1 pillar has a confirmed, narrowly-scoped remaining gap** (ECONOMY) — the broad
  goal-generation investigation this review previously called for has *already happened and mostly
  closed* (`TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`, done). It precisely isolated 3
  factors; 1 of the 3 (the arrival-transition wiring) is fixed. What's left is 2 specific,
  already-diagnosed factors, not a fresh investigation — see Finding 2.
- **8 pillars are healthy, intentionally bounded, or fully closed** (FACTION, INFORMATION, SOCIAL,
  AGENCY, NARRATIVE, COMBAT, PROGRESSION, and COGNITION's query-routing half, now wired) — no
  action recommended for any of them.

---

## Findings (evidence-backed, 2026-08-05 refresh)

Full evidence, exact deltas, and root-cause chains for all four findings below are in
`current_state.md`'s "2026-08-05 refresh" section — summarized here for the broader-view read.

### Finding 1 — WORLD pillar anchors are stale against an intentional scoring change (real, urgent, small)

`TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (landed 2026-07-30) correctly added a new, intentional
negative-weighted signal (`spawn_occupancy_violation`, weight -30.0) to `WorldDynamicsScorer`,
routing real `LAW-SPAWN-OCCUPANCY` hard-law violations into the WORLD pillar. `grade_anchors.json`
was never recalibrated against it. Result: 19 of 20 real `test_grade_regression.py` failures found
this refresh are this exact pattern. This is real, working detection surfacing a
previously-invisible signal — not a regression — but the WORLD regression gate cannot currently
distinguish this known baseline shift from a genuine future regression until the anchors are
recalibrated.

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

### Finding 3 — 1 unreliable calibration run this refresh (informational, unconfirmed cause)

`unit_selfmodel_pilot_seed42_1000t` failed its calibration integrity check under observability
backpressure (`pressure_mode_final=PRESSURE`) and was excluded. Likely session-load-related (this
machine had substantial concurrent load during the refresh) — not investigated further; flagged
for awareness, not as a finding requiring action.

### Finding 4 — a previously-documented tooling bug is confirmed resolved

`current_state.md` had long carried a note that `evaluate_simq.py`'s live-calibration mode
silently mishandled the one scenario whose profile name differs from its world name. Re-checked
the current source directly and confirmed via this refresh's own normal automated run (no
workaround needed): the bug is fixed. No outstanding tooling issue in this path.

---

## Full Pillar Health (2026-08-05, 75 of 76 scenarios)

| Pillar | S | A | B | C | D | Read |
|---|---|---|---|---|---|---|
| WORLD | 0 | 3 | 62 | 10 | 0 | **Finding 1** — anchors stale, not a real drop |
| NARRATIVE | 8 | 59 | 4 | 4 | 0 | Healthy, real spread, unchanged |
| COMBAT | 0 | 0 | 44 | 31 | 0 | Healthy, archetype-correct spread |
| PROGRESSION | 0 | 8 | 39 | 28 | 0 | Healthy, unchanged |
| FACTION | 31 | 15 | 6 | 23 | 0 | Declared structurally complete (roadmap Phase 5) |
| INFORMATION | 0 | 3 | 36 | 36 | 0 | Declared structurally complete (roadmap Phase 5) |
| COGNITION | 8 | 5 | 40 | 22 | 0 | Both halves wired and closed (`TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`) |
| SOCIAL | 16 | 0 | 0 | 59 | 0 | Staged depth is the deliberate permanent bar (roadmap Phase 5) |
| ECONOMY | 0 | 1 | 16 | 58 | 0 | **Finding 2** — both factors resolved to decisions: Factor 1 is a policy question (not filed), Factor 2 confirmed correct behavior, not a bug (closed 08-05) |
| AGENCY | 0 | 8 | 0 | 67 | 0 | C-by-design, `ENABLE_ADVENTURE_ROUTING` opt-in (DA-ruled) |

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

Explicitly the user's decision, not pre-decided here — but the shape of the options:

- **Item A** is small, urgent, and fully diagnosed — a strong hotfix-tier candidate on its own,
  independent of any other decision.
- **Item B2 is resolved** (2026-08-05) — investigated as instructed, confirmed correct scorer
  behavior, no fix made. The investigation-first discipline paid off directly: forcing a fix here
  would have manufactured an unrealistic route exactly as the sequencing caution warned against.
- **Item B1** is not recommended to file as a ticket right now — it's a policy question about
  reopening a DA ruling, not a defect. Noted here for visibility only; would need explicit user
  intent to reopen the DA decision before it becomes ticket-worthy.

---

## Related

- `docs/audits/D20_simq_integration.md` — original wiring/calibration audit (closed)
- `docs/simulation_quality/current_state.md` — refreshed-in-place numeric snapshot, full evidence
- `docs/simulation_quality/quality_scoring_contract.md` — the authoritative scoring spec
- `docs/simulation_quality/eval_matrix_results.md` — append-only historical calibration batch log
- `docs/simulation_quality/corpus_tier_taxonomy.md` — corpus tier structure and per-world classification
- `docs/plans/archive/simq_development_roadmap.md` — the closed 6-phase roadmap this review follows on from
- `docs/parity_ledger/infrastructure.yaml` (INFRA-242) — ECONOMY `gold_sink_fired` finding detail
