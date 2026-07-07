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

**Status as of 2026-07-04 (TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE): DOCUMENTED EXCEPTION.**
seed456's AGENCY grade is fixed at **D** (up from `F`), and this is accepted as a permanent,
evidenced exception to AC6's "≥ B for all 3 seeds" gate — not a further remediation target. Root
cause: entity 23's `sociability` roll lands just under the `FORM_PARTY` gate
(`src/domains/adventure/generator.py:124`), and no resource node in `simq_routing_test`'s world
content lists `hometown` in `source_region_tags` (`src/world/providers/resources.py:69`), while all
heroes spawn in `hometown` — so this entity has zero legal non-defer route for its entire 500-tick
life, seed-independently, once its personality roll lands this way. This is a genuine, provable,
legitimate-stasis case (confirmed by `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE`'s investigation),
not a decision-logic or scoring bug — the scoring fix in that ticket (per-entity streak attribution
+ one-shot capped escalation) corrects the *magnitude* of the penalty (`F` → `D`) but cannot and
should not force the grade to `B`, since the underlying behavior (491 legitimate consecutive
defers) is real, and the `defer_idle` per-event weight is explicitly out of that ticket's authorized
scope. The world-content gap producing the zero-route condition is tracked separately as
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` (a `hometown` resource-tag authoring fix, not
a scoring or decision-logic change); even if that lands, this per-seed exception record is retained
as historical evidence for this run — a future re-anchor would be a new anchor update, not a
retroactive edit here.

**Status as of 2026-07-06 (TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP): EXCEPTION CLOSED
(grade improved).** `wood_node` and `herb_patch`'s `source_region_tags` in
`data/content/world/resources.yaml` now additively include `"hometown"` (both kinds were already
physically placed there by `frontier_village_core.yaml`; only the catalog-level gating tag was
missing — see investigation.md §1a for the root mechanism). Entity 23 in seed456 now has a legal
`gather_resource` route in `hometown` for its entire life, interrupting its
491-event `defer_with_reason` streak. Re-verified AGENCY grade: `A` (up from `D`).
`grade_anchors.json`'s `simq_routing_test_seed456_500t.AGENCY` anchor updated to `A`.
seed42/seed123 re-verified live (not assumed inert): AGENCY held at `A`/`A`, no regression on any
of the other 9 pillars. This closes the per-seed legitimate-stasis exception documented above as a
historical record only — the record itself is retained for traceability (it correctly described the
state of the world *before* this fix), not deleted or rewritten. (Two other seed456 pillars,
COGNITION and NARRATIVE, moved by one grade step each — S→A and A→S respectively — as a downstream
consequence of entity 23's freed decision stream; both remain within the ±1-letter anchor band per
`test_grade_regression.py`, so neither anchor was re-pinned.)

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

**Second exception class — per-seed legitimate-stasis (TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE):**
unlike the archetype-C exception above (a *pillar-inactive-by-flag* exception, applying uniformly
whenever `ENABLE_ADVENTURE_ROUTING=OFF`), this is a *pillar-active-but-content-constrained*
exception: routing is genuinely ON and the scorer is scoring correctly for
`simq_routing_test_seed456`, but one entity's personality roll combined with a resource-tagging gap
in this specific world's content leaves it with zero legal routes for its whole life, capping the
achievable grade at D regardless of scoring-formula correctness. See AC6 above for the full
evidence chain. [Closed 2026-07-06 by `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s
content fix — the resource-tagging gap is fixed and seed456's AGENCY grade improved to `A`; see the
"EXCEPTION CLOSED" status paragraph in AC6 above for the full re-verification evidence.]

