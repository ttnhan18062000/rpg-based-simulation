# Phase 9: Strategic & Social Cognition

Phase 9 recovers the next major semantic surface of the original `src`: deep strategic intelligence, social narrative mechanics, and bounded progression systems. It builds directly on the verified local gameplay baseline established by Phase 8 (Combat, Tactics, World Interaction).

## Baseline Assumptions (from Phase 8 Exit Package)

1. **Local Combat is Authoritative**: Strategic AI does not need to simulate combat outcomes.
2. **Tactical AI is Self-Contained**: Phase 9 focuses on high-level redirection and goal-setting.
3. **Environment Constraints are Absolute**: Movement and LoS are enforced by `LegalityServiceV2`.

## Phase 9 Ledger Rows (UNSUPPORTED → Target: SUPPORTED)

| Ledger ID | Feature | Current Status |
| :--- | :--- | :--- |
| LEG-RPG-116 | Strategic pivot (Danger) | UNSUPPORTED |
| LEG-RPG-117 | Scar detection | UNSUPPORTED |
| LEG-RPG-119 | Betrayal (Avenge) | UNSUPPORTED |
| LEG-RPG-123 | Refutation drops trust | UNSUPPORTED |
| LEG-RPG-125 | Contradiction degrades cert | UNSUPPORTED |
| LEG-RPG-141 | Dynamic Quests | UNSUPPORTED |
| LEG-RPG-144 | Innate Talents (Genetics) | UNSUPPORTED |
| LEG-RPG-145 | Skill scaling (Types) | UNSUPPORTED |
| LEG-RPG-150 | Belief cycle (Rumors) | UNSUPPORTED |
| LEG-RPG-151 | Narrative memory logging | UNSUPPORTED |

## Legacy Checklist Coverage (Unchecked → Target)

Phase 9 targets the following unchecked subsystem groups:

- **Part 1 §Strategic mind** (8 unchecked atomic items): Interruption resistance, lead bandwidth, concern intake, detour limits, event interpretation, knowledge uncertainty, cognition graph export.
- **Part 1 §Social** (8 unchecked atomic items): Betrayal history, social learning, contracts, reputation, turning points, group cooperation, recruitment.
- **Part 2 §Strategic tests** (~143 unchecked tests): Bounded blockers, detours, project continuity, strategic slices, cognition capacity, event interpretation, lead learning, social cognition, source trust, uncertainty resolution, cognition graph, strategy models, strategic brain integration, strategic capacity, strategic continuity, strategic explainability, strategic persistence, strategic replay, strategic transport, strategic world integration, strategic biasing, strategic uncertainty, blocker resolution, strategic services, strategy system.
- **Part 2 §Social tests** (~30 unchecked tests): Betrayal consequence, learning social, lived models, social meaning, social contracts, social recruitment, social reasoning, familiarity scaling.

## Current V2 State Assessment

| Module | Lines | Maturity |
| :--- | :--- | :--- |
| `src_v2/core/strategic.py` | 27 | **Thin** — Only `BlockerState`, `LeadState`, `StrategicComponent` |
| `src_v2/systems/strategic.py` | 135 | **Baseline** — Crafting blockers, material resolution, process_outcome stub |
| `src_v2/systems/social.py` | 74 | **Baseline** — Trust recalibration, recruitment eval, betrayal stub |
| `src_v2/core/state.py` (SocialComponent) | ~5 | **Thin** — trust_history, betrayal_count, public_reputation only |

> [!IMPORTANT]
> The strategic and social layers are currently **stub-level**. Phase 9 requires significant model expansion and new system implementations, not just hardening of existing code.

## User Review Required

> [!WARNING]
> **Scope Decision**: The legacy checklist contains ~180 unchecked strategic/social test items. Phase 9 cannot recover all of them. This plan proposes recovering the **10 ledger rows** and the **~16 atomic checklist items** from Part 1 §Strategic + §Social, plus the most critical test-derived items. Items like recruitment haggling, war state transitions, and territory conquest are deferred to Phase 10.

> [!IMPORTANT]
> **Progression Scope**: LEG-RPG-144 (Innate Talents/Genetics) and LEG-RPG-145 (Skill Scaling) are allocated to Phase 9 in the ledger. These are progression/class features. Should they stay in Phase 9, or be deferred to Phase 10 alongside other progression items (combat rewards, veterancy, breakthroughs)?

---

## Proposed Changes

### Milestone 1: Phase 8 Exit Closure and Phase 9 Readiness

Establishes the entry gate. No code changes — governance only.

#### Tasks:
1. **Freeze the Phase 9 row set** — Collect all Phase 9-owned rows from the ledger, exclude Phase 10 compatibility rows.
2. **Define explicit closure conditions** — Every Phase 9 row gets a testable finish line.
3. **Publish downstream blockers** — Identify what Phase 10 cannot do without Phase 9.
4. **Restate the current support boundary** — Honest assessment of strategic/social support entering Phase 9.
5. **Publish the Phase 9 entry package** — Formal readiness gate.

