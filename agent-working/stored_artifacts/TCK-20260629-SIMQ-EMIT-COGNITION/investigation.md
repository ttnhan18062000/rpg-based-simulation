---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-COGNITION
artifact_type: investigation
tags: [simq, cognition, belief, information, event-emission]
---

# Investigation: TCK-20260629-SIMQ-EMIT-COGNITION

## Pattern confirmed: all phases are @staticmethod, no event_recorder

PP-03 `SelfModelUpdatePhase.apply()` — static, no event_recorder  
PP-04 `InformationBeliefPhase.apply()` — static, no event_recorder  
PP-26 `PaidInformationTransactionSystem.enforce()` — static, no event_recorder  
PP-30 `StrategicIntelligenceSystem.fused_strategic_pass()` — static, no event_recorder  

Same constraint as PP-12 (agency ticket): use EventExtractor state diff + EntityUpdate fields.

## Detectable from StateUpdate.entity_updates

### PP-03 SelfModelUpdatePhase
Sets `entity_updates[eid].self_model_bundle_set = new_bundle` when self-model is refreshed.
→ **`self_model_updated`**: `e_upd.self_model_bundle_set is not None`

### PP-04 InformationBeliefPhase
On successful assimilation sets:
  `property_updates["last_assimilated_subject"]` and `property_updates["last_assimilated_tick"]`
→ **`belief_assimilated`**: `prop.get("last_assimilated_tick") == tick`
→ **`belief_updated`**: same (assimilation = belief content changed)

### PP-26 PaidInformationTransactionSystem
Appends `ResourceTransferIntent(source_kind="INFORMATION_PURCHASE", gold_cost=cost)` to
`entity_updates[eid].resource_transfers`.
→ **`paid_information_transaction`**: iterate resource_transfers, find source_kind=="INFORMATION_PURCHASE"

### PP-30 StrategicIntelligenceSystem (state diff)
Leads are stored in `entity.strategic.leads: Dict[str, LeadState]`.
`LeadState.certainty: LeadCertainty` changes after PP-30 scoring pass.
→ **`lead_certainty_changed`**: compare `curr_leads[lid].certainty != prior_leads[lid].certainty`

## Events requiring phase hooks (NOT in this ticket)

| Event | Blocker |
|---|---|
| `knowledge_default_fallback` | Requires knowing entity made decision on zero-certainty leads |
| `belief_stale` | Requires threshold comparison per belief — no property_update set |
| `decision_diverged_by_belief` | Requires comparing decisions of multiple entities in same region |
| `lead_contradiction_resolved` | No signal in StateUpdate or state diff |
| `paid_info_changed_goal` | Requires cross-tick correlation (paid info → goal change within 5 ticks) |

## event_category mapping
- `self_model_updated`, `belief_assimilated`, `belief_updated`, `lead_certainty_changed` → `"strategy"`
- `paid_information_transaction` → `"economy"` (gold exchange)