**Second routing-capable archetype — `hero_guild_routing` (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-
AGENCY):** `hero_guild_routing` is a second world that forces `ENABLE_ADVENTURE_ROUTING=ON`, set in
its own profile YAML (`config/simulation_quality/profiles/hero_guild_routing.yaml`) from its first
compile. Unlike `simq_routing_test`'s purpose as a minimal calibration/test world, `hero_guild_routing`
is authored at real-archetype scale (31 entities, 4 regions — comparable to `urban_political`'s
30/3 and `dungeon_crawl`'s 32/4) with an explicit adventuring/route-selection framing, making it the
first routing-capable world in the corpus that is also a shipped-gameplay-scale archetype rather than
a calibration fixture. AGENCY graded `A` at all 3 measured seeds (42/123/456, 500t) — see its
subsection under "Unit-Tier Isolation Worlds" below for the full table and the resource-tag-coverage
finding this ticket surfaced (not fixed). This does not change the scope of the "AGENCY=C in every
calibration world except `simq_routing_test`" ruling for any of the 9 non-routing worlds above — it
only adds `hero_guild_routing` as a second, named exception to that ruling, exactly as
`simq_routing_test` already was.

**Third exception class — `urban_political`'s dormant `hometown` gap, accepted as permanent
non-issue (TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP):**
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`'s investigation (§4(i)) found that
`urban_political` shares both `frontier_village_core` (places `wood_node`/`herb_patch` in
`hometown`) and `hero_adventurers` (spawns all 3 hero-role entities in `hometown`) with
`simq_routing_test` — the same module combination that produced `simq_routing_test_seed456`'s
`defer_with_reason` stasis failure mode before that ticket's catalog fix. That fix (adding
`"hometown"` to `wood_node`/`herb_patch`'s `source_region_tags` in
`data/content/world/resources.yaml`) is global and already covers `urban_political` too, as a
confirmed side effect — verified directly against the current catalog file
(`TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`'s investigation). This gap remains
permanently dormant, not merely temporarily inert: per the archetype decision above
(`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`) and `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s explicit
choice to author a brand-new routing-capable world (`hero_guild_routing`) rather than enable routing
on `urban_political` — the closest existing candidate, having a `hero_guild`-framed population
already — `urban_political` is confirmed to never force `ENABLE_ADVENTURE_ROUTING=ON`. Its
archetype framing (settlement/political, FACTION/ECONOMY/SOCIAL-weighted, `Regression/baseline`
tier per `corpus_tier_taxonomy.md`) was never intended as adventuring/routing-oriented. No further
action is required unless a future ticket explicitly proposes reversing both
`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` and `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s
Out-of-Scope ruling for `urban_political`.

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

## FACTION/INFORMATION Content Expansion — End-to-End Tier (TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION)

Bespoke, archetype-matched `faction_tension_overrides` (all 8 worlds below) and, where an
archetype-honest fit exists, `information_source_profiles`/`pending_information_responses` (6 of 8
— `dungeon_crawl` and `wilderness_survival` have no settlement/service-bearing module and are
documented skip cases) were authored directly into each world's `data/worlds/{world}/world.yaml`
(never the frozen `data/content/world_compositions/{world}.yaml` mirror). This **supersedes** the
FACTION=C / INFORMATION=C rows recorded for these 8 worlds everywhere else in this document
(`dungeon_crawl`'s own tables above, `sandbox_world`'s own tables above, and all 5 "Newly-Anchored
Worlds" tables above) — those tables are retained for historical traceability of the pre-expansion
state, not rewritten in place, per this doc's existing convention (see the `dungeon_crawl`
hazard-kind-recompile note and `simq_routing_test`'s "Historical pre-recompile table" for
precedent).

Every world was recompiled with 0 new warnings (dungeon_crawl, sandbox_world, wilderness_survival,
swamp_border_world, frontier_living_world, frontier_extended, generated_frontier_3_42) or its one
confirmed **pre-existing, unrelated** warning (`highland_traverse`'s `survey_river_route` /
`'river'` region-tag mismatch — present in the committed baseline before this ticket's edit,
unaffected by the FACTION/INFORMATION content). All touched worlds' calibration anchors were
re-verified against a **freshly re-run** calibration (never a stale-data diff) per
`tools/calibrate_simq.py`, and every drifted anchor was updated in place in
`tests/simulation_quality/fixtures/grade_anchors.json`.

**Cross-world drift pattern (attributed, not a regression):** In every world where
`information_source_profiles`/`pending_information_responses` + `ENABLE_BELIEF_ASSIMILATION: "ON"`
were seeded, COGNITION also moved C→B in addition to INFORMATION C→B. This is the same dual-emission
mechanism already documented for `urban_political` above (`src/observability/event_extractor.py:285-295`,
tagged `PP-04`): a single assimilated response emits both a `belief_assimilated` event (scored by
`InformationScorer`) and a `belief_updated` event (scored by `CognitionScorer`) from the same
underlying fact. No pillar outside FACTION/INFORMATION/COGNITION drifted in any of the 8 worlds —
confirmed per-world before each anchor update (COMBAT/ECONOMY/SOCIAL/WORLD/NARRATIVE/PROGRESSION/AGENCY
held at their pre-expansion grades in every touched anchor).

### dungeon_crawl — FACTION only (INFORMATION: documented skip)

**Judgment call:** `goblin_warband: 0.5` / `bandit_company: 0.5` — two aggressive humanoid factions
vying for control of the ruins/dungeon, matching this world's own "escalating bandit threat"
framing. `undead_remnants`/`wild_beast_pack` (also populated) stay at catalog default (ambient
hazard, not political). **INFORMATION skipped**: no settlement/service module exists in this
world's composition (`ruins_mystery_quest`, `goblin_camp_conflict`, `old_mine_resource_loop`,
`scalable_bandit_camp` are all non-population/non-settlement modules) — forcing a notice-board
archetype here would be dishonest. No `feature_flags:` block added to
`config/simulation_quality/profiles/dungeon_crawl.yaml`; its existing `pillar_weights:` block is
untouched.

| Run | FACTION (was → now) | INFORMATION | COGNITION |
|---|---|---|---|
| seed42_200t | C → S (29 `diplomatic_transition` hits) | C (unchanged, skip) | C (unchanged) |
| seed{42,123,456}_500t | C → A | C (unchanged) | C (unchanged) |
| seed{42,123,456}_1000t | C → A | C (unchanged) | C (unchanged) |
| seed{42,123,456}_2000t | C → B | C (unchanged) | C (unchanged) |

### sandbox_world — FACTION + INFORMATION

**Judgment call:** `town_council: 0.5` / `merchant_league: 0.5` — governance-vs-commerce tension in
the settlement present. **INFORMATION fit:** `frontier_village_core` provides the settlement;
seeded a `town_notice_board` guide profile (`accuracy=0.4`, `freshness=0.6`) with one
`pending_information_responses` entry (`hometown_danger`, targeting
`frontier_village_population_frontier_guard`, the real resolved population id — `pop_0` does not
exist in this world's compiled output; that positional id only arises from the `hero_adventurers`
module, which none of these 8 worlds compose). New `config/simulation_quality/profiles/sandbox_world.yaml`
sets `ENABLE_BELIEF_ASSIMILATION: "ON"`.

| Run | FACTION (was → now) | INFORMATION | COGNITION |
|---|---|---|---|
| seed{42,137,999}_200t | C → S (29 hits) | C → B (1 `belief_assimilated` hit) | C → B (dual-emission) |
| seed42_1000t | C → A | C → B | B (unchanged — already B pre-expansion) |
| seed42_2000t | C → B | C → B | B (unchanged) |

### wilderness_survival — FACTION only (INFORMATION: documented skip)

**Judgment call:** `undead_remnants: 0.5` / `wild_beast_pack: 0.5` — the only 2 populated factions,
both hazard-type; framed as escalating territorial rivalry between the undead battlefield and the
wolf den's beast pack over the same survivor-camp territory, matching this world's "high danger...
escalating" framing. **INFORMATION skipped**: no settlement-adjacent module in composition
(`forest_deep_ecology`, `wolf_den_near_forest`, `undead_battlefield`, `survivor_camp_shelter` spawns
no settlement population of its own — confirmed against the resolved YAML's `entities[].faction`
list, which contains only `undead_remnants`/`wild_beast_pack`).

| Run | FACTION (was → now) | INFORMATION | COGNITION |
|---|---|---|---|
| seed{42,123,456}_200t | C → S (29 hits) | C (unchanged, skip) | C (unchanged) |

`test_population_stability[wilderness_survival]` re-confirmed passing post-recompile.

### highland_traverse — FACTION + INFORMATION

**Judgment call:** `town_council: 0.5` / `merchant_league: 0.5` — the `settled_quarter` module's own
service-hub archetype (governance vs. trade services). **INFORMATION fit:** seeded a
`route_waystation_guide` profile with a `mountain_pass_conditions` response (region corrected to the
actual resolved region id `mountain_pass_zone`, not the module name `mountain_pass`), targeting
`frontier_village_population_frontier_guard` (the `settled_quarter` module reuses the
`frontier_village_population` recipe, so this id resolves here too). New
`config/simulation_quality/profiles/highland_traverse.yaml` sets `ENABLE_BELIEF_ASSIMILATION: "ON"`.

| Run | FACTION (was → now) | INFORMATION | COGNITION |
|---|---|---|---|
| seed42_200t | C → S (29 hits) | C → B (1 hit) | B (unchanged — already B pre-expansion) |
| seed123_200t | C → S | C → B | C → B (dual-emission) |
| seed456_200t | C → S | C → B | C → B (dual-emission) |

Recompile surfaced 1 pre-existing warning (`survey_river_route`/`'river'` tag mismatch — confirmed
present in the committed pre-ticket baseline via `git show HEAD`, unrelated to this ticket's edit).

### swamp_border_world — FACTION + INFORMATION

**Judgment call:** `town_council: 0.5` / `swamp_tribe: 0.5` — border tension between the frontier
village's governance and the swamp tribe on its border, matching this world's own "lizardfolk
tribes and swamp trolls" framing (`bandit_company` deliberately not used — not populated here).
**INFORMATION fit:** seeded a `town_notice_board` profile with a `swamp_border_danger` response
(region: `swamp_border_territory`, the actual resolved region id — corrected from the module-name
guess `sunken_swamp_border`). New `config/simulation_quality/profiles/swamp_border_world.yaml` sets
`ENABLE_BELIEF_ASSIMILATION: "ON"`.

| Run | FACTION (was → now) | INFORMATION | COGNITION |
|---|---|---|---|
| seed{42,123,456}_200t | C → S (29 hits) | C → B (1 hit) | C → B (dual-emission) |

### frontier_living_world — FACTION + INFORMATION

**Judgment call:** `bandit_company: 0.5` / `merchant_league: 0.5` — the `bandit_road_trade_pressure`
module's own built-in tension (bandit threat vs. merchant trade), the most mechanically literal fit
among all 8 worlds. **INFORMATION fit:** seeded a `town_notice_board` profile with a
`trade_road_bandit_activity` response (region: `bandit_road`, matching the resolved region id
exactly). New `config/simulation_quality/profiles/frontier_living_world.yaml` sets
`ENABLE_BELIEF_ASSIMILATION: "ON"`. The frozen `data/content/world_compositions/frontier_living_world.yaml`
mirror (read by `test_real_content_world_compositions.py`) was left untouched and re-verified passing.

| Run | FACTION (was → now) | INFORMATION | COGNITION |
|---|---|---|---|
| seed{42,123,456}_200t | C → S (29 hits) | C → B (1 hit) | C → B (dual-emission) |

### frontier_extended — FACTION + INFORMATION

**Judgment call:** `orc_clan: 0.5` / `forest_wardens: 0.5` — this world's own *additions* over
`frontier_living_world` (`orc_clan_territory` + `forest_warden_grove`), framed as orc territorial
expansion encroaching on the forest wardens' grove — deliberately not reusing
`frontier_living_world`'s bandit/merchant pair, since `frontier_extended` is a superset composition
and needs distinct content. **INFORMATION fit:** seeded a `town_notice_board` profile with an
`orc_clan_encroachment` response (region: `orc_stronghold`, the actual resolved region id —
corrected from the module-name guess `orc_clan_territory`), a subject deliberately distinct from
`frontier_living_world`'s `trade_road_bandit_activity`. New
`config/simulation_quality/profiles/frontier_extended.yaml` sets `ENABLE_BELIEF_ASSIMILATION: "ON"`.

| Run | FACTION (was → now) | INFORMATION | COGNITION |
|---|---|---|---|
| seed{42,123,456}_200t | C → S (29 hits) | C → B (1 hit) | C → B (dual-emission) |

### generated_frontier_3_42 — FACTION + INFORMATION, content-only, NO new anchor

**Judgment call:** `arcane_circle: 0.5` / `orc_clan: 0.5` — the `moon_cult_ruins` module's arcane
circle under territorial pressure from the `orc_clan_territory` module, a pairing unique to this
world. **INFORMATION fit:** seeded a `town_notice_board` profile with a `moon_cult_ruins_mystery`
response (region: `moon_cave`, the actual resolved region id — corrected from the module-name guess
`moon_cult_ruins`). New `config/simulation_quality/profiles/generated_frontier_3_42.yaml` sets
`ENABLE_BELIEF_ASSIMILATION: "ON"`. **`moon_cult` (declared by `moon_cult_ruins` but not actually
populated) deliberately received no tension override** — only `arcane_circle` from that module is
populated.

**This world has zero existing `grade_anchors.json` entries and deliberately receives none from this
ticket** (per the ticket's own scope: "re-verify existing calibration anchors," which does not apply
here — newly anchoring a world is a materially bigger task than re-verifying one, out of this
ticket's scope). The 3-seed 200t calibration below is documentation-only evidence that the new
content produces a genuine, non-inert signal — it is **not** added to `FAST_ANCHOR_KEYS`/
`SLOW_ANCHOR_KEYS` or `grade_anchors.json`. This world remains outside the anchored calibration
corpus by design; a future ticket to newly-anchor it is a separate, larger scope decision.

| Run | FACTION | INFORMATION | COGNITION |
|---|---|---|---|
| seed{42,123,456}_200t | S (29 hits) | B (1 hit) | B (2 hits) |

---

## Zero-Pillar World Confirmation

**Superseded for FACTION (all 5) and for INFORMATION (4 of 5) as of
TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION** — see the new section above. `wilderness_survival`
remains INFORMATION=C by documented judgment call (no settlement-adjacent module); the other 4
(`highland_traverse`, `swamp_border_world`, `frontier_extended`, `frontier_living_world`) now grade
INFORMATION=B. This section's original text is retained below for historical traceability of the
pre-expansion state.

Five confirmed zero-*flag-gated*-pillar worlds (AGENCY/FACTION/INFORMATION/SOCIAL always C in
default mode — structural, feature-gate blocked, not duration-limited):
- `wilderness_survival`, `highland_traverse`, `swamp_border_world`
- `frontier_extended`, `frontier_living_world`

**Now anchored as of TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS** — see "Newly-Anchored Worlds" above.
COGNITION/ECONOMY also remain C in all five (no merchant NPCs, no non-combat cognitive triggers,
same archetype pattern as `dungeon_crawl`'s documented COGNITION/ECONOMY C — see the Archetype
Note above). COMBAT/NARRATIVE/PROGRESSION/WORLD are the pillars these five worlds contribute
genuine new signal for; more ticks will not activate AGENCY/FACTION/INFORMATION/SOCIAL without
enabling the relevant feature flags (explicitly out of scope for this ticket). AGENCY/SOCIAL remain
C in all 8 worlds this document covers — neither `ENABLE_ADVENTURE_ROUTING` nor
`ENABLE_SOCIAL_COOPERATION` was touched by the FACTION/INFORMATION content expansion above.

---

## Corpus World-Scale Summary (TCK-20260704-SIMQ-CORPUS-SCALE-METRIC)

Consolidated scale reporting for all 10 worlds under `data/worlds/`, pulled directly from each
world's `world_compile_report.json`. Earlier per-world reporting in "Newly-Anchored Worlds" above
covered entity/region counts for only 5 of the 10 worlds and did not include resource-node,
building, quest, or populated-faction counts anywhere in this doc — this table closes that gap in
one place rather than patching five scattered headers. `distinct_populated_factions` counts unique
`entity.properties["faction_id"]` values actually assigned to a compiled entity (not the static
16-entry `AuthoritativeState.factions` catalog, which is constant across all worlds and therefore
not a meaningful per-world signal on its own — see
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md` §2).

