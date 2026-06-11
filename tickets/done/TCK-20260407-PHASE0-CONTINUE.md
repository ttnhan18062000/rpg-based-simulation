---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260407-PHASE0-CONTINUE
phase: done
date: 2026-04-07
tags: [phase0, continue]
---

# TCK-20260407-PHASE0-CONTINUE: Finishing Phase 0 Foundations

## Goal
Complete the Phase 0 foundational constraints for the Macro-Interest redesign by moving dynamic social state to the `SocialRegistry`, cleaning up `IdentityAspect` and `MindAspect` to avoid duplication, and formalizing the `InterpretedEvent` pipeline.

## Status
INPROGRESS

## Scope
- Align `IdentityAspect` and `MindAspect` to avoid state duplication (`reputation`, `hero_familiarity`).
- Implement/Consolidate `SocialRegistry` as the single source for authoritative directed bonds.
- Refine `MindAspect.narrative` to use the `InterpretedEvent` model.
- Enforce salience and retention limits (50 memories, 20 bonds) as per Phase 0 constraints.

## Acceptance Criteria
- [ ] `IdentityAspect` contains ONLY static identity data (Archetype, OCEAN, life_directive).
- [ ] `MindAspect` redirects dynamic social queries to `SocialRegistry`.
- [ ] `SocialRegistry` exists and is populated during interpreted event updates.
- [ ] `MindAspect.prune_memories()` behaves correctly for salience.
- [ ] All AI and E2E tests pass 100%.

## Related
- `design_shift_implementation_plan_high_level.md`
- `docs/architecture/macro_interest_constraints.md`
- `TCK-20260406-PHASE0`

**Tier:** standard
**Type:** chore
**Priority:** P1
