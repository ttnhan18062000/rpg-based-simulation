# Investigation — TCK-20260619-E53A-FACTION-AGENT

## What Exists

### Faction Enum (thin)
`src/core/enums.py` — `Faction(IntEnum)` with four values: HERO_GUILD(0), MONSTER_HORDE(1), TOWN_COUNCIL(2), NEUTRAL(3). Used only as a numeric tag on entity identity (`IdentityComponent.faction: int`). No durable per-faction state exists anywhere in the codebase.

### RegionState.owner_faction_id
`src/core/state.py:L220` — `owner_faction_id: Optional[int]` on `RegionState`. This is the only bridge between faction and territory today — a foreign-key reference with no corresponding FactionState to hang data on.

### FactionSocialMemory (campaigns domain)
`src/domains/campaigns/social_memory.py` — A per-faction hostility record for cross-episode persistence (E43D). This is a campaign-layer concept, NOT a tick-level durable model. It demonstrates the frozen-dataclass + to_dict/from_dict pattern but lives in a different layer and must not be confused with the tick-level `FactionState` this epic adds.

### FactionSemanticsService (content_semantics)
`src/content_semantics/faction.py` — A catalog-side service that resolves faction IDs from the content repository. Provides the faction identity layer (catalog facts) but no behavioral state.

### DirectiveState (core/strategic.py)
`src/core/strategic.py:L221` — Entity-level `DirectiveState(id, kind, target, priority, salience, created_tick)`. Lives inside `StrategicComponent.directives`. The `FactionDirective` introduced by E53Aa/E53Ab is a separate, faction-scoped struct that feeds into entity-level `DirectiveState` via E53Ac's propagation step.

### StrategicUpdate / directives_add_or_update
`src/core/updates.py:L485` — `StrategicUpdate.directives_add_or_update: list[DirectiveState]` is the authoritative mutation path for entity directives. Directive propagation in E53Ac must produce `EntityUpdate` objects carrying `StrategicUpdate` changes — not mutate state directly.

### WorldEmergencePhase pattern
`src/domains/world_emergence/phase.py` — The reference pattern for a domain phase: stateless static `execute(state, update, ...)` method, reads state, produces `StateUpdate` deltas, wired into the authoritative pipeline. `FactionDecisionPhase` should follow this pattern exactly.

### RESOURCE_DEPLETED event
`src/domains/world_emergence/schema.py:L19` — `WorldEventCategory.RESOURCE_DEPLETED`. Already emitted by `src/engine/economy.py` (lines 128, 215) and consumed by WorldEmergencePhase. Faction awareness (E53Ad) will consume the same event stream to increment `tension_level`.

### AuthoritativeState (state.py:L1003)
Current fields include: `entities`, `resource_nodes`, `regions`, `groups`, `local_scars`, etc. The `factions: Dict[str, FactionState]` field will slot in alongside `groups`. `AuthoritativeState` is `frozen=True` with `slots=True` — any new field requires explicit placement and `__post_init__` cache-reset consideration.

### GovernorPolicy (engine/policy.py)
`GovernorPolicy` is a frozen config dataclass — it does NOT contain a registry of phase classes. Phase registration happens in `src/engine/phases.py` via `get_authoritative_phases()` returning `TickPhase` enum members. `FactionDecisionPhase` must be wired into the engine via the pipeline, not via `GovernorPolicy`. The ticket's scope note "registered in GovernorPolicy" is imprecise — the correct insertion point is the authoritative pipeline configuration or a SystemCadence entry.

### TickPhase enum (engine/phases.py)
`TickPhase` is FROZEN by Phase 4 Baseline Freeze Contract. No new `TickPhase` entries may be added. `FactionDecisionPhase` must execute within an existing phase (most likely COLLECTION or RESOLUTION) as a domain sub-phase, similar to `WorldEmergencePhase`.

## What Is Needed

1. **FactionState durable model** — frozen dataclass in `src/core/state.py`, adjacent to `GroupRecord`. Fields per ticket scope. Includes `to_canonical_dict` / `from_dict` for JSON round-trip.
2. **AuthoritativeState.factions field** — `Dict[str, FactionState]` with `field(default_factory=dict)`.
3. **FactionDirective struct** — lightweight frozen dataclass (faction_id, directive_kind, target_faction, priority) produced by the decision phase. Likely lives in `src/engine/faction_decision.py` or `src/core/strategic.py`.
4. **FactionDecisionPhase** — stateless static `execute(state, recent_events)` class in `src/engine/faction_decision.py`. Wired into pipeline as a sub-phase within COLLECTION or as a cadenced call from `world_dynamics.py` / the engine loop.
5. **Directive propagation to entity scoring** — `AdventureRouteScorer` in `src/domains/adventure/scoring.py` reads `state.factions` to adjust urgency scores based on entity role and proximity to contested/allied regions.
6. **Faction tension update service** — reads `WorldEvent` list, filters `RESOURCE_DEPLETED` events in faction territory, produces `WorldUpdate` or a new `FactionUpdate` carrying `tension_level` delta, applied via the authoritative path.

## Key Architectural Decisions

### Decision 1: FactionState location
Place in `src/core/state.py` alongside `GroupRecord` (line ~514). This keeps all durable world models co-located and follows the existing pattern for state addition (E52A added `population_cohorts` to `RegionState` using the same file).

### Decision 2: TickPhase frozen — FactionDecisionPhase runs as sub-phase
`TickPhase` cannot be extended. `FactionDecisionPhase.execute()` should be called from within the existing engine loop, cadenced via `SystemCadence` (e.g. every N ticks), similar to how `WorldEmergencePhase` is invoked. The exact wiring point should be determined at implementation time by reading `src/engine/kernel.py` tick loop and `world_dynamics.py`.

### Decision 3: FactionDirective is not DirectiveState
`DirectiveState` is an entity-level concept. `FactionDirective` is a faction-level output that the propagation step (E53Ac) translates into `DirectiveState` updates on matching entities. These must remain distinct types.

### Decision 4: Tension update must go through authoritative path
`tension_level += 0.1` must be expressed as a typed update (e.g. `FactionUpdate.tension_delta`) applied via `ApplyPath`, not mutated directly. If `FactionUpdate` does not yet exist, it must be added to `src/core/updates.py` as part of E53Aa.

### Decision 5: faction IDs are strings (catalog-registered)
`FactionState.faction_id: str` should match the IDs in the catalog (`FactionSemanticsService` / `src/content_semantics/faction.py`). The existing `Faction(IntEnum)` enum is a numeric tag on entities; the new `FactionState` uses string IDs consistent with how other catalog entities (regions, resource nodes) are keyed.

## Risk Notes

- `AuthoritativeState` uses `slots=True` — adding a new field requires care around existing `field(default=None, repr=False, compare=False)` cache fields and `__post_init__`. Follow exact pattern of existing field additions (see E52A RegionState changes).
- The `docs/systems/grand_strategy.md` doc describes legacy behavior that must NOT be ported. Verify any reference to it is for concept-only orientation.
- `docs/systems/faction_contract.md` does not yet exist — it must be created as part of this epic's deliverables (likely in E53Ad or as a final step of E53Ac).
