# Plan — TCK-20260619-E42-INFO-SEEKING

## Approach

Build the `information_seeking` project kind by extending existing UnknownFact + LeadState. Introduce InformationProvider as a new entity archetype attribute. Wire paid transactions through ResourceTransferIntent.

## Sequence

**E42A → E42B → E42C → E42D → E42E** (strictly sequential; each depends on prior)

---

## E42A · InformationNeed from UnknownFact

**Extend** `UnknownFact` (`src/core/self_model.py:L65`) with:
```python
seeking_project_id: Optional[str] = None   # link to generated ProjectState
priority: float = 0.0                       # how urgently the gap matters
```

Add `information_seeking` to `ProjectKind` enum in `src/core/strategic.py`.

New `InformationNeedDetector` in `src/engine/domain/cognition_extras.py`:
- Scans `KnowledgeModelComponent.unknown_facts`
- For facts where `seeking_project_id is None` and `priority > 0.5`: generate a new `ProjectState(kind=ProjectKind.INFORMATION_SEEKING, ...)`
- Returns `StrategicUpdate(projects_add=[new_project], unknown_facts_update={fact_subject: extended_fact})`

---

## E42B · InformationProvider Archetypes

**New file** `src/domains/information/providers.py`:

```python
class InformationProviderArchetype(str, Enum):
    MERCHANT = "MERCHANT"
    GUILD_MASTER = "GUILD_MASTER"
    ELDER = "ELDER"

@dataclass(frozen=True, slots=True)
class InformationProviderState:
    entity_id: int
    archetype: InformationProviderArchetype
    reliability_score: float = 1.0          # degrades on belief_contradiction
    knowledge_domains: Tuple[str, ...] = () # e.g. ("resource_source", "faction_tension")
    knowledge_age: int = 0                  # ticks since knowledge was last updated
```

Register `InformationProviderState` in `AuthoritativeState` as `information_providers: Dict[int, InformationProviderState] = field(default_factory=dict)`.

---

## E42C · Paid Transaction + Lead Quality

When entity executing `information_seeking` project reaches an `InformationProvider`:

1. Compute `transaction_cost: int` = base 10 gold × (1.0 / provider.reliability_score)
2. Emit `ResourceTransferIntent(source_kind="INFORMATION_PURCHASE", gold_delta=-transaction_cost, target_entity_id=provider.entity_id)`
3. On accepted: generate `LeadState(kind=lead_kind, certainty=quality_to_certainty(provider.reliability_score), ...)`
4. Lead quality: `reliability ≥ 0.8 → EXACT`, `0.5-0.8 → APPROXIMATE`, `< 0.5 → VAGUE`

---

## E42D · Lead Contradiction + Replanning

When entity arrives at lead destination and finds state inconsistent (resource depleted, entity dead, faction hostile):

1. Emit `SimulationEvent(kind="belief_contradiction", entity_id=..., payload={lead_id, provider_id})`
2. Decrement `InformationProviderState.reliability_score -= 0.1` via `StateUpdate`
3. Mark `LeadState.test_outcome = "FAILURE"` and increment `failure_count`
4. Generate new `InformationNeed` (seeking_project) to re-find the resource/entity

---

## E42E · PERSON and CONCEPT Lead Types

Add `LeadKind` enum to `src/core/strategic.py`:
```python
class LeadKind(str, Enum):
    LOCATION = "location"
    OBJECT = "object"
    EVENT = "event"
    PERSON = "person"
    CONCEPT = "concept"
```

Migrate `LeadState.kind` from `str` to `LeadKind`. Add `CONCEPT_LEAD` routing: entity seeks out entities with domain knowledge matching the concept (e.g., "alchemy_recipe" → seeks GUILD_MASTER with `"recipe_definition"` in `knowledge_domains`).

After E42E: update `docs/simulation/domains/belief_and_detour_contract.md` and `docs/simulation/domains/information_contract.md`. Update `docs/parity_ledger/strategic_cognition.yaml`. Run `make knowledge-index-update`.
