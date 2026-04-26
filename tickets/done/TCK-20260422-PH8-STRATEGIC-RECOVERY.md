# TCK-20260422-PH8-STRATEGIC-RECOVERY

## Title
Phase 8 Strategic Recovery: Combat, Tactical, & Local World Closure

## Status
DONE

## Request Summary
Recover the authoritative moment-to-moment gameplay layer, including deterministic combat, tactical AI, and local world-interaction semantics (terrain, buildings, LoS).

## Scope
- Implementation of `TacticalDecisionSystem` for pursuit and retreat.
- Implementation of `LegalityServiceV2` for LoS and terrain blockage.
- Integration of High Ground and Bracketing bonuses in `AuthoritativeApplyPipeline`.
- Parity proofing against legacy damage resolution and tactical evaluation.
- Publication of Phase 8 Exit Package and Proof Bundle.

## Out of Scope
- Multi-region strategic coordination (Phase 9).
- Character class and skill tree progression (Phase 10).
- Dynamic terrain destruction.

## Acceptance Criteria
- [x] Deterministic combat resolution bit-identical to legacy formula.
- [x] Tactical AI handles pursuit, retreat, and stickiness.
- [x] Legality service enforces LoS and terrain constraints.
- [x] 100% pass rate on contract and parity tests.
- [x] Phase 8 exit package published.

## Related Tickets
- TCK-20260422-RECOVERY-GAPS
- TCK-20260422-PH7-HARDENING-CLOSURE

## Related Docs
- docs/engine/phase8_exit_package.md
- docs/engine/phase8_proof_bundle.md
- docs/engine/divergence_log.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260422-PH8-STRATEGIC-RECOVERY/

## Related Code Areas
- src/engine/tactical.py
- src/engine/legality.py
- src/engine/pipeline.py
- tests/parity/test_combat_parity.py
- tests/parity/test_tactical_parity.py

## Implementation Notes
- Coerced legacy engagement logic into a deterministic priority chain (Lowest HP > Closest > Lowest ID).
- Diverged from legacy variance/evasion to prioritize substrate clarity.
- Implemented Manhattan-step LoS checks for performance-stable legality.

## Test Summary
- 100% pass on `tests/tactical/test_tactical_behavior.py`.
- 100% pass on `tests/parity/test_combat_parity.py`.
- Verified bit-identical damage resolution for fractional armor mitigation.

## Files Changed
- src/core/state.py
- src/engine/legality.py
- src/engine/pipeline.py
- src/engine/town_resolution.py
- docs/engine/divergence_log.md
- docs/engine/legacy_replacement_ledger.md

## Completion Summary
Phase 8 has successfully recovered the authoritative gameplay layer. The engine now supports deterministic combat, bounded tactical AI, and local world interaction. All parity and contract proofs are passing, and the exit package has been published to establish the baseline for Phase 9.
