---
status: active
layer: simulation
authority: P1
audience: developer
tags: [simulation-quality, corpus, calibration]
---

# SimQ Current State Report

**Purpose:** a single, periodically-refreshed snapshot of where the 10-pillar quality corpus
actually stands right now — distinct from `eval_matrix_results.md`, which is an append-only
historical log of every calibration batch since 2026-07-02. That log is the evidentiary record;
this doc is the answer to "what's the current picture," refreshed in place rather than layered
with dated notes. When this doc and `eval_matrix_results.md` disagree, re-run the refresh command
below — this doc should always reflect the latest run, not accumulate history of its own.

**Last refreshed:** 2026-08-06, via a real full-corpus live engine re-run (`make simq-full-audit-full`,
79 of 79 anchor scenarios produced a report — 0 exclusions this run, including
`unit_selfmodel_pilot_seed42_1000t`, which was unreliable in the earlier 2026-08-05 same-day
refresh but completed cleanly here). This refresh is the closing snapshot for a full working
session (5 fixes, 5 investigations, 1 new corpus world — see "2026-08-05/06 session summary"
below), superseding the mid-session 2026-08-05 refresh whose "Finding 1"/"Finding 2" text below is
now historical record of what was found and fixed, not the current state.

---

## 2026-08-05/06 session summary

A full working session covering all 11 tickets in `tickets/done/simulation-quality/`. Real
fixes/changes: **(1)** WORLD pillar anchors recalibrated against the `spawn_occupancy_violation`
signal (37 scenarios, `TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION`); **(2)** cognition-graph
capture policy bug fixed (`TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`); **(3)** the F grade
band added to `GRADE_ORDER` in 3 places (`TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP`); **(4)** all 7
real `HardLawMonitor` laws now bridged into SimQ, up from 1 (`TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP`,
new `world_hard_law_violation` signal, confirmed 0 real corpus occurrences this refresh); **(5)** a
new corpus world, `quest_dense_frontier` (ratio 1.0 quest-def/entity, closing a genuine scale-
diversity gap, `TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE`) — corpus grew from 76 to 79
anchors. Investigated-and-closed-without-a-fix: ECONOMY's craft/buy scorer bias (confirmed correct
behavior, not a bug), the `EntityBehaviorScorecard` redundancy question (nuanced, no revival
needed), cross-pillar correlation (no real signal found in the corpus). Found stale rather than
fixed: 3 of 4 targeted corpus-scale-diversity gaps (faction-density, resource-density,
AGENCY-real-archetype) turned out already closed by pre-existing worlds
(`crowded_frontier`/`resource_dense_basin`/`hero_guild_routing`) and undocumented — corrected
`corpus_tier_taxonomy.md` instead of shipping redundant world content in each case.

