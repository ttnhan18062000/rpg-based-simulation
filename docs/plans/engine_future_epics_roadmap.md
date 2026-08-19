---
status: active
layer: architecture
authority: P1
audience: agent
tags: [roadmap, epics, gap-analysis, long-term, faction, campaign, quest, progression, world-evolution]
---

# Engine Future Epics — Full Gap Analysis & Long-Term Roadmap

## Method

Five parallel investigations were run, each following the mandatory `search_docs` → `graphify` → targeted-file-read order, covering: (1) combat/economy/entity anatomy, (2) cognition/social/motivation, (3) world evolution/worldbuilding/faction-macro, (4) kernel/observability/performance/testing infrastructure, (5) adventure/quests/progression/campaigns/scenario lab. Each cross-checked the parity ledger (`docs/parity_ledger/*.yaml`) for `divergent`/`missing`/`unsupported` entries and `docs/compliance/gap_analysis.md`/`known_limitations.md` for already-documented gaps, rather than re-guessing from the three prior planning docs (`feature_summary.md`, `expected_first_release.md`, `rpg_feature_direction.md`).

This supersedes the earlier, narrower `docs/plans/release-spine-and-feature-packs.md` — its four items are folded in below as section E.

## Headline Finding

**There is no faction/diplomacy/war system in the current engine.** `docs/systems/grand_strategy.md` describes a legacy system (`src/systems/strategy_system.py`, `src/core/world_state.py`) that does not exist anywhere in current `src/` — only `src/content_semantics/faction.py` remains, which is catalog data, not behavior. None of the three prior planning docs caught this; they assumed some macro-political layer existed. This is the single largest concrete gap found and should weigh heavily in prioritization.

**Direction note:** per explicit project direction, this and every other epic below is to be designed and built fresh against the current architecture (domain ownership, authoritative mutation pipeline, typed durable state) — not ported, adapted, or kept compatible with any legacy system or semantics. `grand_strategy.md` is cited only to establish that no macro-political layer currently exists, not as a design source. The legacy doc itself is a candidate for archival/removal once the fresh system replaces its conceptual territory, rather than being kept around as a compatibility reference.

## Engine Maturity Snapshot

| Layer | Maturity | Headline |
|---|---|---|
| Infrastructure (kernel, mutation pipeline, observability, performance, testing) | **Mature** — `infrastructure.yaml` parity ledger is 100% `verified`, zero open divergences | Only narrow gaps remain (granular phase permissions); not a fruitful area for new epics |
| Combat / Economy / Entity Anatomy | **Mature core, shallow macro layer** | Resource regeneration, macro-economy health, and progression planning are real gaps; a couple of P0 parity-ledger items are open bugs, not epics |
| Cognition / Social | **Mature core, shallow long-run proof** | Personality, belief, reputation all implemented; what's missing is active agency (entities seeking information) and cross-episode persistence |
| World Evolution / Worldbuilding | **Mixed — regional/ecology mature, macro-political absent** | Worldgen-module-epic (modules/composition/procedural gen) is done. Regional trauma/sovereignty/calamity is solid. Faction diplomacy/war/history-compiler/culture-drift: **does not exist** |
| Gameplay Loop / Product Surface | **Fragmented** | No persistent multi-episode campaign system, no Scenario Runtime Service, quests are static, no progression planner — this is where "lab tooling" hasn't yet become a "product" |

## Immediate Cheap Fixes (not epics — handle as hotfixes/small standard tickets, independent of sequencing below)

These are pre-existing, already-flagged issues found during the scan, not new proposals:

| Item | Source | Note |
|---|---|---|
| `COMB-006` AoE legality split (impact-center vs. radius legality unified check) | `parity_ledger/combat_movement.yaml`, status `missing`, **P0** | Already flagged in the ledger itself |
| `COMB-290` wound threshold doc/code divergence (`damage > max_hp * 0.25` vs. mechanics bible) | `parity_ledger/combat_movement.yaml`, **P1 divergent** | Parity bug, needs doc or code reconciliation |
| `COMB-133`/`COMB-134` empty ledger stubs ("Phase 8 owns:" / "Phase 9 owns:" with no content) | `parity_ledger/combat_movement.yaml`, **P0 missing** | Documentation gap, not behavior gap — but P0 per ledger rules |
| `STRAT-164`/`STRAT-177`, `SOC-134` missing parity tests | `parity_ledger/strategic_cognition.yaml`, `social_narrative.yaml`, **P0 missing** | Test debt on otherwise-certified subsystems |
| `RPG-INFRA-095` ID collision — one ID, two unrelated meanings, was in `logic_checklist_exhaustive.md` vs. parity ledger | infra fork | Resolved by `TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP`: the file (orphaned, unwired from Makefile/CI) is archived to `docs/archive/logic_checklist_exhaustive.md`; `docs/parity_ledger/*.yaml` is the sole authoritative parity-tracking mechanism going forward, so the collision no longer has two live sources |
| `docs/engine/known_limitations.md` is stale | flagged independently by **3 of 5 forks** | At least one claim (blacksmith-only towns) is already contradicted by done work (`TCK-20260425-PH7-M3-RECOVERY`). Needs a refresh/retire pass before it misleads another investigation — this doc is exactly the kind of authoritative source CLAUDE.md's Context Scan rule tells agents to trust |

