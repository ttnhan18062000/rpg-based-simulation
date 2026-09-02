---
status: authoritative
layer: systems
authority: P1
audience: agent
last_verified: 2026-09-01
tags: [content, semantics, contract, compile-time]
---

# Content Semantics Contract

`src/content_semantics/` provides **advisory compile-time semantic defaults** derived from the content catalog. It is **not authoritative simulation state** — nothing in this layer participates in the `AuthoritativeState` hash or the tick-path resolution pipeline.

The Compliance ID namespace for this subsystem is **WORLD-SEM-\***.

---

## Authoritative Status

**NOT authoritative.** This layer is consumed at world-building / compilation time, not during simulation ticks. It bridges the catalog (static YAML) to the compiler and world assembly pipeline by providing typed semantic lookups.

---

## Purpose and Usage

`content_semantics` services answer three classes of questions:

1. **Legacy mapping** — translate catalog string IDs to legacy enum values (Faction enum, EntityRole enum) for backward-compatible code paths.
2. **Relationship projection** — project a relationship label between two factions given context (distance, location, combat state).
3. **Compile defaults** — provide numeric fallback values when a specific profile is absent from the catalog.

All services are instantiated with a loaded `CatalogRepository`. They hold no mutable simulation state.

---

## FactionSemanticsService (`src/content_semantics/faction.py`)

Compliance IDs: WORLD-SEM-001 (faction.py:1), WORLD-SEM-002 (faction.py:1).

**Singleton pattern:** `get_faction_semantics_service()` maintains a process-level singleton (`_semantics_service_cache`). The cache is populated on first call using `ContentPathConfig().content_root` and `CatalogRepository.load_all()`.

- `configure_faction_semantics_service(repo)` — installs a pre-built service into the cache (use in app boot and test setup).
- `reset_faction_semantics_service()` — clears the cache (use in test teardown).

**What it provides:**
- `get_legacy_faction_bucket(faction_id)` → `Faction` enum — translates dynamic catalog faction ID to the legacy integer enum. Falls back to `Faction.NEUTRAL` if ID not found.
- Hostility and protection queries — whether faction A treats faction B as hostile.

**Faction ID resolution priority:**
1. `entity.identity.properties["faction_id"]` (dynamic catalog ID string)
2. `entity.identity.faction` (legacy Faction enum or int)
3. Returns `"neutral"` as final fallback (`get_faction_id_str`)

---

## RelationProjectionService (`src/content_semantics/relation.py`)

Compliance IDs: WORLD-SEM-003 (relation.py:1), WORLD-SEM-004 (relation.py:1).

Projects a relationship label between two factions using catalog `PerspectiveDefinition` and `FactionRelationshipDefinition` records. If `source_race`/`target_race` are both set and a matching `RaceRelationRecord` (`social/race_relations.yaml`) exists, its `axes.hostility` may upgrade (never downgrade) the resolved label, gated off for same-faction pairs to preserve the Friendly Fire law.

**Projection contract:**
- Input: `perspective_id`, `source_faction_id`, `target_faction_id`, optional `RelationContext`
- Output: `RelationProjection` with `label` (string), `axes` (Dict[str, str]), `confidence` (float 0–1), `relationship_model`, `source_records` (list of catalog IDs used)

**RelationContext fields** (all optional): `distance`, `location`, `intruding`, `combat_engaged`, `target_race`, `source_race`.

**Fallback:** If no matching perspective or faction relationship is found, returns a default neutral projection with `confidence=0.0`.

---

## RoleSemanticsService (`src/content_semantics/role.py`)

Compliance IDs: WORLD-SEM-003 (role.py:1), WORLD-SEM-004 (role.py:1).

Maps dynamic catalog role IDs to legacy `EntityRole` enum values and provides profile lookups.

**What it provides:**
- `get_legacy_entity_role(role_id)` → `EntityRole` — maps catalog role ID → legacy enum via `RoleDefinition.legacy_engine_role`. Falls back to keyword matching on the role_id string: HERO → EntityRole.HERO, SHOP/STORE → SHOPKEEPER, MONSTER → MONSTER, CITIZEN/CIVILIAN → CITIZEN, WORKER/PEASANT → WORKER, GUARD → GUARD. Final fallback: `EntityRole.CITIZEN`.
- `get_role_family(role_id)` → str — returns `RoleDefinition.role_family` or `"civilian"` if not found.
- `get_default_stats_profile(role_id)` → Optional[str] — returns `RoleDefinition.default_stats_profile` or `None`.

**Real, structural caveat** (`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`): this
service's own real, catalog-aware lookup is only ever reached at compile time via
`WorldCompiler.compile()`'s own local `get_role_enum()`/`get_faction_enum()` helpers
(`src/worldbuilding/compiler.py`) when a `CompileContext` with a pre-populated `legacy_roles`/
`legacy_factions` mapping is passed in — `WorldCompiler.compile()` has no `catalog_repo`
parameter of its own and cannot call `RoleSemanticsService` directly. Real archetype role_ids
like "predator_hunter"/"raider"/"scout" almost never literally contain the keyword-fallback's
own matched substrings, so a caller that omits `context` silently gets the naive fallback's
default (`EntityRole.CITIZEN`), not a real catalog lookup. Use
`WorldRepository.load_world_with_context()` (not `load_world()`) when compiling a world whose
`entity.identity.role`/`.faction` values need to be correct.

---

## DefaultSemanticsService (`src/content_semantics/defaults.py`)

Compliance IDs: WORLD-SEM-005 (defaults.py:1), WORLD-SEM-006 (defaults.py:1).

Provides numeric compile-time defaults in four categories. Falls back to hardcoded constants if `repo.defaults` is empty.

| Method | What it returns | Hardcoded fallback |
|---|---|---|
| `get_entity_combat_defaults()` | hp, max_hp, atk, def, attack_range, readiness | hp=100, max_hp=100, atk=10, def=0, range=1, readiness=100.0 |
| `get_building_durability_defaults()` | hp, max_hp | hp=500, max_hp=500 |
| `get_resource_harvest_defaults()` | required_ticks | required_ticks=10 |
| `get_faction_vault_defaults()` | starting_gold | starting_gold=1000.0 |

Source: first `DefaultCompileProfile` record found in `repo.defaults`. If `repo.defaults` is empty, hardcoded values apply.

**Usage:** Called by the world compiler when a specific profile is not assigned to an entity or building. These values are baked into compiled world state — not applied at runtime.

---

## Compliance ID Index

| ID | Source file | Line | Description |
|---|---|---|---|
| WORLD-SEM-001 | src/content_semantics/faction.py | 1 | FactionSemanticsService contract |
| WORLD-SEM-002 | src/content_semantics/faction.py | 1 | Faction singleton pattern contract |
| WORLD-SEM-003 | src/content_semantics/relation.py | 1 | RelationProjectionService contract |
| WORLD-SEM-004 | src/content_semantics/role.py | 1 | RoleSemanticsService contract |
| WORLD-SEM-005 | src/content_semantics/defaults.py | 1 | DefaultSemanticsService contract |
| WORLD-SEM-006 | src/content_semantics/defaults.py | 1 | Hardcoded fallback defaults contract |
