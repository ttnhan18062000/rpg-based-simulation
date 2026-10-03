---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260501-E4-PHASE-ONE
artifact_type: plan
tags: [e4, phase, one]
---

# Implementation Plan - Phase E4.1 Determinism

## Goal
Harden the engine's deterministic foundation to support 100% reproducible simulations, ensuring that the V2 authoritative logic is resilient to concurrency and execution mode differences.

## Proposed Changes

### [Component] Deterministic RNG
- **File**: [rng.py](file:///home/vboxuser/Work/rpg-based-simulation/src/platform/rng.py)
- **Change**: Finalize domain separation. Ensure `Domain` enum in `src/core/enums.py` covers all active V2 systems.
- **Enforcement**: Add a lint-like check (or marker) to prevent `next_float`/`next_int` (stateful) usage in concurrent-capable systems.

### [Component] Canonical State Hasher
- **File**: [checkpoint.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/checkpoint.py)
- **Change**: Include `camps`, `social.bonds`, and `interaction.history` in the canonical data export.
- **Validation**: Ensure `json.dumps(sort_keys=True)` remains stable even with complex nested dictionaries.

### [Component] Replay Parity
- **File**: [kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py)
- **Change**: Inject a "Determinism Guard" that compares hashes between a primary run and a secondary "ghost" run in audit mode.

## Verification Plan

### Automated Tests
- `pytest tests/unit/platform/test_rng_determinism.py`: Verify that `get_float` is truly stateless and seed-stable.
- `pytest tests/integration/test_long_run_determinism.py`: Run 1,000 ticks twice and compare final `AuthoritativeState` hashes.
- `protocol_validator.py`: Verify that new determinism markers are tracked.

### Manual Verification
- Run the engine with `--audit` flag and verify no "Stability Guard" failures occur during heavy combat/social scenarios.
