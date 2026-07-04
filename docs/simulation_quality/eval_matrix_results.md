# SimQ Multi-Seed / Multi-Tick Evaluation Matrix Results

**Ticket:** TCK-20260702-SIMQ-EVAL-MATRIX
**Date:** 2026-07-02
**Corpus expansion:** 8 anchor entries → 25 anchor entries

---

## Overview

This document records the grade distributions from the multi-seed, multi-tick calibration matrix.
Seventeen new calibration runs were executed across four signal-producing worlds. Per-pillar grades
are extracted from `data/calibration/{run_key}/quality_report.json` and committed to
`tests/simulation_quality/fixtures/grade_anchors.json`.

Zero-pillar worlds (AGENCY/COGNITION/ECONOMY/SOCIAL/FACTION/INFORMATION all C in default mode)
were not included at the time: `wilderness_survival`, `highland_traverse`, `swamp_border_world`,
`frontier_extended`, `frontier_living_world`. All confirmed structurally feature-gate blocked.
**Now anchored as of TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS** — see "Newly-Anchored Worlds"
section below. The feature-gate-blocked pillars remain C (unchanged, structural, not a
regression); these worlds add entity-count/region-count/module-family diversity to the corpus
(COMBAT/NARRATIVE/PROGRESSION/WORLD signal), not new pillar coverage.

---

> **NOTE (TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY — D2 formula fix):** Grade tables in this document
> were re-calibrated on 2026-07-02 after fixing the tick-dilution artifact (H2) in the
> normalized_score formula. The original formula divided raw_score by current_tick, causing
> identical activity to receive lower grades in longer runs. The corrected formula uses
> `max(floor_tick, last_event_tick)` as divisor, where `floor_tick = current_tick // 4`.
> All 25 anchored scenarios were re-run; 24 pillar grades changed. The most significant
> change: **COMBAT and PROGRESSION in dungeon_crawl now hold A at 500t and 1000t** (previously B
> due to tick-dilution). WORLD holds B (unchanged — it was genuinely active throughout).
> The "A→B decay" pattern previously described in the stability analysis is resolved.

> **NOTE (TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — hazard-kind recompile drift):** `dungeon_crawl`
> and `simq_routing_test` were both stale-compiled (resolved YAML predated the 2026-07-01
> hazard-kind fixes) and both use `old_mine_resource_loop`, one of the 7 modules that gained a
> `hazard_kind` declaration under this ticket (Step 1a). Per the Step 4a drift-check procedure
> (mirroring the D2-fix precedent above), all 13 pre-existing anchor entries for these two worlds
> were refreshed and diffed against their committed values after recompiling:
> **8 of `dungeon_crawl`'s 10 keys drifted** (COMBAT A→B and PROGRESSION A→B at 200t/500t;
> NARRATIVE B→A at 500t/1000t/2000t; COMBAT A→B at 1000t; WORLD A→B at 200t) — attributed to the
> `old_mine_spider_cluster` population no longer taking unconditional hazard-drain in `old_mine`
> now that the region declares `hazard_kind: "NATURAL_TERRAIN"` and `wild_beast_pack` declares
> matching `hazard_immunities`, which changes survival/engagement dynamics feeding these pillars.
> `dungeon_crawl_seed123_2000t` and `dungeon_crawl_seed456_2000t` showed **no drift**. `grade_anchors.json`
> was updated in place for the 8 drifted keys only. **`simq_routing_test`'s 3 keys could not be
> independently re-verified** — re-running its `ENABLE_ADVENTURE_ROUTING=ON` calibration crashes
> with `KeyError: Resource not found in ResourceRegistry: STONE` (a pre-existing, unrelated bug in
> `src/world/ecology.py`'s dynamic resource-node generation, confirmed via `git stash` bisection to
> reproduce identically with and without this ticket's content changes — see Implementation Notes
> in `tickets/done/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS.md`). `simq_routing_test`'s 3 anchor
> entries are left unchanged (not silently marked as verified); a follow-up ticket is recommended
> for the `ResourceRegistry` gap.

