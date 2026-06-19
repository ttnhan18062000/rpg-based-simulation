---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [audit, documentation, currency, staleness, mechanics-bible, engine-contracts]
---

# D17 — Documentation Currency

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | C — Developer Tooling |
| **State** | `done` |
| **Impact** | 4 / 5 |
| **Interest** | 3 / 5 |
| **Priority** | 7 |
| **Method** | code-read + review |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Which documentation files contain claims that contradict
the current source code? Stale authoritative docs silently mislead implementation work —
agents and developers implementing against the Mechanics Bible or engine contracts must
be able to trust them.

**Related dimensions:** D10 (Test Coverage) — stale biological threshold values mean some
parity tests may assert wrong expected values. D09 (System Wiring) — pipeline phase count
discrepancy found during this audit; both docs cross-reference. D12 (Pattern Consistency)
— naming inconsistency between pipeline doc and code may signal broader doc-code divergence.

---

## Review Method

Each target document is spot-checked: 3–5 claims per file are selected and verified against
the current source code. Selection targets numeric constants, phase counts, and named
behaviors — claims precise enough to be wrong.

**Files audited:**
- `docs/engine/known_limitations.md`
- `docs/engine/kernel.md`
- `docs/engine/authoritative_pipeline.md`
- `docs/mechanics/01_entity_anatomy.md`
- `docs/mechanics/02_combat_laws.md`
- `docs/mechanics/03_economic_laws.md`
- `docs/mechanics/04_strategic_cognition.md`
- `docs/mechanics/05_world_evolution.md`
- `docs/mechanics/06_worldbuilding_foundation.md`

### Staleness Classification

| Status | Meaning |
|---|---|
| `current` | Claim verified against source code — correct |
| `stale` | Claim contradicts current source code with specific evidence |
| `uncertain` | Claim is qualitative, or numeric constants exist but were not traced to source |

### Finding Severity Scoring

Key findings are scored on four dimensions, each 1–5. Maximum: 20.
Higher score = higher priority to correct.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Magnitude** | Off by < 10% or naming only | Wrong value / wrong mechanism | Opposite or wildly wrong claim |
| **Reference Frequency** | Rarely consulted | Referenced in agent investigations | Primary implementation reference |
| **Blast Radius** | Misleads one isolated task | Misleads an architecture decision | Misleads P0 parity targets or multiple systems |
| **Self-Cert Risk** | No authority claim in doc | Doc is authoritative but acknowledged stale | Doc explicitly claims to be verified and current |

---

## `docs/engine/known_limitations.md`

Last updated: 2026-04-21 (pre-dates worldgen epic of 2026-06-16; may have more gaps not sampled here).

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | "Linear Stepping Only — V2 relies on direct linear stepping toward coordinates" | `current` | D02 confirmed; `FlowFieldService` in `src/systems/world_systems/navigation.py` — linear stepping, no A* |
| 2 | "No Complex Regeneration — Resource nodes do not support complex regeneration logic" | `current` | D02 confirmed; `ResourceEcologyService` called live but internals have no regeneration cycles |
| 3 | **"Blacksmith Only — The Blacksmith is the single supported town-resolution building"** | **`stale`** | `src/engine/town_resolution.py:90–101` handles `"inn"`, `"home"`, `"tavern"` building types in addition to blacksmith. Inn REST action and tavern EAT action are live code paths. |
| 4 | "Material-Only Blockers — StrategicIntelligenceSystem only recognizes crafting blockers for Material resources" | `uncertain` | Consistent with D02 investigation but not re-verified against current source this session |
| 5 | "Worker Parity — Sequential mode only officially ratified for bit-identical parity" | `current` | D02 confirmed; also consistent with `src/engine/worker_manager.py` structure |

**Summary:** 1 confirmed stale, 3 current, 1 uncertain. The Blacksmith-Only claim was likely
invalidated by TCK-20260425-PH7-M3-RECOVERY as flagged in the D02 investigation.

---

