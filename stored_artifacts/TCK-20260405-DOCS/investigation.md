# Investigation: Documentation Out-of-Sync (AOA Pivot)

## Current Status
The project has undergone a major refactor to Aspect-Oriented Architecture (AOA).
Key documents in `docs/` still refer to legacy systems.

### Major Discrepancies Found:
- **`architecture.md`**:
    - Still mentions "Modular Evolution (Restructure in Progress)".
    - Describes an older 4-phase tick cycle, whereas the new system has 7 phases (PreSystems, Scheduling, Collection, Resolution, Cleanup, Finalization, Persistence).
    - `ActionProposal` fields are out of date (it now carries `IntentUpdate` records).
- **`entities_and_factions.md`**:
    - Defines `Entity` with a flat `stats: Stats` field and flat `ai_state`.
    - Mentions `StatsProxy` which has been deleted in favor of `StatBreakdownService`.
    - Doesn't mention the new `Aspect` modules (`identity`, `spatial`, `combat`, `progression`, `mind`, `interaction`, `inventory`).
- **`ai_system.md`**:
    - Describes a `7-Phase Cognitive Pipeline` that doesn't perfectly align with the new `AIBrain` phases (sensory, appraisal, deliberation, finalization).
    - Mentions `pickle` for worker serialization; it has been replaced by JSON.
    - Doesn't document the nested `mind` state (`decision`, `perception`, `emotion`, `navigation`, `narrative`).
- **`api_reference.md`**:
    - Missing the new introspection endpoints: `/stat_breakdown`, `/combat_traces`, `/scheduler_timeline`.
    - `EntitySchema` is flat, but the actual presenter-based output is Aspect-oriented.

## Source of Truth
- `final_implementation_plan_3.md`: Contains the roadmap and verified changes.
- `src/core/entities/entity.py`: Canonical entity structure.
- `src/core/aspects/`: Domain models.
- `src/engine/world_loop.py`: Canonical tick orchestration.
- `src/api/presenters/`: Canonical API output shaping.
