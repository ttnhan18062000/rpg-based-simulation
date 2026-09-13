---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING
phase: open
date: 2026-09-13
tags: [cognition, information, economy]
---

# TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING

## Title
Adventure-originated `ASK_INFORMATION` intents deduct gold and deliver nothing — and the trace
record claims the transaction succeeded

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Filed as part of `docs/plans/rpg_design_roadmap/rpg_knowledge_investigation_closure_plan.md`
(§3.1), the one genuinely new defect found while scoping that plan. Re-verified directly against
`src/engine/intent/action_intent.py:144-151` before filing.

When an `ASK_INFORMATION` intent arrives without a `query_kind` key in its payload — which is
every intent built by `ObjectiveIntentResolver` (`src/domains/adventure/resolver.py`), since that
resolver never sets `query_kind` — the handler takes this branch:

```python
if "query_kind" not in intent.payload:
    # Adventure/AGENCY-domain-originated intent (ObjectiveIntentResolver) -- behavior
    # must stay byte-identical to pre-fix code. Do not read "cost_paid" here.
    gold_deduct = intent.payload.get("cost_gold", 0)
    return {entity.id: EntityUpdate(
        entity_id=entity.id,
        inventory=InventoryUpdate(gold_delta=-gold_deduct),
    )}
```

No query is issued, no provider is consulted, no `KnowledgeFact` is assimilated. The entity pays
`cost_gold` and receives nothing in return. This is strictly worse than the mechanism not existing
at all: it is a live gold sink that shows up in aggregate economy numbers looking like real
commerce, when nothing was actually purchased.

**It also mis-records itself.** The `IntentTrace` built earlier in the same handler
(`action_intent.py:135-142`) is constructed with `execution_result="SUCCESS"` before either branch
runs, so the trace for this branch actively asserts a successful information transaction that
never happened.

This was a **deliberate, documented deferral** — the handler's own comment requires this branch
stay "byte-identical to pre-fix code" — taken while closing the Information-domain branch beside
it (which does correctly wire through to real assimilation, gated separately — see the plan doc
and `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS`). Defensible at the time;
it is exactly the class of deferral this repo has repeatedly lost track of.

**Not covered by any existing ticket.** `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-
NO-LEADS` enumerates six gaps — two fact-write paths, four lead-creation paths — this is none of
them; it is the intent handler's own unpaired gold deduction on the Adventure-originated branch.

**Needs no disposition decision.** Charging gold for nothing is wrong regardless of whether the
wider knowledge/investigation layer ever gets connected (see the plan doc, §3.2's gated decision).
If the layer stays dormant, the correct fix is simply to stop charging for nothing — this doesn't
wait on that decision.

## Scope
- Stop the Adventure-originated branch from deducting `cost_gold` when it cannot deliver an actual
  answer, OR route it through the same real query/assimilation path the Information-domain branch
  uses (a design call — bring the two real options to peer if the fix isn't a straightforward
  "don't charge for nothing," since `ObjectiveIntentResolver` never setting `query_kind` may itself
  be a gap worth closing rather than working around).
- Correct the `IntentTrace.execution_result` for this branch so it stops asserting `SUCCESS` for a
  transaction that delivered nothing.
- Real test evidence: an Adventure-originated `ASK_INFORMATION` intent (no `query_kind`) no longer
  silently deducts gold with no delivered value, and its trace record reflects what actually
  happened.

## Out of Scope
- Wiring `ObjectiveIntentResolver` to set `query_kind` and route through the full Information-domain
  path — that's the design fork covered by `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-
  FACTS-NO-LEADS`'s own disposition decision, not decided here.
- `ENABLE_INFORMATION_INTENT_EXECUTION`'s own default-off state — unrelated flag, not this ticket's
  concern.
- Any of the six gaps already owned by `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-
  NO-LEADS`.

## Acceptance Criteria
- [ ] Adventure-originated `ASK_INFORMATION` intents no longer silently deduct gold while
      delivering nothing (either stop charging, or route to a real delivery path — recorded with
      rationale for whichever is chosen).
- [ ] `IntentTrace.execution_result` for this branch reflects reality, not an assumed `SUCCESS`.
- [ ] Real test evidence for both of the above.
- [ ] No regression in tests covering `action_intent.py`'s `ASK_INFORMATION` handling.

## Related Tickets
- `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (open — the wider layer's
  six gaps; this ticket is explicitly none of them, and does not wait on that ticket's disposition)
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY` (open — downstream, blocked on
  the inert-layer ticket's disposition, not on this one)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open — sequenced last in
  the governing plan, unrelated defect)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_knowledge_investigation_closure_plan.md` (§3.1 — the plan that
  found and sequences this defect)
- `docs/mechanics/04_strategic_cognition.md` (authoritative Leads/Knowledge definitions)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/engine/intent/action_intent.py` (lines 135-151 — `IntentTrace` construction and the
  Adventure-originated `ASK_INFORMATION` branch)
- `src/domains/adventure/resolver.py` (`ObjectiveIntentResolver` — never sets `query_kind`, which
  is why every Adventure-originated intent hits the broken branch)

## Assumptions / Open Questions
- Whether the right fix is "stop charging" or "route to real delivery" is not predetermined here —
  Scope requires investigating which is the smaller, more correct change before implementing.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
