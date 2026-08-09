---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION

## Context (this ticket's own origin)
Filed as a direct follow-up to `TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY` (same
session): personality now measurably affects the real-time flee decision (bravery dampens panic),
but that ticket's own Finding 4 confirmed bravery has **zero race/archetype correlation** in real
content — pure per-entity RNG. The user asked for real, diverse combat outcomes after a
simulation; this is the confirmed foundation that needs fixing first.

## Search history (this session)
`search_docs` for "personality trait generation race archetype bravery greed sociability content
correlation entity_archetypes" surfaced real, valuable prior-work history: `TCK-20260619-P0-
ENTITY-INIT` (RESOLVED a *different*, earlier bug — "PersonalityComponent(greed=0.0, bravery=0.0,
...) for every entity", i.e. ALL-ZERO personality, fixed by seeding real per-entity RNG values —
this is the fix whose real per-entity variance this ticket builds on, not duplicates);
`docs/audits/D05_entity_differentiation.md` F1 (documents that same resolved finding);
`TCK-20260628-E11B-PERSONALITY-AUDIT`/`E11C-WEIGHT-TUNING`/`E-PERSONALITY-CALIBRATION` (a real,
already-verified calibration history confirming bravery *does* produce measurably distinct
strategic-route behavior — `STRAT-226` in `docs/parity_ledger/strategic_cognition.yaml`, ≥2×
`combat_engage` rate differential between bravery quartiles). None of this prior work touched
race/faction *correlation* — only confirmed per-entity RNG variance exists and matters.

## Real entity-construction architecture — 3 distinct paths found, not 1
Confirmed via direct source read (not assumed):

1. **`WorldCompiler.compile()`'s `pop_spec`-driven path** (`src/worldbuilding/compiler.py`) — the
   path real corpus worlds tested this session actually use (`urban_political`, `dungeon_crawl`,
   `swamp_border_world` all confirmed via live probe: `archetype_id=None`, `faction_id` set).
   Seeds personality via real per-entity `DeterministicRNG` — this is the confirmed-live target
   for this ticket's own fix.
2. **`WorldEntitySpawner._spawn_archetype_native()`** (`src/worldassembly/entity_spawner.py` →
   `ArchetypeEntityFactory.build_entity()`) — a separate "worldassembly" module. Confirmed via
   direct read: **never sets personality at all** — any entity spawned through this path gets the
   builder's own all-zero `PersonalityComponent()` default, the same class of bug
   `TCK-20260619-P0-ENTITY-INIT` already fixed once, but for a different, newer code path that
   evidently came after that earlier fix (or wasn't covered by it).
3. **`WorldEntitySpawner._spawn_legacy_guard()`** (same file, its own "legacy" branch) — **also**
   never sets personality. Both of `WorldEntitySpawner`'s own branches are affected, not just the
   archetype-native one.

`WorldEntitySpawner` is only called from `src/scenarios/catalog_state_builder.py` (confirmed via
grep) — not from `WorldCompiler.compile()` or the main kernel/pipeline directly. Real blast radius
in live corpus gameplay **not fully quantified** — all 3 worlds this session tested use path 1
exclusively for their initial population. Disclosed as a real, confirmed, separate finding — see
Scope Decision below, not fixed in this ticket (filed as its own follow-up).

## Fix implemented: faction-alignment-derived bravery bias
`src/worldbuilding/compiler.py`'s personality-seeding call site (path 1 above) now applies a real,
content-derived bravery bias before the existing RNG draw, via a new `get_bravery_bias()` helper.
Per the user's own explicit direction (`AskUserQuestion`, this session — "code lookup table"
chosen over new content-schema authoring or reusing `cognition_profile`'s qualitative fields):
derives from the real, already-loaded `alignment_bucket` field
(`data/content/social/factions.yaml`, via `FactionSemanticsService.get_alignment_bucket()`) rather
than a raw per-faction-string table, so any future faction inherits a sensible bias automatically
through its own real content classification, with no new schema required.

Bias table (`_BRAVERY_BIAS_BY_ALIGNMENT_BUCKET`): `wild` +0.35 (apex predators, e.g.
`wild_beast_pack`), `invader` +0.25 (raiders, e.g. `goblin_warband`/`bandit_company`/
`dragon_cult`), `rival` +0.15 (contesting factions, e.g. `orc_clan`/`swamp_tribe`), `defender`
+0.05 (professional guards/heroes, e.g. `hero_guild`/`town_council`), `neutral` +0.0 (civilians/
merchants, e.g. `merchant_league`). Additive, clamped to `[0.0, 1.0]`, applied on top of the
existing per-entity RNG draw — preserves individual variance within each faction while shifting
the population mean.

**Real, direct verification** (not assumed): re-ran the exact same live-world probe methodology
used throughout this session. `dungeon_crawl`'s real compiled population, post-fix:
`wild_beast_pack` avg bravery 0.889, `goblin_warband`/`undead_remnants`/`bandit_company` avg
0.73-0.83 (invader bucket). `urban_political`: `bandit_company` (invader) 0.852 >
`hero_guild`/`town_council` (defender) 0.61-0.72 > `merchant_league` (neutral) 0.492. Real,
ordered, measurable population skew, individual per-entity min/max ranges still varying widely
within each faction (RNG variance preserved).

## Scope decision
- **Fixed**: the confirmed-live path (`WorldCompiler.compile()`).
- **Disclosed, not fixed**: `WorldEntitySpawner`'s own two branches (`_spawn_archetype_native`,
  `_spawn_legacy_guard`) both never set personality. Fixing this properly requires threading a
  world seed through `WorldEntitySpawner.spawn_from_context()` → `_spawn_one()` →
  `ArchetypeEntityFactory.build_entity()` (none of which currently receive one) — a real,
  non-trivial signature change across 3 functions in 2 files, not a small addition. Given its live
  blast radius in real corpus gameplay is not yet confirmed (only 1 real caller found,
  `catalog_state_builder.py`), this is proportionately a separate ticket, not force-fit here.

## Docs Requiring Update
- `docs/mechanics/04_strategic_cognition.md`: the bias table is a tuning constant, not a certified
  Mechanics Bible formula (same reasoning already applied to `xp_multiplier`/`readiness_speed`
  earlier this session) — but the real, faction-correlated mechanism itself is worth a brief
  cross-reference from the existing bravery/Risk Multiplier section this same session already
  extended for the tactical panic/flee wiring.
