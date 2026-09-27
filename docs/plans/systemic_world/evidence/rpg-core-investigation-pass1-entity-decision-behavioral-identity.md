---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `rpg-core-investigation-pass1-entity-decision-behavioral-identity.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Investigation Report — Pass 1: Entity Decision & Behavioral Identity

**Scope:** personality, traits/characteristics, archetypes, needs, preferences/values, goals,
beliefs/memory, relationships, the decision pipeline, behavioral continuity. Life trajectory
(capability growth, role/profession evolution, opportunity generation, reputation propagation) is
Pass 2's job — this report only reaches it where Pass-1 evidence already touches it.

**Method:** `search_docs` → direct file reads/grep, every claim cited to a file:line or a specific
ticket. `UNKNOWN` used explicitly where evidence didn't resolve a question. Two classification axes
kept separate throughout, per the user's refinement — never blurred:
- **Semantic assessment** (does a Rule exist for this at all): *already covered* / *covered but
  realization incomplete* / *semantically ambiguous* / *genuine World Rule gap* / *derived-narrative
  only*.
- **Existing Rule realization status** (is an existing Rule actually realized in the repo):
  `SUPPORTED` / `PARTIAL` / `CONFLICTING` / `MISSING` / `INERT-OFF` / `UNKNOWN` — the Catalog's own
  vocabulary (`docs/plans/simulation_semantic_control_plane/architecture.md` §4).

**Constraint honored:** no canonical Rule text read-modified — `docs/world_rules/capability-
progression/*.md` and siblings were read-only throughout (M4 of the Semantic Control Plane is live
against those files). All potential Rule changes below are prose findings, never draft Rule text.

---

## A. Executive finding

Entity decision-making in this repository is **substantially more compositional than the closed
World Rule Catalog's own Final Integration Batch or the (now three-month-old) D05 audit would
suggest on their own.** The central finding: `ScoreModifierSystem.apply_modifiers()`
(`src/ai/score_modifiers.py:12-74`) is a **single, universal post-processing pipeline applied to
every scored goal for every entity**, composing, in order: (1) personality bias (multiplicative),
(2) life-stage multiplier, (3) a "boredom tax" (habituation — repeated pursuit of the same goal kind
reduces its future utility), (4) a **strategic-learning bias derived from `TurningPointState`
records** — durable, typed, per-entity life-history events (`betrayal`, `near_death`, `first_kill`,
`great_victory`, `loss`) that shift future goal preference, and (5) structural blocker suppression.

This is not a single narrow wire. It is the literal implementation of the brief's own "STRONG"
stress-test model — `disposition/history/values → goal preference → choices → lived history →
changed future decisions` — for at least the combat/social/exploration goal axes, verified by
production code, not aspiration. The weakest link is not the mechanism's existence but its
**breadth of triggering opportunity**: personality's `greed`/`sociability` dimensions were measured
with weak real-world effect (Δ<0.05 Shannon-entropy shift) in a 2026-06-28 empirical audit, and the
audit's own diagnosis was "opportunity set too thin," not "wiring broken" — a partial mitigation
(weight increase) shipped the same week (§E, F below).

**Biggest strengths:** (1) a real, typed, capped, producer-verified turning-point/history-bias loop
that is genuinely self-reinforcing; (2) personality composes across at least four distinct causal
domains (combat targeting, goal-kind utility, party role assignment, leadership succession — §E);
(3) memory, temporal urgency, and spatial familiarity are cleanly separated, typed, and (mostly)
tested per `memory_contract.md`.

**Biggest structural gaps:** (1) `SocialScorer` — the actual GoalKind.SOCIAL base-utility
scorer — is a hardcoded placeholder returning a flat `10.0` regardless of any relationship, trust,
or context state (§G); (2) a currently-active P1 engine-contract doc (`rpg_refinement_pillars.md`)
describes an archetype mechanic ("Pillar Traits" — Colossus/Archmage/Juggernaut) whose only concrete
spec lives in `docs/archive/`, with zero matching implementation in `src/` (§E); (3) the
lived-history → recognition → reaction gap the Final Integration Batch already found (six of seven
subject scales) is directly visible again here at the personality/decision layer: turning points
change an entity's own future behavior, but nothing found in this pass propagates that changed
behavior into *other entities' knowledge of who this entity has become* — the loop closes internally
but not socially (§G, §I).

---

## B. Existing concept inventory

| Concept | Semantic owner | Stored/derived | Causal/non-causal | Main consumers | Mutable? | Runtime evidence | Semantic assessment | Realization status |
|---|---|---|---|---|---|---|---|---|
| **Personality** (`greed`, `bravery`, `sociability`, `industry`) | `src/core/state.py:525-544` (`PersonalityComponent`) | Stored, persistent | Causal | `PersonalityService.get_goal_modifiers` (`src/ai/personality.py`), `EngagementRiskEvaluator` (combat caution), `PartyCompositionScorer` (role assignment, `party_composition.py:45-198`), `PartyLifecycleService` (leadership election, `party_lifecycle.py:45`) | Seeded once at spawn (`build_personality_for_entity`, `entity_spawner.py:126`, `compiler.py:612-618`); **UNKNOWN whether it changes post-spawn from lived history** — no consumer found writing to `PersonalityComponent` after creation | Empirically measured: bravery STRONG (Δ=-0.719 Shannon entropy), industry MODERATE (Δ=-0.226), greed/sociability WEAK (Δ<0.05) — `TCK-20260628-E11B-PERSONALITY-AUDIT` | Already covered — Batch 06's AGENCY-02 ("influence, not determination") directly describes this pattern; already cited by `conflict-combat.md`'s own Repository Findings | `SUPPORTED` for bravery/industry; `PARTIAL` for greed/sociability (mechanism real, real-world effect weak — starved-opportunity pattern, not broken wiring, per the audit's own diagnosis) |
| **Class tier** (e.g. Mage→Archmage) | `src/core/classes.py` (`ClassTierOption`) | Derived from level + attribute threshold | Causal (grants abilities/passives — not verified in this pass) | `docs/core/attributes_and_classes.md:192,211` (Lv10, INT≥30 gate) | Mutable via progression, one-directional (no de-promotion path found) | Doc-level only in this pass; **UNKNOWN at runtime** without a Pass 2/deeper trace | Covered but realization incomplete for the runtime causal effect — not verified this pass | `UNKNOWN` |
| **"Pillar Traits"** (Colossus/Archmage/Juggernaut, massive global multipliers at Lv50/75/100) | Claimed by `docs/engine/contracts/rpg_refinement_pillars.md` (status: active, authority: P1) | Claimed causal state | **No implementation found** — zero hits for "Colossus"/"Juggernaut"/"Pillar Trait" anywhere in `src/` | None found | N/A | Zero runtime evidence; only concrete spec lives in `docs/archive/systems/combat_and_progression.md:285-293` (an *archive* doc) | Derived/narrative-only in current reality, but the currently-active contract doc still asserts it as live design | `MISSING` — and the doc itself appears stale/inaccurate on this specific point (out of this pass's scope to fix — flagged for Pass 2 or a separate doc-accuracy note) |
| **Turning points** (betrayal, near_death, first_kill, great_victory, loss) | `src/core/strategic.py:200-206,357-425` (`TurningPointState`, `TurningPointKind`) | Stored, persistent, capped (`max_turning_points=20`) | **Causal** — directly biases future goal utility | `StrategicLearningService.get_goal_biases()` (`src/systems/strategic_systems/learning.py`), consumed by `ScoreModifierSystem.apply_modifiers()` | Append-only, capped list; producers confirmed in `contracts.py:245`, `appraisal.py:427`, `intelligence.py:1155,1166` | Directly traced producer→consumer this pass (see §C, §F) | Genuine World Rule gap or already-covered-elsewhere — **UNKNOWN which**; this is exactly HP-01/02/05's "historical continuity/provenance" territory but at the *individual behavioral-disposition* level HP doesn't explicitly name — flagged, not resolved, per the constraint against drafting Rule text | `SUPPORTED` — real, typed, producer-and-consumer verified |
| **Boredom** (`entity.strategic.boredom`) | `src/core/strategic.py` (not read in full this pass) | Stored, per-goal-kind | Causal — subtractive utility tax | `ScoreModifierSystem.apply_modifiers()` line 42-45 | Mutated by `intelligence.py` (`boredom_delta` on project outcome, lines 1162,1173) | Directly traced this pass | Not previously named in the Catalog under this word — **semantically ambiguous** whether it's a Domain Rule of its own or an Inherited application of an existing habituation/diminishing-returns concept | `SUPPORTED` |
| **Relationships — structural/grudge/nemesis** | `src/systems/social_systems/relationships.py`, `memory.py` | Stored, per-other-entity | Causal | `check_nemesis_promotion` (combat targeting priority, per `rpg_refinement_pillars.md` §4.1 — not independently re-verified this pass), `CausalAttributionService` (`party_abandoned` → trust-failure lesson) | Mutable, bounded (`grudge_history` clamped [0.0, 5.0]; promoted to `nemesis_ids` at ≥3.0) | Directly traced producer/consumer this pass | Already covered — Batch 09's SOC-01/SOC-02 (structural relation vs. subjective attitude are distinct; reciprocity is not automatic) matches this shape closely | `SUPPORTED` |
| **Trust (social contracts)** | `SocialAppraisalSystem.appraise_contract()` (`docs/mechanics/07_social_political_dynamics.md`) | Derived per-interaction | Causal — gates contract acceptance | Team-Up/Trade/Paid-Information contract kinds (`TCK-20260824-AFFECTION-CONTRACT-GATE`) | Not verified this pass whether trust itself persists or is recomputed each appraisal | Doc-level; not independently re-traced in code this pass | Already covered — Batch 09 territory | `UNKNOWN` (not independently re-verified this pass) |
| **Social goal base utility** (`GoalKind.SOCIAL`) | `SocialScorer` (`src/ai/goals/scorers.py:74-77`) | N/A — hardcoded | **Non-causal / stub** | `ScoreModifierSystem` (multiplies a constant) | N/A | Direct code read: `return GoalScore(kind=GoalKind.SOCIAL, utility=10.0)` with comment "Placeholder for social interaction utility" | Genuine World Rule gap at the realization level — the Rule (relationships matter, AGENCY-02) is already covered; this specific *scorer* just doesn't consume any of that real state as its base signal | `MISSING` for the base-utility signal specifically (personality/life-stage/history modifiers still apply multiplicatively on top of the constant, so it is not fully inert — see §G) |
| **Memory — causal/spatial/temporal** | `src/domains/memory/` (`memory_contract.md`) | Stored, typed, bounded (causal), capped familiarity (spatial) | Causal, but causal-memory→route-scoring path is feature-flagged | `AdventureRouteScorer` (2 of 10 `future_advice` values consumed) | Mutable, append/evict (causal), increment/cap (spatial) | `ENABLE_MEMORY_UPDATE` confirmed **still OFF** in current `feature_flags.py:24` (re-verified live, not from the doc alone) | Already covered — MEM-02 (`knowledge-information.md`) states experiential memory and declarative belief are distinct, tracked separately — matches exactly | `INERT-OFF` — wired, typed, tested, but not active in production, confirmed current as of this investigation |
| **Belief / knowledge model** | `src/cognition/knowledge_model.py` (`KnowledgeModelService`) | Stored, distinct from Memory domain | Causal (not independently re-traced this pass beyond the contract doc's own claim) | Adventure/motivation/cognition layers per `memory_contract.md:11` | Not verified this pass | Not independently re-traced this pass | Already covered — Batch 06's KNOW-01/02, MEM-02 | `UNKNOWN` (relying on doc + prior Batch 06 evidence, not independently re-verified this pass) |
| **Life stage** (CHILD/ADULT/ELDER) | `src/core/state.py:519-523` (`LifeStage` enum), `src/ai/life_stage.py` (`LifeStageService`) | Stored | Causal — multiplies goal utility per kind | `ScoreModifierSystem.apply_modifiers()` line 25,39 | Presumably progresses with age/tick — **not verified this pass** | Directly confirmed as a real, applied multiplier in the central scoring pipeline | Not previously classified against the Catalog this pass — likely Batch 05 (Life/Body, LIFE-*) territory, not independently checked | `SUPPORTED` for the multiplier mechanism; transition mechanism itself `UNKNOWN` |
| **Settlement personality** | `src/domains/culture/settlement_personality.py` (`SettlementPersonalityService`) | Derived, region/settlement-scoped | Non-causal (descriptive only in this pass's evidence — `describe()` call sites are presenter/API routes, `campaigns.py:210,216`) | API presenters (`api/routes/campaigns.py:178`) | Not verified | Direct code read of call sites | **Naming collision worth flagging**: a second, unrelated concept sharing the word "personality" with the entity-level `PersonalityComponent` — Batch 11B's own Culture family (`CultureState`) is the more likely semantic home, not this pass's entity-level personality concept | `SUPPORTED` for its own narrow descriptive purpose; not a duplicate of entity personality, just a naming risk |

---

## C. Decision pipeline (actual repo-grounded causal flow)

Confirmed, code-traced (not the docstring's aspirational "5-Phase Cognitive Cycle" from
`rpg_refinement_pillars.md`, which was cross-checked but not independently re-verified phase-by-phase
this pass — treat that doc's own phase names as a plausible high-level map, not independently
re-confirmed here):

```
1. GoalScorer.score() per GoalKind         (src/ai/goals/scorers.py, base.py)
   → base utility from need/opportunity state (e.g. HarvestScorer reads nearest resource node
     and current sleep_debt/hunger; SocialScorer returns a hardcoded 10.0 — see §G)

2. ScoreModifierSystem.apply_modifiers()   (src/ai/score_modifiers.py:12-74)
   For every scored GoalKind, in this exact order:
   a. personality_bias   = PersonalityService.get_goal_modifiers(entity.identity.personality)
      → utility *= (1.0 + bias)
   b. life_stage_mult    = LifeStageService.get_goal_multipliers(entity.identity.life_stage)
      → utility *= mult
   c. boredom_tax         = entity.strategic.boredom.get(kind, 0.0)
      → utility -= boredom_tax * 0.5   (if > 0)
   d. strategic_learning  = StrategicLearningService.get_goal_biases(entity.strategic.turning_points)
      → utility += tp_bias
   e. blocker_suppression: unresolved blocker on this goal kind → utility *= (1 - severity);
      access-blocked target → utility *= 0.1
   f. floor: fatigue/hunger never drop below 20% of raw utility; all others floor at 0.0

3. Selection: highest-utility GoalScore wins (tie-break rule not re-verified this pass — referenced
   in `strategic.py`'s own inline comments as `sort(key=lambda x: (-x.utility, x.kind))`)

4. Action execution → WorkerPool proposal → authoritative apply (not re-traced this pass — outside
   Pass 1's decision-formation scope)

5. Consequence feedback:
   - ProjectStatus.COMPLETED (score > 15.0) → TurningPointState(kind="great_victory") + boredom -2.0
   - ProjectStatus.COMPLETED (score ≤ 15.0) → TurningPointState(kind="victory" — a bare string,
     NOT a member of TurningPointKind; see §G) + boredom -2.0
   - ProjectStatus.ABANDONED → TurningPointState(kind="loss") + boredom +5.0
   (src/systems/strategic_systems/intelligence.py:1145-1174)
   → feeds back into step 2d on the entity's future ticks.
```

This is a real closed loop for the combat/exploration/social(-bias, not base-utility) axes: choice →
consequence → turning point → future goal preference. The loop is **internal to the entity** — it
does not touch reputation, relationships with others, or opportunity availability in this pass's
evidence (Pass 2 territory, flagged in §I).

---

## E. Personality / Characteristic / Archetype findings

### Personality

Answering the brief's own §3 questions directly, using the refined central question (breadth/
compositionality, not existence):

- **Stored persistently, seeded at spawn**: yes — `build_personality_for_entity(entity_id,
  faction_id, seed)`, called from both `entity_spawner.py:126` and `archetype_factory.py:93`, and
  directly in `compiler.py:612-618`. A defensive comment in `archetype_factory.py:87-91` explicitly
  names the *class* of bug this guards against (all-zero defaults) — a durable fix, not a one-off
  patch, still holding as of this investigation.
- **Can lived history modify it post-spawn?** **UNKNOWN** — no write path to `PersonalityComponent`
  found after entity creation in this pass. This is a real, specific open question distinct from
  "does personality matter" — personality here is an *innate seed*, not itself a product of lived
  experience. (Contrast with turning points, §C, which *are* history-derived and *do* feed back into
  behavior — the STRONG model's history-conditioning is real, but it currently runs through
  turning-points, not through personality mutation.)
- **Deterministic or biasing?** Biasing — every modifier in `PersonalityService.get_goal_modifiers()`
  is additive-to-1.0 multiplicative, never a hard gate. Matches AGENCY-02's "influence, not
  determination" directly.
- **Directly consumed, or stored but inert?** Directly and *broadly* consumed — confirmed across
  four independent causal domains: combat caution (`EngagementRiskEvaluator`, cited in
  `conflict-combat.md`'s own Repository Findings), goal-kind utility (`get_goal_modifiers`, 10
  goal-kind mappings across bravery/greed/industry/sociability), party role assignment
  (`PartyCompositionScorer` — "OCEAN compatibility," `party_composition.py:45-198`, 40% weight), and
  leadership succession (`PartyLifecycleService`, "periodic leadership re-election based on OCEAN
  sociability trait," `party_lifecycle.py:45`).
- **Dimensions independent?** Yes structurally (`PersonalityComponent` is a flat 4-field dataclass,
  no cross-field coupling found), but **empirically unequal in effect**: bravery STRONG
  (Δ=-0.719), industry MODERATE (Δ=-0.226), greed/sociability WEAK (Δ<0.05) —
  `TCK-20260628-E11B-PERSONALITY-AUDIT`, 1000-tick audit, 33 entities/81 snapshots, `urban_political`
  scenario, seed=42. The audit's own diagnosis: the wiring is correct (weights applied as designed),
  but greed/sociability's target routes (economic/social) are underrepresented in that scenario's
  opportunity mix (harvesting: 2 occurrences, combat_engage: 22, in 1000 ticks) — a **starved**
  pattern (same shape as the Compass §10 `STARVED` classification this session cross-checked earlier
  this week), not a broken-mechanism finding. A partial mitigation shipped the same week
  (`TCK-20260628-E11C-WEIGHT-TUNING`: greed/sociability weights raised 0.30→0.50 and 0.30(?)→0.40,
  narrowing the measured gap) — **this pass did not re-run the audit to confirm the mitigation's
  real-world effect three months later; flagged as `UNKNOWN`, not assumed fixed.**
- **"OCEAN" terminology is a misnomer worth flagging precisely**: the actual psychological Big-Five
  OCEAN model (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) is **not
  implemented anywhere** — `grep -r "openness\|conscientiousness" src/` returns zero hits. "OCEAN"
  in this codebase is a label applied to the unrelated 4-dimension `PersonalityComponent`
  (bravery/greed/industry/sociability). This is a terminology-accuracy finding, not a semantic gap —
  the mechanism itself is real; the name over-claims a specific, well-known model it doesn't
  implement.

### Characteristics / Traits

No generic `trait`/`characteristic` container was found separate from `PersonalityComponent` and
`AttributeComponent` (STR/AGI/VIT/END/INT/SPI/WIS/PER/CHA, `src/core/state.py:548-558`) in this
pass's evidence. The brief's §4 concern about collapsing unlike concepts (brave/scarred/noble-born/
fire-resistant/merchant/famous) into one container does **not** appear to be realized here — this
repo instead keeps at least three separate typed containers (personality, attributes, and whatever
owns class/role identity), which is closer to the Catalog's own admission-discipline instinct than
the brief's worst-case scenario. **Not exhaustively verified** — a dedicated trait/tag system could
exist elsewhere and wasn't found by this pass's search terms; flagged `UNKNOWN` rather than asserted
absent.

### Archetypes

Two genuinely distinct mechanisms answer to "archetype" language, and conflating them would be a
real error:

1. **Entity archetype (content-authoring template)** — `ArchetypeEntityFactory`
   (`stored_artifacts/TCK-20260609-ARCHETYPE-ENTITY-FACTORY/`), `ResolvedEntityArchetype`
   (`TCK-20260604-PHASE25-ARCHETYPE-POPULATION-RESOLVER`). This is a **content-authoring/world-
   assembly concept** — a compile-time template resolved into `EntityState` at spawn, not a runtime
   identity the entity itself holds or reasons about. Matches the brief's §2-D "narrative/analytical
   interpretation... authoring hint" category closely, though it does causally determine the
   entity's *initial* stats/role, so it's not purely narrative either — it's a real
   **content-generation-time causal input**, distinct from a runtime-mutable identity.

2. **Class tier (e.g. Mage → Archmage)** — `src/core/classes.py`'s `ClassTierOption`, gated by level
   + attribute thresholds (`docs/core/attributes_and_classes.md:192,211`). This is closer to the
   brief's "coherent" model (`history + behavior + capability + role → derived archetype`) — it's
   derived from progression, not assigned arbitrarily. **Not independently verified at runtime this
   pass** (no `src/` trace of the actual stat/ability grant on tier-up) — flagged `UNKNOWN`.

3. **"Pillar Traits" (Colossus/Archmage-as-multiplier/Juggernaut) — likely stale doc claim, not a
   real third mechanism.** `docs/engine/contracts/rpg_refinement_pillars.md` (status: active,
   authority: P1) names these as live design ("massive global multipliers... unlock at levels 50,
   75, 100"), but the only concrete spec (exact thresholds, stat bonuses) is in
   `docs/archive/systems/combat_and_progression.md:285-293` — an **archive** doc — and zero matching
   implementation exists in `src/` (`grep -r "Colossus\|Juggernaut\|Pillar Trait" src/` → no hits).
   This reads as an active-authority doc citing archived, unimplemented design language as if
   current. Out of scope to fix in this investigation (not a World Rule, and not this pass's file to
   edit); flagged for whoever owns `docs/engine/contracts/`.

None of the three "archetype" concepts found here match the brief's §5 "dangerous" model
(`archetype = HERO → entity automatically chooses heroic decisions`) — no hard behavioral gate keyed
directly off archetype/class was found; all discovered effects run through stat/threshold changes
consumed by the same utility-scoring pipeline as everything else, consistent with AGENCY-02's
"influence, not determination."

---

## F. Other important factors discovered

- **Boredom / habituation** (§B, §C) — a real, causal, per-goal-kind diminishing-returns mechanism
  not named anywhere in the original brief's search-term list. This is directly relevant to Section
  17's "Counterforces" question (can trajectories stall/reverse) — repeated pursuit of the same goal
  kind measurably reduces its own future attractiveness, a real self-limiting feedback loop.
- **Blocker suppression** (§C step e) — a structural-obstacle mechanism that multiplicatively
  suppresses a blocked goal kind's utility (down to ×0.1 for access blocks). This is the closest
  thing found in this pass to a "genuine constraint that can stall a trajectory" — worth Pass 2's
  attention for whether blockers can be entity-history-dependent (e.g., does reputation ever create
  a blocker?) or are purely mechanical/spatial.
- **Nemesis system** (§B) — real, typed, threshold-gated (`grudge_history` ≥ 3.0 → `nemesis_ids`
  promotion). This is the clearest example found in this pass of history-conditioned,
  relationship-specific (not generic) behavioral divergence: two entities with identical objective
  circumstances but different grudge histories toward a specific third party would plausibly make
  different combat-targeting choices — directly answering the brief's §10 stress-test shape, though
  only for the combat-targeting-priority case, not verified more broadly.
- **`entity.strategic.boredom` and `entity.strategic.turning_points` are BOTH inputs to the exact
  same `ScoreModifierSystem.apply_modifiers()` call** — meaning history-conditioning is not a single
  isolated mechanism but at least two independently-produced, compositionally-applied signals
  converging on the same decision point. This strengthens the "compositional, not narrow-wire"
  reading of the central stress test considerably beyond what the personality-only evidence alone
  would suggest.

---

## G. Broken or unproven causal edges

| Edge | Status | Evidence |
|---|---|---|
| `SocialScorer` base utility → real relationship/trust state | **Broken (stub)** | `scorers.py:74-77` — hardcoded `utility=10.0`, comment says "Placeholder." Personality/life-stage/history modifiers still apply multiplicatively on top, so social goal *ranking relative to other goals* is not fully inert, but the *base signal* ignores who the interaction is with entirely. |
| Causal memory (`avoid_enemy`/`boost_party_trust` advice) → route scoring | **Wired but INERT-OFF** | `ENABLE_MEMORY_UPDATE = FeatureMode.OFF`, re-verified live in `feature_flags.py:24` as of this investigation (not just cited from the 2026-06-13 doc) — genuinely still off today, unlike the `combat_engagement` flag this session found flipped-without-doc-update earlier this week. |
| `TurningPointState.kind` typed as `TurningPointKind` enum, but a real producer assigns a bare `"victory"` string not in that enum | **Type-safety gap, not a behavioral break** | `intelligence.py:1157` (`kind="great_victory" if project.score > 15.0 else "victory"`) vs. `strategic.py:363` (`kind: TurningPointKind`) vs. `strategic.py:200-206` (enum has no `"victory"` member). `StrategicLearningService.get_goal_biases()` happens to check for both strings explicitly (line 23: `tp.kind == 'great_victory' or tp.kind == 'victory'`), so the bias still applies — behaviorally masked, but the type contract is violated. |
| Personality → post-spawn mutation from lived history | **Unproven, not confirmed broken** | No write path to `PersonalityComponent` found after `build_personality_for_entity()` at spawn. Genuinely `UNKNOWN`, not asserted MISSING — a targeted search for a mutation path wasn't exhaustive. |
| Turning points / boredom / grudges → propagate to *other entities'* knowledge of this entity | **Not found in this pass's evidence** | The entire chain traced in §C is internal to the one entity. No consumer found in this pass reading another entity's `turning_points`, `boredom`, or `grudge_history` to affect *its own* decisions about the first entity. This is the same shape as the Final Integration Batch's own already-documented recurring late-stage gap (lived-history → recognition → reaction), now observed again at the personality/decision layer specifically — not a new finding in kind, a new confirming instance. |
| "Pillar Traits" archetype mechanic | **Doc asserts live; code shows none** | See §E.3. |

---

## H. World Rule assessment

Using the semantic-assessment axis strictly (does a Rule exist), separate from realization status
(already given per-row in §B):

- **Already covered adequately**: personality-as-bias (AGENCY-02), relationship structural-vs-
  subjective distinction (SOC-01/02), experiential-memory-vs-belief distinction (MEM-02), memory
  informing-not-deciding (`memory_contract.md`'s own explicit "memory informs decisions but does not
  make them" boundary, matching Batch 06's Agency/Decision framing).
- **Covered but realization incomplete**: causal-memory-informed route scoring (`INERT-OFF`, real
  Rule content, real code, flag off); greed/sociability personality effect (`PARTIAL`, starved
  opportunity, not a Rule gap).
- **Semantically ambiguous**: whether "boredom" (habituation/diminishing returns) and "turning
  points" (discrete significant-event history) are already fully subsumed by an existing Rule
  family or represent a genuinely under-named sub-concept within Capability/Progression or
  History/Provenance. Not resolved this pass — flagged for whoever integrates this report, per
  Option C.
- **Genuine World Rule gap candidate**: the entity-level instance of the lived-history →
  recognition → reaction gap (§G, last row) — but this is very likely **the same gap already named
  by the Final Integration Batch**, not a new one, just re-confirmed at a different subject layer
  (personality/decision rather than object/place/organization). Recommend treating it as
  *corroborating evidence* for the existing finding, not a new Rule candidate, pending Pass 2's own
  check of whether it composes any differently at the life-trajectory layer.
- **Derived/narrative only**: "Pillar Traits" as currently doc-described (no live mechanism to
  attach a Rule to); `SettlementPersonalityService`'s descriptive output (already narrowly-scoped,
  presenter-facing).

---

## I. Life-Chronicle stress test (partial — Pass 1 evidence only)

Two trajectories, one combat-adjacent and one not, tested against Pass 1's evidence only. **Both
require Pass 2 to complete** — Pass 1 can only explain the *decision* side, not the *opportunity/
capability-growth/reputation* side of either chronicle.

**Trajectory 1 — "A soldier who survives a near-death experience becomes cautious."**
`Age 25: nearly dies in an ambush. Age 26 onward: avoids similar engagements, takes safer contracts.`
- **Can Pass 1's evidence explain this?** Yes, directly: `near_death` → `TurningPointState(kind=
  NEAR_DEATH)` → `StrategicLearningService.get_goal_biases()` → `biases['combat'] -= weight * 2.0`
  → `ScoreModifierSystem` applies this to all future combat-goal scoring. This is a **fully
  supported** causal chain in this pass's own evidence — the strongest positive finding in the
  report.
- **What Pass 1 cannot explain**: why or whether *other entities* (a guild, a captain) would notice
  and offer this entity safer contracts as a result — that requires an opportunity-generation
  mechanism responsive to the entity's own changed disposition, which is Pass 2 territory and
  connects directly to the Final Integration Batch's own late-stage gap.

**Trajectory 2 (non-combat) — "A merchant's apprentice who is repeatedly betrayed becomes
withdrawn and distrustful of trade partnerships."**
`Age 20: forms a trade partnership. Age 22: partner defaults on the deal (betrayal). Age 23 onward:
avoids new trade partnerships, works alone.`
- **Can Pass 1's evidence explain this?** Partially: `betrayal` → `TurningPointState(kind=
  BETRAYAL)` → `biases['social'] -= weight` → suppresses `GoalKind.SOCIAL`'s scored utility. But
  because `SocialScorer`'s own *base* utility is a hardcoded constant (§G), the story this actually
  supports is weaker than it sounds: the entity becomes less likely to *pursue* social goals in
  general, not specifically less likely to trust *trade partnerships* — the mechanism doesn't
  distinguish "avoid this specific partner" from "avoid social activity broadly," because
  `SocialScorer` never reads who the interaction is with. The Nemesis/grudge system (§F) would
  support a *partner-specific* version of this story if the betrayal were modeled as a grudge-
  worthy event against a specific entity ID rather than (or in addition to) a generic
  `TurningPointState` — **not verified this pass whether contract defaults actually produce a
  grudge as well as a turning point**; `contracts.py:245`'s `betrayal_tp` was found but its sibling
  grudge-write (if any) wasn't traced.

Both trajectories confirm the report's central claim: the *decision-conditioning* half of the STRONG
model is real and evidenced, but the *social-propagation/opportunity-generation* half is Pass 2's to
confirm or refute.

---

## J. Recommendations (individually bucketed, Option C — no global integration decision made)

1. **`SocialScorer`'s hardcoded base utility (§G, §B)** — **surgical Rule refinement candidate, low
   confidence without Pass 2.** This looks like a realization gap under an already-covered Rule
   (AGENCY-02/SOC-01), not a new semantic gap — recommend routing to the Semantic Control Plane's M3
   triage as a realization finding once Combat's own M4 mapping work has landed, rather than a new
   Catalog batch.

2. **"Pillar Traits" doc/reality mismatch (§E.3, §H)** — **no Catalog change; a doc-accuracy note
   only**, and outside `docs/world_rules/` entirely (it's an engine contract doc), so it isn't even
   Catalog-track work. Recommend a small, separate note to whoever owns
   `docs/engine/contracts/rpg_refinement_pillars.md`.

3. **Turning-point / boredom self-reinforcing loop (§C, §F) — no World Rule change recommended.**
   This is strong existing realization of already-covered semantics (AGENCY-02, and likely
   History/Provenance's HP family at a level this pass didn't fully trace). Recommend **further
   investigation only**: whether this loop's existing Rule coverage is adequate or whether
   Progression/Capability (Batch 07's PROG-*) should explicitly name habituation/turning-point-
   conditioning as an Inherited application — a documentation-completeness question, not a semantic
   gap, and better answered once Pass 2 shows whether the same loop recurs at the life-trajectory
   layer.

4. **Personality→post-spawn-mutation absence (§E) — further investigation only, not yet a
   recommendation of any kind.** Genuinely `UNKNOWN` whether this is an intentional design boundary
   (personality as innate, fixed-at-birth temperament, with *turning points* carrying all the
   history-conditioning weight instead) or a real gap. This is exactly the kind of question the
   brief's own §23 warns against resolving by assumption — needs either a design-intent check
   against `core_rpg_design_direction.md` or Pass 2's own life-trajectory evidence before any Rule
   action is recommended.

5. **The entity-level lived-history→recognition→reaction gap (§G, §I) — no new Rule; treat as
   corroborating evidence for the Final Integration Batch's existing finding**, not a separate
   Catalog action. Recommend this be folded into whatever process eventually re-examines that
   existing finding (already flagged in `roadmap.md`), not spun up as independent work.

6. **"OCEAN" terminology mismatch (§E) — no Catalog or code action recommended.** Purely a naming-
   accuracy observation for whoever next touches personality-related documentation; does not affect
   any Rule's semantic content.

No finding in this pass rose to "new World Rule required" — every genuine gap found (`SocialScorer`,
memory feature-flag, personality post-spawn mutation) is a realization or documentation question
under Rules that already exist, consistent with how compositional the actual decision pipeline turns
out to be once `ScoreModifierSystem` (not just the narrower `AdventureRouteScorer` the 2026-06-19
D05 audit examined) is accounted for.
