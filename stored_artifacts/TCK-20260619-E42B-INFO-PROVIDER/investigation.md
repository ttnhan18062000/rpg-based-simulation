---
status: active
artifact_type: investigation
ticket_id: TCK-20260619-E42B-INFO-PROVIDER
date: 2026-06-21
---

# Investigation — TCK-20260619-E42B-INFO-PROVIDER

## Prerequisite Status

TCK-20260619-E42A-INFO-NEED is DONE (`tickets/done/TCK-20260619-E42A-INFO-NEED.md`).
`ProjectKind.INFORMATION_SEEKING` and `ObjectiveKind.ASK_INFORMATION` are confirmed
present in `src/core/strategic.py` (lines 94, 129).

## Existing Information Domain

`src/domains/information/` contains: `assimilation.py`, `bridge.py`, `contradiction.py`,
`normalizer.py`, `phase.py`, `resolver.py`, `route_impact.py`, `router.py`, `schema.py`,
`trust.py`. No `providers.py` exists yet.

`src/domains/information/schema.py` defines `InformationSourceProfile`, `InformationSourceKind`,
`NormalizedInformationResponse`, etc. — these are query/response schemas for the existing
information routing system. The new `InformationProviderState` is durable world state
(registered in AuthoritativeState), distinct from the ephemeral `InformationSourceProfile`
used in the information pipeline.

## AuthoritativeState Analysis

`AuthoritativeState` is defined at line 999 of `src/core/state.py`. It does NOT have its own
`to_canonical_dict()` method — the method is on per-component dataclasses and on `EntityState`.
The ticket's reference to "update to_canonical_dict()" is interpreted as: add a
`to_canonical_dict()` method directly to `InformationProviderState` (consistent with all
other state models in state.py), and ensure the `information_providers` field on
`AuthoritativeState` is serializable deterministically (sorted by entity_id).

The `StateFingerprinter` in `src/replay/fingerprint.py` is the component that serializes
`AuthoritativeState` for replay. The `information_providers` field should also be added to
`to_readonly()` as a `ReadOnlyDict`.

## Patterns from Existing State

- `quest_registry: Dict[str, QuestOpportunity]` — TYPE_CHECKING import pattern (line 12)
- `groups: Dict[int, GroupRecord]` — frozen in `to_readonly()` with `shallow_freeze()`
- New dicts with typed-record values use `ReadOnlyDict(...)` in `to_readonly()`

## Determinism

`information_providers` is `Dict[int, InformationProviderState]`, keyed by `entity_id` (int).
Serialization must sort by key. `InformationProviderState` needs a `to_canonical_dict()` method
for deterministic serialization. `knowledge_domains: Tuple[str, ...]` is already ordered/frozen.

## Test Location

`tests/unit/cognition/test_information_seeking.py` — existing file for E42A tests.
The acceptance-criterion test `test_information_provider_registered_in_authoritative_state`
must be added here (it does not exist yet).
