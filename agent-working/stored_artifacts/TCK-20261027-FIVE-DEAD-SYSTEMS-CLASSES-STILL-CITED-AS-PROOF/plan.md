---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261027-FIVE-DEAD-SYSTEMS-CLASSES-STILL-CITED-AS-PROOF
artifact_type: plan
tags: [world, engine]
---

# Plan (written at close from the work as done; the ticket was hand-orchestrated, not run through the plan phase)

Order followed, one class at a time, each after a recorded reachability check:

1. Interim `divergence_note` on TOWN-009, TOWN-076, TOWN-020 (first commit, through `parity_ledger_writer`).
2. `LootSystem`: re-prove TOWN-009/076 through `AuthoritativeApplyPipeline.refine` and `InteractionSystem.enforce`; repoint the loot cases in `test_resource_conservation.py`; delete.
3. `TownServiceSystem`: re-prove TOWN-020 on the live inn path plus a negative test; delete.
4. `CraftingSystem`: reachability check, re-prove PROG-098..101/107 on `ActionIntentAdapter.execute` and the resolver's CRAFTING branch; grade PROG-097 `divergent`; delete.
5. `QuestSystem`: move the ESCORT enum test, repoint WORLD-116; delete.
6. `GuildIntelSystem`: Bible ch07 section 7 as designed, not in effect (rpg-designer's OK, two corrections), TOWN-042 `unsupported`, docs corrected; delete.
7. Registry: completeness check 0 unbound; regenerate all views; full `tests/unit/tools`.
8. Proof: `paired --neutral` 1000t (no live runtime path changes), then push.

Scope guard: no live source behavior change (ruling #757 issuecomment-6426148939 item 4); PROG-097 is recorded, not fixed.
