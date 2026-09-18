#!/usr/bin/env python3
"""
The atlas card <-> mechanism id mapping (TCK-20260915-ARTIFACT-STATE-CONVERGENCE), reused directly
from TCK-20260915-MECHANISM-REGISTRY-FOUNDATION's own investigation.md citation table rather than
re-derived -- that table is the authoritative record of which atlas card each mechanism id was
seeded from, including the exact badge index for the 2 cards that split into 2 mechanisms.

Verified programmatically against the real atlas JSON before trusting it as a hand-authored
mapping (TCK-20260915-ARTIFACT-STATE-CONVERGENCE's own investigation.md): 71 non-design-idea atlas
cards, 73 citations in Foundation's table, covering 73 of the registry's 75 mechanism ids (the
remaining 2 -- `nest`/`lair` -- have no atlas card, sourced from the wiring map only, per
Foundation's own investigation).

Most cards map 1:1 to one mechanism id, using the card's own first/only badge as the state
indicator. Two shapes are exceptions, both hand-verified against the real card structure rather
than assumed:
  - SPLIT cards: one card originally carried 2 badges describing 2 genuinely distinct mechanisms
    (Foundation's own Judgment Calls 1 and 2). Badge index N corresponds to
    SPLIT_CARD_MECHANISMS[(section, card_index)][N].
  - PARTIAL-COVERAGE cards: one card describes more sub-systems than the registry seeded as
    distinct mechanisms (Foundation's own Judgment Call 5 -- `entity-cognition#11`'s "Memory
    Capacity & Trustfulness" card has 3 badges for 3 tiers, but only Tier 2 ("Rich") was seeded as
    its own mechanism, `knowledge_model`, at that card's badge index 1; Tiers 1 and 3 are the SAME
    mechanisms as `goal_hierarchy` and `causal_spatial_memory` respectively, cited from their own,
    different cards instead).
"""
from __future__ import annotations

from typing import Dict, Tuple