| World | Seed | Entities | Regions | Resource Nodes | Buildings | Quests | Distinct Populated Factions |
|---|---|---|---|---|---|---|---|
| wilderness_survival | 101 | 11 | 4 | 4 | 1 | 7 | 2 |
| sandbox_world | 42 | 18 | 3 | 5 | 5 | 6 | 3 |
| highland_traverse | 91 | 18 | 5 | 3 | 5 | 6 | 3 |
| urban_political | 202 | 30 | 3 | 3 | 7 | 9 | 4 |
| dungeon_crawl | 303 | 32 | 4 | 3 | 1 | 9 | 4 |
| swamp_border_world | 77 | 26 | 4 | 7 | 5 | 6 | 4 |
| simq_routing_test | 42 | 30 | 3 | 5 | 6 | 7 | 5 |
| frontier_living_world | 42 | 46 | 7 | 9 | 6 | 16 | 6 |
| generated_frontier_3_42 | 42 | 44 | 6 | 9 | 6 | 16 | 7 |
| frontier_extended | 43 | 56 | 10 | 13 | 6 | 22 | 9 |
| crowded_frontier | 601 | 38 | 4 | 4 | 5 | 12 | 6 |
| resource_dense_basin | 602 | 23 | 3 | 7 | 6 | 7 | 4 |
| frontier_marches | 603 | 62 | 9 | 13 | 6 | 19 | 9 |

