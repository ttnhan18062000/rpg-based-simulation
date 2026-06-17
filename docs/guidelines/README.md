---
status: active
layer: guidelines
authority: P1
audience: developer
---

# Implementation Guidelines & Best Practices

Standards and conventions for developers contributing to the RPG Engine V2.

## 🗺️ Navigation

- **[Design Patterns](design_patterns.md)**: Architectural spines (Aspects, Systems, Presenters).
- **[Intentional Divergences](intentional_divergences.md)**: Documented shifts from legacy behaviors.
- **[Architectural Conventions](../engine/architecture_reference.md)**: Technical implementation details for low-level systems.

## 🛠️ Contribution Rules

1.  **Authoritative Pipeline**: Never mutate state directly; always propose via `StateUpdate`.
2.  **Deterministic RNG**: Use `DeterministicRNG` for all stochastic logic.
3.  **Typed Contracts**: Prefer strict enums and dataclasses over raw strings/dicts.
4.  **Testing First**: Every new logic law must be accompanied by an integrity test.
