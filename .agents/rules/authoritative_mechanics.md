---
trigger: always_on
---

# Authoritative Mechanics Rule

## Simulation Truth
The "Mechanics Bible" located in `docs/mechanics/` and the "Architectural Deep-Dives" in `docs/engine/` are the definitive sources for simulation laws, formulas, and pipeline behavior.

## Rules:
- **Consistency**: All logic changes MUST be consistent with the laws defined in the Mechanics Bible.
- **Parity**: Documentation and Source Code must remain in 100% semantic parity. If logic changes, corresponding documentation in `docs/mechanics/` or `docs/engine/` MUST be updated in the same session.
- **Reference**: When explaining or implementing mechanics, cite the specific Chapter in `docs/mechanics/` or the Phase/Law ID in `docs/engine/`.
- **Precedence**: In case of ambiguity between legacy behavior and the V2 Mechanics Bible, the Mechanics Bible takes precedence.

## Key Reference Paths:
- `docs/mechanics/`: Core simulation laws (Combat, Economics, Strategy, etc.)
- `docs/engine/authoritative_pipeline.md`: The 17-phase apply sequence.
- `docs/engine/kernel.md`: The deterministic loop and stability guard.
- `docs/core/state.md`: Immutability and state composition laws.
