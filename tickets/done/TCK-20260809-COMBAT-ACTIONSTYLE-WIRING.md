---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ACTIONSTYLE-WIRING
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-ACTIONSTYLE-WIRING

## Title
`ActionStyle` (BALANCED/AGGRESSIVE/EVASIVE) has real, already-wired combat-behavior hooks
(kiting distance, opportunity-attack escape) but was never assigned anything but the class
default anywhere in real entity generation — the direct mechanism needed to make the user's
requested diverse combat outcomes real

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Direct follow-up to `TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION` (same session): that
ticket made bravery real and race-correlated; this ticket wires the mechanism that actually turns
personality/race variance into observable combat *outcome* diversity. `ActionStyle` already has 2
real, consumed code hooks (`src/engine/tactical.py`'s kiting-distance bias for `SKIRMISHER`-role
entities, `src/engine/movement.py`'s opportunity-attack suppression on a deliberate `EVASIVE`
retreat) but every real entity kept the class default (`BALANCED`) regardless of personality.

Mid-implementation, the user gave a real design correction: personality/action-style tuning
values should be data-driven, not hardcoded per-race in Python. Both this ticket's own new
`action_style_thresholds` AND the sibling ticket's already-landed bravery-bias table were moved
together into a single real data file, `data/content/social/personality_bias.yaml`.

## Scope
1. Derive `ActionStyle` from an entity's own final (bias-applied) bravery value at generation.
2. Move the personality-tuning data (bias table + thresholds) into a real data file, code reads
   it (per explicit user direction).
3. Trace `ActionStyle`'s own full real consumption in `tactical.py`/`movement.py` to confirm
   which hooks are genuinely real vs. dead, so the fix's own real effect is honestly scoped.

## Out of Scope
- Fixing `tactical.py`'s own confirmed-dead `AGGRESSIVE` range-bonus and `EVASIVE`
  reposition-stub sub-branches — a separate, real bug in that function's control flow, disclosed
  not fixed (scope creep risk into re-auditing the whole function).
- `WorldEntitySpawner`'s own separate zero-personality bug (already filed, sibling ticket).
- Richer `combat_started`/`combat_ended` observability (already disclosed, sibling ticket).

## Acceptance Criteria
- [x] investigation.md confirms real `ActionStyle` consumers, including which sub-branches are
      genuinely dead code (not assumed all consumers are real)
- [x] The user's mid-session data-driven design correction is absorbed for both this ticket and
      its sibling's own already-landed code, not left half-migrated
- [x] Real gap-closing work re-verified against real corpus data (dungeon_crawl, urban_political)
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION (DONE, same session — the ticket whose own
  bravery-bias output this ticket consumes, and whose hardcoded table this ticket's own
  data-driven migration also covers)
- TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY (DONE, same session — the ticket whose
  own Finding 3 first confirmed `ActionStyle`'s dormancy)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` (updated)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/worldbuilding/compiler.py` (`get_action_style_for_bravery`, `_load_personality_bias_config`)
- `src/engine/tactical.py` (real kiting-distance consumer; confirmed-dead range-bonus/reposition-stub)
- `src/engine/movement.py` (real opportunity-attack-suppression consumer)
- `data/content/social/personality_bias.yaml` (new, shared with the sibling ticket)
- `src/content/repository.py`, `src/content/matrix.py` (registered the new data file correctly)

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Added `get_action_style_for_bravery(bravery)` (`src/worldbuilding/compiler.py`), reading
`action_style_thresholds` from the same data-driven config the sibling ticket introduced
(`aggressive_at_or_above: 0.65`, `evasive_at_or_below: 0.35`). Wired into the real personality-
seeding call site: `action_style=get_action_style_for_bravery(personality.bravery)`, using the
entity's own final, bias-applied bravery.

Per the user's own mid-session direction, migrated BOTH this ticket's new thresholds AND the
sibling ticket's already-landed `_BRAVERY_BIAS_BY_ALIGNMENT_BUCKET` hardcoded dict into one real
data file, `data/content/social/personality_bias.yaml`. `compiler.py` now reads it via a cached
loader with an in-code fallback (matching the shipped data exactly) so a missing/malformed file
never crashes world compilation. Registered the new file as a real, intentional non-catalog file
(`NON_CATALOG_FILES` in `src/content/repository.py`) and added a `DESIGN_ONLY` entry to
`src/content/matrix.py`'s content usage matrix (a full `CatalogRepository` schema/resolver would
be disproportionate for a small, flat tuning table).

Traced `ActionStyle`'s own full real consumption before claiming this fix "activates" anything:
kiting-distance bias (`tactical.py:549-594`) and opportunity-attack suppression on `EVASIVE`
retreat (`movement.py:185-186`) are both real and consumed. `tactical.py`'s own `AGGRESSIVE`
range-bonus and `EVASIVE` reposition-stub (`tactical.py:596-603`) are confirmed **dead code** — a
local variable mutated but never read by the function's own downstream branches, independent of
whether `action_style` is ever set. Disclosed honestly rather than overclaiming this fix's real
scope.

Real re-verification (live compiled worlds): `dungeon_crawl`'s `wild_beast_pack` population (avg
bravery ≈0.89) → 5/5 real entities `AGGRESSIVE`. `urban_political`'s `merchant_league` (no bias) →
a real, roughly even 3/3/3 split across `BALANCED`/`AGGRESSIVE`/`EVASIVE`.

## Test Summary
New tests in `tests/unit/worldbuilding/test_world_compiler.py`:
`test_get_action_style_for_bravery_thresholds`, `test_compiler_faction_bravery_bias_produces_real_action_style_skew`,
`test_personality_bias_config_loads_from_real_data_file`,
`test_personality_bias_config_falls_back_safely_on_bad_file` (the latter 2 also cover the
sibling ticket's own data-driven migration). `tests/unit/content/` (232 tests, covering the new
data file's registration) all pass. Scoped pytest (`tests/unit/worldbuilding/`,
`tests/unit/worldassembly/`, `tests/unit/combat/`, `tests/unit/strategic/`,
`tests/unit/entities/`, `tests/unit/content/`, `tests/unit/core/`, `tests/unit/tactical/`,
`tests/unit/movement/`): 1052 passed, 2 pre-existing unrelated failures (confirmed via prior
bisection this session).

## Files Changed
- `src/worldbuilding/compiler.py` — added `get_action_style_for_bravery()`,
  `_load_personality_bias_config()` (data-driven, replaces the sibling ticket's hardcoded dict),
  wired `action_style` into personality seeding.
- `data/content/social/personality_bias.yaml` — new data file.
- `src/content/repository.py` — registered the new file in `NON_CATALOG_FILES`.
- `src/content/matrix.py` — added a `DESIGN_ONLY` content usage matrix entry.
- `tests/unit/worldbuilding/test_world_compiler.py` — 4 new tests.
- `docs/mechanics/04_strategic_cognition.md`, `docs/mechanics/content_usage_matrix.md` (auto-
  regenerated) — updated.

## Completion Summary
Wired the real mechanism (`ActionStyle`) that turns the sibling ticket's own race-correlated
bravery into observable combat-outcome diversity: predator factions now genuinely kite less and
lose their safe-retreat option less often, while civilian factions get a real, even split across
styles — verified with real, live compiled-world data. Absorbed the user's own real,
mid-implementation design correction (data-driven tuning, not hardcoded-per-race code) for both
this ticket and its sibling's already-landed code, rather than leaving the codebase in a
half-migrated state. Traced and honestly disclosed 2 genuinely dead sub-branches of `ActionStyle`'s
own consumption in `tactical.py` rather than overclaiming this fix's real scope.
