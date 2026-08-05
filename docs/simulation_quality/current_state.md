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

**Last refreshed:** 2026-08-05, via a real full-corpus live engine re-run (`make simq-full-audit-full`,
`data/calibration/` was empty going in — a fresh-checkout state, not a targeted diff). 75 of 76
anchor scenarios produced a report (`unit_selfmodel_pilot_seed42_1000t` hit `PRESSURE`-mode
backpressure during calibration and was excluded as unreliable — see Known Issue below). This
refresh found 2 real findings the 2026-07-13 refresh predates: **(1)** the WORLD pillar's committed
anchors are now stale against a real, intentional scoring change landed since, and **(2)** an
ECONOMY fix that looked promising on paper has zero measured effect on this corpus. Both detailed
below. Superseded text (2026-07-13, post `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`): "75 real
scenario entries, 18 worlds... each entry independently verified against a live run at the time it
was last committed."

---

## 2026-08-05 refresh — 2 real findings

### Finding 1: WORLD pillar anchors are stale — a real scoring change, not a regression

`test_grade_regression.py` (fast tier, 200t/500t) found **20 of 65 comparable scenarios** drifted
beyond score tolerance — **19 of the 20 are the WORLD pillar**, every one scoring *lower* than its
anchor by a consistent delta (e.g. `anchor=0.09 → actual=-0.06`, `anchor=0.59 → actual=0.44`,
`anchor=0.24 → actual=0.09` — deltas cluster around -0.15/-0.12/-0.075 depending on scenario).

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
| WORLD | 0 | 3 | 62 | 10 | 0 | **A 4→3, B 71→62, C 0→10 — real regression-gate-visible drop** |

The one non-WORLD outlier, `urban_political_seed42_200t` (NARRATIVE `A`, SOCIAL `S` — letter
grades unchanged, only the raw `normalized_score` drifted outside its tolerance band), is far more
likely ordinary run-to-run variance (already documented in `docs/audits/D20_simq_integration.md`'s
wall-clock-throttle findings) than a real issue — not part of the WORLD pattern above.

**Not yet fixed in this refresh** — recalibrating `grade_anchors.json`'s WORLD column is a real,
scoped follow-up, deliberately not done unilaterally as part of a status-report refresh.

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
     outscored by `form_party`/`gather_resource`.
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

### Known issue — 1 unreliable run this refresh

`unit_selfmodel_pilot_seed42_1000t` failed its calibration integrity check
(`pressure_mode_final=PRESSURE`, `dropped_count=0` — events were sampled/shed under observability
backpressure, not silently lost, but the run is flagged unreliable and excluded here). Likely
session-load-related (this machine was running substantial concurrent load during this refresh),
not a content issue — unconfirmed, not investigated further as part of this refresh.

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
this doc's numbers as current. Real full-corpus engine runtime: ~15-20 minutes for the 76-scenario
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

## Current grade distribution (75 of 76 anchor entries, live-corpus run, 2026-08-05)

`unit_selfmodel_pilot_seed42_1000t` excluded — unreliable run this refresh, see Known Issue below.
WORLD's distribution reflects Finding 1 above (stale anchors, not a real regression); ECONOMY's
reflects Finding 2 (fix landed, zero measured effect on this corpus). All other pillars are
materially unchanged from 2026-07-13 within normal rounding.

| Pillar | S | A | B | C | D |
|---|---|---|---|---|---|
| WORLD | 0 | 3 | 62 | 10 | 0 |
| NARRATIVE | 8 | 59 | 4 | 4 | 0 |
| COMBAT | 0 | 0 | 44 | 31 | 0 |
| PROGRESSION | 0 | 8 | 39 | 28 | 0 |
| FACTION | 31 | 15 | 6 | 23 | 0 |
| INFORMATION | 0 | 3 | 36 | 36 | 0 |
| COGNITION | 8 | 5 | 40 | 22 | 0 |
| SOCIAL | 16 | 0 | 0 | 59 | 0 |
| ECONOMY | 0 | 1 | 16 | 58 | 0 |
| AGENCY | 0 | 8 | 0 | 67 | 0 |

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

### 0. Recalibrate WORLD pillar anchors against the new spawn-occupancy signal — NEW, URGENT

**Why now:** Finding 1 above — `TCK-20260716-PLACELEGAL-SIMQ-SIGNAL` (07-30) correctly,
intentionally added a new `spawn_occupancy_violation` signal to WORLD DYNAMICS scoring, but
`grade_anchors.json` was never recalibrated against it. Result: 19 of 20 real
`test_grade_regression.py` failures found by this refresh are this exact stale-anchor pattern —
the regression gate is currently crying wolf on WORLD for every scenario that happens to have any
spawn-occupancy collision, which is real signal, not noise, but the *anchors* don't know that yet.
Until this is recalibrated, WORLD's regression gate cannot distinguish a genuine future regression
from this already-known, already-explained baseline shift.

**Shape of the work:** re-run calibration for the ~19 affected `WORLD` anchor entries (or the full
corpus, simpler and safer) and commit the new WORLD scores/grades to `grade_anchors.json`. Small,
mechanical, well-scoped — the root cause is already fully diagnosed by this refresh, no further
investigation needed first.

**Effort estimate:** S — a recalibration + anchor-file update, not new logic.

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

**What remains, precisely:** Factor 2 is the one real, actionable, narrowly-scoped remaining gap —
it doesn't require reopening AGENCY's DA ruling (Factor 1), it's already empirically isolated
(`AdventureRouteScorer`'s existing bias terms, not touched by any prior ticket), and closing it
would let ECONOMY actually produce a live signal in the routing-enabled worlds that already exist
in the corpus. Whether Factor 1 (turning `ENABLE_ADVENTURE_ROUTING` on more broadly) should also be
revisited is a separate, real decision — it would mean reopening a DA ruling, not a pure bug fix,
and is not assumed here.

**Effort estimate:** S-M for Factor 2 alone (a scorer-bias investigation + fix, with the routing
mechanism itself already proven correct) — substantially smaller than this recommendation's
original "unknown, likely larger than M" estimate, now that the harder routing-infrastructure work
is already done.

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