**New this refresh (2026-08-06), not yet investigated in depth:** 2 single-draw score-tolerance
failures — `hero_guild_routing_seed42_500t`/COGNITION (anchor 1.016, actual 1.827) and
`generated_frontier_3_42_seed456_200t`/NARRATIVE (anchor 0.979, actual 0.761). Both are within
letter-grade band (A/A in both cases, confirmed via `evaluate_simq.py`'s own PASS table) — only the
score-tolerance check flags them. Neither this session's tickets nor any other work touched either
world's content or the COGNITION/NARRATIVE scorers. Notably, `urban_political_seed42_200t` — the
one failure cited as "stable" throughout this session's earlier tickets — did *not* reproduce in
this run, which is itself evidence this is ordinary single-draw variance (the specific
scenario/pillar that flakes shifts run to run) rather than a new regression. Not investigated
further or added to `SCORE_TOLERANCE_OVERRIDES` this refresh — that mechanism's own precedent
(see the override table's comments in `test_grade_regression.py`) requires multiple independent
fresh draws before committing a widened floor, to avoid overfitting a tolerance band to one
sample of noise. Flagged here for whoever picks this up next.

---

## 2026-08-05 refresh — 2 real findings

### Finding 1: WORLD pillar anchors were stale — FIXED (`TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION`)

**Status: resolved 2026-08-05.** `test_grade_regression.py` (fast tier, 200t/500t) originally found
**20 of 65 comparable scenarios** drifted beyond score tolerance — **19 of the 20 were the WORLD
pillar**, every one scoring *lower* than its anchor by a consistent delta (e.g. `anchor=0.09 →
actual=-0.06`, `anchor=0.59 → actual=0.44`, `anchor=0.24 → actual=0.09` — deltas clustered around
-0.15/-0.12/-0.075 depending on scenario). This was a live-corpus finding from earlier the same day
(2026-08-05); the recalibration below fixes it.

Root cause, confirmed not assumed: `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (landed 2026-07-30) added
a new, intentional, negative-weighted signal (`spawn_occupancy_violation`, weight **-30.0**) to
`WorldDynamicsScorer`, routing real `LAW-SPAWN-OCCUPANCY` hard-law violations
(`HardLawMonitor.check_initial_placement()`) into the WORLD DYNAMICS pillar. The committed
`grade_anchors.json` predates this addition — every scenario whose initial placement happens to hit
even one spawn-occupancy collision now correctly loses points the anchor never accounted for. This
is real, working, intentional detection surfacing a previously-invisible signal — **not a quality
regression** — but the anchors need recalibrating to the new baseline before WORLD's regression
gate is trustworthy again. Real corpus-wide effect (75 fresh reports vs. the 07-13 table):

| Pillar | S | A | B | C | D | vs. 07-13 |
|---|---|---|---|---|---|---|
| WORLD (pre-fix) | 0 | 3 | 62 | 10 | 0 | **A 4→3, B 71→62, C 0→10 — real regression-gate-visible drop** |
| WORLD (post-fix, 08-05) | 0 | 3 | 63 | 10 | 0 | anchors recalibrated against `spawn_occupancy_violation`; distribution now matches live scoring |

The one non-WORLD outlier, `urban_political_seed42_200t` (NARRATIVE `A`, SOCIAL `S` — letter
grades unchanged, only the raw `normalized_score` drifted outside its tolerance band), is far more
likely ordinary run-to-run variance (already documented in `docs/audits/D20_simq_integration.md`'s
wall-clock-throttle findings) than a real issue — not part of the WORLD pattern above, and
explicitly out of `TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION`'s scope (WORLD-only). Still open,
unrelated to this finding.

**Fixed 2026-08-05** (`TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION`): recalibrated all 37 affected
scenarios' WORLD entries in `grade_anchors.json` against a fresh full-corpus live-engine run,
touching only the WORLD key per scenario (verified: 0 non-WORLD pillar entries changed).
`test_grade_regression.py -m "not slow"` now passes 64/65 comparable scenarios — the sole remaining
failure is the pre-existing, unrelated `urban_political_seed42_200t` NARRATIVE/SOCIAL variance
noted above, not WORLD.

### Finding 2: ECONOMY still produces zero real events — but the remaining gap is now precisely
### isolated to 2 named, already-diagnosed factors, not an open-ended goal-generation mystery

**Corrected 2026-08-05** — this finding originally understated how much work had already gone
into this exact question. The real chain, in order:

1. `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` — authored real content into 3 more worlds, found
   zero effect, discovered the gap was structural not content-volume.
2. `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` (**DONE**) — root-caused and fixed a general
   `ObjectiveKind` routing gap: `TacticalDecisionSystem` only understood `REACH_LOCATION`, silently
   dropping every other objective kind. Wired the previously-orphaned `ObjectiveIntentResolver`
   into production, fixed 2 more structural gaps found along the way (`ServiceOpportunityProvider`
   never called; unresolvable opportunity-id target refs). **Ran real, non-mocked calibration
   verification (not just unit tests)** and precisely isolated 3 remaining contributing factors,
   deliberately left out of that ticket's scope:
   - **Factor 1**: `ENABLE_ADVENTURE_ROUTING` defaults `OFF` in every shipped profile — System A
     (where the fix lives) never runs during real calibration. Tied to AGENCY's own DA-ruled
     intentional design (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`) — not casually reversible.
   - **Factor 2**: even with routing ON, `AdventureRouteScorer` never selects
     `craft_upgrade`/`buy_upgrade` — empirically confirmed 0 selections across 2 real routing-enabled
     calibration runs (0/492 in `hero_guild_routing`, 0/342 in `simq_routing_test`), consistently
     outscored by `form_party`/`gather_resource`. **Investigated and closed 2026-08-05**
     (`TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS`): this is **correct scorer behavior,
     not a miscalibration**. Traced to `scoring.py`'s flat `blocker_penalty=2.0`, which fires
     whenever `route.blockers` is non-empty and clamps the final score to `0.0`
     (`max(0.0, final_score)`). `AdventureRouteGenerator` sets a blocker whenever the entity lacks
     the `has_gold`/`has_item` a craft/buy opportunity requires (`generator.py:54-68`,
     `services.py:50-111`) — and since entities never harvest resources or earn gold (Factor 3's
     own zero-harvest finding), craft/buy opportunities are *correctly* blocked every time. No
     scoring fix was made — per direct user guidance this session, forcing craft/buy to score
     higher without entities actually having the resources would manufacture an unrealistic route,
     not close a real gap. The real fix, if pursued, is upstream (Factors 1/3), not this scorer.
   - **Factor 3**: `ObjectiveIntentResolver`'s `REACH_RESOURCE → MOVE_TO` mapping never transitions
     to a harvest action on arrival. Filed as a direct follow-up:
     `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION`.
3. `TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` (**DONE**) — fixed Factor 3 specifically.

**This session's fresh full-corpus re-run (2026-08-05) directly confirms Factor 3's fix, while
real, did not close the gap**: `resource_harvested`/`item_crafted`/`trade_executed`/
`shop_transaction` combined still appear in **zero** calibration runs, corpus-wide (`grep` across
all 75 `quality_scores.jsonl` files). This is exactly consistent with Factors 1 and 2 remaining
unaddressed — `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP`'s own Completion Summary predicted
precisely this outcome, explicitly deferring both to "a differently-scoped ticket (the
`simq_audit`/calibration workstream)." ECONOMY's grade distribution is unchanged from 07-13 (0 S /
1 A / 16-17 B / 57-58 C — within 1-report rounding). **The real remaining work is narrowly Factor
2** (Factor 1 requires reopening a DA-ruled decision, out of scope without a fresh decision) — see
the corrected Recommendation 2 below.

