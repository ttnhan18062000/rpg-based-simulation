# Investigation — TCK-20260609-ENTITY-RUNTIME-CONTRACT

## Current Behavior
- No `src/entities/` module exists; no boundary model between catalog resolution and EntityState creation
- `ResolvedEntityArchetype` (src/content/resolver.py:341) is the catalog-layer resolved archetype with nested profile objects
- `EntityState` (src/core/state.py:568) is the runtime entity with combat/identity/inventory components
- `EntityRole`, `Faction` enums in src/core/enums.py
- V2EntityBuilder in src/testing/ constructs EntityState directly without catalog knowledge

## Mechanics/Engine Constraints
- docs/core/state.md: immutability law — contract must be frozen
- Architecture rule: boundary model must not import catalog loaders

## Parity Ledger Overlap
None — new model, no existing parity entries.

## Prior Work
- TCK-20260608-NORMALIZED-MODULE-REFS: similar pattern of flat typed boundary model

## Risks
- None — pure additive new module
