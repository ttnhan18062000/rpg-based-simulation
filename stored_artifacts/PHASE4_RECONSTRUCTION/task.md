# Phase 4 Task List

## Milestone 0: Truth Closure (Pre-Milestone Gate)
- [x] TCK-[REPLAY-RACE]: Resolve Replay Manager Thread-Safety
    - [x] Snapshot metadata in `_rotate_chunk`
    - [x] Decouple manifest updates from IO threads
- [x] TCK-[STARTUP-VAL]: Hardened Patch-Friendly Startup Boundaries
    - [x] Refactor `Kernel.__init__` profile validation
- [x] TCK-[CPU-GOV]: End-to-End CPU Resource Contract
    - [x] Implement proactive concurrency shedding in `Governor`
- [x] TCK-[PHASE-LAW]: Tick-Phase Contract Alignment
    - [x] Align `Kernel.tick_once` with the "Law of 6 Phases" docstrings
    - [x] Formalize Step 7 (Persistence) as strictly No-Op for state

## Milestone 4: Resource Interaction Core (Recovery)
- [x] TCK-[INTERACT-PRESS]: Weight Pressure and Inventory Parity
    - [x] Implement weight tracking in `InventoryComponent`
    - [x] Enforce weight-based rejection in `InteractionSystem`
- [x] TCK-[INTERACT-LOOT]: Channeled Looting and Interruption Recovery
    - [x] Implement ground-item looting
    - [x] Verify movement-induced interaction reset
- [x] TCK-[TOWN-LOOP]: Town-Driven Material Resolution
    - [x] Implement authoritative "sell-on-entry" logic
    - [x] Verify gold/secondary resource conversion