### Known issue — RESOLVED, 0 unreliable runs in the 2026-08-06 refresh

The 2026-08-05 mid-session refresh (quoted above) had 1 unreliable run
(`unit_selfmodel_pilot_seed42_1000t`, `pressure_mode_final=PRESSURE`), suspected session-load-
related. The 2026-08-06 closing full-corpus re-run (79/79 scenarios) completed this exact scenario
cleanly (`pressure_mode_final=NORMAL`, `guard_passed=true`), consistent with the session-load
theory — not investigated further, since it didn't recur.

---

`TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` composed `trading_company_hub` into 3 more worlds
(`frontier_living_world`, `frontier_extended`, `swamp_border_world`) and recalibrated their 9
anchors (3 worlds x 3 seeds, 200t) — this moved 9 anchors' COMBAT/PROGRESSION/SOCIAL/WORLD/
NARRATIVE columns (new entities/quest content changing those pillars' event counts as a side
effect) but **ECONOMY itself did not move for any of the 9** — see Recommendation 2 below for why.

**To refresh this report:** if `data/calibration/` already has fresh (<24h) reports for every
scenario, `python3 tools/evaluate_simq.py --dry-run` is enough. Otherwise (as it was for this
refresh — a fresh checkout has none), use `make simq-full-audit-full` to re-run the live engine
across the full corpus first (the previously-documented live-mode tooling bug is resolved, see
below — safe to use directly now), then re-derive the grade table from `data/calibration/*/quality_report.json`
directly (`evaluate_simq.py`'s own comparison table only prints if every scenario succeeds with
zero calibration errors — see `main()`'s `error_count > 0` early-exit). If `test_grade_regression.py`
reports any drift, resolve it first (stale anchor vs. real regression — see
`docs/audits/D20_simq_integration.md` for the established investigation pattern) before treating
this doc's numbers as current. Real full-corpus engine runtime: ~15-20 minutes for the 79-scenario
fast+medium tier (200t/500t/1000t); expect to run it in the background.

**Previously-documented tooling bug — RESOLVED, confirmed 2026-08-05.** This doc previously
described `_run_calibration()` as never forwarding `--profile` to `calibrate_simq.py`, causing
`urban_political_selfmodel_probe_seed42_200t` to silently fall back to a meaningless synthetic
scenario. Re-checked the current source directly: `_run_calibration()` (`tools/evaluate_simq.py`)
now passes `"--profile", profile_name` explicitly. Confirmed empirically too — this refresh's
normal automated full-corpus run (no standalone workaround) produced exactly the correct,
previously-only-manually-obtainable result for that scenario (COGNITION=S/5610 events,
FACTION=S/29, SOCIAL=S/770, NARRATIVE=A/11). Whatever fixed this was not specifically tracked
against this doc's own paragraph — the fix landed as a side effect of other SimQ work between
07-13 and 08-05. No outstanding tooling bug in this path as of this refresh.

---

## Current grade distribution (79 of 79 anchor entries, live-corpus run, 2026-08-06)

The full session's closing snapshot — 0 unreliable runs, 3 more anchors than the 2026-08-05
mid-session table (76 → 79, from `quest_dense_frontier`'s 3 new seeds). WORLD reflects the
post-recalibration anchors (Finding 1, resolved); ECONOMY reflects Finding 2 (investigated,
confirmed correct behavior, no fix needed). All other pillars are materially unchanged from the
2026-08-05 table within normal rounding, aside from the 2 single-draw score-tolerance variances
noted in the session summary above (both within-band, not grade-distribution-visible here).

| Pillar | S | A | B | C | D |
|---|---|---|---|---|---|
| WORLD | 0 | 3 | 66 | 10 | 0 |
| NARRATIVE | 8 | 58 | 6 | 7 | 0 |
| COMBAT | 0 | 0 | 47 | 32 | 0 |
| PROGRESSION | 0 | 10 | 41 | 28 | 0 |
| FACTION | 31 | 15 | 6 | 27 | 0 |
| INFORMATION | 0 | 3 | 36 | 40 | 0 |
| COGNITION | 9 | 5 | 40 | 25 | 0 |
| SOCIAL | 16 | 0 | 0 | 63 | 0 |
| ECONOMY | 0 | 1 | 17 | 61 | 0 |
| AGENCY | 0 | 8 | 0 | 71 | 0 |

(2026-07-13 history, preserved for context) WORLD/PROGRESSION moved by 2/1 entries respectively as
a side effect of `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`'s content addition (new entities/quest
content shifting those pillars' event counts in `frontier_living_world`/`frontier_extended`'s 200t
anchors) — **not** an intentional target of that ticket, which targeted ECONOMY. As of this
2026-08-05 refresh, ECONOMY's distribution remains effectively unchanged (0/1/16-17/57-58 across
both refreshes, within 1-report rounding) — see Finding 2 above and Recommendation 2 below, now
corrected to reflect the harvest-wiring fix's zero measured effect on this corpus.