> **NOTE (TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP — STONE/WOOD/IRON kind-emission fix,
> `simq_routing_test` re-verified for the first time):** `src/world/ecology.py`'s dynamic
> resource-node generator emitted hardcoded `"WOOD"`/`"STONE"`/`"IRON"` literals that matched no
> `ResourceRegistry` entry (catalog ids are lowercase — `wood_node`/`iron_vein` — and no `"stone"`
> resource existed at all). Fixed: emission now uses real catalog ids (`wood_node`/`iron_vein`/a
> newly-authored `stone_outcrop`), and `yields_item` is derived from
> `ResourceRegistry.get(kind).yield_item` instead of hand-computed. `simq_routing_test`'s 3 regions
> (`hometown`, `goblin_camp`, `old_mine`) all compile to `kind` values other than `FOREST`/`MOUNTAIN`
> (`TOWN`/`WILDERNESS`), so under the pre-fix code **every** ecology-seeded node in this world was
> `"STONE"` — the crash was 100% deterministic once ecology's tick-200 seed check fired, meaning no
> prior calibration of this exact world+`ENABLE_ADVENTURE_ROUTING=ON` combination had ever run to
> completion since the bug was introduced (2026-05-18) or since the 2026-07-01 hazard-kind recompile
> changed this world's entity/RNG dynamics. **This is therefore the first real, complete calibration
> of the post-hazard-kind-recompile `simq_routing_test` world** — the 3 previously-committed anchor
> entries were stale placeholders from before both the recompile and this fix, not a comparable
> baseline. All 10 pillars drifted for all 3 seeds (seed42/123/456); `grade_anchors.json` was updated
> in place for all 3 keys. Full new pillar breakdown in the updated table below.
>
> **AC6 gate violation found (out of scope to fix here):** `seed456` now grades `AGENCY=F`
> (`normalized_score=-345.08`), breaking the AC6 gate ("AGENCY ≥ B confirmed for all three
> `simq_routing_test` seeds"). Root cause traced in `quality_scores.jsonl` for
> `run_1783171252_1673`: entity 23 enters a sustained `defer_with_reason` streak starting at
> **tick 176** — before ecology's first seed check (tick 200) can possibly write any
> `wood_node`/`iron_vein`/`stone_outcrop` node into state — so this stasis dynamic is provably
> unrelated to the STONE/WOOD/IRON content fix or to the new `stone_outcrop` resource (whose
> `source_region_tags=("frontier_village",)` doesn't even match any of this world's actual region
> ids, so `stone_outcrop` opportunities never surface here regardless). The escalating
> `stasis_per_tick` penalty (`config/simulation_quality/scoring_weights.yaml:20`, `-3.0` per tick
> past `stasis_gate_ticks`, applied per subsequent defer event) compounds once a population-wide
> idle streak crosses the gate, producing the large negative raw score (`-172541.0` over 693 AGENCY
> events, 491 of them `defer_idle`/`stasis_N`-tagged). This is a pre-existing property of the
> 2026-07-01-recompiled world + `AgencyScorer`'s stasis formula, first observable now only because
> the STONE crash no longer blocks this world from running to completion — it is not introduced by
> this ticket's fix and is out of scope to remediate here (touching `AgencyScorer`/entity idle
> decision logic is unrelated to a `ResourceRegistry` catalog-id bug). **A follow-up ticket is
> recommended** to investigate why `seed456` (and not `seed42`/`seed123`) drives an entity into a
> sustained defer streak in this world, and whether AC6's "AGENCY ≥ B for all 3 seeds" gate needs
> revision or the underlying stasis-entry condition needs a fix.
>
> **Anchor schema note:** `tests/simulation_quality/fixtures/grade_anchors.json`'s consumer
> (`tests/simulation_quality/test_grade_regression.py`, `GRADE_ORDER = ["D","C","B","A","S"]`)
> has no representable slot for `F` — `test_grade_anchor_file_exists_and_valid` asserts every anchor
> is a `GRADE_ORDER` member. `seed456`'s AGENCY anchor is therefore recorded as `"D"` (the schema's
> floor, not the true observed grade) purely so the fixture stays schema-valid; the true raw grade
> is `F` (`normalized_score=-345.08`). This is intentional: with anchor=`D`, a re-run that still
> grades `F` will correctly keep failing `test_grade_within_anchor_band` (`"F"` is not in
> `GRADE_ORDER` at all, so no anchor value can silently absorb it) until the underlying stasis bug
> is actually fixed and re-anchored.

---

## Grade Distribution Tables

### Notation

- Each cell shows the grade per seed (seed42 / seed123 / seed456) or a single grade where all seeds agree.
- "Stable" means identical grade across all seeds at that tick count.
- GRADE_ORDER: D < C < B < A < S