#### Affected files:
- `docs/engine/phase9_backlog.md` [NEW]
- `docs/engine/phase9_closure_conditions.md` [NEW]
- `docs/engine/phase9_entry_package.md` [NEW]
- `docs/engine/phase9_entry_support_boundary.md` [NEW]

---

### Milestone 2: Strategic Cognition Deepening

Recovers the strategic mind subsystem beyond baseline blockers/leads.

#### Tasks:
1. **Expand `StrategicComponent` model** — Add directives, projects, objectives, concerns, obligations, contracts, offers, candidate zones, hypotheses as typed fields.
2. **Implement interruption resistance** — Project switching uses margin logic, not full rescore (Part 1 §Strategic checklist item).
3. **Implement lead/concern bandwidth** — Profile-specific retention limits (Part 1 §Strategic checklist items).
4. **Implement detour suggestion** — Blockers + leads → detour within breadth/depth limits.
5. **Implement lead suppression** — Rejected/tested leads are suppressed to avoid blind retries.
6. **Implement event interpretation** — Events can mutate directives, projects, concerns, and source trust (LEG-RPG-116 strategic pivot, LEG-RPG-117 scar detection).

#### Affected files:
- [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/core/strategic.py) — Model expansion
- [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/systems/strategic.py) — System logic
- [NEW] `src_v2/systems/event_interpreter.py` — Event-to-strategic mutation pipeline
- [NEW] `src_v2/systems/detour.py` — Detour suggestion from blockers/leads
- [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/core/state.py) — StrategicComponent wiring
- [NEW] `tests_v2/strategic/test_interruption_resistance.py`
- [NEW] `tests_v2/strategic/test_lead_bandwidth.py`
- [NEW] `tests_v2/strategic/test_detour_suggestion.py`
- [NEW] `tests_v2/strategic/test_event_interpretation.py`

---

### Milestone 3: Social Narrative Recovery

Recovers the social subsystem: betrayal, trust, reputation, contracts, and recruitment.

#### Tasks:
1. **Expand `SocialComponent` model** — Add familiarity bonds, private narrative history, contract obligations, group membership.
2. **Implement betrayal consequence pipeline** — Private betrayal overrides public reputation (LEG-RPG-119 Avenge).
3. **Implement social learning** — Familiarity/trust bonds update from interaction evidence.
4. **Implement social contracts** — Explicit strategic objects with persistent consequences for honoring/breaking.
5. **Implement recruitment depth** — Trust, debt, greed, capability fit, prior trauma evaluation.
6. **Implement source trust recalibration** — Refutation drops trust (LEG-RPG-123), contradiction degrades certainty (LEG-RPG-125).

#### Affected files:
- [MODIFY] [social.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/systems/social.py) — System expansion
- [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/core/state.py) — SocialComponent expansion
- [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/core/updates.py) — SocialUpdate expansion
- [NEW] `src_v2/systems/contracts.py` — Social contract lifecycle
- [NEW] `tests_v2/social/test_betrayal_consequence.py`
- [NEW] `tests_v2/social/test_social_contracts.py`
- [NEW] `tests_v2/social/test_recruitment_depth.py`
- [NEW] `tests_v2/social/test_source_trust.py`

---

### Milestone 4: Belief & Knowledge Systems

Recovers the knowledge uncertainty layer and narrative memory.

#### Tasks:
1. **Implement belief cycle** — Rumors, stale beliefs, threat estimation (LEG-RPG-150).
2. **Implement narrative memory** — Turning points, trauma biasing, victory confidence (LEG-RPG-151).
3. **Implement knowledge uncertainty** — Leads/candidate zones/hypotheses remain uncertain until resolved.
4. **Implement cognition graph export** — Exposes persisted strategic state without becoming the source of truth.

