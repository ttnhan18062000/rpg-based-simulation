---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `m2-findings.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# M2 findings — inheritance observer encounter check (TCK-20260927-INHERITANCE-OBSERVER-ENCOUNTER-CHECK)

Task: M2 only. Four separate checks for the single staged tick-0 inheritance. No test written, no files changed: no in-world carrier exists, and a test asserting that absence would pin a gap as intended behavior.

## 1. World state: PASS (scenario runtime)
`tests/simulation_quality/test_heir_inventory_transfer_corpus.py` re-run 2026-09-27 with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest ... -q` gives `1 passed in 0.72s`. The heir's inventory gains the deceased's items through `LifecycleSystem.resolve_lifecycle` (`src/systems/lifecycle_systems/lifecycle.py:240-262`). This is state only, not observer evidence. (Note: this worktree has no `.venv`; use the main checkout's venv.)

## 2. Encounter: BLOCKED. No in-world carrier exists (confirmed by code inspection)
Carriers checked:
- **Perception model**: `PerceivedEntity` (`src/core/cognition.py:28-34`) holds only id/kind/position/salience/confidence, with no inventory or equipment. `WorldSignal` (`src/domains/perception/salience.py:14-29`) likewise has no item fields. `PerceptionUpdatePhase` (`src/domains/perception/phase.py:19`) has **no production caller** outside its own module (repo grep). The only `WorldSignal(` constructor is `src/domains/fame/legend.py:87`.
- **KnowledgeModelService** (`src/cognition/knowledge_model.py:30-80`): it assimilates paid `InformationResponse`s only. The provider fact types are `resource_source`, `recipe_definition`, `danger_rating` and `lead` (`src/world/providers/information.py:86,124,158`). None covers another entity's possessions.
- **Combat OpponentModel** (`src/domains/combat_engagement/schema.py:83-101`): power, skills and outcomes only. No items.
- **Inventory reads in cognition/AI** (`src/ai/goals/scorers.py:9,83`, `src/domains/information/resolver.py:69`): all read the entity's *own* inventory.
- **Grief trigger** (`src/observability/event_extractor.py:1722-1762`, drained at `src/engine/kernel.py:659,716`): this is the one real in-world effect of the death. Allies with `trust_history >= ALLY_TRUST_THRESHOLD` get a grief concern. It does not qualify as a carrier for this check, for three reasons:
  - It carries the **death**, not the inventory change.
  - It is trust-scoped and location-independent, so it does not depend on viewpoint.
  - It originates in the observability pass.
- **Developer-only surfaces**: `src/observability/live/entity_inspector.py`, `event_extractor` events, and API presenters in `src/api/`. These are excluded as in-world carriers.

Because nothing carries the state change to an observer, non-leakage of `cognition.motivation.named_intention` / `strategic.blockers` is vacuously true for in-world channels. It is untestable until a carrier exists.

## 3. Provenance: ABSENT (confirmed)
The transfer is a plain `ResourceTransferIntent(source_kind="CHEST", transfer_kind="AUTO")` (`lifecycle.py:252-257`). There is no inheritance-origin marker, and no event, memory or history record that an observer could perceive. The only death-adjacent world event is the economic vacancy signal (`src/economy/vacancy.py:25-65`), which concerns the vacated role, not the inheritance. Even if a carrier for item visibility existed, the clue would be only the ambiguous "this person now carries an item", with nothing that identifies inheritance.

## 4. Inference: BLOCKED
No legitimate clue is encounterable by a situated observer, so there is nothing for a blinded human exercise to evaluate. No evidence packet was produced, because building one would require inventing an omniscient projection.

## Statuses
- **M2 technical status: COMPLETE.** All four checks answered. Checks 1-3 are verified in the current repository. Check 2's result is `BLOCKED_WITH_REASON: no in-world carrier`.
- **Player-facing status: BLOCKED**, not PENDING, for this clue. `PLAYER-EXPERIENCED` is not claimed.

## Proposed follow-up: minimum missing evidence-production capability
- **Candidate A: a viewpoint-scoped visible-equipment signal.** This would let a co-located observer's perception include coarse visible equipment of perceived entities (equipped slots only, never inventory contents or cognition). Owner: perception domain (`src/domains/perception/`).
  - Prerequisite: `PerceptionUpdatePhase` must be wired into the production pipeline at all. That wiring gap is itself worth a ticket.
  - This yields only the ambiguous clue "now carries X".
- **Candidate B: a local inheritance event witnessed by co-located or bonded entities.** This would make an inheritance-origin clue possible. Owner: lifecycle/lineage domain.
  - It should be witness-scoped by proximity/bond, not a global feed.
  - It follows the direct-participation vs. uninvolved-witness vs. hearsay distinction in roadmap §3.4.

Either is a design choice for a later ticket. Neither is a universal event/reputation feed.

Out of scope noted: the grief trigger's location-independence (an omniscient, trust-scoped read) may itself conflict with the epistemic principle. That is worth a look under roadmap §3.4, not M2.
