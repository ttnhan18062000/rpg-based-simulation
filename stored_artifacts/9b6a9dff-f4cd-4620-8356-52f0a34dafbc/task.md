# Milestone 1: Phase 4 Exit & Phase 5 Readiness
- [x] Task 1: Movement Parity Promotion
- [x] Task 2: Resource Interaction Parity
- [x] Task 3: Resource Contract and Domain Invariants
- [x] Task 4: Release Truth and Phase 5 Entry

# Milestone 2: Town Resource Resolution Core
- [x] Task 1: Freeze Town Resolution Scope
- [x] Task 1: Freeze Town Resolution Scope (Locked scope for town-side resolution logic)
- [x] Task 2: Capture V1 Town Oracle (Captured baseline oracle data for regression testing)
- [x] **Milestone 3: Contract Enforcement & Finalization**
    - [x] Implement Contract Test Suite for Town Resolution (7/7 contract tests passing)
        - [x] Verify "Law of Value" (Price parity & auto-sell enforced)
        - [x] Verify "Law of Materials" (Material/Gold consumption enforced)
        - [x] Verify "Law of Knowledge" (Recipe learning required before craft)
    - [x] Publish Support Boundary / Milestone Completion Proofs (Walkthrough and docs finalized)
    - [x] Implement `InventoryComponent` expansion (Added authoritative `gold` field)
    - [x] Implement `IdentityComponent` (Tracks `known_recipes` and `craft_target`)
    - [x] Implement `TownResolutionSystem` (Handles passive healing/recovery law)
    - [x] Implement `ShopSystem` (Enforces Law of Profit & auto-sell)
    - [x] Implement `BlacksmithSystem` (Enforces Laws of Materials & Knowledge)
    - [x] Verify V2 parity with V1 Town Oracle (Bit-identical across 6 scenarios)
    - [x] Harden state hashing for town-side truth (Canonical hashing of new components)
    - [x] Create blacksmith.py (Crafting Law)
- [x] Task 6: Integrate with Truth Surfaces (Replay/Cert) (Integrated with `CanonicalStateHasher` and `ApplyPath` validation)
- [x] Task 7: Parity & Contract Verification (Successfully achieved bit-identical parity and 100% contract enforcement)
- [x] Task 8: Publish Support Boundary (Formalized Support Boundary in `resource_phase5_implementation_milestone_2.md` and walkthrough)
