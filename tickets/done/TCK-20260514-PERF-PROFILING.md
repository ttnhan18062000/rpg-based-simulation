# TCK-20260514-PERF-PROFILING

## Title
Implement Engine Profiling Suite

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement a robust profiling harness to establish performance baselines and debug subsystem hotspots in the V2 RPG Engine.

## Scope
- Create `scripts/profile_engine.py`
- Implement `ProfilingHarness` with `cProfile` integration
- Define baseline scenarios (Idle, Movement, Resource, Strategic)
- Setup reporting to `reports/profile/`

## Out of Scope
- Implementing py-spy or Scalene (will be done in a follow-up)
- Optimizing code discovered by the profiler (this ticket is for the tool only)

## Acceptance Criteria
- [ ] `scripts/profile_engine.py` exists and is executable
- [ ] Reports are generated in `reports/profile/`
- [ ] Scenarios correctly initialize different world states
- [ ] `cumtime` reports identify major hotspots

## Related Tickets
- None

## Related Docs
- [docs/superpowers/specs/2026-05-14-engine-profiling-design.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/superpowers/specs/2026-05-14-engine-profiling-design.md)

## Related Stored Artifacts
- [profiling_implementation.md](file:///home/vboxuser/Work/rpg-based-simulation/profiling_implementation.md)

## Related Code Areas
- `src/engine/kernel.py`
- `src/engine/pipeline.py`

## Implementation Notes
- Use `V2EntityBuilder` for all entity creation.
- Keep the harness lightweight.

## Test Summary
- Manual verification of generated reports.

## Files Changed
- [NEW] `scripts/profile_engine.py`
- [NEW] `docs/superpowers/specs/2026-05-14-engine-profiling-design.md`

## Completion Summary
- TBD
