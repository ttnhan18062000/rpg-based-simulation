---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION
artifact_type: investigation
tags: [content]
---

# Investigation — TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION

**Not accidental duplication — a genuine two-track information pipeline, confirmed via the dispatch
site.** `src/domains/information/phase.py` is the single call site that decides which model a given
piece of new information becomes:
- Line 69: `InformationAssimilationService.assimilate(actor, norm, state.tick)` for **active query
  responses** (`NormalizedInformationResponse`, e.g. asking someone a direct question) — writes into
  `KnowledgeModelComponent.facts` (`KnowledgeFact`, capacity-bounded at 10, no decay observed).
- Line 162: `ObservationBeliefBridge.process_observation(actor, obs_event, state)` for **raw witnessed
  events** (`obs_event`) — writes into `StrategicComponent.beliefs` via `BeliefCycleSystem` (`BeliefEntry`,
  contradiction-tracked, decays toward staleness — `decay_stale_beliefs()`,
  `src/systems/strategic_systems/belief.py`).

This is a coherent split by pipeline stage (structured/queried vs. raw/observed), not two systems doing
the same job. `BeliefEntry`'s real consumers use it for exactly the uncertain/contested-claim behavior
its own lifecycle implies: `src/systems/strategic_systems/detour.py`'s `_score_detour()` matches a
belief by `subject` against a `lead.subject` and applies `matching_belief.contradictions * 25.0` as a
detour-scoring penalty — a real, live use of the contradiction-tracking `KnowledgeFact` has no
equivalent for.

**Real, narrower gap found**: no unified "what does this entity currently believe/know about subject X"
accessor exists anywhere — `src/core/cognition_accessors.py` only exposes `get_knowledge_model()`
(the `KnowledgeFact` side); nothing analogous surfaces `strategic.beliefs`. Confirmed no current live
consumer needs the fused view (checked every real consumer of both fields) — this is a latent gap, not
an active bug, consistent with the earlier finding that the two representations serve different pipeline
stages.

**Separate, smaller finding, not part of the reconciliation question**: `StrategicComponent.beliefs` is
declared `Dict[str, Any]`, not `Dict[str, BeliefEntry]` (`src/core/strategic.py:425`) — loosely typed,
and in practice holds two different shapes. `src/domains/cooperation/evaluators.py:47` reads
`entity.strategic.beliefs.get("combat_risk")`, a fixed-key ad-hoc dict lookup, not a `BeliefEntry` at
all. Confirmed via repo-wide grep: **`"combat_risk"` is never written anywhere in `src/`** — this read
is dead code, always returning `None`. Flagged as a separate, minor follow-up; not blocking this
ticket's own decision, since it doesn't bear on the `BeliefEntry`/`KnowledgeFact` question.