## `docs/engine/kernel.md`

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | **First phase table (6 phases): Init → Governance → Scheduling → Deliberation → Resolution → Persistence** | **`stale`** | Code (`kernel.py:_tick_once_inner`) has 7 phases with different names. "Governance" is not a phase — governor evaluates inside `_phase_init()`. "Deliberation" is called "Collection" in code. Cleanup and Advancement phases are absent from this table. |
| 2 | Second phase table (7 phases): Init → Scheduling → Collection → Resolution → Cleanup → Advancement → Persistence | `current` | Matches `_tick_once_inner()` exactly — all 7 `_phase_*` method calls confirmed |
| 3 | "Stability Guard: fingerprint at tick start; re-verified after Scheduling and Collection" | `current` | `_guard_stability("Scheduling", ...)` and `_guard_stability("Collection", ...)` confirmed in `kernel.py:303–311` |
| 4 | "Hard Law Monitor invoked in Advancement phase; DEBUG/CERTIFICATION throws `HardLawViolationError`" | `current` | `_run_hard_law_checks()` called in `_phase_advancement()` at line 625; mode-specific policy confirmed |
| 5 | "Content Hot-Path Guard (WORLD-CAT-004): `load_all()` forbidden inside tick; warmup in `__init__()`" | `current` | `_tick_context_active.active = True` in `tick_once()`, `ContentWarmupService.warmup()` in `__init__()` confirmed |

**Summary:** 1 confirmed stale, 4 current. The doc contains two phase tables that contradict
each other — the first table is the stale one. A developer reading top-to-bottom sees the
wrong phase count and wrong phase names first.

---

## `docs/engine/authoritative_pipeline.md`

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | **"17 phases of refinement" (numbered table)** | **`stale`** | `src/engine/pipeline.py:refine()` has 30+ named `run_phase()` calls: `trust_boundary`, `actor_validity`, `self_model`, `information_belief`, `cooperation`, `contracts`, `blacksmith`, `adventure_decision`, `action_routing`, `position_swaps`, `movement_routing`, `combat_engagement`, `interaction_routing`, `interaction_enforcement`, `building_sabotage`, `town_resolution`, `world_dynamics`, `world_emergence`, `quest_rewards`, `shop`, `resource_transactions`, `evolution`, `progression_conversion`, `strategic_intelligence`, `near_death_hardening`, `occupancy_resolution`, `lifecycle`, `groups`, `active_contracts`, `expired_offers`, `capacity_enforcement`. The 17-phase doc describes an earlier version of the pipeline. |
| 2 | **"Phase 8: Task Translation (TOWN-164)"** | **`stale`** | No phase named `task_translation` exists in current `pipeline.py`. `TOWN-164` appears as a compliance ID in the file header but is not a standalone phase. The interactions are now handled by `interaction_routing` + `interaction_enforcement` + `building_sabotage`. |
| 3 | **"Phase 10: Combat Hardening (COMB-121)"** | **`stale`** | `near_death_hardening` phase exists in code but is in the final group (after `strategic_intelligence`), not phase 10. Phase ordering in doc does not match code. |
| 4 | "All changes must be represented as a `StateUpdate` and refined through these phases" | `current` | Architectural law confirmed — `pipeline.py:41` comment and entire pipeline structure enforce this |
| 5 | "Ecological Dynamics phase (INFRA-001): Deaths increase regional trauma; Sovereignty Law" | `current` | `WorldDynamicsSystem.resolve_dynamics()` called as "world_dynamics" phase; trauma and sovereignty logic confirmed in `world_dynamics.py:78–82` |

**Summary:** 3 confirmed stale, 2 current. The 17-phase table is the most significant
doc-code gap found in this audit. It describes ~half the actual phase count, uses wrong
phase names, and has wrong ordering. Any agent implementing against this doc will build
incorrectly sequenced logic.

---

## `docs/mechanics/01_entity_anatomy.md`

