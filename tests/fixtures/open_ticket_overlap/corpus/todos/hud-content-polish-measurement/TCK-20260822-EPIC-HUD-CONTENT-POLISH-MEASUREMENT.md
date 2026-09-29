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
Cross-panel consistency pass plus the first real measurement against M1's baseline — gated on M3 (M4 of
`docs/plans/hud_delivery_roadmap.md`, revised)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2) ships one real vertical slice.
`TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3) extracts chassis pieces from it and migrates the
remaining panels. Neither milestone's own scope includes stepping back to check the whole HUD is
consistent, or measuring the finished result against real before/after evidence — that cross-cutting work
only makes sense once the full HUD is wired, so it stays its own milestone (M4).

**Revision (2026-08-22):** originally scoped to measure against a formal scoring-rubric document and apply
a RimWorld/Crusader-Kings-specific content-design direction. An external design review (`tmp/hud_review.md`)
argued RimWorld/CK3 alone is too narrow a reference class for a *spectator* view of an autonomous
simulation (those games design for a player making decisions; this HUD answers "what's happening," "what
changed," "why did this happen," "is this local or systemic" — closer to observability dashboards, GIS
systems, and RTS/4X observer modes) — and that measurement should happen against a real recorded baseline,
not a first-ever score with nothing to compare against. M1 now records that baseline directly
(`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`, scope item 5) instead of this epic producing the first
score from nothing.

## Scope
Not created yet — this epic is scope-only, gated, and not to be broken into child tickets until M3 ships
(see Assumptions / Open Questions). Prospective scope:
- **Cross-panel consistency audit**, broadened beyond the original RimWorld/CK3-only framing per the
  review: progressive disclosure (`CollapsibleSection` usage), consistent color/tooltip layering
  (`HERO_CLASS_COLORS`/`TRAIT_COLORS`/`DMG_TYPE_COLORS`/`TAG_COLORS` in `frontend/src/constants/colors.ts`),
  and — the principle carried through this whole roadmap — that every panel's default view prioritizes by
  information volatility/attention-worthiness (recent, changing, anomalous) rather than static/alphabetical
  order, matching what `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` established for `EntityList.tsx`.
  Audit for panels that drifted from this, rather than assuming M2/M3 landed it consistently everywhere.
- **Real before/after measurement**: re-run the same representative observer tasks M1 measured as its
  baseline, against the now-fully-wired HUD, producing real evidence of improvement (or regression) rather
  than a first-time score with nothing to compare against.
- **Evidence-gated evaluation** of whether further investment is justified — resizable/pinnable panels,
  curated workspace presets (a compromise the review suggested between RimWorld/CK3-style fixed panels and
  EVE Online-style freeform windows) — only if the measurement pass produces real evidence such investment
  would pay off, not spec'd speculatively here.
- Fix whatever the measurement/consistency pass finds falling short, within this epic's own child tickets —
  this milestone closes the loop M1 opened, it doesn't just report a score and stop.

## Out of Scope
- Everything in M1, M2, or M3's own scope — this epic starts only after M3 ships (which is itself gated on
  M2, which is gated on M1 — so effectively the full chain must be done).
- Redesigning the chassis itself if the measurement pass finds a structural problem — that becomes a
  revision to `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`'s own follow-on work, not silently absorbed
  here as a content fix.
- Building workspace presets, resizable panels, or any other evidence-gated investment without the evidence
  actually in hand first.
- The live-map renderer effort (`docs/plans/live_map_scaling_roadmap.md`) — fully separate, no file
  overlap.

## Acceptance Criteria
- [ ] Not started until `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` (M3) is DONE
- [ ] A documented, ordered child-ticket breakdown exists before implementation begins (not created yet)
- [ ] Each child ticket, when opened, references this epic and `docs/plans/hud_delivery_roadmap.md`
- [ ] A real, dated before/after measurement result exists, comparing against M1's recorded baseline (not a
      first-ever score with nothing to compare against), and is stored somewhere durable
- [ ] The information-volatility default-view principle is verified consistent across every panel, not just
      `EntityList.tsx`
- [ ] No implementation happens directly on this epic ticket

## Related Tickets
- `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` — M1, the source of the baseline this epic measures
  against (not a direct gate on this epic — M3 is, transitively via M2).
- `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` — M2, an indirect prerequisite (via M3).
- `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` — M3, the direct hard prerequisite: this epic does not
  start until M3 ships.

## Related Docs
- `docs/plans/hud_delivery_roadmap.md` — the revised milestone sequencing this epic is M4 of
- `docs/plans/hud_design_system_foundation_epic.md` — the original RimWorld/CK3-vs-EVE-Online research;
  broadened per the revision above
- `tmp/hud_review.md` — the external design review that prompted this epic's broadened reference class and
  baseline-comparison approach

## Related Stored Artifacts
None.

## Related Code Areas
- Cross-cutting — every component `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` and
  `TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING` touched
- `frontend/src/constants/colors.ts` — the color/layering constants this epic's consistency pass checks
  against

## Assumptions / Open Questions
- **Hard gate, not an assumption**: this epic must not begin — including its own child-ticket breakdown —
  until M3 is DONE. Revisit scope-item detail once the actual wired HUD exists to measure; the
  measurement/consistency details here are necessarily provisional until then.
- Where the measurement result gets stored durably (a new `docs/` doc, a `stored_artifacts/` entry,
  something else) is not decided here — worth resolving at this epic's own Scope phase once child tickets
  are broken out, not assumed now.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
