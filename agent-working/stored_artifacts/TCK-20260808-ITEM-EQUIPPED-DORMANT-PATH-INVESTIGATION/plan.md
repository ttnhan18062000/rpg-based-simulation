---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION
artifact_type: plan
tags: [progression, simulation-quality]
---

# Plan — TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION

## Decision: no fix, document 2 confirmed, distinct, actionable findings

Both real producers were traced to confirmed causes (see investigation.md), but neither is a
narrow, safe fix within this investigation ticket's own mandate — flipping
`ENABLE_PROGRESSION_EVOLUTION` needs the same real controlled-verification discipline as the
`ENABLE_ADVENTURE_ROUTING` sibling investigation used (which found a real regression only by
testing it), and wiring `EquipmentService.auto_equip()` into the pipeline needs a real design
decision (which phase, what cadence, which entities) this ticket has no mandate to make.

## Steps
1. Update `docs/audits/D21_entity_lifecycle_foundation_layers.md` to record both confirmed
   findings under `item_equipped`.
2. Close this ticket with a "no fix, 2 confirmed distinct findings" completion.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| Trace both real caller chains, confirm via real execution whether either produces item_equipped | investigation.md — confirmed via direct code/config tracing (flag never set ON anywhere; zero real callers) |
| Real root cause(s) reported honestly, "content gap not a bug" a valid outcome | investigation.md's own conclusion |
| If a real fix lands, re-verified | N/A — no fix lands in this ticket |
| Scoped pytest passes | Test phase |
