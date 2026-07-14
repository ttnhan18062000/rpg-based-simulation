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

**Last refreshed:** 2026-07-13 (post `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`), from the committed
`tests/simulation_quality/fixtures/grade_anchors.json` (**75 real scenario entries, 18 worlds** —
corrected from the previously-cited "72 entries, 17 worlds"; the file's 3 non-scenario meta keys
(`_note`, `_instructions`, `_grade_order`) had been under-excluded by one in the prior count, and
`TCK-20260713-SIMQ-SCORE-CEILING-FIX` separately added 1 new world, `unit_information_density`,
3 seeds) — each entry independently verified against a live run at the time it was last committed,
spot-checked here via a standalone `calibrate_simq.py` re-run of
`urban_political_selfmodel_probe_seed42_200t` (see Known Issue below for why the full-corpus live
run couldn't be used directly this time).

`TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` composed `trading_company_hub` into 3 more worlds
(`frontier_living_world`, `frontier_extended`, `swamp_border_world`) and recalibrated their 9
anchors (3 worlds x 3 seeds, 200t) — this moved 9 anchors' COMBAT/PROGRESSION/SOCIAL/WORLD/
NARRATIVE columns (new entities/quest content changing those pillars' event counts as a side
effect) but **ECONOMY itself did not move for any of the 9** — see Recommendation 2 below for why.

**To refresh this report:** `python3 tools/evaluate_simq.py --dry-run`, then update the table below
from its output. Prefer `--dry-run` for now — see the known tooling bug below before running the
live (non-dry-run) full-corpus mode. If `--dry-run` reports any `REGRESS` pillars, resolve those
first (stale anchor vs. real regression — see `docs/audits/D20_simq_integration.md` for the
established investigation pattern) before treating this doc's numbers as current.

**Known issue — `tools/evaluate_simq.py`'s live (non-`--dry-run`) mode has a real bug:**
`_run_calibration()` (line 59) never forwards `--profile` to `calibrate_simq.py`; `_parse_run_key()`
(line 45) derives the calibration `--name` purely from the run_key's regex-matched prefix. For any
run_key where the profile name differs from the world name (currently only
`urban_political_selfmodel_probe_seed42_200t`, the probe fixture added this session), this passes
the *profile* name where the *world* name is expected. `calibrate_simq.py`'s world-loading then
silently falls back to a generic synthetic scenario (`world_id: "unknown"`,
`scenario_name: "PROD_SMALL"`, confirmed via that run's `run_manifest.json`) instead of erroring —
producing a near-empty, meaningless result that gets compared against the real anchor. Verified via
a standalone re-run of the same scenario, which reproduces the correct, anchor-matching result
(COGNITION=S/5610 events, FACTION=S/29, SOCIAL=S/770, NARRATIVE=A/11) — confirming this is a tooling
bug, not a quality regression. Evidence preserved in `tmp/evaluate_simq_bug_evidence/`. Not yet
filed as a ticket.

---

## Current grade distribution (75 anchor entries, 18 worlds)

| Pillar | S | A | B | C | D |
|---|---|---|---|---|---|
| WORLD | 0 | 4 | 71 | 0 | 0 |
| NARRATIVE | 7 | 55 | 9 | 4 | 0 |
| COMBAT | 0 | 1 | 46 | 28 | 0 |
| PROGRESSION | 0 | 8 | 39 | 28 | 0 |
| FACTION | 30 | 15 | 6 | 24 | 0 |
| INFORMATION | 0 | 3 | 35 | 37 | 0 |
| COGNITION | 8 | 8 | 37 | 22 | 0 |
| SOCIAL | 15 | 0 | 0 | 60 | 0 |
| ECONOMY | 0 | 1 | 17 | 57 | 0 |
| AGENCY | 0 | 8 | 0 | 67 | 0 |

WORLD/PROGRESSION moved by 2/1 entries respectively as a side effect of
`TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`'s content addition (new entities/quest content shifting
those pillars' event counts in `frontier_living_world`/`frontier_extended`'s 200t anchors) — **not**
an intentional target of that ticket, which targeted ECONOMY. ECONOMY's own distribution is
unchanged (0/1/17/57) — the content addition did not move it; see Recommendation 2 below.

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

Three remain genuinely open — not previously investigated-and-declined, unlike FACTION/
INFORMATION/SOCIAL depth (closed) or AGENCY rollout (closed). None requires re-litigating any
existing DA ruling. Numbering preserved from the prior refresh for continuity even though item 1 is
now done; 4 was (and remains) a measurement-validity fix that probably belongs before 2 and 3 in any
real sequencing, since it affects whether *any* future content-authoring or engine work would even
be visible in the grades.

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

**What this means for future work:** the real gap is upstream, in the strategy/cognition layer — no
entity archetype currently generates an accepted harvest, craft, or trade intent, so
`trading_company_hub`'s merchants (and every other archetype in the corpus) never exercise the
resolution path `event_extractor.py` reads from. This is structurally similar to AGENCY's
`ENABLE_ADVENTURE_ROUTING` gap (a real behavior path that exists but has no live trigger in any
shipped world/profile) — **not** a "the modules/populations aren't there yet" problem, which is
what this recommendation originally assumed. A follow-up investigation into why no entity ever
forms/accepts a NODE/CRAFTING/SHOP_BUY/SHOP_SELL intent (goal-generation in the strategy layer, or
a missing wiring analogous to AGENCY's) is the next real step for this pillar — content authoring
alone cannot close it further. Not filed as a new ticket by this recommendation update; left for a
deliberate scoping decision given the depth of engine-layer work implied.

**Effort estimate for the follow-up:** unknown until the strategy-layer investigation is done — likely
larger than the M estimate this recommendation originally carried, since the gap is now understood
to be a missing decision/goal-generation path rather than a content-volume shortfall.

### 3. Wire `ActionIntentAdapter.execute()` into the production tick pipeline

**Why now:** this is the specific, named blocker the Phase 5 gate identified and explicitly
deferred as "a distinct future initiative if gameplay ever actually needs live self-model
query-routing" — not a re-opening of a closed question, but picking up a thread that was
deliberately left for exactly this kind of follow-up decision.

**Shape of the work:** add a new gated phase to `src/engine/pipeline.py` (matching the existing
`run_phase("cooperation", ...)` / `run_phase("information_belief", ...)` pattern) that takes the
`ActionIntent` routed by `InformationBeliefPhase` Branch B and calls
`ActionIntentAdapter.execute()` on it, merging the resulting `EntityUpdate` back into the tick's
update set. Should start as an investigation ticket — the exact merge point, ordering relative to
the two existing information/cooperation phases, and whether a new feature flag is needed (almost
certainly yes, to keep this off by default in shipped profiles) all need scoping before
implementation.

**Effort estimate:** M-L — this is real engine work (a new pipeline phase, not content authoring),
but narrowly scoped: the routing and execution logic already exist and are already tested in
isolation; the gap is purely the missing call site.

### 4. Persist raw `normalized_score` alongside the letter grade, with its own tolerance check

**Why now:** `grade_anchors.json` stores only the discretized letter (`"S"`, `"B"`, etc.) — never
the raw `normalized_score` that produced it, even though every `quality_report.json` computes and
prints it. Combined with S being an unbounded top band (`>2.0`, no ceiling specified), this makes
the regression-detection goal itself blind in both directions for any pillar already at S: a real
improvement (e.g. norm-score 2.1 → 10.0) shows as "S → S", invisible — but so does a real
*regression* (10.0 → 2.1) that doesn't happen to cross a full band boundary. The anchor system can
currently only catch changes that cross a grade-letter line, not changes in magnitude within one.

**Why this isn't the excluded Non-Goal:** SimQ's §14 explicitly rules out "historical run
comparison" (dashboards, trend charts across runs over time) — that stays out of scope, reaffirmed
2026-07-10. This is narrower: one additional number stored per anchor entry, checked with one
additional tolerance assertion, squarely inside the existing regression-detection goal (§1), not a
new comparison/analytics capability.

**Shape of the work:** extend `grade_anchors.json`'s schema to carry `{"grade": "S", "score":
2.87}` per pillar instead of a bare string (migration needed for all 75×10 existing entries);
extend `test_grade_regression.py`'s comparison to also assert the raw score stays within a
tolerance band (e.g. ±15%) of the anchored value, independent of whether the letter grade moved.
Should start as an investigation ticket to confirm the right tolerance width empirically (too tight
→ false positives from legitimate run-to-run variance already documented in
`docs/audits/D20_simq_integration.md`'s wall-clock-throttle findings; too loose → doesn't actually
catch anything the letter-only check wouldn't).

**Effort estimate:** S-M — schema migration touches every anchor entry, but the logic itself is a
straightforward tolerance check, not new scoring infrastructure.

**Not recommended right now:** re-opening FACTION/INFORMATION/SOCIAL/AGENCY depth (all closed with
real evidence, see Phase 5 ruling), or any of SimQ's explicit MVP Non-Goals (per-entity profiles,
historical run comparison, real-time alerting, ML anomaly detection, automated config suggestion —
`quality_scoring_contract.md` §14, reaffirmed out of scope by explicit user decision 2026-07-10).

---

## Related

- `docs/simulation_quality/quality_scoring_contract.md` — the authoritative scoring spec
- `docs/simulation_quality/eval_matrix_results.md` — full historical calibration batch log
- `docs/simulation_quality/corpus_tier_taxonomy.md` — corpus tier structure and per-world classification
- `docs/plans/archive/simq_development_roadmap.md` — the closed roadmap this report's "declared
  complete" pillars trace back to
- `docs/audits/D20_simq_integration.md` — wiring/calibration history, investigation-pattern precedent