#### Affected files:
- [NEW] `src_v2/systems/belief.py` — Belief cycle engine
- [NEW] `src_v2/systems/narrative.py` — Narrative memory logging
- [MODIFY] [strategic.py](file:///home/vboxuser/Work/rpg-based-simulation/src_v2/systems/strategic.py) — Knowledge uncertainty integration
- [NEW] `src_v2/systems/cognition_export.py` — Graph export (read-only presenter)
- [NEW] `tests_v2/cognition/test_belief_cycle.py`
- [NEW] `tests_v2/cognition/test_narrative_memory.py`
- [NEW] `tests_v2/cognition/test_knowledge_uncertainty.py`
- [NEW] `tests_v2/cognition/test_cognition_graph_export.py`

---

### Milestone 5: Bounded Progression Recovery (Conditional)

> [!NOTE]
> This milestone is **conditional** on user approval. It covers LEG-RPG-141 (Dynamic Quests), LEG-RPG-144 (Genetics), and LEG-RPG-145 (Skill Scaling). If these are deferred to Phase 10, this milestone is skipped.

#### Tasks:
1. **Implement dynamic quest generation** — Quest generation depends on environment/scar awareness (LEG-RPG-141).
2. **Implement innate talents** — Genetics-driven talent multipliers (LEG-RPG-144).
3. **Implement skill scaling types** — Physical/Magical/Elemental scaling (LEG-RPG-145).

#### Affected files:
- [NEW] `src_v2/systems/quests.py`
- [NEW] `src_v2/systems/genetics.py`
- [MODIFY] `src_v2/core/state.py` — ProgressionComponent
- [NEW] `tests_v2/progression/test_quest_generation.py`
- [NEW] `tests_v2/progression/test_genetics.py`
- [NEW] `tests_v2/progression/test_skill_scaling.py`

---

### Milestone 6: Phase 9 Exit Package & Closure

Finalizes documentation, proofs, and handoff.

#### Tasks:
1. **Consolidate proof bundle** — All Phase 9 contract and parity tests.
2. **Publish exit package** — Formal Phase 9 completion and Phase 10 handoff.
3. **Update legacy replacement ledger** — All Phase 9 rows → SUPPORTED.
4. **Update legacy checklists** — Mark recovered items.
5. **Archive implementation plans** — Move to `docs/archive/`.

#### Affected files:
- [NEW] `docs/engine/phase9_exit_package.md`
- [NEW] `docs/engine/phase9_proof_bundle.md`
- [MODIFY] `docs/engine/legacy_replacement_ledger.md`
- [MODIFY] `legacy_checklist_part1.md`
- [MODIFY] `legacy_checklist_part2.md`

---

## Phase 9 Extension: Remaining Legacy Families

These milestones address the gaps identified in `resource_phase9_updated.md`, recovering the final set of RPG consequence families from the original `src`.

### Milestone 7: Routine, Biological Needs, and Life-Rhythm Closure

#### Tasks:
1. **Implement routine-state model** — Add `BiologicalComponent` to `src_v2/core/state.py` (sleep debt, hunger, rest pressure).
2. **Implement routine goal biasing** — Biological needs generate `ConcernState` and affect strategic scores in `src_v2/systems/strategic.py`.
3. **Add contract tests** — Direct proof for sleep/hunger/rest logic.

### Milestone 8: Hero Lifecycle, Permadeath, Succession, and Heirloom Closure

#### Tasks:
1. **Implement hero lifecycle state** — Aging, near-death survivor, and permadeath classification in `src_v2/core/lifecycle.py`.
2. **Implement succession semantics** — Heir designation and heirloom transfer in `src_v2/systems/lifecycle.py`.
3. **Add direct tests** — Lifecycle continuity and inheritance proof.

### Milestone 9: Recruitment Negotiation and Contract Richness Closure

#### Tasks:
1. **Expand recruitment to negotiation** — Counter-offers and haggling rounds in `src_v2/systems/social.py`.
2. **Add richer willingness factors** — Trust, debt, loyalty, and resentment integrated into evaluation.
3. **Add contract tests** — Social negotiation depth proof.

### Milestone 10: Region-Scale Strategic Consequence Closure

#### Tasks:
1. **Implement region-consequence records** — Suppression, danger, and conquered-region status in `RegionState`.
2. **Implement regional pivots** — Strategic intelligence reacts to regional danger and conquest.
3. **Add direct tests** — Region-scale strategic consequence proof.

### Milestone 11: Anchored-World Behavior

#### Tasks:
1. **Implement place attachment** — Home-aware retreat and attachment persistence.
2. **Implement leash/camp ecology** — Beyond-leash return and camp reinforcement.
3. **Implement proximity bonding** — Low-intensity social linkages from spatial proximity.
4. **Add direct tests** — Anchored-world behavior proof.

### Milestone 12: Role, Trait, and Identity-Weighted Decision Closure

#### Tasks:
1. **Implement explicit role derivation** — Dynamic role transition with hysteresis in `StrategicIntelligenceSystem`.
2. **Implement role-aware biasing** — Traits and identity materially nudge utility scores.
3. **Add direct tests** — Role/trait identity logic proof.

### Milestone 13: Phase 9 Remainder Proof and Exit Correction

#### Tasks:
1. **Update support boundary** — Restate truth after remainder closure.
2. **Add parity coverage** — Characterization proof for new families.
3. **Rebuild exit package** — Final Phase 9 truth bundle.

---

## Verification Plan

### Automated Tests
- `pytest tests_v2/ai/test_biological_needs.py`
- `pytest tests_v2/progression/test_lifecycle.py`
- `pytest tests_v2/social/test_recruitment_negotiation.py`
- `pytest tests_v2/strategy/test_region_consequences.py`
- `pytest tests_v2/world/test_leash_and_camp.py`
- `pytest tests_v2/ai/test_role_derivation.py`
- `pytest tests_v2/ -v` — Full regression check.

### Manual Verification
- Audit `EntityState` snapshots to ensure biological needs persist correctly across ticks.
- Verify `StrategicUpdate` objects contain the new `ConcernState` reasons.
- Inspect `SocialUpdate` objects for negotiation results.
