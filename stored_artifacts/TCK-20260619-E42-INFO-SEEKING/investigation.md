# Investigation — TCK-20260619-E42-INFO-SEEKING

## Summary

Passive belief/lead system exists and is solid. The key gap is _deliberate_ information seeking: entities currently receive leads passively but cannot decide to seek them out and pay for them. `UnknownFact` already models the "entity knows it doesn't know X" concept — this is the foundation `InformationNeed` should build on rather than duplicate.

## Key Findings

### What Already Exists

**LeadState** (`src/core/strategic.py:L187`):
```python
@dataclass(frozen=True, slots=True)
class LeadState:
    id: str
    kind: str  # 'location', 'object', 'event', 'person' — PERSON and CONCEPT leads missing
    subject: str
    detail: str = ""
    discovered_tick: int = 0   # staleness basis: current_tick - discovered_tick
    certainty: LeadCertainty   # VAGUE, APPROXIMATE, EXACT
    source_entity_id: Optional[int] = None
    tested: bool = False
    test_outcome: Optional[str] = None
    failure_count: int = 0
    suppression_until_tick: int = 0
```

`kind` already has 'person' as a valid string value — but `PERSON_LEAD` and `CONCEPT_LEAD` are not defined or filtered in any lead consumer. They need to be formally added to a `LeadKind` enum.

**UnknownFact** (`src/core/self_model.py:L65`):
```python
@dataclass(frozen=True, slots=True)
class UnknownFact:
    subject: str        # e.g. "material.moon_resin.source"
    reason: str         # "provider_partial", "never_queried", etc.
    recorded_tick: int = 0
```

This IS the `InformationNeed` concept. E42A should _extend_ UnknownFact rather than create a parallel model: add `seeking_project_id: Optional[str] = None` to link to a generated seeking project.

**KnowledgeFact** (`src/core/self_model.py:L49`):
```python
@dataclass(frozen=True, slots=True)
class KnowledgeFact:
    subject: str
    fact_type: str
    details: Dict[str, Any] = field(default_factory=dict)
    certainty: float = 1.0
    source_id: Optional[str] = None
    recorded_tick: int = 0   # staleness basis
```

Staleness = `current_tick - recorded_tick`. Confidence decay formula: `certainty * max(0.1, 1.0 - (current_tick - recorded_tick) * DECAY_RATE)` where `DECAY_RATE = 0.0001` (certainty halves over 5000 ticks).

**Belief system doc**: `docs/simulation/domains/belief_and_detour_contract.md` — has BeliefEntry model with `certainty` field. CONFIRM: BeliefEntry and KnowledgeFact are distinct (BeliefEntry is world-model beliefs; KnowledgeFact is factual domain knowledge like recipe/resource).

**Information contract doc**: `docs/simulation/domains/information_contract.md` — information domain: how beliefs are received, validated, contradicted, source trust updated.

**D01 audit** says [PARTIAL]: blockers are material-resource-only; leads are coordinate-only; no "ask guide/merchant"; no paid information.

### What Is Missing

1. `UnknownFact.seeking_project_id` field — link known-unknown to a generated project
2. `InformationProvider` archetype model: `provider_id`, `archetype` (MERCHANT/GUILD_MASTER/ELDER), `reliability_score`, `knowledge_age`, `knowledge_domains[]`
3. `paid_information` transaction via `ResourceTransferIntent` (gold transfer on lead purchase)
4. Lead contradiction: `belief_contradiction` event when entity arrives at location and finds state inconsistent with lead
5. `PERSON_LEAD`, `CONCEPT_LEAD` as `LeadKind` enum values (LeadState.kind is currently a raw string)
6. Knowledge staleness decay processor in cognition/belief update loop

### Architecture Note

`information_seeking` project kind must be added to `ProjectKind` enum in `src/core/strategic.py`. The project generation path: `UnknownFact detected → information_seeking ProjectState created → entity routes to InformationProvider entity → paid transaction → LeadState received → lead scored → route executed → outcome tested → if contradiction, `belief_contradiction` event, provider reliability_score decremented`.

The `paid_information` gold transfer must go through `ResourceTransferIntent` to satisfy conservation law (Chapter 03 economic laws).