# (section, card_index) -> single mechanism id, using that card's own badge[0] as the state
# indicator. Built from Foundation's own investigation.md citation table.
CARD_TO_MECHANISM_ID: Dict[Tuple[str, int], str] = {
    ("entity-action", 0): "combat_resolution",
    ("entity-action", 1): "tactical_decision",
    ("entity-action", 2): "combat_engagement",
    ("entity-action", 3): "movement",
    ("entity-action", 4): "action_pacing_readiness",
    ("entity-action", 5): "interaction_channeling",
    ("entity-action", 6): "conversation",
    ("entity-action", 7): "entity_trade",
    ("entity-action", 8): "team_up",
    ("entity-profile", 0): "attributes_biology",
    ("entity-profile", 1): "derived_stats",
    ("entity-profile", 2): "race_archetype",
    ("entity-profile", 3): "class_assignment",
    ("entity-profile", 4): "personality",
    ("entity-profile", 5): "build_diversity",
    # entity-profile#6 and #10 are SPLIT cards -- see SPLIT_CARD_MECHANISMS below, not here.
    ("entity-profile", 7): "genetics_aptitude",
    ("entity-profile", 8): "evolution",
    ("entity-profile", 9): "skill_unlocks",
    ("entity-profile", 11): "entity_role",
    ("entity-modification", 0): "trauma",
    ("entity-modification", 1): "status_effects",
    ("entity-cognition", 0): "self_model",
    ("entity-cognition", 1): "declared_cognition_schema",
    ("entity-cognition", 2): "perception",
    ("entity-cognition", 3): "emotion",
    ("entity-cognition", 4): "affection_relationship_bonds",
    ("entity-cognition", 5): "motivation_doctrine",
    ("entity-cognition", 6): "commitment_betrayal",
    ("entity-cognition", 7): "temporal_pressure",
    ("entity-cognition", 8): "goal_hierarchy",
    ("entity-cognition", 9): "belief_cycle",
    ("entity-cognition", 10): "information_trust_deception",
    # entity-cognition#11 is a PARTIAL-COVERAGE card -- see PARTIAL_COVERAGE_CARDS below.
    ("entity-cognition", 12): "causal_spatial_memory",
    ("entity-cognition", 13): "adventure_routing",
    ("entity-cognition", 14): "quest_generation_sourcing",
    ("entity-cognition", 15): "strategic_intelligence_core",
    ("entity-cognition", 16): "committed_intentions",
    ("entity-cognition", 17): "cognition_capacity_fatigue",
    ("group-layer", 0): "party_formation",
    ("group-layer", 1): "guilds",
    ("faction-layer", 0): "diplomacy",
    ("faction-layer", 1): "betrayal_siege_war",
    ("faction-layer", 2): "social_contracts",
    ("faction-layer", 3): "reputation",
    ("faction-layer", 4): "social_memory",
    ("faction-layer", 5): "cross_episode_social_consequences",
    ("faction-layer", 6): "cross_episode_grief_nemesis",
    ("faction-layer", 7): "country_lifecycle",
    # SPLIT 2026-09-17 (TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY):
    # regional_trauma_hazards_sovereignty split into regional_trauma/regional_sovereignty. This
    # card's own desc is entirely about ownership/conquest tracking (RegionState.owner_faction_id,
    # FactionState.territory) -- repointed at regional_sovereignty, the half it actually
    # describes. regional_trauma has no atlas card citation, same as any other mechanism found via
    # direct code enumeration rather than an atlas card.
    ("region-layer", 0): "regional_sovereignty",
    ("region-layer", 1): "demographic_cohort_cycle",
    ("world-layer", 0): "campaigns",
    ("world-layer", 1): "chronicle",
    ("world-layer", 2): "opportunity_rumor_seeds",
    ("world-layer", 3): "cultural_drift",
    # SPLIT 2026-09-17 (TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY):
    # calamities_boss_spawns split into calamity_intensity/world_boss_spawn. This card's own desc
    # ("boss spawns... in high-hazard regions") centers on the boss-spawn half -- repointed at
    # world_boss_spawn. calamity_intensity has no atlas card citation.
    ("world-layer", 4): "world_boss_spawn",
    ("world-layer", 5): "world_generation",
    ("world-layer", 6): "gods_pantheon_blessings",
    ("worldobject-layer", 0): "equipment_scoring",
    ("worldobject-layer", 1): "inventory_trade_conservation",
    ("worldobject-layer", 2): "crafting",
    # SPLIT 2026-09-17 (TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY):
    # buildings_town_services split into buildings/town_services. This card's own desc ("real
    # town-service registry... inn rest, blacksmith repair... church's BLESSING/RESURRECTION
    # services") is entirely about the services -- repointed at town_services. buildings (the
    # physical structures) has no atlas card citation.
    ("worldobject-layer", 3): "town_services",
    ("worldobject-layer", 4): "building_sabotage",
    ("clan-layer", 0): "clan",
    ("race-layer", 0): "race_collective_force",
    ("city-layer", 0): "city",
    ("beyond-city", 0): "camp",
    ("beyond-city", 1): "ruins_mines_battlefields",
    ("beyond-city", 2): "settlement_capacity_axis",
}

# (section, card_index) -> [mechanism id for badge[0], mechanism id for badge[1]]
SPLIT_CARD_MECHANISMS: Dict[Tuple[str, int], list] = {
    ("entity-profile", 6): ["aging_death", "succession"],
    ("entity-profile", 10): ["xp_leveling", "breakthrough_bonuses"],
}

# (section, card_index) -> {badge_index: mechanism_id} for cards where only SOME badges
# correspond to a registry mechanism (the others are folded into different mechanisms cited
# elsewhere, per Foundation's own Judgment Call 5).
PARTIAL_COVERAGE_CARDS: Dict[Tuple[str, int], Dict[int, str]] = {
    ("entity-cognition", 11): {1: "knowledge_model"},  # badge[0]=Tier1(~goal_hierarchy elsewhere), badge[1]=Tier2(knowledge_model), badge[2]=Tier3(~causal_spatial_memory elsewhere)
}


def all_mechanism_card_badge_positions() -> Dict[str, list]:
    """mechanism_id -> [(section, card_index, badge_index), ...] -- almost always a single
    1-element list, except mechanisms with no atlas card at all (nest, lair), which are absent
    from this mapping entirely (not an error -- checked by the caller separately)."""
    result: Dict[str, list] = {}
    for (section, idx), mech_id in CARD_TO_MECHANISM_ID.items():
        result.setdefault(mech_id, []).append((section, idx, 0))
    for (section, idx), mech_ids in SPLIT_CARD_MECHANISMS.items():
        for badge_idx, mech_id in enumerate(mech_ids):
            result.setdefault(mech_id, []).append((section, idx, badge_idx))
    for (section, idx), badge_map in PARTIAL_COVERAGE_CARDS.items():
        for badge_idx, mech_id in badge_map.items():
            result.setdefault(mech_id, []).append((section, idx, badge_idx))
    return result
