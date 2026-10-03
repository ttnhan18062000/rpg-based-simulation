---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION

## Chosen approach (resolved with the user via AskUserQuestion)
"Code lookup table" — derived from the real, already-loaded `alignment_bucket` content field
rather than (a) authoring a new personality-bias schema per archetype in
`entity_archetypes.yaml`, or (b) reusing `cognition_profiles.yaml`'s qualitative
`risk_modeling` field (rejected: not designed to mean "bravery", would be an interpretation).
The alignment-bucket approach gets the "no new content schema" benefit of a pure code table while
staying accurate to real, already-curated content classification — new factions automatically
inherit a sensible bias through their own real `alignment_bucket` assignment.

## Implementation
- `get_bravery_bias(faction_str: str) -> float` (`src/worldbuilding/compiler.py`): looks up
  `FactionSemanticsService.get_alignment_bucket(faction_str)`, maps through
  `_BRAVERY_BIAS_BY_ALIGNMENT_BUCKET`, defaults to `0.0` on any resolution failure (never crashes
  world compilation for an unrecognized faction string).
- Wired into the existing personality-seeding call site: `bravery = min(1.0, max(0.0, rng_draw +
  bias))` — additive and clamped, preserving the existing per-entity RNG determinism/variance.
- Bias magnitudes chosen to be clearly measurable (real re-verification showed >0.2 average
  separation between predator and civilian factions) without saturating every predator to bravery
  ≈1.0 (still real individual variance within each faction, confirmed via `len(set(...)) > 1`).

## Rejected / deferred
- **New `entity_archetypes.yaml` personality schema**: rejected per the user's own explicit
  choice — larger content-authoring scope than needed for the confirmed gap.
- **`cognition_profile`-derived heuristic**: rejected per the user's own explicit choice —
  semantic mismatch risk (those fields describe reasoning style, not risk tolerance).
- **Fixing `WorldEntitySpawner`'s own zero-personality bug** (both branches): real, confirmed,
  same-class bug, but requires threading a world seed through 3 function signatures across 2
  files — a real architectural change, not a small addition, and its live corpus blast radius
  isn't yet confirmed. Deferred to its own follow-up ticket (filed alongside this one's own
  closure) rather than force-fit here.

## Verification plan
- Direct unit tests: `get_bravery_bias()` against real content faction IDs across all 5 real
  `alignment_bucket` values, plus an unrecognized-faction no-crash case.
- A full synthetic-world compile test (30 predators, 30 merchants) asserting real, measurable
  population-level bravery separation while individual variance is preserved.
- Re-run this session's own live-world probe methodology against real `dungeon_crawl`/
  `urban_political` compiled populations to confirm the fix produces the expected real ordering.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md confirms real cause (uncorrelated RNG) with real data | Done — live probes, 3 real worlds |
| Fix uses the user's own chosen approach (code lookup table) | Done — alignment_bucket-derived |
| Real gap-closing work re-verified against real corpus data | Done — dungeon_crawl/urban_political post-fix probes show real ordering |
| Scoped pytest passes | Done |
