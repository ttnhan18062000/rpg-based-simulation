# Task: Milestone 7 - Structured Reason Migration

- [x] **Core Models: Observability Metrics**
    - [x] Update `ArenaResult` and `ScenarioReport` in `src/core/models/arena.py` to include `rejection_counts`.
- [x] **Logic Hardening: Legality Service**
    - [x] Add `verify_targeting_legality` and `verify_occupancy` returning `ActionReason`.
- [x] **Action Migration: Movement & Combat**
    - [x] Update `MoveAction.validate` to set structured rejections.
    - [x] Update `CombatAction.validate` to set structured rejections.
- [x] **AI Hardening: Tactical Evaluator**
    - [x] Replace `LEGACY_FALLBACK` with specific codes.
- [x] **Engine: Explicit Rejection Auditing**
    - [x] Update `ConflictResolver` to ensure all rejections attach an `ActionReason(is_rejection=True)`.
    - [x] Aggregate these explicit rejections in `ArenaRunner`.
- [x] **Documentation: Final Specification**
    - [x] Create `docs/overhaul_spec.md`.
- [x] **Verification**
    - [x] Implement `tests/arena/test_observability_audit.py`.
    - [x] Verify 100% regression stability.
    - [x] Duplicate test audit (1357 unique tests).