Last verified: 2026-06-06 (per frontmatter).

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | 9 core attributes: STR, AGI, VIT, END, INT, SPI, WIS, PER, CHA | `current` | `src/core/state.py:395–405` — `AttributeComponent` has exactly these 9 fields |
| 2 | **"Hunger threshold: 100.0 → Starvation (5 damage/tick)"** | **`stale`** | `src/engine/apply.py:97`: `if bio.hunger >= 95.0: total_passive_dmg += 2`. Threshold is **95.0** (not 100.0) and damage is **+2** (not 5). |
| 3 | **"Sleep Debt threshold: 80.0 → Fatigue (-50% ATK/DEF)"** | **`stale`** | `src/engine/apply.py:98`: `if bio.sleep_debt >= 98.0: total_passive_dmg += 1`. Threshold is **98.0** (not 80.0) and the penalty is **+1 HP damage** (not an ATK/DEF multiplier). |
| 4 | "Wound Threshold: `damage >= max_hp * 0.40`" | `current` | `src/engine/rpg_depth.py:110`: `WOUND_THRESHOLD_RATIO = 0.40` — matches exactly |
| 5 | "Scar penalty: 30% of original wound's stat penalties" | `current` | `src/engine/rpg_depth.py:194–196`: `wound.atk_penalty * 0.3` — matches exactly |

**Summary:** 2 confirmed stale, 3 current. The biological threshold values are materially
wrong — an agent implementing starvation/fatigue behavior against this doc would use
wrong thresholds and wrong penalty types.

---

## `docs/mechanics/02_combat_laws.md`

Last verified: 2026-06-06 (per frontmatter).

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | Damage formula: `Damage = Atk * (Atk / (Atk + Def * 2.0 + 1.0))` | `current` | `src/engine/combat.py:45`: `raw_damage = int(atk * (atk / (atk + dfn * 2.0 + 1.0)))` — matches exactly |
| 2 | High Ground `+0.20` Atk, Flanking `+0.15` Atk, Surrounded `+0.25` Atk | `current` | `src/engine/combat.py:66,71,76`: confirmed values match |
| 3 | Shatter `x1.50` Atk, Exhaustion `x0.80` Atk | `current` | `src/engine/combat.py:85,89`: `atk_mult *= 1.5` and `atk_mult *= 0.8` — confirmed |
| 4 | Cover `+0.30` Def, Bond Synergy `+0.10` Atk | `uncertain` | Code uses `COVER_REDUCTION` and `BOND_SYNERGY_BONUS` class constants — values not traced to definitions this session |
| 5 | "Minimum Damage: every hit deals at least 1 damage" | `current` | `src/engine/combat.py:46`: `return max(1, raw_damage)` — confirmed |

**Summary:** 0 stale, 4 current, 1 uncertain. Chapter 2 is the best-maintained mechanics chapter.

---

## `docs/mechanics/03_economic_laws.md`

Last verified: 2026-06-06 (per frontmatter).

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | "Atomic Conservation Law — both source and sink update in a single atomic step; rollback if either fails" | `current` | D02 confirmed `ResourceTransactionResolver` in `src/core/conservation.py`; `resource_transactions` pipeline phase confirmed |
| 2 | "Slot Limit: 16 slots; Weight Limit: 100.0 kg" | `uncertain` | Pattern is consistent with code structure but default values not verified against `InventoryComponent` defaults this session |
| 3 | "Home Storage: 32 slots, 200.0 kg" | `uncertain` | Not verified against `home_storage` state component this session |
| 4 | "Selling price: `Item_Base_Value * 0.5 * Market_Multiplier`" | `uncertain` | Consistent with `ShopSystem.enforce()` call in pipeline but formula not traced to source |
| 5 | "Depletion — charges reach 0, node removed and enters regeneration phase (if applicable)" | `current` | `src/engine/world_dynamics.py:165–174`: cooldown countdown confirmed; when `cooldown_remaining == 1` node recharges to `max_charges`. Consistent with this claim. |

**Summary:** 0 stale, 2 current, 3 uncertain. The atomic conservation law is well-verified; numeric defaults need a dedicated follow-up check.

---

## `docs/mechanics/04_strategic_cognition.md`

