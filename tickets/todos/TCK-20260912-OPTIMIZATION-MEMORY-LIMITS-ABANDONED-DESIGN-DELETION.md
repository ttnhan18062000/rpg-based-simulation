---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260912-OPTIMIZATION-MEMORY-LIMITS-ABANDONED-DESIGN-DELETION
phase: open
date: 2026-09-12
tags: [performance, architecture]
---

# TCK-20260912-OPTIMIZATION-MEMORY-LIMITS-ABANDONED-DESIGN-DELETION

## Title
Delete `src/domains/optimization/memory_limits.py` — one half superseded, one half tracks state that was never built anywhere

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found and determined during `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION` (`stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-
DETERMINATION/investigation.md`, section 5). Filed as its own ticket, separate from the clean
deletion (`TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION`) and the orphaned-capability
determination (`TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION`), because its
reasoning is distinct from both: it isn't a clean "already done better elsewhere" case, and it
isn't "a real capability nothing else provides" either.

`MemoryCapacityLimits` has 4 independent bounded-eviction categories:
- **`add_fact()`/`MemoryFact`/`get_facts()`**: superseded.
  `InformationAssimilationService.assimilate()` (`src/domains/information/assimilation.py:48-53`)
  already enforces `max_facts=10` inline, with a different eviction algorithm (oldest-first, per
  the comment at `src/engine/intent/action_intent.py:158`) — same job, different implementation,
  confirmed live (though currently unexercised for unrelated reasons documented in
  `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION`, not this ticket's to
  re-litigate).
- **`add_opponent()`/`add_reward()`/`add_coop_memory()`**: NOT orphaned capability in the sense the
  other 5 "is this wanted" behaviors are — a search of `src/core/strategic.py` and the rest of
  `src/core/` found no opponent-salience, reward-salience, or cooperation-memory tracked state
  anywhere in the current cognition model (`entity.strategic.leads/concerns/hypotheses/projects`
  are the real bounded categories, a structurally different design). This reads as an abandoned
  design direction (early RL-flavored opponent/reward modeling, never adopted in any form) rather
  than a capability gap — there is nothing for these methods to bound, since the state they'd bound
  doesn't exist.

## Scope
- Delete `src/domains/optimization/memory_limits.py` in full (`MemoryCapacityLimits`, `MemoryFact`).
- Confirm (grep) zero remaining references anywhere in `src/`/`tests/` before deleting, including
  zero references to `opponent`/`reward`/`coop_memor` salience tracking anywhere else that this
  deletion could be silently removing a real, still-relevant concept from — the investigation's own
  grep found none, but re-confirm as part of this ticket's own pickup rather than trusting a stale
  snapshot.

## Out of Scope
- The other 4 follow-up tickets from the same determination — each has its own scope and reasoning.
- Re-litigating `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION`'s own
  disposition of `assimilate()`'s real-run inertness — that finding is accepted as-is here.

## Acceptance Criteria
- [ ] `src/domains/optimization/memory_limits.py` deleted in full.
- [ ] Grep re-confirms zero remaining references to `MemoryCapacityLimits`/`MemoryFact` anywhere,
      and zero real opponent/reward/coop-memory salience tracking anywhere else in `src/`.
- [ ] No regression in any test suite touching `src/domains/optimization/` or
      `src/domains/information/assimilation.py`.

## Related Tickets
- `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` (origin)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit, Cluster C1)
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (the fact-writing
  path's own real disposition, referenced but not reopened)

## Related Docs
- `stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION/
  investigation.md` (section 5, full evidence)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/domains/optimization/memory_limits.py`
- `src/domains/information/assimilation.py` (the confirmed-live replacement for `add_fact()`)

## Assumptions / Open Questions
None — disposition is clear and already evidenced by the origin ticket's own investigation.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
