"""
tests/unit/domains/progression/test_progression_decision_canonical_hash.py

TCK-20260830-HOTFIX-PROGRESSION-DECISION-CANONICAL-HASH-CRASH

Regression coverage: ProgressionConversionPhase.execute() must produce a
`last_progression_decision` property_update that survives a full canonical-hash pass
(CanonicalStateHasher.get_hash()) without raising TypeError. Prior to the fix, the raw
ProgressionDecisionResult dataclass was stored directly into property_updates, and
CanonicalStateHasher.to_canonical_json() calls plain json.dumps() with no custom encoder --
this crashed deterministically the first time ENABLE_PROGRESSION_EVOLUTION ran through a
real Kernel loop (see stored_artifacts/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION).
"""
from __future__ import annotations

import json
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, ReadOnlyDict
from src.core.updates import StateUpdate
from src.domains.progression.phase import ProgressionConversionPhase
from src.engine.checkpoint import CanonicalStateHasher


def _state_with_progression_decision_applied() -> AuthoritativeState:
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True))
    entity = b.build()

    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    refined_update = ProgressionConversionPhase.execute(state, StateUpdate())

    entity_update = refined_update.entity_updates[1]
    assert "last_progression_decision" in entity_update.property_updates

    merged_properties = dict(entity.identity.properties)
    merged_properties.update(entity_update.property_updates)
    updated_entity = replace(
        entity,
        identity=replace(entity.identity, properties=ReadOnlyDict(merged_properties)),
    )
    return replace(state, entities={1: updated_entity})


def test_progression_decision_survives_canonical_hash():
    updated_state = _state_with_progression_decision_applied()

    canonical_json = CanonicalStateHasher.to_canonical_json(updated_state)

    decoded = json.loads(canonical_json)
    decision_dict = decoded["entities"]["1"]["properties"]["last_progression_decision"]
    assert isinstance(decision_dict, dict)
    assert set(decision_dict.keys()) >= {"entity_id", "selected", "trace", "reason"}
    assert decision_dict["entity_id"] == 1


def test_progression_decision_get_hash_does_not_raise():
    updated_state = _state_with_progression_decision_applied()

    hash_value = CanonicalStateHasher.get_hash(updated_state)

    assert isinstance(hash_value, str)
    assert len(hash_value) == 64