Last verified: 2026-06-06 (per frontmatter).

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | Goal hierarchy: Tier 1 Survival → Tier 2 Biological → Tier 3 Social → Tier 4 Economic | `uncertain` | Consistent with scorer/priority structure in `src/ai/goals/` but tier numbering not directly verified |
| 2 | **"Interruption Margin = `Profile_Resistance * 30.0`"** | **`stale`** | `src/systems/strategic_systems/intelligence.py:915`: `retention_margin = profile.interruption_resistance * profile.resistance_multiplier`. The multiplier is `resistance_multiplier` from the profile — not a hard-coded `30.0`. The value of `resistance_multiplier` varies by entity profile. |
| 3 | Blocker types: Access, Material, Inventory, Congestion | `uncertain` | Consistent with parity ledger (Material-only resolvers confirmed by known_limitations.md) but full blocker type inventory not re-verified |
| 4 | "Perception Radius: 10.0 to 15.0 units" | `uncertain` | Consistent with `DomainView.get_neighbor_view(radius=10.0)` in `src/engine/domain/view.py` but upper bound not verified |
| 5 | "Info Decay: leads lose certainty every 100 ticks" | `uncertain` | Lead staleness exists in `StalenessEntry` (confirmed by graph query) but decay interval not verified against source this session |

**Summary:** 1 confirmed stale, 0 current, 4 uncertain. The interruption margin formula hardcodes
30.0 but the actual implementation uses a configurable `resistance_multiplier`. This is a
meaningful divergence for agents implementing switching logic.

---

## `docs/mechanics/05_world_evolution.md`

Last verified: 2026-06-06 (per frontmatter).

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | "Resource Nodes respawn after 100 ticks by default" | `uncertain` | `world_dynamics.py` decrements `cooldown_remaining` and recharges when it hits 1. The initial cooldown value is set at depletion time (not in world_dynamics) — default value not confirmed this session |
| 2 | "Every entity death adds +1.0 to regional Trauma Score" | `uncertain` | `CalamityService.apply_calamity_consequences()` handles trauma distribution but exact delta not confirmed |
| 3 | "Sovereignty thresholds: Hero ≥ +100.0, Monster ≤ -100.0" | `current` | `src/engine/world_dynamics.py:79,82`: `current_influence >= 100.0` and `current_influence <= -100.0` — confirmed exactly |
| 4 | "Suppression: entities lose -5.0 Readiness per tick" | `current` | `src/engine/apply.py:134`: `readiness=max(0.0, comb.readiness - 5.0)` when `region.suppression_active` — confirmed |
| 5 | "Environmental Fatigue: Sleep Debt +1.0 in hazardous regions" | `current` | `src/engine/apply.py:141`: `bio.sleep_debt + 1.0` when `stamina_drain > 1.0` weather multiplier — confirmed |

**Summary:** 0 stale, 3 current, 2 uncertain. The world evolution doc is in reasonable shape for its verifiable claims.

---

## `docs/mechanics/06_worldbuilding_foundation.md`

Last verified: 2026-06-06 (per frontmatter).

| # | Claim | Status | Evidence |
|---|---|---|---|
| 1 | "Coordinate System: strictly locked to `grid`" | `current` | `src/worldbuilding/schema.py` validated by worldgen epic; grid-only topology confirmed |
| 2 | "Kahn's Topological Sort for dependency resolution; cycle → abort" | `current` | `WorldAssembly` / `WorldBuildingCompiler` confirmed to use DAG-based dependency resolution (worldgen epic, D02) |
| 3 | "Pydantic Validation → Spatial Check → CompileContext Overrides → Assembly" | `current` | Consistent with `WorldBuildingCompiler`, `ContentValidator`, and assembly pipeline from D02 |
| 4 | "Provenance manifest sidecar output per run" | `current` | `src/engine/kernel.py:151–171`: `RunManifest` created in `__init__()` with `provenance_manifest_path` field — confirmed |
| 5 | "All chapters are Certified Level 1 (Authoritative). Documentation matches current source code." | **`stale`** | This audit found stale claims in chapters 01 (biological thresholds) and 04 (interruption margin formula). Chapter 06's own self-certification is therefore incorrect. |

**Summary:** 1 confirmed stale (self-certification claim), 4 current. Chapter 06 is structurally
sound but its blanket "Certified Level 1" claim is invalidated by the staleness found elsewhere.

---

## Cross-File Summary

