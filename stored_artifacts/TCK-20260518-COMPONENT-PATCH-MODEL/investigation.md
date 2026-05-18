# Investigation: Component-Level Patch Model

## Current State & Problem
Currently, `StateUpdate` contains `entity_updates: Dict[int, EntityUpdate]`. When `ApplyPlanBuilder` or `ApplyPath` processes an entity update, it calls `ApplyPath._apply_entity_update_to_dict`.
`EntityUpdate` is a monolithic dataclass containing 25 fields (mostly optional updates like `identity`, `navigation`, `combat`, `inventory`, `strategic`, `social`, etc.).
Checking every optional field in `EntityUpdate` creates extensive conditional branching in the critical path (`_apply_entity_update_to_dict`).

## Proposed Architecture
1. **`ComponentPatch` Hierarchy**:
   Define an abstract base class `ComponentPatch` in `src/engine/patches.py` with methods:
   - `is_noop() -> bool`
   - `merge(other: ComponentPatch) -> ComponentPatch`
   - `apply(entity: EntityState, changes: Dict[str, Any]) -> None`

   Specific patch classes:
   - `KindPatch`
   - `LifecyclePatch`
   - `BiologicalPatch`
   - `InteractionPatch`
   - `IdentityPatch`
   - `NavigationPatch`
   - `CombatPatch`
   - `StaminaPatch`
   - `InventoryPatch`
   - `EquipmentPatch`
   - `StrategicPatch`
   - `QuestPatch`
   - `SocialPatch`
   - `TaskPatch`
   - `AttributePatch`
   - `RewardPatch`
   - `WoundPatch`

2. **Patch Extraction & Execution**:
   A helper function `extract_patches(update: EntityUpdate) -> List[ComponentPatch]` converts an `EntityUpdate` into a list of non-noop patches.
   To ensure order-sensitive recalculation (e.g. attributes, equipment, identity, wounds before combat derived stats), `ComponentPatch` classes can be assigned an ordering priority (or extracted in a fixed, safe order), and derived stat recalculation can be handled seamlessly if any stat-impacting patches are applied.

3. **Performance & Parity**:
   The patches will directly replace the monolithic `if update.X:` checks in `ApplyPath._apply_entity_update_to_dict`.
