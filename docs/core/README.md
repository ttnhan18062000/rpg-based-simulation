---
status: authoritative
layer: core
authority: P0
audience: developer
last_verified: 2026-06-06
---

# Core Models & State

This directory contains documentation for the foundational data models and state management of the RPG Engine.

## Files
- [Authoritative State](../core/state.md): Lifecycle of the frozen state container.
- [Entities](../core/entities.md): Entity composition and component mapping.
- [Attributes & Classes](../core/attributes_and_classes.md): Derived stats and breakthrough milestones.
- [Items & Inventory](../core/items_and_inventory.md): Slot-based inventory and item templates.
- [Dirty State & Dependency Model](../core/dirty_state_and_dependency.md): Dirty flag system, dependency expansion graph, and pipeline routing.
- [Update Intent Pipeline](../core/update_intents.md): Typed update intent taxonomy, lifecycle (create → merge → apply), and compaction semantics.