| File | Stale | Current | Uncertain | Priority |
|---|---|---|---|---|
| `known_limitations.md` | 1 | 3 | 1 | P1 — Blacksmith claim actively misleads planning |
| `kernel.md` | 1 | 4 | 0 | P1 — First phase table is wrong, and appears before the correct one |
| `authoritative_pipeline.md` | 3 | 2 | 0 | **P0** — 17-phase table is half the real count; phase names wrong |
| `mechanics/01_entity_anatomy.md` | 2 | 3 | 0 | P1 — Biological thresholds are numeric and precisely wrong |
| `mechanics/02_combat_laws.md` | 0 | 4 | 1 | P2 — Mostly current; two constants unverified |
| `mechanics/03_economic_laws.md` | 0 | 2 | 3 | P2 — Structural laws correct; numeric defaults uncertain |
| `mechanics/04_strategic_cognition.md` | 1 | 0 | 4 | P1 — Interruption margin formula is wrong; much uncertain |
| `mechanics/05_world_evolution.md` | 0 | 3 | 2 | P2 — Current where verified |
| `mechanics/06_worldbuilding_foundation.md` | 1 | 4 | 0 | P2 — Self-certification claim only (structural content correct) |
| **Total** | **9** | **25** | **7** | |

---

## Key Findings

### Finding 1: `authoritative_pipeline.md` is significantly out of date — Severity: 18 / 20

| Dimension | Score | Reason |
|---|---|---|
| Magnitude | 5 | Doc says 17 phases; code has 30+. Phase names and order wrong. |
| Reference Frequency | 5 | Primary reference for pipeline implementation work |
| Blast Radius | 5 | Any agent adding a new pipeline phase will use wrong insertion points |
| Self-Cert Risk | 3 | Doc does not claim to be verified but is authoritative by category |
| **Total** | **18** | |

The 17-phase table describes an earlier version of the pipeline. Current `pipeline.py:refine()`
has 30+ named phases including 7 new Enhanced RPG domain phases (`self_model`,
`information_belief`, `cooperation`, `adventure_decision`, `combat_engagement`,
`world_emergence`, `progression_conversion`) plus additional infrastructure phases that
were not present when the doc was written. Phase names, numbers, and ordering in the
doc do not match the code.

**Risk:** Any agent or developer implementing new pipeline phases will use wrong insertion
points and wrong phase names.

### Finding 2: `kernel.md` has two conflicting phase tables — Severity: 14 / 20

| Dimension | Score | Reason |
|---|---|---|
| Magnitude | 4 | First table has wrong phase count AND wrong names; second table is correct |
| Reference Frequency | 4 | `kernel.md` is the first doc any new developer reads |
| Blast Radius | 3 | Developer reading linearly gets wrong count first; likely to catch it on second read |
| Self-Cert Risk | 3 | No explicit verified claim but kernel.md is authoritative |
| **Total** | **14** | |

The first table shows 6 phases (including non-existent "Governance" phase and
"Deliberation" instead of "Collection"). The second table (7 phases) is correct. A
developer reading linearly sees the wrong count first.

### Finding 3: Biological thresholds in mechanics/01 are numerically wrong — Severity: 16 / 20

| Dimension | Score | Reason |
|---|---|---|
| Magnitude | 5 | Hunger: doc 100.0/5dmg vs code 95.0/+2dmg. Sleep debt: doc 80.0/-50%ATK vs code 98.0/+1HP dmg. Wrong threshold AND wrong effect type. |
| Reference Frequency | 4 | mechanics/01 is the primary entity anatomy reference |
| Blast Radius | 4 | Any agent implementing starvation/fatigue uses wrong trigger points and wrong penalty model |
| Self-Cert Risk | 5 | Mechanics Bible explicitly states "All chapters Certified Level 1 (Authoritative)" |
| **Total** | **16** | |

Hunger starvation: doc says threshold=100.0, damage=5/tick. Code: threshold=95.0, damage=2.
Sleep debt fatigue: doc says threshold=80.0, penalty=-50% ATK/DEF. Code: threshold=98.0,
penalty=+1 HP damage. Both the trigger point and the effect type differ for sleep debt.

