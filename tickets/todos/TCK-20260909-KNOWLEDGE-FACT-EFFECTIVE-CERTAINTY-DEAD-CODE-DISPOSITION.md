---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION
phase: open
date: 2026-09-09
tags: [architecture, strategy]
---

# TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION

## Title
Determine whether `effective_certainty()` (KnowledgeFact decay) is abandoned or unfinished intent — real, tested, zero callers

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found during `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`'s own investigation, while
correcting an unrelated parity-ledger `test_path` citation error. `effective_certainty(fact:
KnowledgeFact, current_tick: int) -> float` (`src/cognition/knowledge_model.py:137`) implements a
real, correctly-unit-tested time-based decay formula (`certainty * max(0.1, 1.0 - elapsed *
0.0001)`) for `KnowledgeFact` — but `grep -rn "effective_certainty" src/` (excluding tests) finds
**zero callers anywhere**. `docs/simulation/belief_and_detour_contract.md`'s own claim that
`KnowledgeFact` is "capacity-bounded, no decay" is accurate as a description of current live
behavior (confirmed correct — do NOT flag that doc line as wrong; with zero callers, no decay in
fact happens, so the doc is not stale here).

**This is the 7th instance this session's own batch of work has found of real, often
unit-tested code with no live caller** (alongside `BiologicalSystem.update()`,
`CatalogScenarioStateBuilder`'s own chain, `decay_stale_beliefs()` before this ticket wired it in,
`spawn_calamity()`, `invalidate_read_model`, and the raid-discard stub) — a recurring pattern
across this codebase of "implemented and tested" not implying "reachable at runtime," which unit
tests and parity-ledger entries have both, at times, certified as if it did.

## Scope
- Determine, from real evidence (git history / design docs / commit messages around when
  `effective_certainty()` and its test were added), whether this represents:
  - **Abandoned intent**: decay for `KnowledgeFact` was considered and deliberately dropped (in
    which case the doc's "no decay" claim is a record of a real decision, and the function should
    likely be deleted as truly dead code), or
  - **Unfinished intent**: `effective_certainty()` was meant to be wired into a real consumer
    (e.g. threat estimation, lead scoring, or a query-response staleness check) and simply never
    was (in which case wiring it in is the real fix, following the `decay_stale_leads()`
    precedent this session already established for the sibling `LeadState` mechanism).
- Record a disposition (remove / wire-in-as-new-ticket) with the evidence for which one it is —
  do not guess; the answer is not in the code alone.

## Out of Scope
- Actually wiring `effective_certainty()` in, or deleting it — this is a disposition-only ticket;
  if "wire in" is the finding, re-file as its own standard-tier ticket with real scope, matching
  the `BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION` precedent.
- `belief_and_detour_contract.md`'s "no decay" claim — confirmed accurate, not touched here.
- `LeadState`/`BeliefEntry` decay — already handled by
  `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`.

## Acceptance Criteria
- [ ] Real evidence (git blame/log, related tickets, design docs) establishes whether this is
      abandoned or unfinished intent.
- [ ] A disposition (remove / flag-as-fix-option-in-a-new-ticket) is recorded with that evidence.
- [ ] If "remove": the dead function and its own test are deleted, verified via
      `tests/unit/cognition/` passing unchanged.
- [ ] If "unfinished": a new ticket is filed with real scope for wiring it in; this ticket closes
      recording that handoff, no code changed here.

## Related Tickets
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` (origin of this finding)
- `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`,
  `TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION` (precedent: same disposition-ticket pattern)

## Related Docs
- `docs/simulation/belief_and_detour_contract.md` (confirms `KnowledgeFact` "no decay" — accurate,
  not to be edited unless this ticket's own finding is "unfinished intent" and a fix lands)
- `docs/simulation/domains/information_contract.md` (the `KnowledgeFact` model's own contract)

## Related Stored Artifacts
None yet — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/cognition/knowledge_model.py` (`effective_certainty()`)
- `src/core/self_model.py` (`KnowledgeFact`)

## Assumptions / Open Questions
- Whether abandoned or unfinished is the central, deliberately-unresolved question this ticket
  exists to answer — not assumed either way here.
- **Third option to check, per peer review during `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`
  (2026-09-11), not confirmed here, just flagged**: "abandoned" and "unfinished" aren't the only two
  possibilities — this codebase now has 3 independently confirmed instances of a third shape,
  **superseded** (a real implementation left in place alongside a *different* live mechanism doing
  the same job): `EntityGenerator.spawn_calamity()` vs. `CalamityService.
  process_world_dynamics()`'s own inline `spawn_monster()` call, `BiologicalSystem.update()` vs.
  `apply.py`'s own passive hunger/sleep-debt decay, and the `src/domains/optimization/` package (8
  modules) vs. `ResourceGovernor`/`GovernorPolicy`. Worth a real check during Investigate — is there
  a *different* live mechanism computing certainty/staleness for `KnowledgeFact` or a sibling type,
  that `effective_certainty()` might duplicate rather than being the sole (missing) implementation
  of decay — before concluding abandoned or unfinished.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
