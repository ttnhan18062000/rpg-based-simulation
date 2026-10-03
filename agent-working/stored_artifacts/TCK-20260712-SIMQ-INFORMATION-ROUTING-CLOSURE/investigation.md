---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE
artifact_type: investigation
tags: [cognition, information, self-model, observability, simulation-quality]
---

# Investigation — TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE

**Retrospective reconstruction note:** this file was written after implementation had already
landed (commit `0a99c725`). The real investigative work behind this ticket was performed by its
parent, `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`
(`stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/investigation.md` — the
authoritative source for everything below), which root-caused the routing dead-end and
explicitly recommended this follow-up ticket's scope. This file exists to satisfy the standard-tier
staging-artifact requirement retroactively and to give this ticket its own citable investigation
record, not to redo that investigation.

## Current Behavior

Root-caused directly against the real compiled `urban_political` state (actor 23, seed
42/123/456-invariant), reproduced independently by the parent investigation:

1. `InformationQueryRouter.route()` (`src/domains/information/router.py:102-103`, pre-fix) sorts
   candidates by `(-expected_certainty, cost_gold)` with no affordability awareness — a paid,
   higher-certainty candidate (`traveling_merchant_rumors`, cost 5, certainty 0.33) always outranks
   a free, lower-certainty one (`town_notice_board`, cost 0, certainty 0.20), even when the entity
   cannot afford the paid option.
2. `InformationBeliefPhase.apply()` (`src/domains/information/phase.py:92-105`, pre-fix) only ever
   tried `candidates[0]` — no fallback to `candidates[1]` when resolution fails.
3. `InformationIntentResolver.resolve()` (`src/domains/information/resolver.py:65-69`, pre-fix)
   silently returned `None` when `actor_gold < candidate.cost_gold` — no structured signal, even
   though `KnowledgeModelService.assimilate()` (`src/cognition/knowledge_model.py:67-70`) already
   has an `"insufficient_gold"` `answer_kind` branch with no producer anywhere in `src/`.
4. `src/observability/event_extractor.py:276-299` (pre-fix) had no extractor branch for
   `last_routed_query_subject`/`last_routed_query_tick` (Branch B's own property-update keys, set at
   `phase.py:101-104`) — a successful routing action was structurally invisible to SimQ scoring.
5. `ASK_INFORMATION` intent execution (`src/engine/intent/action_intent.py:127-141`, pre-fix) only
   deducted gold and appended an internal `IntentTrace` — never produced an
   `InformationResponse`/`pending_information_responses`-equivalent entry a later tick's Branch A
   could re-assimilate.

Entity 23's compiled `inventory.gold == 0` on all three anchor seeds, which is what turns (1)-(3)
into a hard, reproducible dead-end rather than a theoretical one.

## Mechanics / Engine Constraints

- `docs/simulation_quality/quality_scoring_contract.md` §5 (COGNITION/INFORMATION event types):
  confirmed `route_new_query` was not already reserved for a different event before adding it —
  checked directly during Implement (ticket's Implementation Notes, Step 3).
- `docs/plans/idea_information_belief_trigger_wiring.md`'s anti-drift note ("Branch A/Branch B, both
  dead" as of 2026-07-03) bounds this ticket's scope to the 4 root-cause points plus the intent-
  closure gap — not the full belief-assimilation response cycle.
- Branch A's existing capacity-bounded assimilation chain
  (`InformationResponseNormalizer` → `InformationAssimilationService`, already used at
  `phase.py:56-69`) is the correct reuse target for closing the `ASK_INFORMATION` execution loop —
  confirmed by architecture review (round 2) over a hand-rolled `KnowledgeFact` merge.

## Parity Ledger Overlap

- `docs/parity_ledger/infrastructure.yaml::INFRA-266` (added by the parent investigation ticket,
  pre-fix framing: "routing does not generalize") — left untouched as the historical pre-fix
  record, per the parent investigation's explicit recommendation and the `INFRA-259`/`INFRA-260`
  precedent of keeping split-verdict entries separate rather than overwriting them.
- `docs/parity_ledger/infrastructure.yaml::INFRA-267` (new, added by this ticket's implementation) —
  documents the fixed state: routing resolves end-to-end against real `urban_political` state for at
  least one candidate, across all 3 anchor seeds, via direct test-harness invocation.
- `docs/parity_ledger/strategic_cognition.yaml::STRAT-245`, `docs/parity_ledger/substrate.yaml::SUB-374`
  — confirmed not affected by this ticket's scope (per parent investigation's overlap analysis;
  this ticket does not touch canonical-hash or self-model-participation behavior).

## Prior Work

- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/` — parent investigation; full
  root-cause evidence chain, file:line citations, seed-invariance confirmation. This ticket
  implements exactly its "Recommended follow-up engine-fix ticket" section (3 numbered points, plus
  the intent-closure gap as a 4th).
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-BRANCH-B/` — the original 3-bug materialization fix
  chain (this ticket does not touch materialization, only routing).
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT/` — established the isolated-
  materialization pilot methodology this ticket's probe-fixture formalization extends.

## Risks and Open Questions

- **Router ranking heuristic left untouched** — per the parent investigation's explicit note that
  `(certainty before cost)` is plausibly intentional design, not a bug in isolation, and only becomes
  a hard failure combined with zero starting gold and no fallback. Implementation chose the
  phase-level fallback + structured-signal fix over re-sorting the router, per the ticket's own
  Assumptions/Open Questions section — confirmed by the still-passing, unmodified
  `test_phase5_information_query_router.py` (3 tests).
- **`ActionIntentAdapter.execute()` has no production tick-pipeline call site** — the intent-closure
  fix (point 5) is verified reachable via direct test-harness invocation and the probe-fixture
  calibration run, not via any live-gameplay activation path. No shipped profile turns
  `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` ON together, so this fix has no live-
  gameplay effect yet — see the ticket's Completion Summary for the full caveat.

## Anti-Drift Hazards

- Do not read this ticket as having activated Branch B in any live simulation — it closes dead code
  paths and proves them correct under direct invocation; it does not wire anything into the
  production tick pipeline.
- Do not widen the fix into "the full belief-assimilation response cycle" — mirrors
  `docs/plans/idea_information_belief_trigger_wiring.md`'s existing anti-drift note and the parent
  investigation's own scoping boundary.
- Do not conflate this ticket's `INFRA-267` (fixed-state) entry with `INFRA-266` (historical pre-fix
  record) — they document different points in time for the same subsystem and must both remain
  queryable.
