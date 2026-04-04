# TCK-20260405-SKILL-SCALING: Unified Skill Damage Resolution

## Status: INPROGRESS
## Priority: P1
## Scope: Unify skill scaling with authoritative DamageResolutionService.

## Acceptance Criteria
- [ ] `DamageResolutionService.resolve` accepts skill-specific overrides.
- [ ] `ActionSystem._get_use_skill_updates` delegates damage resolution to `DamageResolutionService`.
- [ ] Magical skills (e.g., Arcane Bolt) correctly scale with `MATK`.
- [ ] Physical skills (e.g., Power Strike) correctly scale with `ATK`.
- [ ] Skills can trigger critical hits and be evaded based on standard combat formulas.
- [ ] 100% pass rate in new `test_skill_scaling.py` suite.

## Related Tickets
- [TCK-20260405-CONVERGENCE](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260405-CONVERGENCE.md)
