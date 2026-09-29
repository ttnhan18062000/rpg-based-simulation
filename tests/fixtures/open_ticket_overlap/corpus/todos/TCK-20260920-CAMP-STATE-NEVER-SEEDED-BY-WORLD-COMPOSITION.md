---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION
phase: open
date: 2026-09-20
tags: [world]
---

# TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION

## Title
`CampState` is real, wired, and correctly implements monster spawning/raids/clearing rewards — but
no compiled or procedurally-generated world today seeds any `state.camps`, so it is a permanent
no-op in every real run

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found and confirmed while resolving `camp`'s own unbound-claims entry
(`TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION`, batch 2 of the
mechanism-registry unbound-claims program). `registries/mechanisms.yaml`'s own `camp` entry has
carried this finding since 2026-09-16 (`verdict: contradicted`) but was never given its own tracking
ticket — only cross-referenced against the shared
`docs/plans/world_composition_precondition_gap_finding.md` document, alongside two siblings
(`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-
NEVER-FIRES`) that each already had one.

`CampState` (`src/core/state.py`) is a real, complete state model — spawns monsters, triggers raids,
runs a real clearing-reward loop — and is correctly wired into the apply path. But no compiled or
procedurally-generated corpus world today ever populates `state.camps` with a single real camp
instance, so the entire mechanic is a structural no-op regardless of how correct its own code is.
Same shape as the two siblings above: not dead code, not a wiring gap, but a mechanic whose
precondition (a `camp`-kind world object actually existing in a world's own composition) is never
satisfied by anything in the current world-generation pipeline.

## Scope
- Confirm directly why no compiled/procgen world ever seeds `state.camps` — check whether `camp`
  world-object placement exists anywhere in `WorldCompiler`'s own content-resolution logic at all,
  or whether it was never wired into world composition in the first place (as opposed to being
  wired but never triggered, the shape the two sibling tickets found).
- Check whether any content schema (`data/content/world/`) even declares a `camp`-kind template
  that composition could place, or whether the content side itself is the gap.
- Propose a real fix (content-authoring: add camp placement to one or more world modules;
  world-gen: add a camp-placement rule to `WorldCompiler`; or something else) — bring findings and
  options to peer/user review before implementing, same investment-cap discipline the two sibling
  tickets already established for this pattern family.

## Out of Scope
- Any change to `CampState`'s own apply-path logic — already confirmed correct and wired.
- The two sibling instances (`lair`, `calamity_intensity`) — each already has its own ticket.

## Acceptance Criteria
- [ ] A real, evidence-backed explanation for why no corpus world seeds `state.camps`.
- [ ] A proposed fix, reviewed with peer/user before any implementation.
- [ ] `docs/plans/world_composition_precondition_gap_finding.md` updated with this as its own
      confirmed instance (already partially done — see Implementation Notes).

## Related Tickets
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-
  NEVER-FIRES` — same pattern family, each already tracked; this ticket gives `camp` the same
  standing.
- `TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION` — where this gap
  in tracking (a real, contradicted finding with no dedicated ticket) was noticed.

## Related Docs
- `docs/plans/world_composition_precondition_gap_finding.md` — the shared pattern document; this
  ticket adds `camp` as a named instance.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/core/state.py` (`CampState`)
- `src/worldbuilding/compiler.py` (`WorldCompiler`, where camp placement would need to be added if
  missing)
- `data/content/world/` (camp-kind content templates, if any exist)

## Assumptions / Open Questions
Whether the gap is purely content-authoring (no world module places a camp) or a deeper world-gen
gap (no placement RULE exists at all, even for authors who wanted to place one) is the central open
question — not yet distinguished.

## Implementation Notes
Not yet started. Filed to give this finding the same dedicated tracking its two sibling instances
already have, per `registries/mechanisms.yaml`'s own `camp` entry (`verified.verdict: contradicted`,
dated 2026-09-16) never having one.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
Open. Filed 2026-09-20 to close a real tracking gap found while resolving `camp`'s own
unbound-claims entry — a confirmed, contradicted finding that had lived in the registry and a
shared pattern doc for 4 days with no dedicated ticket of its own, unlike its two siblings.
