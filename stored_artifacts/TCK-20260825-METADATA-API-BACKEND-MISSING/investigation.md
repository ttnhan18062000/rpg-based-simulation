---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260825-METADATA-API-BACKEND-MISSING
artifact_type: investigation
tags: [hud, content]
---

# Investigation — TCK-20260825-METADATA-API-BACKEND-MISSING

## Context scan
`mcp__knowledge-search__search_docs` and `graphify query` run first, per CLAUDE.md's mandatory
Context Scan. Surfaced `src/api/routes/manifest.py`/`src/api/presenters/manifest_presenter.py` as
the closest real structural precedent (a read-only, catalog-backed REST route with its own
presenter), and confirmed `frontend/src/contexts/MetadataContext.tsx`/
`frontend/src/types/metadata.ts` as the exact, already-specified contract to satisfy.

## Server-side source of truth for each of the 8 domains
Traced `CatalogRepository` (`src/content/repository.py`) field-by-field against
`frontend/src/types/metadata.ts`'s already-specified shapes. Real, populated backing data exists
for a solid majority of sub-fields; a real minority have **zero** backing data anywhere in this
codebase (confirmed via repo-wide grep, not assumed) — the ticket's own Assumptions section
anticipated exactly this ("some domains ... may need to report a partial result"), and per explicit
user decision this session, all 8 routes are built now: real data everywhere it exists,
correctly-shaped empty/defaulted data everywhere it doesn't, each decision documented inline in
`metadata_presenter.py` and summarized below (never fabricated content).

| Domain | Real backing | Notes |
|---|---|---|
| `enums.materials` | `catalog.materials` (id/name) | `walkable` has no corresponding static concept anywhere (walkability is a computed per-tile occupancy property, `LegalityServiceV2.verify_occupancy`) — defaulted `False` for every entry |
| `enums.ai_states` | none | `[]` |
| `enums.tiers` | none | `[]` (`CLASS_TIER_REGISTRY` exists but is per-class tier options, not a generic tier enum) |
| `enums.rarities` | derived from `catalog.items[*].rarity` | distinct real values actually used, not a separate registry |
| `enums.item_types` | derived from `catalog.items[*].categories[0]` | `ItemDefinition` has no discrete `item_type` field; first category tag used as the primary type per its own field docstring |
| `enums.damage_types` | none | `[]` |
| `enums.elements` | `catalog.elements` | real |
| `enums.entity_roles` | `src/core/enums.py::EntityRole` (real IntEnum, 6 members) | no description text exists anywhere — defaulted `""` |
| `enums.factions` | `catalog.factions` | real |
| `enums.faction_relations` | `catalog.faction_relationships` | real |
| `enums.entity_kinds` | `catalog.entity_archetypes` | same real source `ManifestPresenter.present_manifest`'s own `entity_kinds` field already uses |
| `items` | `catalog.items` (id/name/rarity/gold_value/item_type) | `ItemDefinition` has **no** combat-stat-bonus fields, `damage_type`, `element`, `heal_amount`, or `mana_restore` at all — every one of those defaulted to 0/""; `sell_value` reuses `base_value` (no separate sell-price concept exists) |
| `classes` | `src/core/classes.py::CLASS_REGISTRY` (id/name/starting_skills, 4 legacy entries — confirmed the only class registry anywhere) | nearly every other `ClassEntry` field (description/tier/role/lore/playstyle/attr_bonuses/cap_bonuses/scaling/breakthrough) has zero backing — defaulted; `skills`/`race_skills`/`scaling_grades`/`mastery_tiers`/`skill_targets` are all `[]`/`{}` |
| `traits` | `catalog.traits` | real; `trait_type` synthesized via the same stable-sorted-index convention `StatePresenter.terrain_code_map` already uses (no real numeric id exists) |
| `attributes` | `catalog.attributes` | real |
| `buildings` | `catalog.buildings` | real |
| `resources` | `catalog.resources` | real; `respawn_cooldown` has no corresponding `ResourceDefinition` field — defaulted 0 |
| `recipes` | `catalog.recipes` | real — confirmed (not assumed) via direct source read that `src/core/registries.py::RecipeRegistry` (the "actually-live crafting-execution path" `TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE` found) is itself bootstrapped from `CatalogToRecipeRegistryAdapter(catalog_repo).adapt()` — `catalog.recipes` **is** that same live source, count-verified: 25 entries both times |

## Numeric `id` contract vs. string catalog ids
`EnumEntry`/similar frontend types require `id: number`, but every real catalog definition's own id
is a string. This repo already has a precedent for exactly this situation:
`StatePresenter.terrain_code_map()` assigns `0..n-1` over the alphabetically-sorted distinct real
values, "so the same set always maps to the same codes regardless of dict insertion order." Reused
verbatim (`_enum_entries()` helper in `metadata_presenter.py`) rather than inventing a new
convention.

## A real bug found in `MetadataContext.tsx` — this ticket's own "already correct" claim was wrong
The ticket's Related Code Areas lists `frontend/src/contexts/MetadataContext.tsx` as "the caller,
already correct." Live-testing (see Test Summary) found this false: `fetchJson()` sends **no**
`X-API-Key` header at all, while `frontend/src/hooks/useSimulation.ts` already established the real
convention every other authenticated frontend fetch uses (module-level `API_KEY` from
`import.meta.env.VITE_API_KEY`, attached as `X-API-Key`). Since this ticket's own Scope explicitly
requires mounting the new routes with the same `require_admission` auth every other REST route
uses ("no special-casing"), every one of the 8 new routes would 401 for the real running app
without this fix. Confirmed by live-testing against a real backend + real Vite dev server before
the fix (401) and after (200) — not assumed. Fixed `MetadataContext.tsx`'s `fetchJson()` to attach
the header, mirroring `useSimulation.ts`'s exact convention. This is a minimal, necessary fix to the
*fetching* logic only — `frontend/src/types/metadata.ts` and the 4 consuming panel components
(explicitly out of scope) were not touched.

## Live verification (not skipped — see Test Summary)
Started a real backend (`python3 -m src serve --port 8000 --api-key-hashes ...`) and a real
frontend dev server (`npm run dev`, port 5173) and confirmed all 8 routes return real, non-empty,
correctly-shaped data through the exact real network path `MetadataContext.tsx` uses (via Vite's
`/api` dev proxy, with the real `X-API-Key` header). Wrote a new rendering test
(`LootPanel.metadata.test.tsx`) using a real response fixture captured live from the running
backend (`iron_sword` → "Iron Sword"/weapon/UNCOMMON/80g, matching `data/content/world/items.yaml`
directly) and confirmed `LootPanel` genuinely renders that real name/type/rarity/gold-value, not
the raw item id fallback.
