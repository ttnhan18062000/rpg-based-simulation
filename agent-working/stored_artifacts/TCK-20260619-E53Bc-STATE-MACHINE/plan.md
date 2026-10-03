---
ticket_id: TCK-20260619-E53Bc-STATE-MACHINE
phase: plan
date: 2026-06-22
---

# Plan — TCK-20260619-E53Bc-STATE-MACHINE

1. `src/domains/faction/diplomatic_state_machine.py` — compute_transitions + compute_common_enemy_pairs
2. `src/engine/pipeline.py` — Phase 8d: diplomatic_transitions run_phase block
3. `tests/unit/faction/test_diplomacy.py` — AC tests (test_diplomatic_state_transitions_valid, test_alliance_reduces_shared_territory_threat) + edge cases
