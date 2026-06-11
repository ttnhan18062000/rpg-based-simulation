---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260425-WORLD-DYNAMICS
artifact_type: test_plan
tags: [world, dynamics]
---

# Test Plan - World Dynamics

## Automated Tests

### Influence & Conquest
- `tests/world/test_influence.py`: Verify influence shifts and ownership transitions.
- `tests/world/test_stronghold.py`: Verify stronghold spawning and removal.

### Macro Threats
- `tests/world/test_calamity_raid.py`: Verify maturity advancement, calamity spawns, and periodic raids.

### Environment & Auras
- `tests/world/test_aura.py`: Verify Aura of Despair debuff application and proximity rules.

### Difficulty Scaling
- `tests/world/test_difficulty_scaling.py`: Verify level and stat scaling based on difficulty tier.

## Manual Verification
- Review authoritative update logs for `entities_add` and `entities_remove` during conquest transitions.
- Check deterministic RNG consistency across multiple runs with same seed.
