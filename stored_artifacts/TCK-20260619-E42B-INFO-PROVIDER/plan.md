---
status: active
artifact_type: plan
ticket_id: TCK-20260619-E42B-INFO-PROVIDER
date: 2026-06-21
---

# Plan — TCK-20260619-E42B-INFO-PROVIDER

## Summary

Create `InformationProviderArchetype` enum and `InformationProviderState` frozen dataclass
in a new file `src/domains/information/providers.py`. Register `information_providers` field
on `AuthoritativeState` in `src/core/state.py`, wired into `to_readonly()` as a `ReadOnlyDict`.
Add acceptance-criterion test to `tests/unit/cognition/test_information_seeking.py`.

## File Changes

### 1. NEW: `src/domains/information/providers.py`

```python
class InformationProviderArchetype(str, Enum):
    MERCHANT = "MERCHANT"
    GUILD_MASTER = "GUILD_MASTER"
    ELDER = "ELDER"

@dataclass(frozen=True, slots=True)
class InformationProviderState:
    entity_id: int
    archetype: InformationProviderArchetype
    reliability_score: float = 1.0
    knowledge_domains: Tuple[str, ...] = ()
    knowledge_age: int = 0

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "archetype": self.archetype.value,
            "reliability_score": self.reliability_score,
            "knowledge_domains": list(self.knowledge_domains),
            "knowledge_age": self.knowledge_age,
        }
```

### 2. MODIFY: `src/core/state.py`

Add TYPE_CHECKING import for `InformationProviderState` (avoids circular import).
Add field on `AuthoritativeState`:
```python
information_providers: Dict[int, InformationProviderState] = field(default_factory=dict)
```
Add to `to_readonly()` `replace()` call:
```python
information_providers=ReadOnlyDict(self.information_providers),
```

### 3. MODIFY: `tests/unit/cognition/test_information_seeking.py`

Add test class `TestInformationProviderState` covering:
- Model construction and defaults
- Archetype enum values
- `to_canonical_dict()` output
- Registration in `AuthoritativeState`
- Frozen immutability

## Architecture Review

- All durable state via frozen typed records: `InformationProviderState(frozen=True, slots=True)` ✓
- No direct state writes: field is registered as default empty dict, populated via AuthoritativeState replace() ✓
- Determinism: `to_canonical_dict()` uses sorted/stable fields; `knowledge_domains` is Tuple ✓
- No raw domain models from API: `InformationProviderState` is the typed record, not an entity ✓
- `to_readonly()` wraps in `ReadOnlyDict` ✓
