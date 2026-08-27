---
status: idea
layer: core
authority: P2
audience: developer
maturity: idea
date: 2026-06-20
tags: [idea, entity-index, semantic-search, information-seeking, performance, spatial-query]
---

# Idea: Semantic Entity Index for World Queries

> **Superseded (2026-08-26):** implemented by `TCK-20260822-SEMANTIC-ENTITY-INDEX`
> (`src/engine/semantic_entity_index.py`, `SemanticEntityIndexes`/`SemanticEntityIndexService`/
> `SemanticEntityQuery`) as a lazy, pull-based, `CacheInvalidationPolicy`-driven derived index
> mirroring `WorldIndexService` -- not the eager Persistence-phase write this doc originally
> proposed (see `docs/engine/performance_contract.md`'s "Semantic Entity Indexes" subsection for the
> shipped lifecycle). Retrofitting `paid_information.py`/faction call sites onto the new index
> remains unscheduled (`TCK-20260822-PAID-INFO-INDEX-RETROFIT`,
> `TCK-20260822-GUARD-SCAN-INDEX-RETROFIT`).

> **Maturity: IDEA** — Not scheduled. Must precede E42 Information Seeking and E53 Faction Diplomacy at scale.

> **Status review (2026-08-22):** re-investigated for staleness. E42 and E53 both shipped DONE within 2 days
> of this idea being raised (2026-06-21/22) — before this doc could be acted on. Neither defined the
> `ProviderLocator`/`TerritorialObserver` interfaces this doc recommended as the drop-in seam (confirmed:
> zero hits repo-wide for either name). The O(N)/O(N×M) scan cost this doc warned about shipped exactly as
> predicted and is still live today: `src/api/... paid_information.py:92,112` — a nested
> `for entity in sorted(state.entities.values()...)` × `for pid in sorted(providers.keys())` scan, sorted
> for determinism, no index. **This changes the recommendation, not just the facts**: retrofitting the
> index now means touching the already-shipped consumer call sites directly (`paid_information.py`,
> `src/domains/faction/`) rather than substituting behind an interface those tickets never built — a bigger,
> riskier change than "drop-in upgrade" as originally framed below.
>
> Separately, `docs/engine/performance_contract.md` §7 documents a `scan_policy`
> (`FULL`/`THROTTLED`/`EXACT_DIRTY`) + `DirtySet` mechanism that exists engine-wide as a generic
> mitigation for O(N) scan cost under pressure. It doesn't replace a semantic index (it doesn't provide
> role/region/faction-keyed lookup) — and, re-verified 2026-08-22, it does not currently gate the
> `paid_information.py` hotspot at all: `src/engine/pipeline_phases/paid_information.py` has zero
> references to `scan_policy` or `DirtySet` anywhere in the file. The nested scan at lines 92/112 runs
> unconditionally every tick regardless of `RuntimeMode` or dirty state, so today's `scan_policy`/`DirtySet`
> mechanism is engine-wide precedent that this call site could adopt, not an applied fix already in place
> at this call site.
>
> The `MOVEMENT_STRESS_100_ACTORS` benchmark scenario cited in an earlier revision of this note is not a
> real wired scenario: `src/perf/scenarios.py`'s `SCENARIO_BUILDERS` registers only `idle`, `movement`,
> `resource`, `combat`, `strategic`, `mixed`, `metropolis` (each parameterized by `entity_count`, not a
> fixed 100-actor preset), and a repo-wide grep finds zero hits for `MOVEMENT_STRESS_100_ACTORS` in
> `src/perf/scenarios.py` or `tests/` — it exists only as a name referenced in doc prose
> (`docs/engine/performance_contract.md`, `docs/performance/perf_baseline_policy.md`), not as code. No
> verified current benchmark scale is available to compare against this doc's own "acceptable at 10-30,
> degrades as it scales" framing — treat that framing as still open, not confirmed either way.
>
> A ticket scoping this should target the retrofit shape (index built against real shipped call sites,
> reconciled with the existing `scan_policy`/`DirtySet` mitigation), not the original "define the interface
> in E42/E53 first" plan in the sections below, which is no longer available.
>
> **Known follow-up, not fixed here:** `CacheInvalidationPolicy.invalidated_indexes()`
> (`src/engine/world_index.py`) adds `"region_index"` to its invalidation set whenever `dirty.region_ids`
> is populated, and `should_invalidate("regions", ...)` checks for that same key — but `WorldIndexes` (same
> file) has no `region_index` field, and `WorldIndexService.get_indexes()` never calls
> `should_invalidate("regions", ...)` in the first place. The unit test
> (`tests/unit/domains/optimization/test_cache_invalidation_policy.py::test_region_dirty_invalidates_region_index`)
> passes because it only asserts set membership, not that a corresponding index field exists. This is
> dead/phantom-field code unrelated to the semantic-index gap this doc tracks — flagged here for a separate
> future ticket, intentionally not fixed in this pass.

---

## Problem

The engine has no structured index over live entity state. Every query — "find all merchants within 5 regions", "find entities with gold > N", "find faction representatives near a contested border" — requires an O(N) linear scan over all entities in the world state. For small worlds (10–30 entities) this is acceptable. As E42 and E53 scale entity counts and query frequency, the cost compounds:

- **E42 Information Seeking** introduces `InformationProvider` archetypes (MERCHANT, GUILD_MASTER, ELDER) that entities query for knowledge. Each tick, every `InformationNeed`-holding entity must find the nearest relevant provider — a query the engine currently cannot answer without scanning all entities.
- **E53 Faction Diplomacy** introduces `FactionDecisionPhase` running at the governance layer. Faction awareness requires observing which entities are near contested borders and which resource nodes are depleted in faction territory — again O(N) per faction per tick.