The 3 stress-tier worlds above (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`) are detailed in their own
"Stress-Tier Worlds" section below; their `Resource Nodes` counts are `world_compile_report.json`'s
`resource_node_count` (number of distinct resource-node definitions actually compiled into
`AuthoritativeState.resource_nodes`, e.g. `frontier_village_core`'s `wood_node`+`herb_patch` = 2
definitions) — the same metric already used for every other row in this table. This is **not** the
same thing as summing each definition's `count:`/charge field (e.g. `wood_node: 8` means one
resource-node definition with 8 harvestable charges, not 8 separate nodes); the two metrics were
conflated during this ticket's own investigation phase, corrected here against the actual measured
field.

`generated_frontier_3_42` has zero entries in `tests/simulation_quality/fixtures/grade_anchors.json`
and is not part of the pillar-grade calibration corpus tracked elsewhere in this doc — it is
included here only for scale-metric completeness (it is one of the 10 worlds under `data/worlds/`),
not as a calibration claim.

---

## Unit-Tier Isolation Worlds (TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO)

Two new **unit-tier** worlds (per `docs/simulation_quality/corpus_tier_taxonomy.md`'s
classification: "isolates exactly one gated mechanic, with everything else at baseline, using
template/synthetic content") were authored and anchored at 3 seeds x 200t each. Both compiled with
`warnings: []` and passed the >=60% alive-floor population-stability guard through 300 ticks at
seed 42 (100% alive at every 50-tick checkpoint, no incident). A third unit-tier world,
`hero_guild_routing` (TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY), was later authored at real-
archetype scale (31 entities, comparable to `urban_political`/`dungeon_crawl` rather than these
first two worlds' template-minimal sizing) and anchored at 3 seeds x 500t, matching
`simq_routing_test`'s calibration length rather than the 200t default — see its own subsection
below for the reasoning.

### unit_faction_tension (unit-tier — 18 entities, 3 regions)

Reuses `sandbox_world`'s exact module pair (`frontier_village_core` + `wolf_den_near_forest`) with
`faction_tension_overrides` seeded on `town_council: 0.5` / `merchant_league: 0.5`. No profile YAML
exists for this world (all feature flags default OFF via `_resolve_profile()`'s `"default"`
fallback).

#### 200t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| AGENCY | C | C | C | stable — no `ENABLE_ADVENTURE_ROUTING` |
| COGNITION | C | C | C | stable |
| COMBAT | C | C | C | stable |
| ECONOMY | C | C | C | stable |
| **FACTION** | **S** | **S** | **S** | genuine non-C signal: 29 `diplomatic_transition`/`tension_active` hits/run, identical across all 3 seeds — matches `urban_political_seed42_200t`'s own "29 hits/run" precedent for the same mechanism |
| INFORMATION | C | C | C | **isolation confirmed** — `information_source_profiles`/`pending_information_responses` both empty, 0 events, as designed |
| PROGRESSION | C | C | C | stable (1 event, below threshold) |
| SOCIAL | C | C | C | stable — no `ENABLE_SOCIAL_COOPERATION` |
| WORLD | B | B | B | stable |
| NARRATIVE | A | A | A | stable, high event density from the reused `sandbox_world` module pair |

FACTION lands at `S`, not merely a non-C letter — the event-count breakdown (29 hits/run, every
seed) confirms this is genuine `FactionScorer` activity (`tension_active`/`diplomatic_transition`
events from a live threshold crossing), not an inert or dormancy-negative false positive. Every
other Pattern-6-adjacent pillar (INFORMATION) stays `C` as expected — isolation confirmed, not a
gap.

### unit_information_source (unit-tier — 16 entities, 1 region)

Composes `frontier_village_core` + `hero_adventurers` (the latter's 3 un-ided
`population_recipes` produce the positional `pop_0`/`pop_1`/`pop_2` addressing `urban_political`
also relies on). Seeds one `information_source_profiles` entry (`town_notice_board`, guide) and one
`pending_information_responses` entry targeting `pop_0`, together with
`ENABLE_BELIEF_ASSIMILATION: "ON"` in `config/simulation_quality/profiles/unit_information_source.yaml`
(confirmed loaded — calibration output shows `profile=unit_information_source`, not `default`).

#### 200t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| AGENCY | C | C | C | stable — no `ENABLE_ADVENTURE_ROUTING` |
| COGNITION | B | B | B | side effect of `belief_updated` also being scored by `CognitionScorer` (2 events/run), same pattern as `urban_political`'s own COGNITION uplift |
| COMBAT | C | C | C | stable |
| ECONOMY | C | C | C | stable |
| FACTION | C | C | C | **isolation confirmed** — `faction_tension_overrides` absent (catalog default 0.0 for all factions), 0 events, as designed |
| **INFORMATION** | **B** | **B** | **B** | genuine non-C signal: exactly 1 `belief_assimilated` hit/run, identical across all 3 seeds — matches `urban_political_seed42_200t`'s own single-fire, tick-length-invariant precedent for this mechanism |
| PROGRESSION | C | C | C | stable (1 event, below threshold) |
| SOCIAL | C | C | C | stable — no `ENABLE_SOCIAL_COOPERATION` |
| WORLD | B | B | B | stable |
| NARRATIVE | A | A | A | stable |

INFORMATION lands at `B` with exactly 1 `belief_assimilated` hit/run (not `S`/`A`) — this is the
expected honest outcome per investigation.md's single-fire, tick-length-invariant characterization
of this mechanism, not a partial failure. FACTION stays `C` as expected — isolation confirmed, not
a gap.

### unit_selfmodel_pilot (unit-tier — 16 entities, 1 region)

Composes `frontier_village_core` + `hero_adventurers` (same module pair as
`unit_information_source`). Seeds one `pending_self_model_information_events` entry targeting
`pop_1` (`unknowns: ["material.wood.source"]` — a real material this composition's own
`frontier_village_core` resource_recipes actually produce, via `wood_node`), together with
`ENABLE_SELF_MODEL_COGNITION: "ON"` in
`config/simulation_quality/profiles/unit_selfmodel_pilot.yaml` (confirmed loaded — calibration
output shows `profile=unit_selfmodel_pilot`, not `default`). `ENABLE_BELIEF_ASSIMILATION` is
absent (default OFF) — deliberately, per this world's own ticket's Scope item 3.

**Framing (load-bearing, not a caveat to skip):** this world isolates and exercises only
`SelfModelUpdatePhase`'s knowledge-assimilation half of "Branch B" (`self_model.knowledge.unknowns`
population, durably materialized via `SelfModelPatch` every tick, producing genuine
`self_model_updated`/`self_model_active` COGNITION-pillar signal at real multi-entity/multi-tick
scale for the first time — validating `INFRA-259`/`SUB-374` beyond the single hand-built unit test
that previously proved them). It does **not** exercise `InformationBeliefPhase`'s query-routing
half of "Branch B" (the literal mechanism
`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization` and Finding
4 refer to) — that logic lives entirely inside the `ENABLE_BELIEF_ASSIMILATION`-gated phase, which
this world never invokes, by design. INFORMATION pillar staying at `C` below is the correct,
predicted isolation result, not a bug or gap.

#### 200t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| AGENCY | C | C | C | stable — no `ENABLE_ADVENTURE_ROUTING` |
| **COGNITION** | **S** | **S** | **S** | genuine non-C signal: 3200 `self_model_updated`/`self_model_active` hits/run, identical across all 3 seeds — exactly `alive_entities (16) x ticks (200)`, confirming `self_model_updated` fires unconditionally every tick for every alive/active entity, not a threshold-crossing or single-fire event |
| COMBAT | C | C | C | stable |
| ECONOMY | C | C | C | stable |
| FACTION | C | C | C | **isolation confirmed** — `faction_tension_overrides` absent, 0 events, as designed |
| INFORMATION | C | C | C | **isolation confirmed, as predicted before the run** — `InformationBeliefPhase` never invoked (`ENABLE_BELIEF_ASSIMILATION` absent); 0 events, exactly as investigation.md §4/§5 foretold, not discovered as a surprise |
| PROGRESSION | C | C | C | stable (1 event, below threshold) |
| SOCIAL | C | C | C | stable — no `ENABLE_SOCIAL_COOPERATION` |
| WORLD | B | B | B | stable |
| NARRATIVE | A | A | A | stable |

COGNITION's signal is real, large-volume, and structurally different from every other pillar signal
in the corpus (every entity, every tick, not a single-fire or threshold-crossing event) — this is
the expected, correct consequence of `self_model_updated` firing unconditionally once
`ENABLE_SELF_MODEL_COGNITION` is ON, not an anomaly. Population stability held at 100% alive through
300 ticks at seed 42 (identical to `unit_information_source`, same module pair, no new
hazard/combat content). INFORMATION stays `C` exactly as this ticket's own Scope item 3 designed and
investigation.md predicted in advance — the query-routing sense of "Branch B" remains proven only by
the existing single-entity unit test
(`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`); extending
that proof to multi-entity/multi-tick scale would require `ENABLE_BELIEF_ASSIMILATION` ON too — a
different, not-yet-scoped follow-on pilot, not this ticket's job.

### hero_guild_routing (unit-tier — 31 entities, 4 regions)

Composes `frontier_village_core`, `hero_adventurers`, `mountain_pass`, `ruins_mystery_quest`, and
`goblin_camp_conflict` (seed 717), with `ENABLE_ADVENTURE_ROUTING: "ON"` set in this world's own
`config/simulation_quality/profiles/hero_guild_routing.yaml` `feature_flags:` block — confirmed
loaded (calibration output shows `profile=hero_guild_routing`, not `default`). Compiled with
`warnings: []`. Unlike `simq_routing_test` — a minimal calibration/test world purpose-built to
exercise `AgencyScorer` in isolation — `hero_guild_routing` is a real-scale, routing-capable
archetype: 31 entities / 4 regions sits almost exactly between `urban_political` (30/3) and
`dungeon_crawl` (32/4), and its description explicitly frames adventuring/route-selection ("a hero
guild's home settlement dispatches adventuring parties across three competing destinations... a
mountain pass, a goblin camp, and haunted ruins") as the world's central mechanic, not an incidental
settlement feature. It is a second, distinct member of the routing-capable archetype category
alongside `simq_routing_test`, not a replacement for it.

#### 500t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| **AGENCY** | **A** | **A** | **A** | genuine non-C signal at real-archetype scale, stable across all 3 seeds — no stasis-collapse anomaly observed (contrast `simq_routing_test_seed456`'s pre-fix F/D collapse) |
| COGNITION | A | S | A | stable-to-high, varies by seed |
| COMBAT | B | B | B | stable |
| ECONOMY | C | C | C | stable — no gather_resource/craft/buy events scored this run |
| FACTION | C | C | C | stable — no `faction_tension_overrides` seeded (isolation-tier default) |
| INFORMATION | C | C | C | stable — no `information_source_profiles` seeded (isolation-tier default) |
| PROGRESSION | B | B | B | stable |
| SOCIAL | C | C | C | stable — no `ENABLE_SOCIAL_COOPERATION` |
| WORLD | B | B | B | stable |
| NARRATIVE | S | S | S | stable, high event density |

**What each check proves, and what it does not:** three separate checks touch this world's
population/routing behavior, and none of them should be mistaken for covering the other two's
concern. `test_population_stability[hero_guild_routing]`
(`tests/unit/worldassembly/test_corpus_diversity.py`) is the generic OFF-flag baseline
survival-mechanic guard every corpus world gets — it runs with `ENABLE_ADVENTURE_ROUTING` at its
default OFF state and is not evidence for this world's ON-flag population floor.
`tests/unit/worldassembly/test_hero_guild_routing_population_stability.py` is the new, standalone,
world-scoped test that genuinely applies `ENABLE_ADVENTURE_ROUTING=ON` onto the compiled
`AuthoritativeState.feature_flags` before driving the kernel — it is the sole, authoritative
evidence for the acceptance criterion's >=60% ON-flag population floor claim, and it passed cleanly
through 500 ticks at seed 42 with no checkpoint below the floor. `tools/calibrate_simq.py`'s 3-seed
calibration matrix (this subsection's table above) is the source of the measured pillar grades,
including AGENCY, but asserts no population floor of its own.

**Resource-tag coverage finding (Step 2, `tests/unit/strategic/test_opportunities.py`):** a gap was
found, not a clean pass. `mountain_pass`'s two resource kinds (`iron_vein`, `frost_shard_cluster`)
carry no `source_region_tags` entry at all in `data/content/world/resources.yaml`, and no resource
definition in that catalog lists `mountain_pass_zone`, `goblin_camp`, or `haunted_battlefield` (the
three new-to-this-world regions) as a `source_region_tags` value — confirmed directly via
`ResourceOpportunityProvider.get_opportunities()`, which returns zero opportunities for a hero
standing in any of those three regions regardless of which resource node is present there. This is
the same class of registry-omission gap `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`
fixed for `hometown`/`wood_node`/`herb_patch`. It is deliberately **not** fixed by this ticket (out
of scope — `data/content/world/resources.yaml` is a shared catalog file, and this ticket's scope is
authoring/calibrating one world, not patching shared content) and is flagged here as a recommended
follow-up: add `mountain_pass_zone` (and, if `ruins_mystery_quest`/`goblin_camp_conflict` later gain
their own resource placements, `haunted_battlefield`/`goblin_camp`) to the relevant resource
definitions' `source_region_tags`. It did not visibly harm this world's measured AGENCY grade (A at
all 3 seeds) — heroes routed to these regions still had `RECOVER`/`ASK_INFORMATION`/`FORM_PARTY`
structural-default routes and the guaranteed `DEFER_WITH_REASON` fallback available, and the
`AdventureDecisionPhase` only ever consults `ResourceOpportunityProvider` (not
`ServiceOpportunityProvider`, confirmed by direct read of `src/domains/adventure/phase.py`) — but a
future world that relies more heavily on gather_resource routes in these regions could be exposed to
the same stasis pattern `simq_routing_test_seed456` hit pre-fix.

---

## Stress-Tier Worlds (TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS)

Three new **stress-tier** worlds (per `docs/simulation_quality/corpus_tier_taxonomy.md`'s
classification: justified by scale/shape alone, not by exercising a new gated mechanic) fill the
corpus's three named scale-diversity gaps
(`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2): a
many-factions/small-map world (gap 1), a resource-saturated/small-map world (gap 2), and a
large-scale FACTION/INFORMATION world (gap 3). All 3 are built entirely from existing
`data/content/world_modules/` catalog content — no new module was authored — and all 3 compiled
with `warnings: []` and passed the >=60% alive-floor population-stability guard through 300 ticks
at seed 42 (`test_population_stability` via `ANCHORED_WORLD_BANDS` membership,
`tests/unit/worldassembly/test_corpus_diversity.py`).

