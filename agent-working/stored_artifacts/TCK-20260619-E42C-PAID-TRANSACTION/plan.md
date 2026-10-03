---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42C-PAID-TRANSACTION
artifact_type: plan
tags: [information-seeking, paid-transaction, lead-quality, resource-transfer]
---

# Plan — TCK-20260619-E42C-PAID-TRANSACTION

## Architecture Review

All durable state changes flow through `ResourceTransferIntent` →
`ResourceTransactionResolver` → authoritative apply path. No direct state
mutation. `LeadState` and project removal go through `StrategicUpdate` in
the intent's `strategic_upd` field, delivered contingently on transaction
acceptance. Gold conservation law is maintained. Determinism preserved (sorted
iteration over providers/entities). No raw domain models exposed.

Gate: PASS

## Steps

### Step 1 — conservation.py: register INFORMATION_PURCHASE source_kind

In `ResourceTransactionResolver.resolve()`, add `"INFORMATION_PURCHASE"` to
the existing tuple at line 255:

```python
if intent.source_kind in ("TOWN_SERVICE", "TAX", "REPAIR_FEE", "SERVICE_FEE", "INFORMATION_PURCHASE"):
```

This gives it the same resolution semantics: check `gold_cost`, reject on
insufficient gold, accept with `gold_delta - gold_cost` and pass through all
contingent updates including `strategic_upd`.

### Step 2 — pipeline_phases/paid_information.py: new module

`PaidInformationTransactionSystem.enforce(state, update)`:

1. Collect all alive entities that have an active `INFORMATION_SEEKING` project
   (check `entity.strategic.projects` for `ProjectKind.INFORMATION_SEEKING` +
   `ProjectStatus.ACTIVE`).
2. For each seeker, find any registered provider in
   `state.information_providers` (take the first sorted by entity_id for
   determinism; skip if seeker == provider entity).
3. Compute `transaction_cost = int(10 * (1.0 / max(0.1, provider.reliability_score)))`.
4. Derive lead certainty:
   - reliability >= 0.8 → `LeadCertainty.PRECISE`
   - reliability >= 0.5 → `LeadCertainty.APPROXIMATE`
   - else → `LeadCertainty.VAGUE`
5. Determine `seeking_subject` from the active INFORMATION_SEEKING project's
   first objective target (or a fallback string).
6. Build `LeadState`:
   ```python
   LeadState(
       id=f"lead_info_{seeker.id}_{provider_id}_{state.tick}",
       kind="information",
       subject=seeking_subject,
       certainty=lead_certainty,
       source_entity_id=provider_id,
       discovered_tick=state.tick,
   )
   ```
7. Find the project_id of the INFORMATION_SEEKING project to remove.
8. Build `StrategicUpdate(leads_add_or_update=[lead], projects_remove=[proj_id])`.
9. Emit `ResourceTransferIntent`:
   ```python
   ResourceTransferIntent(
       source_id=provider_id,
       source_kind="INFORMATION_PURCHASE",
       gold_delta=0,
       gold_cost=transaction_cost,
       transfer_kind="INFORMATION_PURCHASE",
       strategic_upd=strategic_update,
   )
   ```
10. Append intent to `EntityUpdate.resource_transfers` for seeker.

### Step 3 — pipeline.py: register phase

In Phase 6 (Economy & Evolution), before `resource_transactions`:

```python
from src.engine.pipeline_phases.paid_information import PaidInformationTransactionSystem
update = run_phase("paid_information", update,
    lambda u: PaidInformationTransactionSystem.enforce(state, u))
```

### Step 4 — tests: add TestPaidInformationTransaction

In `tests/unit/cognition/test_information_seeking.py`, add a class
`TestPaidInformationTransaction` with:
- `test_paid_transaction_transfers_gold_and_lead`: builds a minimal state with
  seeker (INFORMATION_SEEKING project, gold=50) + provider (reliability=0.9),
  calls `PaidInformationTransactionSystem.enforce`, asserts the seeker entity
  update has a `ResourceTransferIntent` with `source_kind="INFORMATION_PURCHASE"`,
  correct `gold_cost`, and `strategic_upd` containing a PRECISE LeadState.
- `test_vague_lead_for_low_reliability`: provider reliability=0.4 → VAGUE lead.
- `test_no_gold_no_transaction`: seeker has 0 gold — intent still emitted (resolver
  will reject); system is pure decision logic, not the resolver.
- `test_no_provider_no_intent`: no provider registered → no intent emitted.
- `test_no_seeking_project_no_intent`: entity has no INFORMATION_SEEKING project.
