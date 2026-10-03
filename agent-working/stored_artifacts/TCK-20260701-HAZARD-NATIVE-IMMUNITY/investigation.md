---
status: active
artifact_type: investigation
ticket_id: TCK-20260701-HAZARD-NATIVE-IMMUNITY
date: 2026-07-02
---

# Investigation — TCK-20260701-HAZARD-NATIVE-IMMUNITY

> **Revision note (2026-07-02):** This is the plan-of-record investigation, covering the
> corrected `hazard_kind`/`FactionDefinition.hazard_immunities` design. A first implementation
> pass (faction-bucket + region-type design) shipped, passed review/tests, and was marked DONE,
> then **reopened and reverted** after the user identified a requirement that design could not
> satisfy: endurance to a hazard must be declared per faction/race for its own in-fiction
> reason, not inferred from hero-hostility or a coarse legacy faction bucket. The superseded
> first-pass investigation is preserved (marked superseded) at
> `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/investigation.md` for traceability. This
> document supersedes it as the plan of record.

## Context Search (mandatory tools, run first)
- `mcp__knowledge-search__search_docs("hazard drain region native entity faction immunity wolf_den")`
  — top hits: `docs/mechanics/05_world_evolution.md` §3 Regional Sovereignty (bipolar Hero/Monster
  influence, no per-region native-faction field); `docs/audits/D20_simq_integration.md`
  "Extinction symptom — still present" section (empirical proof wolves die in `wolf_den`). No
  existing native-immunity or hazard-endurance mechanism found in docs at first pass.
- `graphify query "EnvironmentService calculate_hazard_drain entity faction native region"` and
  `graphify query "hazard type resistance immunity faction race"` — BFS surfaced the core state
  graph (`RegionState`, `EntityState`, `Faction`, `IdentityComponent`, `FactionState`,
  `CatalogRepository`) but no dedicated "hazard type"/"endurance" node — confirms the concept is
  genuinely new to the codebase, not rediscovering something already wired up.

## Priority Question — Resolved
`data/content/world_modules/wolf_den_near_forest.yaml`: region `wolf_den` (`type: wilderness`,
`hazard_level: 2.0`), population `wolf_pack_small` → faction `wild_beast_pack`
(`data/content/social/factions.yaml:32-39`, `legacy_engine_bucket: "MONSTER_HORDE"`,
`alignment_bucket: "wild"`, `common_races: ["wolf", "spider", "slime"]`).
`docs/audits/D20_simq_integration.md:159-161` confirms empirically that wolves in
`sandbox_world` (post `worldcomposition.v1` migration) still die from their own den's hazard —
**confirmed: no existing hazard endurance mechanism to reuse; this is greenfield.**

## Current Behavior (file:line refs)
- `src/world/environment.py:15-28` — `EnvironmentService.calculate_hazard_drain(region, entity)`
  takes `entity` but never reads it. Base formula:
  `int(region.hazard_level * (1.0 + region.calamity_intensity) * (1.5 if "MIASMA" in
  region.active_modifiers else 1.0) * 10.0)`.
- `src/engine/world_dynamics.py:20-40` — `WorldDynamicsSystem.resolve_dynamics`, sole call
  site, once per living/active entity per tick.

