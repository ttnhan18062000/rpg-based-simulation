---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42C-PAID-TRANSACTION
artifact_type: test_plan
tags: [information-seeking, paid-transaction, lead-quality]
---

# Test Plan — TCK-20260619-E42C-PAID-TRANSACTION

## Scope

Unit tests in `tests/unit/cognition/test_information_seeking.py`.

## Test Cases

### Normal Flow

1. **test_paid_transaction_transfers_gold_and_lead** (acceptance criterion)
   - Seeker entity: INFORMATION_SEEKING project active, gold=50
   - Provider: reliability=0.9
   - Expected: ResourceTransferIntent with source_kind="INFORMATION_PURCHASE",
     gold_cost > 0, strategic_upd with LeadState(certainty=PRECISE) and
     projects_remove containing the project id

2. **test_vague_lead_for_low_reliability**
   - Provider reliability=0.4
   - Expected: LeadState.certainty == LeadCertainty.VAGUE

3. **test_approximate_lead_for_mid_reliability**
   - Provider reliability=0.65
   - Expected: LeadState.certainty == LeadCertainty.APPROXIMATE

4. **test_transaction_cost_formula**
   - Provider reliability=0.5 → cost = int(10 / 0.5) = 20
   - Provider reliability=1.0 → cost = 10
   - Provider reliability=0.1 → cost = int(10 / 0.1) = 100 (capped by max(0.1))

### Edge Cases

5. **test_no_provider_no_intent**
   - No provider in state.information_providers
   - Expected: no ResourceTransferIntent emitted for seeker

6. **test_no_seeking_project_no_intent**
   - Entity has no INFORMATION_SEEKING project
   - Expected: no ResourceTransferIntent emitted

7. **test_seeker_is_own_provider_skipped**
   - Provider entity_id == seeker entity_id
   - Expected: no intent (skip self-transaction)

8. **test_lead_subject_matches_project_objective**
   - Project has ASK_INFORMATION objective targeting "moon_resin.source"
   - Expected: LeadState.subject == "moon_resin.source"

## Run Command

```bash
pytest tests/unit/cognition/test_information_seeking.py -x -v
```
