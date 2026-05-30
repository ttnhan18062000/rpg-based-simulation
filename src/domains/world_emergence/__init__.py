"""
src/domains/world_emergence/__init__.py
───────────────────────────────────────────────────────────────────────────────
Phase 8 — World Emergence Domain Package.
"""

from __future__ import annotations
from src.domains.world_emergence.schema import (
    WorldEventCategory, WorldEvent, WorldEventAggregate, RegionalPressure,
    ResourceScarcitySignal, WorldOpportunityPressure, QuestSeed, RumorSeed,
    ServicePressure, WorldEmergenceResult
)
from src.domains.world_emergence.aggregators import WorldEventAggregator
from src.domains.world_emergence.models import RegionalPressureModel, ScarcityModel, ServiceStatePressureModel
from src.domains.world_emergence.services import (
    WorldOpportunityPressureService, DynamicQuestSeedService, RumorSeedService, WorldToEntitySignalBridge
)
from src.domains.world_emergence.phase import WorldEmergencePhase
