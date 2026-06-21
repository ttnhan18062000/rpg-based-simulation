---
status: done
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42B-INFO-PROVIDER
phase: open
date: 2026-06-20
tags: [information-seeking, information-provider, archetype, phase-4]
---

# TCK-20260619-E42B-INFO-PROVIDER

## Title
Epic 4.2B · InformationProvider Archetypes

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No `InformationProvider` concept exists. This ticket creates the model, registers it in `AuthoritativeState`, and ensures providers can be seeded in scenario YAML via the content catalog.

**Requires:** TCK-20260619-E42A-INFO-NEED

## Scope

New file `src/domains/information/providers.py`:

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
```

Register in `AuthoritativeState` (`src/core/state.py`):
```python
information_providers: Dict[int, InformationProviderState] = field(default_factory=dict)
```

Update `to_canonical_dict()` on `AuthoritativeState` to include `information_providers` in sorted order.

## Acceptance Criteria
- `test_information_provider_registered_in_authoritative_state` passes
- `AuthoritativeState` serializes `information_providers` deterministically

## Related Tickets
- TCK-20260619-E42-INFO-SEEKING (parent epic)
- TCK-20260619-E42A-INFO-NEED (required)
- TCK-20260619-E42C-PAID-TRANSACTION (blocked on this)

## Related Code Areas
- `src/domains/information/providers.py` (new)
- `src/core/state.py` (AuthoritativeState — add information_providers field)

## Test Summary
```bash
pytest tests/unit/cognition/test_information_seeking.py::test_information_provider_registered_in_authoritative_state -x -v
```
## Files Changed
- `src/domains/information/providers.py` (NEW) — InformationProviderArchetype enum + InformationProviderState frozen dataclass with to_canonical_dict()
- `src/core/state.py` — Added TYPE_CHECKING import for InformationProviderState; added information_providers field to AuthoritativeState; wired into to_readonly() as ReadOnlyDict
- `tests/unit/cognition/test_information_seeking.py` — Added TestInformationProviderState class (6 tests)
- `docs/parity_ledger/substrate.yaml` — Added SUB-372 entry

## Completion Summary
Created InformationProviderArchetype (MERCHANT, GUILD_MASTER, ELDER) and InformationProviderState frozen dataclass in src/domains/information/providers.py. Registered information_providers: Dict[int, InformationProviderState] on AuthoritativeState with ReadOnlyDict wrapping in to_readonly(). All 18 tests pass (12 from E42A + 6 new E42B tests). Parity ledger entry SUB-372 added.
