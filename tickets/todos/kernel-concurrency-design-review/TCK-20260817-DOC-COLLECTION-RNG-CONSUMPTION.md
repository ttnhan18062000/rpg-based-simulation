---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION
phase: open
date: 2026-08-17
tags: [documentation, engine, determinism]
---

# TCK-20260817-DOC-COLLECTION-RNG-CONSUMPTION

## Title
Record where (if anywhere) DeterministicRNG is consumed during the tick, and flag executor.py:301's dead packet_seed

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
A grep across domain_logic.py/combat.py/movement.py/worker_logic.py for RNG call patterns found no matches, suggesting combat-roll randomness resolves later in serial Resolution rather than parallel Collection — but this was only confirmed by absence of a grep match. The author wants a definitive investigation of where (if anywhere) DeterministicRNG is consumed during the tick, with the finding recorded in kernel.md or the worker contract either way.

## Scope
- Write a finding (in docs/engine/kernel.md or docs/engine/contracts/simulation_kernel_contract.md) stating the only RNG draw physically inside Collection-phase worker dispatch is executor.py:301's packet_seed, computed but NOT read by worker_logic.py/domain_logic.py/combat.py/movement.py
- State explicitly that combat is deterministic/non-random by mechanics-bible design (docs/mechanics/02_combat_laws.md:11), resolving the open question rather than leaving it an absence-of-grep-match inference
- List the actual downstream RNG consumers found: EntityGenerator (via src/engine/pipeline.py, src/engine/world_dynamics.py), QuestGenerator (via src/engine/pipeline_phases/guild_visit.py, src/engine/quests.py, src/quests/generator.py), GuildSystem (via src/town/guild.py) — confirm these run in serial Resolution/apply, not parallel Collection
- Record the disposition decision for the dead packet_seed at executor.py:301 (remove/defer/wire to something real) explicitly rather than leaving it silently in place
- Add a one-line clarifying note on EntityGenerator constructing a second DeterministicRNG instance (src/systems/world_systems/generator.py) as a minor tension with simulation_kernel_contract.md §7's "singular DeterministicRNG interface" wording

## Out of Scope
- Functionally fixing the dead packet_seed unless the Plan phase explicitly scopes a trivial removal — this is a documentation-recording ticket, not a behavior-change ticket
- Any change to src/platform/rng.py's DeterministicRNG implementation itself

## Acceptance Criteria
- [ ] A written finding (in kernel.md or simulation_kernel_contract.md) states the only RNG draw physically inside Collection-phase worker dispatch is executor.py:301's packet_seed, computed but not read by worker_logic.py/domain_logic.py/combat.py/movement.py
- [ ] Finding explicitly states combat is deterministic/non-random by mechanics-bible design, resolving the open question rather than leaving it an absence-of-grep-match inference
- [ ] Finding lists the actual downstream RNG consumers (EntityGenerator via pipeline.py/world_dynamics.py, QuestGenerator via guild_visit.py/quests.py, GuildSystem via town/guild.py) and confirms they run in serial Resolution/apply, not parallel Collection
- [ ] If the team decides the dead packet_seed at executor.py:301 should be removed/deferred/wired to something real, that decision is recorded explicitly, not left silently in place

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC
- TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING

## Related Docs
- docs/engine/deterministic_execution.md
- docs/mechanics/02_combat_laws.md
- docs/engine/contracts/simulation_kernel_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/executor.py
- src/engine/kernel.py
- src/engine/worker_logic.py
- src/engine/domain_logic.py
- src/engine/combat.py
- src/engine/movement.py
- src/core/worker_protocol.py
- src/engine/pipeline.py
- src/engine/world_dynamics.py
- src/engine/pipeline_phases/guild_visit.py
- src/engine/quests.py
- src/systems/world_systems/generator.py
- src/quests/generator.py
- src/town/guild.py
- src/platform/rng.py

## Assumptions / Open Questions
- packet_seed at executor.py:301 is real dead code (computed, never read) — could confuse future readers into thinking it seeds per-worker randomness; documenting it is the requested fix, not silently removing it as unscoped scope creep
- EntityGenerator's second DeterministicRNG instance is a minor tension with the contract's "singular" wording — worth a one-line clarifying note only, not a functional fix

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
