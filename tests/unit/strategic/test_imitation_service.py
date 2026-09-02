import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.strategic import CognitionProfile
from src.content.repository import CatalogRepository
from src.content.schema import RaceDefinition
from src.content_semantics.faction import (
    configure_faction_semantics_service,
    reset_faction_semantics_service,
)
from src.strategy.role_model_imitation import RoleModelImitationService


@pytest.fixture
def race_catalog():
    repo = CatalogRepository()  # in-memory, no on-disk YAML load
    repo.races = {
        "test_race_high": RaceDefinition(
            id="test_race_high",
            body_model="standard_humanoid",
            need_profile="humanoid_survival",
            sense_profile="normal_humanoid_senses",
            cognition_profile="practical_humanoid",
            drive_profile="cautious_commoner",
            intelligence_tier="high",
        ),
        "test_race_low": RaceDefinition(
            id="test_race_low",
            body_model="quadruped_predator",
            need_profile="carnivore_survival",
            sense_profile="predator_smell_senses",
            cognition_profile="instinctive_animal",
            drive_profile="territorial_predator",
            intelligence_tier="low",
        ),
    }
    try:
        configure_faction_semantics_service(repo)
        yield repo
    finally:
        reset_faction_semantics_service()


def build_entity(entity_id: int, race_id):
    builder = V2EntityBuilder(entity_id).kind("hero").location(0, 0)
    if race_id is not None:
        builder = builder.identity(properties={"race_id": race_id})
    return builder.build()


def test_imitation_scaling_reads_intelligence_tier_high_vs_low(race_catalog):
    high_entity = build_entity(1, "test_race_high")
    low_entity = build_entity(2, "test_race_low")

    high_fidelity = RoleModelImitationService.compute_imitation_fidelity(high_entity)
    low_fidelity = RoleModelImitationService.compute_imitation_fidelity(low_entity)

    assert high_fidelity > low_fidelity
    assert high_fidelity == RoleModelImitationService.HIGH_TIER_FIDELITY
    assert low_fidelity == RoleModelImitationService.LOW_TIER_FIDELITY


def test_imitation_scaling_missing_race_or_tier_fails_safe(race_catalog):
    no_race_entity = build_entity(1, None)
    assert (
        RoleModelImitationService.compute_imitation_fidelity(no_race_entity)
        == RoleModelImitationService.DEFAULT_FIDELITY
    )

    unresolved_race_entity = build_entity(2, "does_not_exist")
    assert (
        RoleModelImitationService.compute_imitation_fidelity(unresolved_race_entity)
        == RoleModelImitationService.DEFAULT_FIDELITY
    )


def test_capacity_service_signature_unchanged_by_role_model_fork():
    field_names = {f.name for f in dataclasses.fields(CognitionProfile)}
    assert field_names == {
        "max_active_projects",
        "max_leads",
        "max_concerns",
        "max_candidate_zones",
        "max_hypotheses",
        "max_turning_points",
        "interruption_resistance",
        "resistance_multiplier",
        "detour_breadth",
        "reserved_detour_depth",
        "max_committed_intentions",
    }