---

### dungeon_crawl

#### 500t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Stable? | Note |
|---|---|---|---|---|---|
| COMBAT | B | B | B | yes | was A pre-recompile; hazard-kind fix to `old_mine_resource_loop` changed `old_mine_spider_cluster` survival dynamics (TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS Step 4a) |
| NARRATIVE | A | A | A | yes | was B pre-recompile (same cause) |
| PROGRESSION | B | B | B | yes | was A pre-recompile (same cause) |
| WORLD | B | B | B | yes | |
| AGENCY | C | C | C | yes | |
| COGNITION | C | C | C | yes | |
| ECONOMY | C | C | C | yes | |
| FACTION | C | C | C | yes | |
| INFORMATION | C | C | C | yes | |
| SOCIAL | C | C | C | yes | |

#### 1000t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Stable? | Note |
|---|---|---|---|---|---|
| COMBAT | B | B | B | yes | was A pre-recompile; hazard-kind recompile shift (Step 4a) |
| NARRATIVE | A | B | A | mostly | seed123 unchanged at B; seed42/456 were B pre-recompile, now A |
| PROGRESSION | B | B | B | yes | floor=250, unchanged |
| WORLD | B | B | B | yes | |
| AGENCY | C | C | C | yes | |
| COGNITION | C | C | C | yes | |
| ECONOMY | C | C | C | yes | |
| FACTION | C | C | C | yes | |
| INFORMATION | C | C | C | yes | |
| SOCIAL | C | C | C | yes | |

#### 2000t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Stable? | Note |
|---|---|---|---|---|---|
| COMBAT | B | B | B | yes | unchanged by hazard-kind recompile |
| NARRATIVE | A | B | B | no | seed42 was B pre-recompile, now A (Step 4a); seed123/456 unchanged (no drift) |
| PROGRESSION | B | B | B | yes | |
| WORLD | B | B | B | yes | |
| AGENCY | C | C | C | yes | |
| COGNITION | C | C | C | yes | |
| ECONOMY | C | C | C | yes | |
| FACTION | C | C | C | yes | |
| INFORMATION | C | C | C | yes | |
| SOCIAL | C | C | C | yes | |

**Stability analysis (dungeon_crawl, post-D2 fix, post-hazard-kind-recompile):** COMBAT and
PROGRESSION now hold **B at 500t/1000t** (down from A) and NARRATIVE now holds **A at 500t and at
1000t/2000t for 2 of 3 seeds** (up from B) — a consequence of Step 4a's hazard-kind recompile of
`old_mine_resource_loop`/`old_mine_spider_cluster` changing this world's survival/engagement
dynamics, not a scoring regression (see the hazard-kind recompile drift NOTE above for the full
attribution and the confirmed-unchanged keys: `dungeon_crawl_seed123_2000t`,
`dungeon_crawl_seed456_2000t`). WORLD holds B across all tick counts (unchanged — it was genuinely
active throughout at last_event_tick≈400). dungeon_crawl remains otherwise deterministic across
seeds within each tick count.

**Archetype Note (TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG):** ECONOMY=C and COGNITION=C
are archetype-correct for dungeon_crawl and are not bugs or gaps. Two root causes:

- **ECONOMY**: `gold_sink_fired` (the only active ECONOMY event path globally) requires
  `GoldSinkSystem` to detect Gini > 0.7 (`INFLATION_SPIRAL_GINI_THRESHOLD` in
  `src/economy/health_monitor.py`). dungeon_crawl's 7 entity groups are all combat/creature
  archetypes (goblin, spider, undead, bandit) — symmetric combat looting keeps the Gini
  coefficient well below 0.7. No merchant NPC and no service buildings exist.
- **COGNITION**: `decision_divergence_detected` fires when "DANGER concern urgency > 0.7 AND
  non-survival project" (`src/systems/event_extractor/phase.py`). dungeon_crawl entities are
  permanently in combat/survival mode — the non-survival project condition is never satisfied.

*Anti-drift:* If a merchant NPC, service building, or entity with a non-combat behavioral
profile (e.g., dungeon guide, treasure hunter) is added to dungeon_crawl, re-run calibration
and reassess these grades.

---

### urban_political

