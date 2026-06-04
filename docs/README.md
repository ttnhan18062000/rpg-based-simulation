# RPG Engine V2 Documentation

Welcome to the Authoritative Developer Documentation for the RPG Engine V2. This documentation suite is organized to mirror the engine's architectural boundaries.

## 🗺️ Navigation Map

### 🏗️ [Core Architecture](core/README.md)
The foundational laws and data structures that govern the simulation.
- [Authoritative State](../core/state.md): The "Single Source of Truth."
- [Entities & Components](../core/entities.md): The anatomy of an actor.
- [Attributes & Classes](../core/attributes_and_classes.md): Progression and power scaling.
- [Items & Inventory](../core/items_and_inventory.md): Resource conservation laws.

### ⚙️ [Simulation Engine](engine/README.md)
The orchestration layer and deterministic loop.
- [Authoritative Pipeline](../engine/authoritative_pipeline.md): The 17-phase refinement sequence.
- [Simulation Kernel](../engine/kernel.md): The 6-phase deterministic loop.
- [Project Lawbook](../engine/project_lawbook_m10.md): Architectural invariants and contracts.
- [Performance Contract](../engine/performance_contract.md): Hardware classes and scaling limits.
- [How to Run Simulation Guide](../observability/how_to_run_simulation.md): Seeding, compiling, and running headless CLI simulations with full observability.

### ⚔️ [Gameplay Systems](systems/README.md)
The implementation of specific RPG domains.
- [Combat & Progression](../systems/combat_and_progression.md): Formulas, damage, and leveling.
- [Strategic Intelligence](../systems/strategic_cognition.md): Bounded cognition and project management.
- [World & Ecology](../systems/world.md): Environment, time, and world events.
- [Buildings & Economy](../systems/buildings_and_economy.md): Harvest, craft, and trade loops.

### 📜 [Compliance & Guidelines](guidelines/README.md)
Standards for contributing and auditing.
- [Design Patterns](../guidelines/design_patterns.md): Coding conventions and architectural spines.
- [Intentional Divergences](guidelines/v2_intentional_divergences.md): Deviations from legacy logic.
- [Logic Checklist](compliance/checklist.md): The master ledger of verified gameplay laws.
- [Gap Analysis](compliance/gap_analysis.md): Tracking documentation-to-code divergences.

### 📖 [Simulation Mechanics Bible](mechanics/README.md)
The non-technical laws and formulas of the V2 simulation.
- [01: Entity Anatomy](mechanics/01_entity_anatomy.md): Biological and physical traits.
- [02: Combat Laws](mechanics/02_combat_laws.md): Deterministic resolution and tactical math.
- [03: Economic Laws](mechanics/03_economic_laws.md): Conservation, trade, and industry.
- [04: Strategic Cognition](mechanics/04_strategic_cognition.md): Goal management and mental models.
- [05: World Evolution](mechanics/05_world_evolution.md): Time, trauma, and regional dynamics.

---

## 🚀 Getting Started

1.  **Read the [Architecture Overview](../engine/architecture.md)** to understand the threaded concurrency model.
2.  **Explore the [Authoritative Pipeline](../engine/authoritative_pipeline.md)** to see how state mutations are refined and applied.
3.  **Review the [Conventions](../engine/architecture_reference.md)** before contributing new logic.

### 🤖 [AI Tooling](ai/README.md)
Claude Code subagents, workflows, and skills for the development and simulation lifecycle.
- [Agents](ai/agents.md): All 11 subagents — roles, inputs, outputs.
- [Workflows](ai/workflows.md): Multi-agent orchestration — phases, args, return values.
- [Skills](ai/skills.md): Slash commands for focused task patterns.
- [Ticket Lifecycle](ai/ticket-lifecycle.md): Complete flow from request to closed ticket, with Phase 28 as example.

---

## 🛠️ Verification
All documentation is verified against the source code via the `tests/docs/` suite. If you find a discrepancy, please mark it with a `TODO:` tag in the code and update the documentation accordingly.
