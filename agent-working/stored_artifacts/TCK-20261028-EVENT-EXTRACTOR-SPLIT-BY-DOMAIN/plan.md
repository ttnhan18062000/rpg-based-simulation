---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-EVENT-EXTRACTOR-SPLIT-BY-DOMAIN
artifact_type: plan
tags: [observability]
---

# Plan
Move `EventExtractor.extract` (1,581 lines) into `src/observability/extraction/`, one module per event domain, with every emitted event unchanged.

Method: each function body is the original text of one block of `extract()`, cut by line range and dedented, with three mechanical renames only: `EventExtractor.<cache>` becomes `run_state.<cache>` (`run_state = ctx.run_state`, the facade class itself, so a test that reassigns a cache still works), `_real_combat_update` becomes the public `real_combat_update`, and module constants lose their underscore where the facade re-exports them. The four rollback flags, `tick`, `now`, `mode`, `update`, `prior_state` and `current_state` are bound at the top of each function from a frozen `ExtractContext`. Set-iteration expressions (`sorted(set(a) | set(b))`, the `list(set)` sites) are moved verbatim.

Layout (call order is the old block order):
- `context.py`: `ExtractContext`, `RunState` protocol.
- `entity.py`: the per-entity sequence. Modules: `lifecycle` (spawn, despawn, movement), `vitals`, `combat`, `progression`, `economy`, `strategy`, `leads`, `social`, `contracts`, `quests`, `capability`.
- World level, in the old order: `strategy.rejection_cascade_events`, `resources`, `world`, `faction`.
- `event_extractor.py` stays the facade: caches, `reset_run_state`, `extract` (resolve flags, build the context, loop over entities, call the world-level functions), `_real_combat_update` and the other private names that `event_shapers.py` imports. It also keeps the code that must import `src.domains` (the phase18 allowlist pins only that file): the world-event loop and `commitment_abandoned`, which `quests.py` reaches through `ctx.abandonment_events`. The `Kernel` import of `building_sabotaged` stays local because Kernel imports this module.
Functions were split further wherever cognitive complexity passed 15 (each split a verbatim sub-block with its inputs passed in or re-read; `continue` became `return events` in two helpers).
