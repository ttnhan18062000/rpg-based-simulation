---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE
artifact_type: plan
tags: [world, engine]
---

# Plan — TCK-20261007-DEAD-SYSTEMS-MODULES-WITH-NO-CALLER-BLOCK-THE-MECHANISM-COMPLETENESS-GATE

Dead-code removal with no behaviour change. Per symbol: run the four-kind reachability check (import by class
name, string registration, importlib, phase table) at main 3533fde71, then delete only what passes. A symbol that
fails a check is kept and reported (rpg-planner-ubuntu's rule, 2026-10-26).

1. Run the four checks for the nine symbols in the ticket (investigation.md).
2. Delete the group that passes with no dependent claim: `world_systems/quest_generator.py` and its shim,
   `RecruitmentAppraiser`, `ChestSystem` (module, shim, its one test file).
3. Keep `SocialContractSystem` (live) and cite it in `social_contracts`' `implemented_by`.
4. Do not delete group C (LootSystem, TownServiceSystem, GuildIntelSystem, QuestSystem, CraftingSystem): each is
   cited as proof or as implementing code by a parity, Bible or compliance claim. That is a parity and Bible
   semantics call for rpg-planner; no ledger or Bible edit in this PR (rpg-planner-ubuntu, 2026-10-26).
5. Update the pins the deletions move, the allowlist line, and the two docs; re-run the completeness check.
6. Hash neutrality: the batch `paired --neutral` run.