#### 500t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| COMBAT | B | B | A | seed456 elevated to A (D2 fix) |
| NARRATIVE | A | A | B | seeds 42 and 123 elevated to A (D2 fix) |
| PROGRESSION | B | B | B | stable |
| WORLD | B | B | A | seed456 elevated to A |
| SOCIAL | S | S | S | SOCIAL=S all seeds (ENABLE_SOCIAL_COOPERATION active; high event density) |
| AGENCY | C | C | C | stable — gated by `ENABLE_ADVENTURE_ROUTING=OFF`, archetype-correct (see AGENCY Cross-World Design Note below) |
| COGNITION | B | B | B | C→B (SimQ Uplift Batch 2, 2026-07-03): `belief_updated` single-fire event, co-scored by `CognitionScorer` |
| ECONOMY | C | C | C | stable |
| FACTION | A | A | A | C→A (SimQ Uplift Batch 2, TCK-20260702-SIMQ-UPLIFT2-FACTION): `bandit_company`/`town_council` seeded at `tension_level=0.5`, 29 `diplomatic_transition` hits/run |
| INFORMATION | B | B | B | C→B (SimQ Uplift Batch 2, TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER): `pending_information_responses` seed + kernel tick-alignment fix, `belief_assimilated` calibration_hits=1/run |

#### 1000t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| COMBAT | B | B | B | stable |
| NARRATIVE | B | B | B | stable |
| PROGRESSION | B | B | B | stable |
| WORLD | B | B | B | stable |
| ECONOMY | B | B | B | all three seeds activated at 1000t |
| SOCIAL | S | S | S | SOCIAL=S all seeds (high event density throughout 1000t run) |
| COGNITION | B | B | B | seed42/seed456 C→B (SimQ Uplift Batch 2); seed123 already B (unchanged) |
| AGENCY | C | C | C | stable — gated by `ENABLE_ADVENTURE_ROUTING=OFF`, archetype-correct |
| FACTION | A | A | A | C→A (SimQ Uplift Batch 2) — same mechanism as 500t, tension seed persists across tick lengths |
| INFORMATION | B | B | B | C→B (SimQ Uplift Batch 2) — single-fire `belief_assimilated` at tick 0, unaffected by run length |

**Stability analysis (urban_political, post-D2 fix):** SOCIAL now grades S across all seeds at
both 500t and 1000t — `ENABLE_SOCIAL_COOPERATION=ON` produces high contract/cooperation event
density throughout the run; last_event_tick ≈ current_tick so the floor does not activate; S is
correct (normalized score >> 2.0). NARRATIVE and COMBAT show some seed-dependent variation (B↔A)
at 500t due to the formula now using last_event_tick; this is genuine quality signal, not noise.
At 1000t, NARRATIVE normalizes to B across all seeds. ECONOMY activates at 1000t for all three
seeds (C→B), confirming duration effect. **SimQ Uplift Batch 2 (2026-07-02/03):** FACTION moved
C→A at both 500t and 1000t (compile-time `tension_level` seeding survives across tick lengths
since it's read live every tick from durable `FactionState`, unlike the two single-fire cases
below); INFORMATION moved C→B at both durations (a single `belief_assimilated` fire at tick 0 —
weight-scaled by tick count, crosses the C/B threshold regardless of run length, but does not
grow with additional ticks); COGNITION moved C→B in 6 of 7 scenarios as a side effect of
`belief_updated` also being scored by `CognitionScorer` (seed123 at 1000t was already B before
this batch, from a separate transient signal). AGENCY remains C — unaffected by this batch;
see the AGENCY Cross-World Design Note below for why that is archetype-correct, not a gap.

---

### simq_routing_test (ENABLE_ADVENTURE_ROUTING=ON)

#### 500t (seeds 42 / 123 / 456) — re-verified 2026-07-04, TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP

> The table below supersedes the pre-fix values (see the dated NOTE above): this is the first
> completed calibration of this world since the 2026-07-01 hazard-kind recompile, because the
> `ResourceRegistry: STONE` crash previously blocked every attempt to run it to completion.

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| AGENCY | A | A | **F** (anchored as D — schema floor, see note) | seed42/123 legitimate (norm 1.42, 0.64); seed456=F, sustained defer/stasis streak from entity 23 starting tick 176 (see AC6 note below) — **not** caused by this ticket's content fix |
| COGNITION | A | S | S | events 101/233/173 respectively |
| COMBAT | C | C | C | 0 combat events all 3 seeds |
| NARRATIVE | S | S | A | seed42/123 norm 4.28/2.37; seed456 norm 1.91 |
| PROGRESSION | C | C | C | norm ≈ -0.06, event_count=1, all 3 seeds |
| WORLD | B | B | B | stable |
| ECONOMY | C | C | C | 0 events, all 3 seeds |
| FACTION | C | C | C | 0 events, all 3 seeds |
| INFORMATION | C | C | C | 0 events, all 3 seeds |
| SOCIAL | C | C | C | 0 events, all 3 seeds |

