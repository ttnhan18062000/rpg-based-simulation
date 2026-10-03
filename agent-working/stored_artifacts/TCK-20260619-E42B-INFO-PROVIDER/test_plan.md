---
status: active
artifact_type: test_plan
ticket_id: TCK-20260619-E42B-INFO-PROVIDER
date: 2026-06-21
---

# Test Plan — TCK-20260619-E42B-INFO-PROVIDER

## Acceptance Criterion Test

`tests/unit/cognition/test_information_seeking.py::test_information_provider_registered_in_authoritative_state`

Verifies:
1. `InformationProviderState` can be constructed with all fields.
2. `AuthoritativeState` has an `information_providers` field (default empty dict).
3. An `InformationProviderState` can be stored in `information_providers` on a live state.
4. `InformationProviderState.to_canonical_dict()` returns a deterministic dict.

## Additional Tests

### Normal Flow
- `test_information_provider_state_defaults` — reliability_score=1.0, knowledge_domains=(), knowledge_age=0
- `test_information_provider_archetype_values` — MERCHANT, GUILD_MASTER, ELDER values match spec
- `test_information_provider_to_canonical_dict_sorted_knowledge_domains` — verifies tuple is rendered in canonical form

### Edge Cases
- `test_information_providers_serializes_deterministically` — two states with same providers produce identical dicts when serialized in sorted key order
- `test_authoritative_state_information_providers_defaults_empty` — fresh AuthoritativeState has empty information_providers

### Architecture
- `test_information_provider_state_is_frozen` — frozen=True prevents mutation
- `test_information_provider_state_importable_from_providers` — import path is correct

## Test Command
```bash
pytest tests/unit/cognition/test_information_seeking.py -x -v -k "provider"
```

Full file run (including E42A tests):
```bash
pytest tests/unit/cognition/test_information_seeking.py -x -v
```
