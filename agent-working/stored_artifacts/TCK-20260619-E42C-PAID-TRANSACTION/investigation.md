---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42C-PAID-TRANSACTION
artifact_type: investigation
tags: [information-seeking, paid-transaction, lead-quality, resource-transfer]
---

# Investigation — TCK-20260619-E42C-PAID-TRANSACTION

## Prior Art

- **TCK-20260619-E42A-INFO-NEED**: Implemented `InformationNeedDetector` in
  `src/engine/domain/cognition_extras.py`. Detects high-priority `UnknownFact`
  entries and generates `INFORMATION_SEEKING` projects via `StrategicUpdate`.
- **TCK-20260619-E42B-INFO-PROVIDER**: Implemented `InformationProviderState`
  in `src/domains/information/providers.py`. Durable record with `entity_id`,
  `archetype`, `reliability_score` (0.0–1.0), `knowledge_domains`, `knowledge_age`.
  Registered in `AuthoritativeState.information_providers` (keyed by entity_id).

## Gold Conservation Path

Gold transfers never mutate inventory directly. They are proposed via
`ResourceTransferIntent` → `ResourceTransactionResolver.resolve()` →
`ResourceTransactionPhase.resolve()` in `pipeline.py` Phase 6.

Existing `source_kind` patterns for fee/service deductions:
- `TOWN_SERVICE`, `TAX`, `REPAIR_FEE`, `SERVICE_FEE` — handled in
  `ResourceTransactionResolver` at line 255 of `conservation.py`.
- Pattern: check `gold < gold_cost`, reject with `ACTION_EXHAUSTION` if
  insufficient; accept with `gold_delta - gold_cost` in `InventoryUpdate`.
- The `strategic_upd` field on the intent is passed through into the
  `TransactionResult`, enabling contingent strategic updates on acceptance.

`INFORMATION_PURCHASE` is not yet registered in the resolver's
`source_kind` dispatch. Must be added to the existing `TOWN_SERVICE` branch
(same semantics: gold deduction, no item transfer, strategic update delivered).

## Project Completion Path

`StrategicUpdate` in `EntityUpdate.strategic` is the canonical path for
project/lead mutations. Fields used:
- `leads_add_or_update` — adds the new `LeadState`
- `projects_remove` — removes the fulfilled INFORMATION_SEEKING project

`UnknownFact.seeking_project_id = None` is achieved by rebuilding the
`SelfModelBundle` via `self_model_bundle_set` on `EntityUpdate`. This is the
same pattern used by `InformationBeliefPhase` (phase.py line 69–80) and
`SelfModelUpdatePhase`.

## Integration Point

The ticket specifies the interaction handler in `src/engine/`. The existing
`InteractionPhase` routes to nodes/ground_items/corpses — it does not handle
entity-to-entity adjacency. There is no existing seeker→provider adjacency
checker.

The cleanest integration is a new `PaidInformationTransactionSystem` called
from `pipeline.py` in Phase 6 (Economy & Evolution), before
`resource_transactions`. This mirrors `GoldSinkSystem` and
`QuestOpportunityRewardSystem` — pure decision logic that injects
`ResourceTransferIntent` entries into `EntityUpdate.resource_transfers` for
downstream authoritative resolution.

The seeker qualifies if:
- Entity has `ProjectStatus.ACTIVE` project of kind `INFORMATION_SEEKING`
- A provider exists in `state.information_providers` (any entity_id — no
  spatial adjacency model is implemented yet; the phase inspects presence in
  the registry, matching the ticket's "adjacent to an InformationProvider"
  intent at the registry level for Phase 4.2)

For the unit test scope the system is tested directly (not via full pipeline),
matching the `GoldSinkSystem` test pattern.

## LeadCertainty Mapping

The ticket specifies:
- `LeadCertainty.EXACT` for reliability >= 0.8
- `LeadCertainty.APPROXIMATE` for 0.5 <= reliability < 0.8
- `LeadCertainty.VAGUE` for reliability < 0.5

Note: `LeadCertainty` enum in `src/core/strategic.py` has `PRECISE` (not
`EXACT`). The ticket uses `EXACT` but the existing enum value is `PRECISE`
(added for direct observation). `APPROXIMATE` and `VAGUE` exist as expected.
The implementation will use `PRECISE` for reliability >= 0.8 to stay
consistent with the canonical enum.

## Files to Modify

1. `src/core/conservation.py` — add `INFORMATION_PURCHASE` to the
   `source_kind` dispatch (in the `TOWN_SERVICE` branch tuple)
2. `src/engine/pipeline_phases/paid_information.py` — new module
   `PaidInformationTransactionSystem`
3. `src/engine/pipeline.py` — register new phase in Phase 6 before
   `resource_transactions`
4. `tests/unit/cognition/test_information_seeking.py` — add
   `TestPaidInformationTransaction` class