WORLD/PROGRESSION/INFORMATION/ECONOMY's `A` columns went from all-zero to non-zero this session
(`TCK-20260713-SIMQ-SCORE-CEILING-FIX`) — see the discriminative-power section below, now updated
to reflect the fix rather than the ceiling problem it fixed.

---

## Per-pillar read

**Discriminative-power check — RESOLVED 2026-07-13 (`TCK-20260713-SIMQ-SCORE-CEILING-FIX`).**
A prior pass this same day found 4 of 10 pillars structurally could not reach grade A or S under
the then-current weight scale, no matter how good the world was — even the single richest ECONOMY
run in the whole corpus (69 scored events) only reached 1/3 of the way to the A threshold (0.5).
That was a weight/normalization-scale problem, not a corpus-coverage problem (content authoring
alone, Recommendation 2 below, would not have fixed it). The fix raised each affected pillar's
**positive** per-event weights only (`config/simulation_quality/scoring_weights.yaml`), computed
per-pillar from each pillar's own richest-observed corpus scenario so that scenario crosses 0.5 —
not a blanket multiplier across pillars, and no negative/dormancy weight or grade threshold was
touched:

| Pillar | Pre-fix max normalized score | Weight multiplier | Post-fix result |
|---|---|---|---|
| WORLD | 0.30 (`frontier_marches_seed123_200t`, 38 events) | x2 | Same scenario now A (0.60) |
| ECONOMY | 0.16 (`urban_political_seed123_1000t`, 69 events) | x4 | Same scenario now A (0.66) |
| PROGRESSION | 0.12 (`generated_frontier_3_42_seed42_1000t`, 44 events) | x5 | Same scenario now A (0.64) |
| INFORMATION | 0.04 (`unit_information_source`, 1 event) | x5 | New `unit_information_density` world (3 events/run) now A (0.60); old 1-event scenario stays B |

