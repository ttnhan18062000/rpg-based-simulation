# Investigation — TCK-20260619-E61A-PLAN-MODEL

## Context Search Results

- `search_docs`: D01 audit confirms ProgressionPlan is MISSING; progression_contract.md covers ProgressionConversionPhase (different from this planner).
- `graphify query`: `CampaignState` in `src/domains/campaigns/state.py`; `SocialMemoryRecord` in `social_memory.py` is the established serialization pattern.

## Key Findings

1. `CampaignState` in `state.py` is not frozen (intentionally mutable); sub-records are frozen.
2. `social_memories: Dict[int, SocialMemoryRecord]` is the direct precedent for `progression_plans: Dict[int, ProgressionPlan]` — same int→str key convention.
3. `SocialMemoryRecord.to_dict()` / `from_dict()` pattern: sorted keys, `.get()` for optional/backward-compatible fields.
4. Module must NOT import from `src.engine` or `src.core.state` (same constraint as state.py).
5. `target_route_family` stored as `str` to avoid circular import with `src/domains/adventure/schema.py`.
6. No existing `ProgressionPlan` class anywhere in the codebase.

## Architecture Boundary Check

New file `progression_plan.py` sits entirely within `src/domains/campaigns/` — no cross-domain imports needed. CampaignState imports it from the same package, identical to `social_memory.py`.