**AC6 gate status (re-verified 2026-07-04):** AGENCY ≥ B confirmed for seed42 (A) and seed123 (A),
but **violated for seed456 (F)** — see the dated NOTE above for root-cause tracing (entity 23's
tick-176 defer streak, provably unrelated to the STONE/WOOD/IRON emission fix or the new
`stone_outcrop` resource). Gate does not fully pass post-recompile; a follow-up ticket is
recommended to investigate the seed456-specific stasis dynamic. The historical pre-recompile
analysis below is retained for traceability only and no longer reflects the current world state.

---

#### Historical pre-recompile table (superseded, retained for traceability)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| AGENCY | B | A | A | seed42=B (floor=100, 40/100=0.40 → B); seeds 123/456=A (D2 fix: 137/100=1.37, 170/100=1.70 → A) |
| COGNITION | C | B | B | seeds 123 and 456 show B |
| COMBAT | B | A | B | seed123 elevated to A (D2 fix) |
| NARRATIVE | A | A | A | stable — highest grade in corpus |
| PROGRESSION | B | B | B | stable |
| WORLD | B | B | B | stable |
| ECONOMY | C | C | C | stable |
| FACTION | C | C | C | stable |
| INFORMATION | C | C | C | stable |
| SOCIAL | C | C | C | stable |

**AGENCY cross-seed confirmation (AC6, post-D2 fix, pre-recompile):**
- seed42: AGENCY=B (floor=100 > last_event_tick=1; 40/100=0.40 → B — correct, initialization burst damped)
- seed123: AGENCY=A (floor=100 > last_event_tick=1; 137/100=1.37 → A — legitimate: 3.4× more events than seed42)
- seed456: AGENCY=A (floor=100 > last_event_tick=1; 170/100=1.70 → A — legitimate: 4.25× more events than seed42)

**Stability analysis (simq_routing_test, post-D2 fix, pre-recompile):** NARRATIVE=A stable across all three seeds.
AGENCY shows seed-dependent variation (B for seed42, A for seeds 123/456) — this is correct
behavior: the floor prevents S-grade inflation from AGENCY's initialization burst at tick 1, and
the grade reflects actual event count differences (137 vs 40 events). COGNITION shows B for seeds
123/456 only — borderline signal, consistent with prior analysis.

---

### sandbox_world

#### 1000t (seed 42 — pre-existing)

| Pillar | grade |
|---|---|
| NARRATIVE | A |
| COGNITION | B |
| ECONOMY | B |
| COMBAT | B |
| PROGRESSION | B |
| WORLD | B |
| AGENCY | C |
| FACTION | C |
| INFORMATION | C |
| SOCIAL | C |

#### 2000t (seed 42 — new)

| Pillar | grade | vs 1000t | Note |
|---|---|---|---|
| NARRATIVE | A | held at A | was B in pre-D2 anchors; D2 fix: last_event_tick active, norm=0.51 → A |
| COGNITION | B | held | |
| ECONOMY | B | held | |
| COMBAT | B | held | |
| PROGRESSION | B | held | |
| WORLD | B | held | |
| AGENCY | C | held | |
| FACTION | C | held | |
| INFORMATION | C | held | |
| SOCIAL | C | held | |

**OQ2 resolution (sandbox_world COGNITION/ECONOMY at 2000t, post-D2 fix):** COGNITION and ECONOMY
both hold at B at 2000t — they do not climb to A. The 1000t→2000t transition shows plateau
behaviour at B. NARRATIVE now holds A at 2000t (upgraded from the pre-fix B — the prior B was
tick-dilution, not genuine quality degradation). NARRATIVE's last_event_tick is close to
current_tick due to sustained quest/chronicle activity throughout the 2000t run, so the formula
correctly rewards the ongoing narrative output.

---

## OQ1 Resolution — urban_political NARRATIVE at 1000t

