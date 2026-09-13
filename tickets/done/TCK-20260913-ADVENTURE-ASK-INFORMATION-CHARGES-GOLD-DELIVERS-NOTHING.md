---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING
phase: done
date: 2026-09-13
tags: [cognition, information, economy]
---

# TCK-20260913-ADVENTURE-ASK-INFORMATION-CHARGES-GOLD-DELIVERS-NOTHING

## Title
Adventure-originated `ASK_INFORMATION` intents record a lying `SUCCESS` trace for a no-op, and
carry a dormant gold-charge shape that would silently activate if ever fed a real cost

## Status
DONE

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

No query is issued, no provider is consulted, no `KnowledgeFact` is assimilated.

**Corrected 2026-09-13, before implementing: the "charges gold" framing above is wrong, and this
correction originates with the peer who filed it.** Direct tracing of the real call path, done
before touching any code, found the gold deduction **does not currently fire in real gameplay —
it is a dormant shape, not an active charge.** `ObjectiveIntentResolver.resolve()` has exactly one
real call site (`src/engine/tactical.py:348`), which passes `payload={"position": target_pos} if
target_pos else {}` — never `cost_gold`. `ObjectiveState` (`src/core/strategic.py:303-310`) has no
field to carry a cost even if one were wanted. Every other `cost_gold` occurrence in `src/` belongs
to an unrelated structure (`InformationSourceProfile`, `PopulationSpec`, progression's repair
cost). So `intent.payload.get("cost_gold", 0)` always evaluates to `0` today; the
`InventoryUpdate(gold_delta=-0)` this branch issued was a real no-op update, not a real charge.
Grepped every test touching this branch — nothing tests or depends on a nonzero deduction here, so
nothing was load-bearing on the dormant shape either.

**What is real and live is the trace.** The `IntentTrace` built earlier in the same handler
(`action_intent.py:135-142`, before this correction) is constructed with `execution_result=
"SUCCESS"` before either branch runs, so the trace for this branch actively asserted a successful
information transaction that never happened — every single time an Adventure-originated
`ASK_INFORMATION` intent reached this handler, which is real, confirmed traffic (the route family
is genuinely scored and selected in real runs). This is the actual live defect this ticket closes:
an `IntentTrace` recording success for a no-op corrupts the evidence base used to decide what's
actually working — the same "looks live and isn't" failure mode this whole arc has been unpicking,
now found built directly into the instrumentation meant to detect it.

The dormant gold-charge shape was removed anyway, not left in place: cheap to remove, forecloses
silent activation if a future caller ever populates `cost_gold`, and a `gold_delta=-0` update was
noise in the update stream regardless of whether it ever carried a nonzero value.

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
- [x] Adventure-originated `ASK_INFORMATION` intents no longer carry the dormant gold-deduction
      shape (removed outright, since it never fires today and stopping it if it ever did is the
      correct behavior either way — see corrected Request Summary above for why this is closing a
      latent shape, not stopping an active exploit).
- [x] `IntentTrace.execution_result` for this branch reflects reality, not an assumed `SUCCESS`.
- [x] Real test evidence for both of the above
      (`test_ask_information_without_query_kind_is_a_true_noop`).
- [x] No regression in tests covering `action_intent.py`'s `ASK_INFORMATION` handling.

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
Investigated before implementing and found the ticket's own "charges gold" framing (inherited from
the governing plan doc, §3.1) was wrong: traced the real call path and confirmed the gold
deduction never fires in production — `cost_gold` is never populated anywhere upstream. Reported
this to peer before touching code, since it changes what "the fix" actually is. Peer confirmed:
fix both anyway (the trace-lie is the real, live defect; removing the dormant charge is cheap and
forecloses future silent activation), and corrected the plan doc and this ticket's own Request
Summary to state the accurate finding rather than let the record inherit the original error.

Split the single `IntentTrace` construction (previously built once, before the `query_kind`
branch, always claiming `SUCCESS`) into two: the no-`query_kind` branch now builds its own trace
with an honest `execution_result` describing the no-op, and returns a bare `EntityUpdate` with no
`InventoryUpdate` at all rather than a `gold_delta=-0` no-op update. The `query_kind`-present
branch (Information-domain path, unaffected) keeps its own `SUCCESS` trace, built after the split
rather than shared.

## Test Summary
- `tests/unit/strategic/test_intents.py` (new test: `test_ask_information_without_query_kind_is_a_
  true_noop`) — 7 passed.
- `tests/unit/strategic/ tests/unit/domains/adventure/ tests/integration/domains/information/
  tests/unit/domains/information/ tests/unit/engine/test_information_intent_execution_phase.py
  tests/unit/tactical/` — 462 passed.
- `tests/integration/domains/test_fused_loop.py` — 10 passed (exercises real
  `pending_action_intent` routing for `ASK_INFORMATION`).

## Files Changed
- `src/engine/intent/action_intent.py` — split the `ASK_INFORMATION` trace construction, removed
  the dormant `InventoryUpdate(gold_delta=-gold_deduct)` for the no-`query_kind` branch.
- `tests/unit/strategic/test_intents.py` — added 1 test.
- `docs/plans/rpg_design_roadmap/rpg_knowledge_investigation_closure_plan.md` — §2/§3.1/§6
  corrected (peer's own error, corrected at peer's own instruction).

## Completion Summary
Fixed the real, live defect (a trace lying about success for a no-op) and removed a dormant,
never-currently-firing gold-charge shape found while verifying the ticket's own premise before
implementing. Corrected the ticket's own framing and the originating plan doc to match what was
actually found, rather than let an unverified claim about active behavior stand once it was shown
to be inferred from code shape rather than confirmed against what actually reaches that code.