INFORMATION could not be fixed by weight alone: reaching 0.5 on its existing 1-event richest
scenario would have required a single-event weight (25) larger than PROGRESSION's own pre-fix
milestone-tier ceiling (15) — a per-event weight so large it would let one occurrence dominate the
entire pillar, itself a discriminative-power problem rather than a fix. A new Unit-tier probe world,
`unit_information_density` (complementary to the existing `unit_information_source` isolation
probe — 3 `belief_assimilated` events/run instead of 1), was added to the corpus to supply the
missing event density; see `corpus_tier_taxonomy.md`'s Unit-tier mapping table.

Structurally-inert scenarios (zero WORLD/ECONOMY/PROGRESSION/INFORMATION activity) are unaffected
by this fix and remain grade C — every pillar's dormancy/zero-activity penalty only fires inside
its own triggering event's handler, so a world with zero events for a signal family never enters
that code path regardless of the positive weight's magnitude (confirmed empirically across the
full regenerated corpus: 0 zero-event anchors changed grade).

**NARRATIVE, COMBAT** — the other two "always-on" pillars, and by contrast were already healthy
before this fix and untouched by it (their weights are unchanged; the ceiling pattern above was
specific to WORLD/ECONOMY/PROGRESSION/INFORMATION). NARRATIVE spans all 4 grades with real spread
(7 S / 55 A / 9 B / 4 C), COMBAT spans a narrower but real range including both B and C outcomes
reflecting genuine archetype differences (a combat-only world scores differently from a low-combat
one).

**FACTION, INFORMATION** — declared structurally complete by the SimQ roadmap's Phase 5 gate
(`TCK-20260713-SIMQ-COVERAGE-DECISION-GATE`, `docs/plans/archive/simq_development_roadmap.md`).
11/17 and 9/17 worlds carry calibrated content respectively; every remaining world has a
documented, tier-appropriate reason to stay inert (Stress/Unit/Regression-tier worlds are
*supposed* to isolate other mechanics). No further content-authoring work is queued for either
pillar.

**SOCIAL** — staged depth declared the permanent bar by the same Phase 5 ruling. 3/17 worlds
activated (`urban_political`, `frontier_living_world`, `highland_traverse`); the one evaluated
non-candidate (`dungeon_crawl`) is structurally incapable (no settlement/civilian module, so the
cooperation gate never opens). Future expansion is opportunistic (if/when a new world is authored
with a qualifying module), not a queued initiative.

**AGENCY** — C in every world except `simq_routing_test`/`hero_guild_routing` is archetype-correct
by design (`ENABLE_ADVENTURE_ROUTING` is opt-in per world, DA-ruled intentional,
`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`). Not a gap.