At 500t, seed123 showed NARRATIVE=A. At 1000t, all three seeds converge to NARRATIVE=B. This
resolves OQ1: the seed123 500t NARRATIVE=A was a window-composition effect (the 200-tick scoring
window at 500t captured a dense narrative burst). At 1000t the window captures the steady-state
rate, which grades to B. NARRATIVE is reliably B in urban_political at 1000t.

---

## OQ2 Resolution — sandbox_world COGNITION/ECONOMY at 2000t

See sandbox_world section above. Both pillars plateau at B. No upgrade to A observed. The
recommendation is to document these as confirmed B-ceiling pillars for sandbox_world in default
mode. NARRATIVE holds A at 2000t post-D2 fix (prior B was tick-dilution artifact).

---

## AC6 — AGENCY Confirmation

**Status as of 2026-07-04 re-verification (TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP): PARTIAL.**
AGENCY ≥ B confirmed for seed42 (A) and seed123 (A) with `ENABLE_ADVENTURE_ROUTING=ON`, but
**seed456 now grades AGENCY=F**, breaking the gate for that seed. This is the first completed
calibration of this world since the 2026-07-01 hazard-kind recompile (the `ResourceRegistry: STONE`
crash previously blocked every attempt to run it to completion — see the dated NOTE near the top
of this document). Root-cause tracing places seed456's failure in a tick-176 entity defer/stasis
streak, provably unrelated to the STONE/WOOD/IRON kind-emission fix (ecology's first seed check
cannot fire before tick 200). A follow-up ticket is recommended to investigate and either fix the
underlying stasis dynamic or revisit this gate's definition. Without this flag, AGENCY=C (as seen
in dungeon_crawl and urban_political default runs) — that part of the gate's premise is unaffected.
(`grade_anchors.json`'s seed456 AGENCY anchor is recorded as `D`, the fixture schema's floor — `F`
has no representable slot in `GRADE_ORDER`; see the schema note in the dated NOTE above.)

