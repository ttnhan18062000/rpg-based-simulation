---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-COGNITION
artifact_type: plan
tags: [simq, cognition, event-extractor]
---

# Plan: TCK-20260629-SIMQ-EMIT-COGNITION

## Ordered Steps

1. In `EventExtractor.extract()` entity loop — after the agency routing block,
   before the quest project loop:
   
   a. COGNITION events from entity_updates (reuse e_upd_routing already fetched, or get fresh):
      - `self_model_updated`: if `e_upd.self_model_bundle_set is not None`
        Payload: `{"entity_id": eid}` (no bundle contents to expose)
        Category: "strategy"
      - `belief_assimilated` + `belief_updated`: if `prop.get("last_assimilated_tick") == tick`
        Payload: `{"subject": prop.get("last_assimilated_subject", "unknown")}`
        Category: "strategy"
      - `paid_information_transaction`: iterate `e_upd.resource_transfers`, find
        `getattr(intent, "source_kind", None) == "INFORMATION_PURCHASE"` (first match only)
        Payload: `{"gold_cost": intent.gold_cost}`
        Category: "economy"

   b. COGNITION: `lead_certainty_changed` from state diff
      - Guard: `hasattr(entity, "strategic") and hasattr(prior_ent, "strategic")`
      - `curr_leads = getattr(entity.strategic, "leads", {}) or {}`
      - `prior_leads = getattr(prior_ent.strategic, "leads", {}) or {}`
      - For each `lid, lead` in `curr_leads.items()`:
        if `lid in prior_leads and lead.certainty != prior_leads[lid].certainty`:
          emit `lead_certainty_changed` with payload `{"lead_id": lid,
          "from_certainty": str(prior_leads[lid].certainty),
          "to_certainty": str(lead.certainty)}`
          Category: "strategy"

2. Write tests in `tests/unit/observability/test_event_extractor_cognition.py`.

## Scope Guards
- One `paid_information_transaction` per entity per tick (break after first intent found)
- Do NOT duplicate e_upd fetch — reuse same variable as agency block
- Do NOT emit `lead_certainty_changed` for new leads (no prior_lead) — new leads are not changes
- `belief_assimilated` and `belief_updated` are different SimQ event types; emit both at same site
