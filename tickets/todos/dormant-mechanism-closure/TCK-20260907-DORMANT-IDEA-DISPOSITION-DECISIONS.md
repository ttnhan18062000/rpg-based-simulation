---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS
phase: open
date: 2026-09-07
tags: [content, architecture]
---

# TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS

## Title
Record explicit dispositions for ideas 50, 62, and 64 — none silently dropped

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 5 of 6. Three
ideas have no real path forward inside this epic's own scope and need an explicit, written
disposition rather than silent omission:
- **Idea 50 (Material-Gated Evolution)** — confirmed unbuilt (M9's own scoping, 2026-09-06): zero real
  code for `alt_outcome_kind`, never assigned to any shipped milestone.
- **Idea 64 (The Empty Chair)** — confirmed unbuilt despite M4's own "12 ideas shipped" PR title
  claiming otherwise: zero real code for `EconomicVacancyEvent`.
- **Idea 62 (Generations Misremember / `FidelityDeriver`)** — blocked on idea 63 (Belief/Religion) not
  existing; idea 63's own schema is flagged genuinely underspecified, confirmed unchanged.

## Scope
- For ideas 50/64: present the roadmap owner with a real decision — schedule as new feature work in a
  future milestone, or explicitly retire from the roadmap. This is not a build ticket; it produces a
  decision, recorded in `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`.
- For idea 62: confirm idea 63's real current schema status is unchanged (still underspecified) during
  Investigate, and record that idea 62 stays blocked pending idea 63's own future design work — not
  re-derive idea 63's design here.
- Correct the roadmap's own M4 section to stop implying idea 64 shipped (a partial correction was
  already made during M9's scoping — confirm it's sufficient, extend if not).

## Out of Scope
- Building ideas 50/64's mechanisms — a product decision, not this ticket's own scope.
- Designing idea 63 — a much larger, separate design question.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] Ideas 50 and 64 each have a real, recorded decision (schedule vs. retire), not left ambiguous.
- [ ] Idea 62's blocked status on idea 63 is confirmed current and clearly recorded.
- [ ] The roadmap doc accurately reflects all three dispositions.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED` (the M9 ticket that originally found ideas 50/64 unbuilt)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
None — this is a documentation/decision ticket, not a code-change ticket.

## Assumptions / Open Questions
- Whether ideas 50/64 get scheduled or retired is a real product decision, not resolved here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