**Historical text (pre-recompile, superseded, retained for traceability):** AGENCY ≥ B confirmed
for all three simq_routing_test seeds (42, 123, 456) with `ENABLE_ADVENTURE_ROUTING=ON`. This is
the gate criterion for the `simq_routing_test` world. Post-D2 fix: seed42=B (floor-damped
initialization burst), seeds 123/456=A (legitimate upgrade reflecting higher event counts — 137 and
170 events vs seed42's 40).

---

## AGENCY — Cross-World Design Note

**Archetype decision (TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA):** AGENCY=C in every calibration
world except `simq_routing_test` is **archetype-correct** and requires no remediation.

**Root cause:** All three AGENCY key events (`route_selected`, `action_executed`,
`route_family_first_use`) are emitted only from `AdventureDecisionPhase`
(`src/domains/adventure/phase.py`). This phase is invoked through `run_phase("adventure_decision",
..., "ENABLE_ADVENTURE_ROUTING")` in `src/engine/pipeline.py`, and `ENABLE_ADVENTURE_ROUTING`
defaults to `FeatureMode.OFF` (`src/domains/optimization/feature_flags.py:16`). When the flag is
OFF, `run_phase` short-circuits before `AdventureDecisionPhase.apply()` runs, so zero
`route_selected`, `action_executed`, or `route_family_first_use` events are ever produced —
`AgencyScorer` (`src/simulation_quality/scorers/agency.py`) has nothing to score and every
default-mode world grades AGENCY=C across all seeds and tick counts (dungeon_crawl, urban_political,
sandbox_world, and the six confirmed zero-pillar worlds in the section below).

`simq_routing_test` is the one calibration world that forces `ENABLE_ADVENTURE_ROUTING=ON`
(see the `simq_routing_test` section above): AGENCY activates (non-C) in all 3 seeds — A, A, and F
(seed456's F is a stasis-dynamic gate violation, not a return to the inactive-flag C — see AC6
above) — demonstrating the scorer and emitters are wired correctly and activate as designed once
the routing gate is open.

`AdventureDecisionPhase` is opt-in by world archetype, not a global default — it represents a
distinct "routing-capable" archetype rather than a baseline behavior every world is expected to
exhibit. AGENCY=C in non-routing worlds is therefore the correct grade, mirroring the dungeon_crawl
ECONOMY/COGNITION archetype pattern documented above (TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG):
structurally inactive by design, not by bug.

**Anti-drift:** If any calibration world other than `simq_routing_test` enables
`ENABLE_ADVENTURE_ROUTING`, AGENCY will activate for that world and its grade anchors in
`tests/simulation_quality/fixtures/grade_anchors.json` must be recalibrated and updated — the C
anchors currently recorded for that world's AGENCY pillar assume the flag stays OFF.

---

## Newly-Anchored Worlds (TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS)

Five worlds that previously had zero calibration-corpus anchor entries were recompiled (picking up
the Step 1 hazard-kind fixes), re-verified for population stability (>=60% alive floor over 300
ticks at seed 42 — see `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md`
Finding 3 for the pre-fix collapse pattern this guards against), and anchored at 3 seeds x 200t
each. None of the four flag-gated pillars (AGENCY/FACTION/INFORMATION/SOCIAL) are reachable by
these worlds by design (out of scope for this ticket) — uniform C is expected and correct, not a
gap.

### frontier_extended (56 entities, 10 regions — >50-entity band, widest region spread in corpus)

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COMBAT | B | B | B | yes |
| NARRATIVE | A | A | A | yes |
| PROGRESSION | B | B | B | yes |
| WORLD | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COGNITION | C | C | C | yes |
| ECONOMY | C | C | C | yes |
| FACTION | C | C | C | yes |
| INFORMATION | C | C | C | yes |
| SOCIAL | C | C | C | yes |

### frontier_living_world (46 entities, 7 regions — fills the 35-50-entity band)

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COMBAT | B | B | B | yes |
| NARRATIVE | A | B | A | mostly |
| PROGRESSION | B | B | B | yes |
| WORLD | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COGNITION | C | C | C | yes |
| ECONOMY | C | C | C | yes |
| FACTION | C | C | C | yes |
| INFORMATION | C | C | C | yes |
| SOCIAL | C | C | C | yes |

### wilderness_survival (11 entities, 4 regions — second <20-entity data point alongside sandbox_world)

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COMBAT | C | C | C | yes |
| NARRATIVE | C | C | C | yes |
| PROGRESSION | C | C | C | yes |
| WORLD | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COGNITION | C | C | C | yes |
| ECONOMY | C | C | C | yes |
| FACTION | C | C | C | yes |
| INFORMATION | C | C | C | yes |
| SOCIAL | C | C | C | yes |

### highland_traverse (18 entities, 5 regions — brings mountain_pass/river_crossing/nomadic_herd/settled_quarter into the anchored corpus)

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COMBAT | B | B | C | no — seed456 lower event count |
| NARRATIVE | A | A | A | yes |
| PROGRESSION | C | C | C | yes |
| WORLD | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COGNITION | B | C | C | no — seed42 elevated |
| ECONOMY | C | C | C | yes |
| FACTION | C | C | C | yes |
| INFORMATION | C | C | C | yes |
| SOCIAL | C | C | C | yes |

### swamp_border_world (26 entities, 4 regions — brings sunken_swamp_border/lizardfolk family into the anchored corpus)

| Pillar | seed42 | seed123 | seed456 | Stable? |
|---|---|---|---|---|
| COMBAT | C | C | C | yes |
| NARRATIVE | A | A | A | yes |
| PROGRESSION | C | C | C | yes |
| WORLD | B | B | B | yes |
| AGENCY | C | C | C | yes |
| COGNITION | C | C | C | yes |
| ECONOMY | C | C | C | yes |
| FACTION | C | C | C | yes |
| INFORMATION | C | C | C | yes |
| SOCIAL | C | C | C | yes |

---

## Zero-Pillar World Confirmation

Five confirmed zero-*flag-gated*-pillar worlds (AGENCY/FACTION/INFORMATION/SOCIAL always C in
default mode — structural, feature-gate blocked, not duration-limited):
- `wilderness_survival`, `highland_traverse`, `swamp_border_world`
- `frontier_extended`, `frontier_living_world`

**Now anchored as of TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS** — see "Newly-Anchored Worlds" above.
COGNITION/ECONOMY also remain C in all five (no merchant NPCs, no non-combat cognitive triggers,
same archetype pattern as `dungeon_crawl`'s documented COGNITION/ECONOMY C — see the Archetype
Note above). COMBAT/NARRATIVE/PROGRESSION/WORLD are the pillars these five worlds contribute
genuine new signal for; more ticks will not activate AGENCY/FACTION/INFORMATION/SOCIAL without
enabling the relevant feature flags (explicitly out of scope for this ticket).