**COGNITION** — split state, the one pillar with a genuinely unresolved half:
- Self-model *materialization* generalizes cleanly and cheaply to real archetype worlds (proven
  on `urban_political`, `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) — this is what drives
  the S/A/B signal in the table above.
- Self-model *query-routing* (Branch B asking "what don't I know, who might know it") is verified
  mechanically correct (`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`, direct test-harness
  invocation) but has **zero live-gameplay reach**: no shipped world profile enables the required
  flag combination, and — confirmed directly, `grep -rn "ActionIntentAdapter" src/` — the
  execution entry point (`ActionIntentAdapter.execute()` in
  `src/engine/intent/action_intent.py:32`) has no production call site anywhere. It exists only
  as a class definition and a docstring mention. Every other gated phase in `src/engine/pipeline.py`
  (`cooperation`, `information_belief`, `adventure_decision`) is wired via a `run_phase(...)` call;
  no equivalent line exists for intent execution. This is a real, well-scoped, unstarted gap — see
  Recommendation 3 below.

**ECONOMY** — the pillar with the most remaining headroom, now for a **different, better-understood
reason** than previously documented here. `EconomyScorer` (`src/simulation_quality/scorers/economy.py`)
listens for 10 distinct event types (harvesting, crafting, trading, gold flow, scarcity, inflation
control, conservation checks, paid-info transactions, quest rewards) — not a thin, single-signal
pillar. This doc previously read the corpus-wide C-heavy distribution as "largely a genuine content
gap: most worlds simply don't have sustained harvest/craft/trade content authored into them."
`TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` tested that reading directly: it composed
`trading_company_hub` (a dedicated merchant population, shop/inn buildings, iron_vein resource
nodes — the same module `urban_political`'s own richest ECONOMY run uses) into 3 more worlds
(`frontier_living_world`, `frontier_extended`, `swamp_border_world`) at merchant_count 3 and 6,
calibrated at 200t (the corpus's anchor length for these worlds) and, diagnostically, 1000t.
**ECONOMY did not move off C in any of the 9 recalibrated anchors, at any merchant_count tested.**
Root-cause investigation found why: `resource_harvested`/`item_crafted`/`trade_executed`/
`shop_transaction` (the 4 event types that would indicate real content-driven activity) have never
fired in **any** calibration run in the corpus — confirmed by grepping every
`data/calibration/*/quality_scores.jsonl`, including all 8 of `urban_political`'s own committed
seed/tick combinations. The corpus's only ever-observed ECONOMY signal is `gold_sink_fired`
(Gini-threshold inflation control, fires from combat-loot wealth inequality, content-independent) —
including the specific 69-event `urban_political_seed123_1000t` run this doc and
`SIMQ-CALIBRATED-001` previously cited as evidence of "real economic activity": all 69 of those
events are `gold_sink_fired`. That prior reading is now confirmed incorrect on this specific point
(see `docs/parity_ledger/infrastructure.yaml` INFRA-242's `support_boundary` for the full finding).
The weight-scale ceiling fix (`TCK-20260713-SIMQ-SCORE-CEILING-FIX`) is unaffected and remains
correct — it is genuinely easier to reach A now — but the underlying assumption about what a
"richer" ECONOMY run represents was wrong: no world in the corpus has ever produced real
harvest/craft/trade signal, because no entity archetype's decision/strategy layer currently
generates an accepted harvest, craft, or trade intent (analogous to AGENCY's own documented
`ENABLE_ADVENTURE_ROUTING` gap). Closing this requires strategy/cognition-layer work, not content
authoring — see Recommendation 2 below for the reframed next step. This pillar was never addressed
by the SimQ roadmap (explicitly out of scope — a Gini-threshold/archetype-composition question, not
the `FeatureMode` gating question the roadmap's 4 pillars shared).

---

## Recommended next features

Numbering preserved from the prior refresh for continuity even though item 1 is now done; 4 was
(and remains) a measurement-validity fix that probably belongs before 2 and 3 in any real
sequencing, since it affects whether *any* future content-authoring or engine work would even be
visible in the grades. Item 0 is new this refresh and is the most urgent — it's the only item
actively degrading the regression-detection gate's own trustworthiness right now.

### 0. Recalibrate WORLD pillar anchors against the new spawn-occupancy signal — DONE

**Status:** done, `TCK-20260805-SIMQ-WORLD-ANCHOR-RECALIBRATION` (2026-08-05). 37 affected `WORLD`
anchor entries recalibrated from a fresh full-corpus run; WORLD-specific `test_grade_regression.py`
failures went from 19 to 0. See Finding 1 above for the original diagnosis.

### 1. Recalibrate the weight/normalization scale for WORLD, ECONOMY, PROGRESSION, INFORMATION — DONE

**Status:** done, `TCK-20260713-SIMQ-SCORE-CEILING-FIX`. See the discriminative-power section above
for the full before/after. Summary: raised each pillar's positive per-event weights only (WORLD x2,
ECONOMY x4, PROGRESSION x5, INFORMATION x5), computed per-pillar from each pillar's own
richest-observed scenario; grade thresholds untouched; a new Unit-tier probe world
(`unit_information_density`) added because INFORMATION's existing 1-event richest scenario could
not be fixed by weight alone without letting a single event dominate the pillar. Full corpus
regression (`pytest tests/simulation_quality/`) showed 0 unattributed regressions — every changed
anchor traces to one of these 4 pillars' weight raise.

### 2. Author ECONOMY-rich content into 2-3 more archetype worlds — ATTEMPTED, ROOT CAUSE FOUND, NOT A CONTENT GAP

**Status:** attempted, `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`. Composed `trading_company_hub`
(dedicated merchant population + shop/inn buildings + resource nodes, `urban_political`'s own
proven module) into `frontier_living_world`, `frontier_extended`, `swamp_border_world` at
merchant_count 3 and 6 (within each world's entity-count band ceiling), recalibrated all 9 anchors
(3 worlds x 3 seeds, 200t). **ECONOMY did not move off C in any of the 9** — this was not a content
gap. Direct evidence: `resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction` have
never fired in any calibration run in the corpus, ever, including `urban_political`'s own 8 seed/
tick combinations and a diagnostic 1000t probe of `frontier_extended` at merchant_count 6. The
corpus's only observed ECONOMY signal, at any content level, is the generic `gold_sink_fired`
Gini-threshold mechanism. See the ECONOMY paragraph above and `docs/parity_ledger/infrastructure.yaml`
INFRA-242 for the full finding.

**2026-08-05 correction — the goal-generation investigation this recommendation called for has
already happened, and mostly closed.** `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` (**DONE**,
landed the day after this recommendation was first written) did exactly the investigation this
section originally called for: found the general `ObjectiveKind` routing gap in
`TacticalDecisionSystem`, fixed it by wiring the previously-orphaned `ObjectiveIntentResolver` into
production, and — critically — ran **real, non-mocked calibration verification**, not just
isolated unit tests, precisely isolating exactly 3 remaining contributing factors (full detail in
Finding 2 above): (1) `ENABLE_ADVENTURE_ROUTING` defaults OFF in shipped profiles, tied to AGENCY's
own DA-ruled design; (2) `AdventureRouteScorer` never selects craft/buy routes even when routing is
on, empirically confirmed 0/492 and 0/342 across 2 real routing-enabled runs; (3) the
`REACH_RESOURCE→MOVE_TO` arrival-transition gap. Factor 3 was fixed by the direct follow-up
`TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` (**DONE**). This session's fresh
full-corpus run confirms Factor 3's fix alone was not sufficient — exactly as that ticket's own
Completion Summary predicted, since Factors 1 and 2 were deliberately left out of its scope.

**Factor 2 — investigated and closed 2026-08-05** (`TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS`):
confirmed correct scorer behavior, not a miscalibration — see Finding 2 above for the full causal
chain. Entities are correctly blocked from craft/buy because they never harvest resources or earn
gold in the first place (the same root cause behind the zero-harvest finding), so
`AdventureRouteScorer`'s flat `blocker_penalty=2.0` correctly zeroes their score every time. No
scoring fix was made — forcing craft/buy to score higher without entities actually having the
resources would manufacture an unrealistic route, not close a real gap.

**What remains, precisely:** with Factor 2 now closed as "working as intended," the only path left
to make ECONOMY produce a live signal is upstream — getting entities to actually harvest/earn gold,
which loops back to Factor 1 (`ENABLE_ADVENTURE_ROUTING`'s default) and the broader
goal-generation chain, not a scorer change. Whether Factor 1 should be revisited is a separate,
real decision — it would mean reopening a DA ruling, not a pure bug fix, and is not assumed here.

### 3. Wire `ActionIntentAdapter.execute()` into the production tick pipeline — DONE

**Status (corrected 2026-08-05 — this section previously, incorrectly, still listed this as
open):** done, `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE`. A new gated phase,
`InformationIntentExecutionPhase`, is wired into `src/engine/pipeline.py` (confirmed live in
source, 2026-08-05: `run_phase("information_intent_execution", ...)` calling
`InformationIntentExecutionPhase.execute()`), behind a new `ENABLE_INFORMATION_INTENT_EXECUTION`
flag (default `OFF` in every shipped profile). Proven firing through a real `Kernel.tick_once()`
loop via a dedicated test
(`test_information_intent_execution_fires_through_kernel_tick_once`) — though the ticket's own
Implementation Notes disclose the `urban_political` corpus itself does not naturally route
Branch B within a 200-tick/seed-42 window, so the proof uses a hand-built scenario, not a live
calibration run. The mechanism is real and correctly wired; whether any shipped world/profile
actually exercises it in practice is a separate, not-yet-answered question — not blocking, since
this item's own AC only required the call site to exist and fire correctly when invoked.

### 4. Persist raw `normalized_score` alongside the letter grade, with its own tolerance check — DONE

**Status (corrected 2026-08-05 — this section previously, incorrectly, still listed this as
open):** done, `TCK-20260713-SIMQ-RAWSCORE-PERSIST`. `grade_anchors.json` now stores
`{"grade": "S", "score": 2.87}` per pillar per anchor entry (confirmed live in the fixture,
2026-08-05 — e.g. `sandbox_world_seed42_200t`'s `FACTION` entry reads
`{"grade": "S", "score": 2.9}`), and `test_grade_regression.py` independently asserts the raw
score stays within a documented tolerance
(`abs_delta <= max(SCORE_TOLERANCE_ABS_FLOOR=0.05, SCORE_TOLERANCE_REL_PCT=0.20 * |anchor_score|)`)
of the anchored value — confirmed live in source, 2026-08-05. This mechanism is exactly what
surfaced Finding 1 above (the WORLD pillar's stale-anchor score-tolerance failures) — this
session's own audit run depended on this fix already being live without realizing it, which is
what caused the original staleness in this section.

**Not recommended right now:** re-opening FACTION/INFORMATION/SOCIAL/AGENCY depth (all closed with
real evidence, see Phase 5 ruling), or any of SimQ's explicit MVP Non-Goals (per-entity profiles,
historical run comparison, real-time alerting, ML anomaly detection, automated config suggestion —
`quality_scoring_contract.md` §14, reaffirmed out of scope by explicit user decision 2026-07-10).

---

## Related

- `docs/audits/D20_simq_quality_status_review.md` — the broader-view synthesis document (findings
  interpretation, candidate work items, epic-scoping recommendation) that draws on this doc's
  numbers; read that doc first for "what should we do about this," this doc for "what are the
  current numbers"
- `docs/simulation_quality/quality_scoring_contract.md` — the authoritative scoring spec
- `docs/simulation_quality/eval_matrix_results.md` — full historical calibration batch log
- `docs/simulation_quality/corpus_tier_taxonomy.md` — corpus tier structure and per-world classification
- `docs/plans/archive/simq_development_roadmap.md` — the closed roadmap this report's "declared
  complete" pillars trace back to
- `docs/audits/D20_simq_integration.md` — wiring/calibration history, investigation-pattern precedent
