# Plan — TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION

## Scope decision (peer-reviewed and user-approved before implementation)
"Genuinely broken" confirmed with real instrumentation (see investigation.md). User approved:
build the minimal accept path, delivering the feature; sophistication (acceptance criteria) deferred.

The scaffolding already specifies the shape: `CooperationPosture.JOIN_PARTY`'s own
`PostureDefinition.intent_mapping` is `"accept_recruitment_offer"`. Three missing pieces, per peer
review:
1. Detect a pending offer directed at this entity.
2. A branch that can select `JOIN_PARTY` when one exists.
3. The missing `elif` that promotes the contract.

## Implementation steps
1. `CooperationDecisionService.find_pending_incoming_offer(entity, state)` — new static method,
   `src/domains/cooperation/services.py`. Scans `state.entities` (contracts are only ever stored on
   the offering entity's own record) for a live, unexpired OFFERED RECRUITMENT contract targeting
   `entity`. Minimal disqualifiers only: offering entity alive/active, `entity` not already grouped.
   Deterministic ordering (sorted offerer ID, then sorted contract ID).
2. `CooperationDecisionService.select()` — new step 0, before the existing "no help needs → SOLO"
   check: if a pending offer exists, return `JOIN_PARTY` with the offerer as partner and the
   contract id stashed in `trace["accepted_contract_id"]`.
3. `CooperationPhase.execute()`:
   - Relax the existing skip-gate (`if not help_needs and group_id is None: continue`) to also
     check for a pending incoming offer, so an entity with no needs of its own still gets evaluated.
   - New block after `map_decision()`: when the decision is `JOIN_PARTY`, promote the offerer's
     contract via `ContractService.accept_contract()` (previously dead, now the real caller),
     writing the resulting `StrategicUpdate` into a `new_entity_updates[offerer_id]` entry — mirrors
     the existing party-cohesion-collapse block's own pattern of writing updates for entities other
     than the loop's current one, since `map_decision()`'s single-entity-return signature can't
     target a different `entity_id`.

## Real bug found and fixed within this same implementation
First pass promoted the contract via a raw `dataclasses.replace(contract, status=ACTIVE)`. This
carries over the original ~10-tick OFFER-stage `expiry_tick`, so `GroupSystem.update_groups()`'s
own `contract_invalid` check treated the just-accepted contract as already expired and dissolved
the group within ticks of formation (confirmed via real instrumentation: groups formed and reached
`STABLE` cohesion status but `state.groups` was empty again by tick 500, trust still 0). Fixed by
switching to `ContractService.accept_contract()` (which internally calls
`SocialContractSystem.transition_contract()`, already correctly resetting
`expiry_tick = tick + terms["duration"]` on ACTIVE transition) instead of hand-rolling the
promotion. Added a regression test asserting the extended expiry specifically.

## Guardrails
- Do not design acceptance-criteria scoring (trust threshold, need matching, faction checks) —
  explicitly deferred per the user's own standing rule. Recorded as D-09 in
  `docs/plans/deferred_tuning_decisions_register.md`.
- Do not touch `FORM_PARTY`'s own route generation/scoring — confirmed it already feeds correctly
  into this same pipeline; the gap was entirely in the accept side, not in getting entities
  physically close.
- Do not widen `GroupSystem.update_groups()`'s own group-formation/dissolution logic — it already
  works correctly once given a real ACTIVE contract; the fix is entirely upstream of it.
