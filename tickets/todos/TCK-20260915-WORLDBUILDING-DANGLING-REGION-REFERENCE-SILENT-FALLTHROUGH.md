---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH
phase: open
date: 2026-09-15
tags: [world]
---

# TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH

## Title
A population recipe's `preferred_regions` can name a region no module in the composition defines,
and silently falls through to the next listed preference with no error — a content-reference class
of defect, not a single-string typo

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found while doing a static world-spec comparison for
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`. The `merchant_caravan` population
recipe (`data/content/entities/populations.yaml`) declares
`preferred_regions: ["trade_road", "hometown"]`. **No module in either `crowded_frontier`'s or
`frontier_living_world`'s composition defines a region literally named `"trade_road"`** —
`bandit_road_trade_pressure` (the module that pulls `merchant_caravan` in) defines a region named
`"bandit_road"` instead, a different id. The reference silently falls through to the second
listed preference, `"hometown"`, with no warning or compile-time error, placing `merchant_league`
entities in the far corner of the map rather than wherever `"trade_road"` was actually meant to
be.

**This is the same shape as several other findings this arc**: the missing difficulty tier
falling back to tier 1, a spatial-grid attribute read that never existed, an item-registry lookup
returning `None` — a reference to something that doesn't exist resolving to a plausible-looking
wrong value instead of failing loudly. The specific string is one instance; the pattern (nothing
validates that a `preferred_regions` entry, or any other region-id reference in world-module
content, actually resolves against the composed region set) is the real defect.

## Scope
- Add compile-time validation (in `WorldCompiler`/`WorldRepository`'s own compile path, or a
  standalone `validate_content.py`-style check run before/during compile) that every region id
  referenced by a `preferred_regions` list (and any other region-id-shaped reference in
  world-module/population content — `spawn_region`, region entries in `regions:` blocks that
  reference an id from elsewhere, etc.) actually resolves against the set of regions the specific
  world composition defines.
- Decide (not assumed here) whether an unresolvable reference should be a hard compile error, a
  loud warning surfaced in the compile report, or both — this changes authored-content behavior
  broadly, so should be a real decision, not silently picked.
- Fix the specific `"trade_road"` vs `"bandit_road"` mismatch once the validation exists to confirm
  the fix (whichever region id was actually intended — check other modules/quests referencing
  `"trade_road"` or `"bandit_road"` for the authored intent before choosing).
- Audit whether this same pattern (a `preferred_regions` or similar reference with no matching
  region) exists elsewhere in the corpus once the validator exists — do not assume this is the
  only instance.

## Out of Scope
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own remaining scope — this is filed
  as its own defect, independent of whether it turns out to be a contributing cause there.
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` (sibling ticket, filed
  separately) — a related but distinct defect (same-named regions with different bounds, not a
  dangling reference).

## Acceptance Criteria
- A real compile-time check exists that would have caught the `"trade_road"` mismatch before this
  investigation found it by hand.
- The specific mismatch is fixed, with the correct intended region id confirmed from authored
  content context, not guessed.
- A decision is recorded (ticket or doc) on whether this class of check is a hard error or a
  warning, with reasoning.

## Related Tickets
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (surfaced this while doing a static
  world-spec comparison)
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` (sibling — the other region-
  composition defect found in the same trace)
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (peer-flagged as possibly sharing this same
  root cause — spawn placement and region geography not lining up — check when picked up)

## Related Docs
_(none — no existing doc covers world-module content validation at this level yet)_

## Related Stored Artifacts
_(none yet — filed as a finding, not yet investigated)_

## Related Code Areas
- `data/content/entities/populations.yaml` (`merchant_caravan`'s own `preferred_regions`)
- `data/content/world_modules/bandit_road_trade_pressure.yaml` (defines `"bandit_road"`, not
  `"trade_road"`)
- `src/worldbuilding/compiler.py::WorldCompiler` (the compile path this validation should attach
  to)
- `tools/validate_content.py` (if a standalone validator is the chosen mechanism)

## Assumptions / Open Questions
- Not yet known whether `"trade_road"` was meant to be `"bandit_road"` (a typo) or whether a
  `"trade_road"` region was meant to exist and was never authored (a missing region) — check
  authored intent (other content referencing `"trade_road"`, git history) before fixing.
- Not yet known how many other dangling region references exist in the corpus — the validator
  should surface this, not be assumed to be a single instance.

## Implementation Notes
_(none — filed as a finding, not yet investigated)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_
