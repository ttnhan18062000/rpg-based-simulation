# Investigation — TCK-20260619-E61B-PLAN-EXPORTER

## Context Search Results

- `search_docs`: E43B pattern — SocialMemoryExporter/Importer wired into CampaignOrchestrator._advance_state() and _build_initial_state().
- `graphify query`: CampaignOrchestrator in orchestrator.py; _advance_state() calls _extract_social_memories(); _build_initial_state() calls SocialMemoryImporter.apply().

## Key Findings from Orchestrator Read

1. `_advance_state(final_state, summary)` is the episode-end hook. It calls `_extract_entity_carry_forwards()` first to get `entity_cfs: Dict[int, EntityCarryForward]`.
2. `_build_initial_state(episode_seed)` is the episode-start hook. It iterates `alive_carry_forwards` and applies social memory imports.
3. `SocialMemoryExporter.export(entity, episode_index)` uses duck typing — entity is an EntityState accessed without module-level import (TYPE_CHECKING only).
4. `SocialMemoryImporter.apply(entity, record)` merges records onto EntityState.

## Circular Import Avoidance

- `state.py` imports `ProgressionPlan` from `progression_plan.py` — so progression_plan.py CANNOT import `EntityCarryForward` from state.py (circular).
- Solution: pass `alive: bool` and `entity_level: int` as primitives — no cross-module dependency needed.
- This is simpler than the `AuthoritativeState` signature in the ticket spec and avoids the circular import constraint explicitly flagged in E61A.

## Wiring Points

- **Export**: in `_advance_state()`, after `entity_cfs = self._extract_entity_carry_forwards(final_state)`, iterate `entity_cfs` and export plans; call `self._state.progression_plans.update(exported)`.
- **Import**: in `_build_initial_state()`, after building entities dict and applying social memory, apply ProgressionPlanImporter for entities that have a plan.
  - Importer updates MilestoneCheck.achieved based on entity's current level; returns new ProgressionPlan via dataclasses.replace.
  - Plans are stored back to CampaignState.progression_plans so downstream code (E61C/D) can access them.
