---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING
phase: open
date: 2026-08-22
tags: [architecture, hud]
---

# TCK-20260822-EPIC-HUD-CONTEXTUAL-PANEL-WIRING

## Title
Extract the chassis pieces the M2 vertical slice proved needed, then migrate the remaining panels
(Building/Loot/ClassHall/Control/Legend + any InspectPanel tabs M2 didn't cover) by workflow — gated on M2
(M3 of `docs/plans/hud_delivery_roadmap.md`, revised)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (M1) ships a thin foundation.
`TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2) proves it against one real, complete observer workflow. This
epic does two things, in order: first extract only the chassis pieces M2's slice actually demonstrated a
need for (not a speculative superset), then migrate everything M2 didn't already cover — the mode-triggered
panels (`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `ControlPanel.tsx`, `Legend.tsx`) plus
any `InspectPanel.tsx` sub-tabs (Class/Quests/Effects/AI/Narrative) the M2 slice's workflow didn't exercise
— grouped by observer workflow rather than by current file/technical grouping.

**Revision (2026-08-22):** originally scoped as an independent sibling to M2, gated only on M1, buildable
in parallel with it. An external design review (`tmp/hud_review.md`) argued that building a chassis
(named-slot layout, component-level tokens) speculatively in parallel with M2's own validation slice
defeats the purpose of validating first — this epic now depends on M2's real output, not just M1's thin
foundation, and its own scope is explicitly bounded by what M2 proves rather than pre-planned here.

## Scope
Not created yet — this epic is scope-only, gated, and not to be broken into child tickets until M2 ships
(see Assumptions / Open Questions). Prospective scope, in two ordered halves:

**Half 1 — Extraction** (do this first, using M2's real slice as the only evidence source):
- A named-slot/config-driven layout engine, replacing M1's minimal wrapper — **only if** M2's slice
  demonstrated a real need to rearrange top-level regions; if it didn't, keep M1's minimal wrapper and
  don't build this.
- Component-level (third-tier) tokens — **only** where a panel in M2's slice proved a genuinely
  independent styling contract that the two-tier system from M1 couldn't express; not declared wholesale.
- Panel-header/navigation conventions and instrumentation hooks, generalized from what M2's slice actually
  used.

**Half 2 — Migration** (using whatever Half 1 extracted, or M1's original thin pieces if Half 1 extracted
nothing):
- The mode-triggered panels (`BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `ControlPanel.tsx`,
  `Legend.tsx`), grouped by observer workflow (event monitoring, building/location investigation,
  loot/inventory investigation, simulation control) rather than by current technical/file grouping.
- Any `InspectPanel.tsx` sub-tab (Class/Quests/Effects/AI/Narrative) M2's five-step slice didn't already
  exercise.
- Verify each panel's underlying data path against the real V2 backend (buildings, resource nodes, chests,
  ground_items, class-hall state) — these fields already exist on `AuthoritativeState`
  (`src/core/state.py`), so this is a real-data-source verification pass per panel, not a from-scratch
  backend integration; any genuine gap found becomes its own future ticket.

## Out of Scope
- Everything in M1's own scope (`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`) and M2's own scope
  (`TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING`) — this epic starts only after M2 ships, not just M1.
- Extracting or building any chassis piece M2's slice did not actually demonstrate a need for — Half 1 is
  bounded by evidence, not by what the original M1 plan speculatively described.
- Measuring the finished result against M1's baseline, or a systematic progressive-disclosure polish pass —
  that's `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (M4), gated on this epic.
- Building any new backend endpoint beyond what already exists on `AuthoritativeState`; if this epic's
  data-path verification finds a genuine serialization gap, that becomes its own future ticket, not
  silently absorbed here.

## Acceptance Criteria
- [ ] Not started until `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` (M2) is DONE — not just M1
- [ ] A documented, ordered child-ticket breakdown exists before implementation begins (not created yet),
      with Half 1 (extraction) ordered before Half 2 (migration)
- [ ] Each child ticket, when opened, references this epic and `docs/plans/hud_delivery_roadmap.md`
- [ ] Half 1's extraction decisions each cite the specific evidence from M2's slice that justified them —
      no chassis piece gets built "because the original plan said so"
- [ ] Panels are migrated grouped by observer workflow, not by current file/technical grouping
- [ ] No implementation happens directly on this epic ticket

## Related Tickets
- `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` — M1, an indirect prerequisite (via M2).
- `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING` — M2, the direct hard prerequisite this epic extracts from and
  is gated on (revised from the original parallel, M1-only-gated relationship).
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` — M4, gated on this epic.

## Related Docs
- `docs/plans/hud_delivery_roadmap.md` — the revised milestone sequencing this epic is M3 of
- `docs/plans/hud_design_system_foundation_epic.md` — M1's original design source; largely superseded by
  M2's real evidence per the revision above
- `tmp/hud_review.md` — the external design review that prompted this epic's revision to
  extraction-then-migration, gated on M2 rather than M1

## Related Stored Artifacts
None.

## Related Code Areas
- `frontend/src/components/BuildingPanel.tsx`, `LootPanel.tsx`, `ClassHallPanel.tsx`, `ControlPanel.tsx`,
  `Legend.tsx` — Half 2 targets
- `frontend/src/components/InspectPanel.tsx` — Half 2 target for any sub-tab M2 didn't cover
- `frontend/src/App.tsx` — Half 1 target, only if a named-slot engine is justified
- `frontend/src/components/Sidebar.tsx` — the mode-switch this epic's Half 2 panels are triggered by, read
  but not modified here (modified by M1/M2 instead)

## Assumptions / Open Questions
- **Hard gate, not an assumption**: this epic must not begin — including its own child-ticket breakdown —
  until M2 is DONE. Its own scope above is deliberately provisional (marked "only if"/"only where") since
  the real answer depends on M2's evidence, not on anything decided here.
- Whether Half 1 extracts anything beyond M1's original thin pieces at all is a genuinely open outcome —
  it's possible M2's slice proves the thin foundation was already sufficient, in which case Half 1 is
  a no-op and this epic is really just Half 2 (migration).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