### Finding 4: Interruption margin formula uses profile constant, not hardcoded 30.0 — Severity: 12 / 20

| Dimension | Score | Reason |
|---|---|---|
| Magnitude | 4 | Wrong constant: doc says 30.0; code uses resistance_multiplier (varies by entity) |
| Reference Frequency | 3 | mechanics/04 consulted for strategy/goal-switching implementation |
| Blast Radius | 3 | Any agent implementing goal interruption computes margin with wrong formula |
| Self-Cert Risk | 2 | mechanics/04 does not explicitly claim recent verification |
| **Total** | **12** | |

`mechanics/04` documents `Interruption_Margin = Profile_Resistance * 30.0`.
Code uses `profile.interruption_resistance * profile.resistance_multiplier`. The 30.0
constant may exist as one profile's `resistance_multiplier` value but it is not universal.

### Finding 5: `known_limitations.md` Blacksmith-Only claim is stale — Severity: 10 / 20

| Dimension | Score | Reason |
|---|---|---|
| Magnitude | 3 | Wrong claim: inn and tavern both handled; not just blacksmith |
| Reference Frequency | 3 | known_limitations.md consulted when scoping town/economy features |
| Blast Radius | 2 | Misleads scoping of new town building types — narrowly scoped impact |
| Self-Cert Risk | 2 | known_limitations.md is descriptive, not certified authoritative |
| **Total** | **10** | |

`TownResolutionSystem` handles `"inn"` (REST action) and `"tavern"` (EAT action) in
addition to blacksmith. The claim was likely accurate before TCK-20260425-PH7-M3-RECOVERY
but was not updated after that ticket completed.

---

### Finding Severity Summary

| Rank | Finding | Severity Score |
|---|---|---|
| 1 | Finding 1 — `authoritative_pipeline.md` 17-phase table | 18 / 20 |
| 2 | Finding 3 — Biological thresholds wrong | 16 / 20 |
| 3 | Finding 2 — `kernel.md` dual conflicting tables | 14 / 20 |
| 4 | Finding 4 — Interruption margin formula wrong | 12 / 20 |
| 5 | Finding 5 — Blacksmith-Only claim stale | 10 / 20 |

---

## Recommended Follow-Up Tickets

| Priority | File | Item |
|---|---|---|
| **P0** | `docs/engine/authoritative_pipeline.md` | Rewrite 17-phase table to reflect actual 30+ phases in `pipeline.py` |
| **P1** | `docs/engine/kernel.md` | Remove or clearly mark the stale 6-phase first table |
| **P1** | `docs/mechanics/01_entity_anatomy.md` | Fix hunger threshold (95.0 / +2 dmg) and sleep debt threshold (98.0 / +1 dmg; HP penalty, not ATK/DEF multiplier) |
| **P1** | `docs/engine/known_limitations.md` | Remove Blacksmith-Only claim; document actual building types supported |
| **P1** | `docs/mechanics/04_strategic_cognition.md` | Fix interruption margin: replace `30.0` with `resistance_multiplier` (profile-defined) |
| P2 | `docs/mechanics/02_combat_laws.md` | Confirm Cover and Bond Synergy constants match `COVER_REDUCTION` and `BOND_SYNERGY_BONUS` values |
| P2 | `docs/mechanics/03_economic_laws.md` | Verify inventory slot/weight defaults against `InventoryComponent` source |
| P2 | `docs/mechanics/04_strategic_cognition.md` | Audit all 4 uncertain claims (goal tiers, blocker types, perception radius, info decay interval) |
| P2 | `docs/mechanics/06_worldbuilding_foundation.md` | Update self-certification claim — not all chapters are currently accurate |

---

## Related Dimensions

- **D10 (Test Coverage)** — stale docs in the Mechanics Bible mean some parity tests may
  be checking against wrong expected values; the `COMB-290` parity entry flagging the
  wound threshold should be re-checked
- **D12 (Pattern Consistency)** — pipeline phase naming inconsistency between doc and code
  may signal broader doc-code divergence in domain contracts
- **D09 (System Wiring)** — the 30+ pipeline phases found here contradict this doc's
  17-phase table; both audits share the same source evidence
