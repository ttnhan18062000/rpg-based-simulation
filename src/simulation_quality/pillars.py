from __future__ import annotations
from enum import Enum
from typing import Any


class PillarId(str, Enum):
    COGNITION = "COGNITION"
    AGENCY = "AGENCY"
    COMBAT = "COMBAT"
    FACTION = "FACTION"
    ECONOMY = "ECONOMY"
    PROGRESSION = "PROGRESSION"
    SOCIAL = "SOCIAL"
    INFORMATION = "INFORMATION"
    WORLD = "WORLD"
    NARRATIVE = "NARRATIVE"


PILLAR_METADATA: dict[str, dict[str, Any]] = {
    PillarId.COGNITION: {
        "name": "Cognition",
        "description": "Belief systems, knowledge quality, subjective decision-making",
        "phase_anchors": ["PP-03", "PP-04", "PP-30"],
        "d01_tier": "Tier 1 (23/25)",
    },
    PillarId.AGENCY: {
        "name": "Agency & Action",
        "description": "Adventure routing, action execution, behavioral entropy",
        "phase_anchors": ["PP-12", "PP-13", "PP-14", "PP-15", "PP-30"],
        "d01_tier": "Tier 1 (24/25)",
    },
    PillarId.COMBAT: {
        "name": "Combat",
        "description": "Entity-level engagement, attrition balance, lifecycle",
        "phase_anchors": ["PP-16", "PP-31", "PP-33"],
        "d01_tier": "Tier 2 (17/25)",
    },
    PillarId.FACTION: {
        "name": "Faction & Military",
        "description": "Diplomacy, military conflict, territory dynamics",
        "phase_anchors": ["PP-08", "PP-09", "PP-10", "PP-11", "PP-23"],
        "d01_tier": "Tier 2 (20/25)",
    },
    PillarId.ECONOMY: {
        "name": "Economy",
        "description": "Resource loop, crafting, trade, ecology",
        "phase_anchors": ["PP-07", "PP-21", "PP-24", "PP-25", "PP-26", "PP-27", "WD-05", "WD-10"],
        "d01_tier": "Tier 1 (22/25)",
    },
    PillarId.PROGRESSION: {
        "name": "Progression",
        "description": "XP, levels, skills, trait expression",
        "phase_anchors": ["PP-24", "PP-28", "PP-29", "PP-31"],
        "d01_tier": "Tier 2 (19/25)",
    },
    PillarId.SOCIAL: {
        "name": "Social",
        "description": "Cooperation, contracts, groups, reputation",
        "phase_anchors": ["PP-05", "PP-34", "PP-35", "PP-36"],
        "d01_tier": "Tier 2 (16/25)",
    },
    PillarId.INFORMATION: {
        "name": "Information & Belief",
        "description": "Knowledge asymmetry, paid info, leads, decision divergence",
        "phase_anchors": ["PP-04", "PP-26", "PP-30"],
        "d01_tier": "Tier 2 (18/25)",
    },
    PillarId.WORLD: {
        "name": "World Dynamics",
        "description": "Ecology, calamity, spawn, trauma, demographics",
        "phase_anchors": ["PP-20", "PP-22", "WD-01", "WD-15"],
        "d01_tier": "Tier 1 (22/25)",
    },
    PillarId.NARRATIVE: {
        "name": "Narrative",
        "description": "Quests, chronicle, world emergence, scenario",
        "phase_anchors": ["PP-23", "PP-24", "PP-33"],
        "d01_tier": "Tier 2 (10/25 partial)",
    },
}

# Pre-calibration grade threshold estimates.
# These constants are the single source of truth — never hardcode in scorers or report builders.
# Calibrated values will be set in TCK-20260628-SIMQ-E7-CALIBRATE.
GRADE_THRESHOLDS: dict[str, float] = {
    "S": 2.0,
    "A": 0.5,
    "B": 0.0,
    "C": -0.5,
    "D": -1.0,
}
