---
content_type: doc
status: historical
layer: ai
authority: P2
audience: agent
tags: [skill, scaling]
---

- [x] Unify Combat Skill Damage Scaling under AOA
    - [x] Refactor `ActionSystem._get_use_skill_updates` to accept `DeterministicRNG`
    - [x] Fix `WorldState` attribute access by passing authoritative RNG through the pipeline
    - [x] Update `CombatAspect` to use property-based `matk` and `mdef` scaling
        - [x] Add `matk_base` and `mdef_base` fields
        - [x] Implement multipliers for magical attributes
        - [x] Add `@setter` compatibility layer for legacy code
        - [x] Update `_map_legacy_stats` for Pydantic validation of existing registries
    - [x] Resolve `Entity` initialization errors in test suite (`kind` field requirement)
    - [x] Verify Scaling Logic with dedicated test suite
        - [x] Physical Scaling verification
        - [x] Magical Scaling verification
        - [x] Elemental Scaling verification
    - [x] Verify No Regressions in E2E combat arena suite