## Candidate Epics

### A. World & History (new ground — nothing here was previously scoped)

| Epic | Current State | Gap | Why It Matters | Size |
|---|---|---|---|---|
| **Faction & Diplomacy System (fresh build)** | No current engine code exists (`src/content_semantics/faction.py` is data, not behavior); legacy `grand_strategy.md` is reference-only for scope, not a design or porting source | War, alliance, siege, conquest, territory pressure — entire macro-political layer | Largest single gap found. No macro-RPG structure above the regional/entity level; blocks any "kingdom history" or multi-faction emergent story | **XL** |
| **History / Chronicle Compiler** | Zero code; only scattered event logs | No event→episode→milestone→era compression. Can't answer "why did this happen" at any timescale beyond raw logs | Required for thousand-year-style simulation and for making completed runs legible to a human | **L** |
| **Demographic / Cohort Population Model** | `SpawnService`/`ResourceEcologyService` exist but are density/spawn-rate driven | No age-structured birth/death/migration cohorts | Needed for any long-horizon (century+) simulation; current model can't show population aging or generational change | **M** |
| **Culture / Myth Drift** | Individual-entity belief/rumor system exists (`belief_and_detour_contract.md`); nothing at culture scale | No culture-level value/taboo/myth distortion mechanism | Speculative, lowest priority of this group — depends on History Compiler existing first to have something to distort | **M**, defer |

### B. Social & Cognition (depth/agency gaps, not missing mechanics)

| Epic | Current State | Gap | Why It Matters | Size |
|---|---|---|---|---|
| **Full Party Adventure Loop** | Recruit, contract appraisal, grudge/betrayal hooks exist (see `cooperation_contract.md`) | No sustained multi-tick party lifecycle, class-compatibility scoring, fair reward-split, escort behavior | Social cohesion currently triggers parties but doesn't sustain them — caps emergent "adventuring party" stories | **M** |
| **Active Information-Seeking / Belief Economy** | Passive leads, belief/trust/strategic-blocker system exists, but blockers are material-resource-only and leads are coordinate-only (no person/concept leads) | No deliberate "ask guide/merchant," no paid info, no contradiction-driven replanning | Entities are still effectively omniscient-by-passive-injection; this is what makes subjective cognition real | **M** |
| **Personality → Long-Run Behavior Calibration** | OCEAN traits, mood, grudges all implemented and locally correct | No test/metric proves personality compounds into distinct long-run life-arcs vs. one-off route nudges | Same gap independently flagged by `feature_summary.md` — now confirmed via parity scan, not just assumed | **S–M** |
| **Social Memory as Campaign Consequence** | Reputation/commitment solid within one run | Nothing persists betrayal/rescue/cooperation history across episodes | Blocked by — should be sequenced after — Persistent Campaign Runtime (section D) since there's no cross-episode state to write into yet | **M**, blocked |

### C. Combat & Economy (macro layer missing under a mature micro layer)

| Epic | Current State | Gap | Why It Matters | Size |
|---|---|---|---|---|
| **Resource Ecology Regeneration** | Nodes largely static/reset-on-reload; confirmed independently by 3 forks | No seasonal growth/depletion/cooldown loop | Scarcity pressure can't emerge organically — undercuts economy, quest generation, and faction conflict all at once | **S–M** |
| **Macro-Economy Health Metrics** | Per-transaction conservation laws are solid (P0 mechanics); dynamic pricing exists for calamity/survival pressure (`TCK-20260503-PRICE-HARDENING`) | No inflation/gold-sink/dead-economy detection; reputation-based shop discounts still explicitly unsupported | Prevents the "infinite shop, frozen economy" failure mode flagged in `rpg_feature_direction.md` | **M** |
| **Combat Ecology Extension (nemesis/grudge depth)** | Persistent grudges and tactical-avoidance of known foes already exist (`combat_and_progression.md` §5) — deeper than the planning docs assumed | Unverified whether it covers multi-year rivalry, retirement-from-fear, or is just single-run | First step is verification, not new build — likely a small extension once depth is confirmed | **S** |
| **Progression Planner** | XP/leveling/evolution-points fully implemented | No multi-episode skill/equipment/build-goal planning | Confirmed independently by two forks; progression is currently tick-local only | **M** |