These are not hypothetical future loads. E42 and E53 are both planned for Phase 2 of the roadmap. Without an index, their governance-phase steps will degrade quadratically as world size grows.

---

## Idea

Build a **Semantic Entity Index** — a maintained, queryable projection of live entity state that supports fast lookup along the dimensions most queried by the engine's strategic and governance layers.

### Index dimensions

| Dimension | Query type | Use case |
|---|---|---|
| `role + class_id` | "All MERCHANT entities" | E42: find InformationProviders by archetype |
| `region_id` | "All entities in Region A" | E53: faction territorial awareness |
| `faction` | "All HERO_GUILD entities near border" | E53: military strength assessment |
| `entity_needs` | "Entities with unsatisfied needs for N ticks" | E23: QuestOpportunityGenerator trigger |
| `knowledge_domain` | "Entities with knowledge of resource locations" | E42: route InformationNeeds to providers |

### Index lifecycle

The index is **maintained incrementally**, not rebuilt each tick. Updates are triggered by authoritative state mutations:
- Entity spawned/despawned → insert/remove from all dimensions
- Entity moves to new region → update `region_id` bucket
- Entity need state changes → update `entity_needs` bucket
- Entity knowledge updated → update `knowledge_domain` bucket

Updates are applied in the `Persistence` phase, after the authoritative pipeline commits. The index is **not** authoritative state — it is a derived projection, equivalent to a database index. It can always be rebuilt from entity state.

### Query API

```python
# O(1) lookup
entity_index.by_role_class(role="MERCHANT", class_id="MERCHANT")
entity_index.by_region(region_id="northern_wastes")
entity_index.by_faction(faction=Faction.HERO_GUILD)

# O(k) range query
entity_index.by_region_and_role(region_id="northern_wastes", role="HERO")

# Combined (join two dimensions)
entity_index.filter(faction=Faction.MONSTER_HORDE, region_id="border_zone_3")
```

All queries return `List[entity_id]` — never raw entity state. Callers dereference through the authoritative world state. The index holds only IDs and indexed attribute values.

### Determinism constraint

Index contents must be deterministically reproducible from the same authoritative world state. The index itself does not participate in tick computation — it is read-only during resolution. Writes happen only in `Persistence`. This satisfies the replay determinism requirement.

---

## Relationship to Planned Tickets

### E42-INFO-SEEKING (performance dependency) — historical, E42 shipped DONE 2026-06-21 without the recommended interface

E42 plans: *"InformationNeed as first-class belief state; InformationProvider archetypes: MERCHANT, GUILD_MASTER, ELDER — each with `reliability_score` and `knowledge_age`; can answer queries about resource locations, faction tensions, entity whereabouts."*

Each entity with an `InformationNeed` must find the most relevant `InformationProvider` — filtered by archetype, reliability, and proximity. With O(N) scanning, this query runs once per entity per tick. In a 50-entity world with 20 entities holding `InformationNeed`, that is 20 × 50 = 1,000 entity comparisons per tick, every tick.

A role+class+region index reduces this to O(k) where k is the count of providers in the relevant region — typically 1–5.

**Impact on E42**: performance dependency, not a blocker. E42 can ship with O(N) scans for initial correctness. But the `InformationNeed` lookup should be isolated behind a `ProviderLocator` interface from the start, so the index can be substituted later without changing E42's behavioral logic.

**Recommendation**: E42 should define the `ProviderLocator` interface. The semantic index implements it. This makes the index a drop-in upgrade, not a refactor.

### E53-FACTION-DIPLOMACY (performance dependency) — historical, E53 shipped DONE 2026-06-22 without the recommended interface

E53 plans: *"Faction awareness: factions observe world events (resource depletion, calamity, entity deaths) and update tension levels; `FactionDecisionPhase`: runs at governance layer; produces faction-level directives (expand territory, seek alliance, respond to threat)."*

Specifically, Phase A of E53 includes: *"Faction directives propagate to entity scoring: GUARD entities near contested border score patrol routes higher; MERCHANT near allied region scores trade routes higher."*

Computing "GUARD entities near contested border" requires: for each faction, for each contested border region, find all GUARD entities in adjacent regions. With O(N) scans, this runs per-faction per-border per-governance-tick. With 4 factions and 8 contested borders, that is 32 full entity scans per governance tick.

A faction+region index reduces each lookup to O(k) — the number of GUARD entities near that specific border.

**Impact on E53**: same pattern as E42. E53 Phase A should define a `TerritorialObserver` interface that `FactionDecisionPhase` calls. The semantic index implements it.

**Risk level: MEDIUM.** E53 will work without the index but will not scale to large worlds. The `FactionDecisionPhase` governance step will become the dominant cost at >50 entities per world.

---

## Open Questions

- Should the index be an in-memory hash map (simple, fast) or a sorted structure (supports range queries like "entities within N hops")?
- Does `knowledge_domain` indexing require the full `InformationProvider.knowledge_age` attribute, or just the domain type?
- What is the rebuild cost if the index becomes inconsistent (e.g., after a bug)? Is a full rebuild each session start acceptable as a safety net?
- Should the index be serialized to disk as part of world state save/load, or always rebuilt from authoritative entity state on load?

---

*Raised: 2026-06-20. Performance debt before E42 and E53; recommend defining provider/observer interfaces in those tickets to enable drop-in index substitution later.*