## Why the first-pass mechanism was rejected
The first pass gated the exemption on `entity.identity.faction == Faction.MONSTER_HORDE and
region.kind == "WILDERNESS"`. User's redirect, verbatim reasoning: (1) a faction/race should
endure a hazard because of its own declared nature (e.g. fiends endure chaos corruption because
they're fiends), not because it happens to be bucketed as hostile-to-hero; (2) factions hostile
to the hero faction must **not** be automatically immune to everything; (3) a hazard kind that
nobody is flagged as enduring must hurt every faction present, including two mutually hostile
ones fighting in it together (hero vs. wolf in toxic gas). The rejected design fails all three:
it conflates "is bucketed `MONSTER_HORDE`" with "endures hazards," and has no way to make any
hazard hurt monsters and heroes equally — it can only ever exempt the `MONSTER_HORDE` side.
Concrete proof this conflation is wrong: `data/content/social/factions.yaml:32-49` —
`wild_beast_pack` and `goblin_warband` both map to `legacy_engine_bucket: "MONSTER_HORDE"` but
have different `alignment_bucket` (`"wild"` vs `"invader"`) — the legacy bucket cannot
distinguish "endures its own habitat" from "is hostile to the town," which are orthogonal facts.

## New Findings Supporting the Corrected Design
- `src/content/schema.py:149-156` — `FactionDefinition(CatalogBaseDefinition)` already carries
  faction-level catalog fields (`alignment_bucket`, `legacy_engine_bucket`, `common_races`,
  `themes`). A `hazard_immunities: List[str]` field fits this class directly.
- `src/content/schema.py:133-142`, `src/content/repository.py:428-429`,
  `data/content/living/races.yaml` — a separate `RaceDefinition` catalog exists
  (`repo.get_race()`), with real per-species entries (e.g. `id: "wolf"`). Confirms "race" is a
  genuine, distinct catalog granularity — supports the user's "faction/race" phrasing as an
  architectural choice, not loose synonym. Not used in this ticket (see Risks below) but a real,
  ready extension point.
- `src/content_semantics/faction.py:42-60` — `get_faction_id_str(entity)` already exists to
  recover an entity's **catalog-level** faction id string (e.g. `"wild_beast_pack"`) at
  runtime, reading `entity.identity.properties["faction_id"]` first, falling back to the legacy
  `Faction` enum name. This is the missing link the first pass didn't use.
- `src/worldbuilding/compiler.py:304-312` and `src/worldassembly/entity_spawner.py:104-114` —
  confirmed **both** production spawn paths (`worldtemplate.v1` and `worldcomposition.v1`)
  populate `entity.identity.properties["faction_id"]` (and `"race_id"`) with the real catalog
  id. No entity-side state needs to be added.
- `src/content_semantics/faction.py:15-28` — `FactionSemanticsService`/
  `get_faction_semantics_service()` is an explicitly-documented **process-level singleton**
  ("a valid performance optimization for the hot path") — resolves the concern that a catalog
  lookup on a per-entity-per-tick call site would be too expensive; it is designed for exactly
  this.
- `src/worldbuilding/schema.py:27-35` (`RegionSpec`) and `src/core/state.py:236-258`
  (`RegionState`) — both already carry `hazard_level` as a plain float with no "flavor"/type.
  No existing `damage_type`/elemental taxonomy exists anywhere in `src/core/enums.py` or
  `docs/mechanics/02_combat_laws.md` (checked) — `hazard_kind` is genuinely greenfield; free to
  name values (`"PHYSICAL"` default, `"NATURAL_TERRAIN"` for wilderness habitats) without
  colliding with an existing convention.
- `tests/unit/content_semantics/test_semantics.py` — existing test pattern
  (`CatalogRepository("data/content"); repo.load_all()`, real content, no mocking) for
  exercising `FactionSemanticsService` — reused for the new
  `get_hazard_immunities`/endurance tests rather than inventing a new test-fixture pattern.
- `src/core/builder.py:163-213` — `V2EntityBuilder.identity(faction=..., properties={...})`
  accepts both the legacy `Faction` and a `properties` dict directly — confirms test fixtures
  can construct entities with a real `"faction_id"` property matching production spawn shape.

## Mechanics/Engine Constraints
- Both `hazard_kind` (region-side) and `hazard_immunities` (faction-side) must default to
  values that produce **zero behavior change** for all existing content/tests:
  `RegionState.hazard_kind: str = "PHYSICAL"`, `FactionDefinition.hazard_immunities: List[str]
  = []`. No existing region or faction in the catalog sets either today.
- `RegionState.to_canonical_dict` (and any other exhaustive-field serializer touching
  `RegionState`) must be checked at implementation time to ensure the new field is included —
  determinism/replay hashing depends on all durable fields being covered.
- `docs/mechanics/02_combat_laws.md` has no damage-type taxonomy to stay consistent with —
  confirmed via grep, no naming collision risk.

## Parity Ledger Overlap (IDs + status)
`docs/parity_ledger/world_dynamics.yaml`:
- `WORLD-060` (line 296): "Regional hazards drain HP/Readiness based on intensity." — entry to
  update with the corrected mechanism's evidence and a real `test_path` (currently points at a
  nonexistent `tests_v2/parity/test_parity_regional_sovereignty.py` — pre-existing staleness,
  not introduced by either pass of this ticket).
- `WORLD-029` (line 285): shares the same dead `test_path` — same fix applies.
- An unrelated hunk in the same file (`camp_constructed` divergence note, owned by
  `TCK-20260701-SIMQ-CAMP-PARITY-CLEANUP`) is present in the working tree — **not** to be
  touched by this ticket; verified untouched after the first-pass revert.

## Prior Work
- `stored_artifacts/TCK-20260701-SANDBOX-MONSTER-BALANCE/plan.md` — first traced the extinction
  to `hazard_level`.
- `tickets/done/TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE.md` — confirms wolves present and dying
  in `sandbox_world` post-migration.
- `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/` (superseded) — first implementation
  pass's full staging trail (faction-bucket + region-type design), preserved for traceability,
  not used as current guidance.

## Risks and Open Questions
- **Faction-level, not race-level.** `hazard_immunities` is implemented on `FactionDefinition`
  only in this ticket. `RaceDefinition` is a real catalog with the same base class and could
  carry the identical field later if a faction ever needs mixed-race endurance (e.g. one race
  within a faction endures a hazard the others don't) — no current content needs this
  (`wild_beast_pack`'s wolves/spiders/slimes are all forest fauna sharing the same habitat).
  Documented as a deliberate, evidence-based scope limit, not an oversight.
- **Fiend/chaos-corruption is illustrative only.** No such faction or region exists in the
  catalog; not authored as part of this ticket. Covered by a synthetic (test-fixture-only) unit
  test so the mechanism is proven generically, without inventing unrequested content.
- **Content scope expansion.** The original ticket's Out of Scope said "engine code only";
  this design requires content authoring (`hazard_kind` on 3 regions,
  `hazard_immunities` on 2 factions) to have any real-world effect. Recorded as a deliberate,
  necessary scope narrowing (compiled `sandbox_world` instance stays untouched; shared catalog
  source content is in scope) in the reopened ticket's Out of Scope section.

## Anti-Drift Hazards
- Do not key the endurance check on the legacy `Faction` IntEnum bucket or on `region.kind`
  (region *type*) — proven wrong by the first pass's rejection.
- Do not implement race-level resolution in this ticket — document as extension point only.
- Do not author fiend/chaos-corruption content — illustrative only, test-fixture-only.
- Do not touch `src/world/calamity.py`, `data/worlds/sandbox_world/`, or the unrelated
  `camp_constructed` hunk in `docs/parity_ledger/world_dynamics.yaml`.
