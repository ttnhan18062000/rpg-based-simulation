# Investigation — PH8 M4: Classes and Skills

## Goal
Implement a registry-backed system for RPG classes (Warrior, Mage, Rogue) and their associated skills.

## Requirements
- **Class Registry**: Define base attributes, starting gear, and available skills for each class.
- **Skill System**: Define skill logic (damage, buffs, costs) and prerequisites.
- **Identity Integration**: `IdentityComponent` should track the current class and learned skills.
- **Combat Integration**: Combat actions should be able to trigger skill effects.

## Proposed Architecture

### 1. Class Definitions (`src/core/classes.py`)
- `ClassKind` (Enum): WARRIOR, MAGE, ROGUE, etc.
- `ClassDefinition` (dataclass): Base stats, skill tree.

### 2. Skill System (`src/core/skills.py`)
- `SkillKind`: ACTIVE, PASSIVE.
- `SkillDefinition`: Damage formula, cooldown, cost.

### 3. Registry (`src/core/registries.py` or similar)
- Centralized storage for class/skill metadata.

## Questions
- Do we support multi-classing?
  For the initial version, single-class focus is better.
- Where do "Action" definitions for skills live?
  In `src/core/actions.py` or a dedicated `skills/logic.py`.
