# PH8 M4: Classes and Skills

Implement a registry-backed system for RPG classes and skills.

## Proposed Changes

### [Models] [NEW] [classes.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/classes.py)
- Define `ClassKind`, `ClassRegistry`, and `ClassDefinition`.

### [Models] [NEW] [skills.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/skills.py)
- Define `SkillKind`, `SkillRegistry`, and `SkillDefinition`.

### [Identity] [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Update `IdentityComponent` to include `class_id` and `learned_skills`.

## Verification Plan

### Automated Tests
- `tests/core/test_class_registry.py`:
  - Verify class lookup.
  - Verify that applying a class updates base stats correctly.
  - Verify skill prerequisite checks.

#### Manual Verification
- CLI inspection of entity class identities.