### crowded_frontier (stress-tier — 38 entities, 4 regions) — fills gap 1 (many-factions/small-map)

Composes `frontier_village_core` + `hero_adventurers` + `bandit_road_trade_pressure` +
`goblin_camp_conflict` + `orc_clan_territory` (seed 601). Reaches 6 distinct populated factions
(`town_council`, `merchant_league`, `hero_guild`, `bandit_company`, `goblin_warband`, `orc_clan`,
confirmed via `world_compile_report.json`'s `distinct_populated_factions` field, not eyeballed)
across only 4 regions — matching `wilderness_survival`'s region count exactly, the smallest region
footprint in the corpus alongside `sandbox_world`. Its 38-entity count is larger than
`wilderness_survival`(11)/`sandbox_world`(18) — this is the unavoidable cost of the region-count
reading of "small-map" (see this ticket's plan.md UQ resolution #1): no catalog combination reaches
6+ distinct populated factions under ~20 entities, because every faction-populating module besides
`hero_adventurers` (which spawns 0 new regions) contributes 5+ entities of its own. No
`faction_tension_overrides`/`information_source_profiles` content was added (tier-purity rule — this
world's justification is scale alone).

#### 200t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| COGNITION | C | C | C | stable |
| AGENCY | C | C | C | stable — no `ENABLE_ADVENTURE_ROUTING` |
| COMBAT | B | B | B | stable |
| FACTION | C | C | C | stable — no `faction_tension_overrides` seeded (tier-purity default) |
| ECONOMY | C | C | C | stable |
| PROGRESSION | B | B | B | stable |
| SOCIAL | C | C | C | stable — no `ENABLE_SOCIAL_COOPERATION` |
| INFORMATION | C | C | C | stable — no `information_source_profiles` seeded (tier-purity default) |
| WORLD | B | B | B | stable |
| NARRATIVE | A | A | A | stable, high event density from the 5-module conflict mix |

Grades are identical across all 3 seeds — no anomalous pillar observed at this density.

### resource_dense_basin (stress-tier — 23 entities, 3 regions) — fills gap 2 (resource-saturated/small-map)

Composes `frontier_village_core` + `old_mine_resource_loop` + `orc_clan_territory` (seed 602). This
fills gap 2 from the resource-**saturated**/small-map direction rather than the
sparse-resources/large-map direction (both fill the same named gap from opposite directions; this
ticket's investigation phase judged resource-saturated/small-map the lower-risk choice, since the
sparse direction would need ~7-8 modules, most needing fresh `hazard_kind` verification, for the
same evidentiary payoff — see plan.md's UQ-2 resolution). `resource_node_count` (the same metric
used throughout this doc's "Corpus World-Scale Summary" table — distinct resource-node definitions,
not summed charge counts) is 7 across 3 regions (~2.33/region), the corpus's new density maximum,
surpassing `swamp_border_world`'s prior 1.75/region (7 nodes/4 regions). This corrects an early
investigation-phase estimate (~12.3/region) that conflated the `count:`/charge field with the
node-definition count; the corrected 2.33/region figure is still the corpus's highest measured
density and still supports the gap-2 justification.

**Resource-tag coverage finding (Step 7, `tests/unit/strategic/test_opportunities.py`):** mixed
result, not a uniform clean pass. `old_mine` (this world's other new-to-the-corpus-composition
region alongside `orc_stronghold`) is covered: `iron_vein` has no explicit `source_region_tags`
metadata in `data/content/world/resources.yaml`, but `CatalogToResourceRegistryAdapter`'s
legacy_id-based fallback (`src/core/registries.py:435-436`) infers `source_region_tags=("old_mine",)`
for it, confirmed via a passing spot-check test
(`test_resource_opportunities_old_mine_iron_vein`). `orc_stronghold`, however, has a genuine gap:
neither resource kind `orc_clan_territory` places there (`iron_vein`, `wood_node`) carries an
`orc_stronghold` `source_region_tags` entry — `wood_node`'s explicit tags are only
`["near_forest", "hometown"]`, and `iron_vein`'s fallback tags are only `("old_mine",)` — confirmed
via `test_resource_opportunities_orc_stronghold_tag_gap`, which asserts zero `gather_resource`
opportunities for a hero standing in `orc_stronghold`. This is the same class of registry-omission
gap `test_resource_opportunities_mountain_pass_zone_tag_gap`
(`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`) already documented, and it pre-dates this ticket:
`orc_clan_territory` is already composed by `frontier_extended`/`frontier_living_world`/
`generated_frontier_3_42`, so this gap has been latent in the corpus since those worlds were
authored, only now surfaced by a targeted spot-check. Deliberately **not** fixed here (shared
catalog file, out of this ticket's authoring-scoped work) — flagged as the same class of follow-up
recommendation: add `orc_stronghold` to `wood_node`'s (or `iron_vein`'s) `source_region_tags`.

#### 200t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| COGNITION | C | C | C | stable |
| AGENCY | C | C | C | stable — no `ENABLE_ADVENTURE_ROUTING` |
| COMBAT | C | C | C | stable |
| FACTION | C | C | C | stable — no `faction_tension_overrides` seeded (tier-purity default) |
| **ECONOMY** | **C** | **C** | **C** | stable, not anomalous — consistent with the corpus's typical ECONOMY=C baseline (matches `urban_political`/`dungeon_crawl`/`swamp_border_world` etc.) despite the elevated resource-node density; no scoring-formula concern found on inspection |
| PROGRESSION | C | C | C | stable |
| SOCIAL | C | C | C | stable — no `ENABLE_SOCIAL_COOPERATION` |
| INFORMATION | C | C | C | stable — no `information_source_profiles` seeded (tier-purity default) |
| WORLD | B | B | B | stable |
| NARRATIVE | A | A | A | stable |

Grades are identical across all 3 seeds — no anomalous pillar observed.

### frontier_marches (stress-tier — 62 entities, 9 regions) — fills gap 3 (large-scale FACTION/INFORMATION, authored-from-inception)

Composes `frontier_village_core` + `hero_adventurers` + `wolf_den_near_forest` +
`goblin_camp_conflict` + `bandit_road_trade_pressure` + `orc_clan_territory` +
`undead_battlefield` + `sunken_swamp_border` + `old_mine_resource_loop` (seed 603) — 9 distinct
populated factions across 9 regions, comparable in scale to `frontier_extended` (56 entities/10
regions) but not a duplicate composition: it shares 6 of `frontier_extended`'s 8 modules but swaps
`forest_warden_grove` for `hero_adventurers` + `sunken_swamp_border`, so its faction mix includes
`hero_guild`/`swamp_tribe` and excludes `forest_wardens`/`spirit_court`.

**Gap-3 reframing (see `corpus_tier_taxonomy.md`'s corrected gap-3 text):** by the time this ticket
was implemented, `frontier_extended`/`frontier_living_world` had already gained
`faction_tension_overrides`/`information_source_profiles` content via the sibling
`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` ticket — so `frontier_marches` is not literally
"the first" data point at this scale, as the original gap-3 framing assumed. It is the first
**authored-from-inception** data point: this content was part of the world's initial composition
and first compile, not retrofitted onto an already-anchored world after the fact.

**Bespoke-content rationale:** `faction_tension_overrides` seeds `bandit_company: 0.5` /
`orc_clan: 0.5` — a tension pair no other existing world declares together (`frontier_extended`
declares `orc_clan`+`forest_wardens`; `frontier_living_world` declares
`bandit_company`+`merchant_league`), chosen because `frontier_marches` is the only world where both
the bandit-road and orc-clan modules are present with neither's usual tension partner in play,
giving a "dual external-threat" framing distinct from either sibling world.
`information_source_profiles`/`pending_information_responses` seeds a `bandit_road_conditions`
query (region `bandit_road`, certainty `0.72`) — deliberately different in subject, region, and
certainty from `frontier_extended`'s `orc_clan_encroachment`/`orc_stronghold`/`0.75` and
`swamp_border_world`'s `swamp_border_danger`/`swamp_border_territory`/`0.7`.

**Parity-ledger extension:** `docs/parity_ledger/faction.yaml::FAC-012` and
`docs/parity_ledger/infrastructure.yaml::INFRA-256` were both extended additively (one new clause
each, no rewording of existing text) citing `frontier_marches` as a second/third real-world data
point for `faction_tension_overrides`/`information_source_profiles` compile-time plumbing at this
scale — closing a prior inconsistency where `INFRA-256` had been extended twice for the E2E ticket's
work but `FAC-012` had not been extended at all despite that same ticket adding
`faction_tension_overrides` to 8 worlds.

**Calibration profile:** unlike `crowded_frontier`/`resource_dense_basin`, this world required a new
`config/simulation_quality/profiles/frontier_marches.yaml` (`feature_flags: {ENABLE_BELIEF_ASSIMILATION:
"ON"}`) — without it, `tools/calibrate_simq.py`'s `_resolve_profile()` falls back to `"default"`,
leaving `InformationBeliefPhase`'s Branch A permanently unreached regardless of the seeded
`pending_information_responses` content. This was traced (not assumed) during this ticket's own
first calibration pass, which measured `INFORMATION=C`/`event_count=0` despite correctly-resolved
compile-time plumbing (`AuthoritativeState.pending_information_responses` had 1 well-formed entry);
adding the missing profile file and recalibrating moved `INFORMATION` to `B`/`event_count=1` across
all 3 seeds, matching the other 8 `information_source_profiles`-bearing worlds' established
C→B pattern.

#### 200t (seeds 42 / 123 / 456)

| Pillar | seed42 | seed123 | seed456 | Notes |
|---|---|---|---|---|
| COGNITION | B | B | B | stable |
| AGENCY | C | C | C | stable — no `ENABLE_ADVENTURE_ROUTING` |
| COMBAT | B | B | B | stable |
| **FACTION** | **S** | **S** | **S** | genuine non-C signal from the seeded `faction_tension_overrides`, stable across all 3 seeds |
| ECONOMY | C | C | C | stable |
| PROGRESSION | B | B | B | stable |
| SOCIAL | C | C | C | stable |
| **INFORMATION** | **B** | **B** | **B** | genuine non-C signal from the seeded `information_source_profiles`/`pending_information_responses` (Branch A, 1 `belief_assimilated`/`belief_updated` hit per run) — see calibration-profile note above |
| WORLD | B | B | B | stable |
| NARRATIVE | A | A | A | stable |

Grades are identical across all 3 seeds — no anomalous pillar observed, and the FACTION/INFORMATION
signals confirm both mechanics scale cleanly to a 62-entity/9-region composition authored from
inception.