### D. Gameplay Loop / Product Surface (the "lab tooling → product" gap)

| Epic | Current State | Gap | Why It Matters | Size |
|---|---|---|---|---|
| **Persistent Campaign Runtime** | `CampaignRunner` exists but is explicitly an **analysis-only** tool (isolated state, no `Failed` state, can't share `AuthoritativeState` with live sim) | No actual multi-scenario continuity / persistent-consequence campaign system exists anywhere — this is a different concept than what currently bears the name "campaign" | Both prior planning docs assumed this existed under the "campaigns" name; it doesn't. Naming collision risk for future tickets — needs a deliberate name choice | **L** |
| **Scenario Runtime Service** | Only `CampaignRunner` (analysis) and sweep/CI batch runs exist; neither has objective/win-loss-stall state or pause/resume/checkpoint | No interactive, product-shaped single-scenario execution loop | Confirmed still missing exactly as both planning docs flagged | **M** |
| **Pressure-Driven Quest Generation** | 5 hardcoded `QuestKind`s, 6 static templates, no chains/expiry/faction-pressure generation | `rpg_feature_direction.md`'s "pressure-generated/faction/legacy quests" fully unimplemented | Good news: `world_emergence`'s `OpportunityType` extension pattern is reusable as the trigger source — this isn't starting from zero | **M** |
| **Decision Explanation Model (durable/queryable)** | Adventure route trace already computed per-tick | Not stored/queryable as a first-class API | Promotes existing data rather than building new logic | **S–M** |

### E. Architecture / Infrastructure (small, folded in from the earlier release-spine doc)

| Epic | Current State | Gap | Why It Matters | Size |
|---|---|---|---|---|
| **Granular Phase Read/Write Domain Permissions** | Coarse singular-mutation-point law enforced and verified | `RPG-INFRA-155`/`156` (declared per-phase read/write domains) unchecked | Narrower than `feature_summary.md`'s "Phase Guard" framing suggested — most of it is already done | **S** |
| **Capability / Support Registry** | Only a narrow unsupported-legacy-features list exists | No backend-readable `OFFICIAL/SUPPORTED/EXPERIMENTAL/DEPRECATED` matrix | Needed as a foundation if Feature Pack architecture (section F) is ever pursued | **M** |
| **Unified Read Model Service** | APIs work but are fragmented across cognition/history/live-status | No single presenter layer | Prevents API divergence as more read-only surfaces get added | **M** |

### F. Pluggable Feature Pack Architecture (deferred big bet — unchanged from `rpg_feature_direction.md`)

Still **zero code, zero docs** beyond the vision doc itself. `FeaturePackManifest`/`RuntimeProfile`/`CompatibilityResolver`/`BalanceExperimentSpec`. One concrete enabler found during this scan: the adventure-routing and world-emergence domains both already use a clean, documented "enum → generator → scorer → mapper → tests" extension pattern (`adventure_routing_contract.md`, `world_emergence_contract.md`) — proven twice at small scale, and the natural template to generalize into the Feature Pack manifest shape. Recommend treating this as **proof-of-concept fuel**, not a reason to start the big architecture yet. **Size: XL, defer.**

## Sequencing Recommendation (not a decision — for discussion)

1. **Cheap fixes first** — the P0 parity-ledger items (`COMB-006`, `COMB-133/134`, `STRAT-164/177`, `SOC-134`) are already-acknowledged debt under the project's own Authoritative Mechanics Rule; low cost, should not wait on epic prioritization.
2. **`known_limitations.md` refresh** — cheap, and prevents future investigations (including this one's method) from citing stale claims.
3. Among the epics, three look like natural anchors for "next big thing" because they unblock others:
   - **Persistent Campaign Runtime** unblocks Social-Memory-as-Campaign-Consequence and gives Faction System / History Compiler somewhere to write consequences.
   - **Resource Ecology Regeneration** unblocks Macro-Economy Health and Pressure-Driven Quest Generation (both want scarcity signals to react to).
   - **Faction & Diplomacy System (fresh build)** is the highest-ceiling single epic but also the largest (XL) — worth deciding deliberately rather than backing into it.

## Open Decisions

This investigation deliberately stops short of picking the next epic — that's a call for you, not something to infer from gap size alone.

---

## Engine Audit Update — 2026-06-19

The 18-dimension audit programme (`TCK-20260618-AUDIT-EPIC`) completed on 2026-06-19. Key findings that update or confirm entries above:

### Critical Bugs Found and Fixed (RC1/RC2/RC3)

Three wiring bugs caused total behavioral stasis in the simulation before any epic work begins. These are **now fixed** but are recorded here because they explain audit run data and because any future investigation of behavioral quality should verify they remain fixed:

- **RC1** (`adventure/phase.py:60`): `AdventureDecisionPhase` never passed `opportunities=` to `AdventureRouteGenerator.generate()`. Primary route loop executed zero times every tick.
- **RC2** (`world/providers/requirements.py:154`): `near_service` requirement hardcoded to `if region_id == "hometown"` — always failed in non-hometown worlds.
- **RC3** (`world/providers/requirements.py`): `PerformanceBudgets.provider_calls_total` (class-level counter) never reset between ticks — exhausted at tick ~25, after which opportunity provider returned empty lists.

### Confirmed and Sharpened Gaps (by epic section)

**Section B — Personality → Long-Run Behavior Calibration:**
Audit D05 confirms this is NOT a calibration problem — it is a **complete initialization absence**. `WorldCompiler.compile()` produces `PersonalityComponent(greed=0.0, bravery=0.0, sociability=0.0, industry=0.0)` for every entity. The OCEAN system and scoring formula are correctly implemented; the world compiler never seeds non-zero values. The fix is in `WorldCompiler` entity spawn, not in the scoring formula.

**Section C — Resource Ecology Regeneration:**
Audit D06 confirms this gap is now also blocking hunger satiation. No food-kind resource node exists in any tested world — entities generate hunger projects indefinitely (every ~30 ticks) but hunger urgency never resolves. This means hunger permanently outscores all economic goals, making economic/crafting balance measurement impossible until either food nodes or hunger threshold calibration is fixed.

**Section D — Decision Explanation Model:**
Audit D15 confirms: route trace computed every tick in `execute_brain()` but discarded at tick boundary. Rich `cognition_graph_snapshots.jsonl` exist per run but only in DEBUG/CERTIFICATION mode, with no REST query API and no tick indexing. Promoting existing computed data to a queryable API would close the P0 gap without new simulation logic.

### New Findings Not Previously in Roadmap

**CI / Test Pipeline — Zero automation (D18):**
No `test.yml` exists. Every push to `main` runs only `deploy-docs.yml` (mkdocs deploy). All certification harness, architecture guards, and regression tests require local invocation. The fix is a single `test.yml` calling `make lane-all-fast` + `make gate-expansion` + `pytest tests/docs/`. This belongs in section E as a **cheap fix**, not an epic.

**Dead Code Cleanup — 9 orphaned src/ directories (D11):**
`src/ai/`, `src/town/` (10 files), `src/entities/` (4 files), `src/views/runtime/actions/`, `src/quests/`, `src/content_semantics/`, `src/systems/` and two others — 36 files, ~2,955 lines of unreachable V1 code. `src/ai/goals/scorers.py` implements the V1 GoalScorer pattern that `design_patterns.md` still documents as the extension point (D12 joint finding). Safe deletion order: views/runtime/actions/ → town/quests/ → entities/ → ai/ (after parity ledger audit for SOC/STRAT compliance IDs). This is a **cheap-fix cluster**, not an epic.

**World Content Authoring Gap (D08):**
Multi-scenario audit found 94% entity attrition in `dungeon_crawl` (32 entities, 1 building, 4 regions) and near-extinction in `wilderness_survival` (0 buildings). Engine handles both correctly; the world content authoring layer is uncalibrated. Urban_political (7 buildings, 27 entities) is the only world producing economic activity (`harvesting`, `town_return`). New world content for balanced dungeon/wilderness scenarios should accompany any content-depth epic (section C/D).

**Scoring Formula Imbalance (D04):**
`blocker_penalty = 2.0` (fixed) vs. max achievable non-blocked score ~2.65. Any route with a single minor blocker scores near zero regardless of urgency. Consider a graduated penalty before quest generation epic (section D) — otherwise quests with any blocker condition will be systematically excluded from entity consideration.
