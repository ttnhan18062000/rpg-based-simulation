# Investigation — TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER

## The declared-intent check (per explicit instruction, before building anything)

Question: does anything declare that entities should learn per-enemy-kind danger *from combat
experience*? Checked, in order: Mechanics Bible, parity ledger, `docs/cognition/
capability_and_knowledge_contract.md`, Epic 4.2's own scope.

### Mechanics Bible

- `docs/mechanics/02_combat_laws.md` — zero mentions of `danger_rating`, `enemy_data`, or any
  per-enemy-kind learning/capability mechanism.
- `docs/mechanics/04_strategic_cognition.md` §6.12 ("Capability-Driven Confidence Bonus") is the
  Bible's own authoritative section for `CapabilityEstimateService` — but it documents only the
  `GATHER_RESOURCE`/`CRAFT_UPGRADE` (resource/recipe) use in `AdventureRouteScorer.score()`. It
  says nothing about the combat/enemy use (`TacticalDecisionSystem.target_score()`,
  `CapabilityContext.for_combat()`) at all — that real, live call site has no Mechanics Bible
  section of its own, let alone one declaring experience-based learning.
- Broader chapter grep for `danger`/`learn`/`experience`/`enemy kind` surfaced only
  `compute_danger_urgency()`/`interpret_regional_danger()` — **region**-danger mechanics (and
  `interpret_regional_danger()` itself has no production caller, a separate, already-known dead
  path) — nothing about a per-enemy-*kind* danger assessment.

### Parity ledger

`docs/parity_ledger/strategic_cognition.yaml` and `combat_movement.yaml`: zero matches for
`danger_rating`, `enemy_data`, or any per-enemy-kind learning entry.

### `docs/cognition/capability_and_knowledge_contract.md`

Documents `CapabilityEstimateService.estimate()`'s combat formula using `confidence = 0.9 if known
enemy type else 0.5` — but never defines what makes an enemy type "known," and the two real
call sites (`scoring.py` for GATHER_RESOURCE/CRAFT_UPGRADE, `tactical.py` for combat targeting) are
both explicitly documented as **ad hoc, scorer-local reads** that never touch
`entity.self_model.capabilities`, which "remains empty in production" either way. The contract
documents the current absence, not an intent to fill it from combat experience.

Also documents `KnowledgeModelService.assimilate()` (`src/cognition/knowledge_model.py`) — a real,
wired mechanism, genuinely distinct from `InformationAssimilationService`
(`src/domains/information/assimilation.py`, the one `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-
DECISION-TIME-READER-INVESTIGATION` found inert). Checked carefully rather than assumed they were
the same, given the similar naming and peer's own caution about stale citations this week:
`KnowledgeModelService.assimilate()` is called from `SelfModelUpdatePhase.run()`
(`src/cognition/self_model_phase.py:114`) when the phase detects an event with an `answer_kind`
attribute (an `InformationResponse`) in its own `events` parameter. `SelfModelUpdatePhase` is gated
`ENABLE_SELF_MODEL_COGNITION`, confirmed `OFF` by default with no corpus profile override (same
established finding from this batch's own ticket 1 investigation). So this second, genuinely
separate assimilation path is *also* currently unreachable in real runs — but more importantly for
this question: even if it were reachable, it assimilates what an information **provider tells** the
entity (`fact_type` values like `"threat_level"`), not what the entity **learns from fighting**.
Being told a location's `danger_rating` by a merchant and learning a creature *kind*'s danger by
surviving a fight against it are different declared mechanisms — the former has partial
infrastructure (unreachable, per above); the latter has none.

### Epic 4.2 · Active Information-Seeking / Belief Economy

`docs/plans/long_term_development_roadmap.md`'s own Epic 4.2 scope is entirely about
`InformationProviders` (MERCHANT/GUILD_MASTER/ELDER) answering queries about **resource
locations, faction tensions, entity whereabouts** — paid transactions, lead contradiction on
arrival, provider reliability decay. Nothing about enemy-kind danger, and nothing about learning
from combat outcomes specifically (its own acceptance signal is entirely about resource leads:
`information_need_identified → ... → lead_received → route_scored_with_lead → belief_contradiction`).

## Conclusion

**Nothing declares that entities should learn per-enemy-kind danger from experience.** The
`KnowledgeFact.fact_type` shape (`"danger_rating"`/`"threat_level"`) could structurally hold it, and
a provider *could* theoretically tell an entity about a creature kind's danger via the existing
(currently unreachable) assimilation path — but no design doc, Mechanics Bible chapter, parity
ledger entry, or roadmap epic declares that entities should acquire this from their own combat
experience, which is the shape of mechanism this ticket's own filing proposed investigating.

Per explicit instruction: stopping here rather than designing or building a learning mechanism.
Reported to peer for a user-level decision rather than proceeding.
