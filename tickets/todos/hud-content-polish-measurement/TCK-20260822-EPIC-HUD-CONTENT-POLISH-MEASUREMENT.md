---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT
phase: open
date: 2026-08-22
tags: [architecture, hud, design-system]
---

# TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT

## Title
Systematic progressive-disclosure polish pass across all wired HUD panels, plus the first real measurement
against M1's rubric — gated on M2 + M3

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2) and `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3)
each re-plug HUD panels into the `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (M1) chassis and wire
them to real data, independently of each other. Neither milestone's own scope includes stepping back to
apply a consistent content-design direction across the whole panel set, or actually measuring the finished
result against M1's own scoring rubric — that cross-cutting work only makes sense once both are done, so it
becomes its own milestone (M4) rather than being split unevenly across M2/M3 or skipped entirely.

## Scope
Not created yet — this epic is scope-only, gated, and not to be broken into child tickets until M2 and M3
both ship (see Assumptions / Open Questions). Prospective scope:
- Apply the RimWorld/Crusader-Kings-style "structured complexity" content-design direction researched
  alongside M1 as a systematic pass across every panel M2 and M3 wired: consistent progressive disclosure
  via `CollapsibleSection`, consistent color/tooltip layering (`HERO_CLASS_COLORS`/`TRAIT_COLORS`/`DMG_TYPE_COLORS`/`TAG_COLORS`
  and friends in `frontend/src/constants/colors.ts`), and a stated, enforced click-depth budget — auditing
  for panels that drifted from the convention rather than assuming M2/M3 landed it consistently.
- Run M1's own metrics/scoring rubric (Task Success Rate, navigation-search success rate, click-depth
  budget, real-estate allocation) against the actual finished HUD for the first time — producing a real
  scored result, not an estimate, in whatever format M1's own open question (composite grade vs. separate
  metrics) resolved to.
- Fix whatever the measurement pass finds falling short of the rubric's bar, within this epic's own child
  tickets — this milestone closes the loop M1 opened, it doesn't just report a score and stop.

## Out of Scope
- Everything in M1, M2, or M3's own scope — this epic starts only after both M2 and M3 ship.
- Redesigning the chassis itself (skeleton, theme tokens, navigation map) if the measurement pass finds a
  structural problem — that becomes a revision to `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`'s own
  follow-on work, not silently absorbed here as a content fix.
- The live-map renderer effort (`docs/plans/live_map_scaling_roadmap.md`) — fully separate, no file
  overlap.

## Acceptance Criteria
- [ ] Not started until both `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2) and
      `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3) are DONE
- [ ] A documented, ordered child-ticket breakdown exists before implementation begins (not created yet)
- [ ] Each child ticket, when opened, references this epic and `docs/plans/hud_delivery_roadmap.md`
- [ ] A real, dated scored result against M1's rubric exists and is stored somewhere durable (not just
      reported in a ticket's Completion Summary and then lost)
- [ ] No implementation happens directly on this epic ticket

## Related Tickets
- `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` — M1, the source of the rubric and content-design
  direction this epic measures/applies (not a direct gate on this epic — M2/M3 are).
- `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` — M2, a hard prerequisite (not a soft reference): this epic
  does not start until M2 ships.
- `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` — M3, a hard prerequisite alongside M2: this epic does
  not start until M3 also ships.

## Related Docs
- `docs/plans/hud_delivery_roadmap.md` — the milestone sequencing this epic is M4 of
- `docs/plans/hud_design_system_foundation_epic.md` — the rubric and RimWorld/CK3-vs-EVE-Online research
  this epic applies and measures against

## Related Stored Artifacts
None.

## Related Code Areas
- Cross-cutting — every component `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` and
  `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` touched
- `frontend/src/constants/colors.ts` — the color/layering constants this epic's consistency pass checks
  against

## Assumptions / Open Questions
- **Hard gate, not an assumption**: this epic must not begin — including its own child-ticket breakdown —
  until both M2 and M3 are DONE. Revisit scope-item detail once the actual wired HUD exists to measure; the
  rubric-application details here are necessarily provisional until then.
- Where the scored result gets stored durably (a new `docs/` doc, a `stored_artifacts/` entry, something
  else) is not decided here — worth resolving at this epic's own Scope phase once child tickets are broken
  out, not assumed now.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
