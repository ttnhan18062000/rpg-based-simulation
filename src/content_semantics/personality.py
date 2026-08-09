# Compliance IDs: WORLD-SEM-005
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from src.core.state import PersonalityComponent

# Real per-entity bravery is RNG-seeded by callers (WorldCompiler.compile(),
# ArchetypeEntityFactory.build_entity()) but was previously uncorrelated with race/faction -- a
# wolf and a citizen drew from the identical distribution
# (TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION / TCK-20260809-COMBAT-ACTIONSTYLE-WIRING).
# Bias magnitudes and ActionStyle thresholds are real gameplay-tuning data, not code logic --
# data-driven from data/content/social/personality_bias.yaml (per explicit user direction) rather
# than hardcoded, so designers can retune without a code change. These module-level fallbacks
# match the shipped data file exactly and are used only if that file is missing or malformed, so
# entity construction never crashes on a bad/absent data file.
#
# Lives in content_semantics/ (not worldbuilding/ or entities/) because it is a real, shared
# cross-cutting helper consumed by both the WorldCompiler.compile() path (src/worldbuilding/) and
# the ArchetypeEntityFactory path (src/entities/, src/worldassembly/)
# (TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY) -- matching this module's own established
# sibling precedent (faction.py, relation.py, role.py) for shared semantic helpers imported across
# multiple subsystems.
_PERSONALITY_BIAS_FALLBACK: Dict[str, Any] = {
    "bravery_bias_by_alignment_bucket": {
        "wild": 0.35, "invader": 0.25, "rival": 0.15, "defender": 0.05, "neutral": 0.0,
    },
    "action_style_thresholds": {
        "aggressive_at_or_above": 0.65, "evasive_at_or_below": 0.35,
    },
}
_personality_bias_cache: Optional[Dict[str, Any]] = None


def _load_personality_bias_config() -> Dict[str, Any]:
    """Loads data/content/social/personality_bias.yaml, cached for the process lifetime."""
    global _personality_bias_cache
    if _personality_bias_cache is not None:
        return _personality_bias_cache
    try:
        path = Path("data/content/social/personality_bias.yaml")
        loaded = yaml.safe_load(path.read_text())
        if not isinstance(loaded, dict) or "bravery_bias_by_alignment_bucket" not in loaded:
            raise ValueError("malformed personality_bias.yaml")
        _personality_bias_cache = loaded
    except Exception:
        _personality_bias_cache = _PERSONALITY_BIAS_FALLBACK
    return _personality_bias_cache


def get_bravery_bias(faction_str: str) -> float:
    """Real, content-derived bravery bias for a faction (see personality_bias.yaml)."""
    try:
        from src.content_semantics.faction import get_faction_semantics_service
        bucket = get_faction_semantics_service().get_alignment_bucket(faction_str)
    except Exception:
        return 0.0
    table = _load_personality_bias_config()["bravery_bias_by_alignment_bucket"]
    return table.get(bucket, 0.0)


def get_action_style_for_bravery(bravery: float) -> int:
    """
    Real ActionStyle (BALANCED/AGGRESSIVE/EVASIVE, src/core/enums.py) derived from bravery, per
    the real thresholds in personality_bias.yaml. Entity-construction paths previously left
    action_style at its class default (BALANCED) for every entity, leaving 2 real, already-wired
    code hooks entirely dormant: kiting distance for SKIRMISHER-role entities
    (src/engine/tactical.py, AGGRESSIVE kites less, EVASIVE kites more) and opportunity-attack
    suppression on a deliberate EVASIVE retreat (src/engine/movement.py)
    (TCK-20260809-COMBAT-ACTIONSTYLE-WIRING).
    """
    from src.core.enums import ActionStyle
    thresholds = _load_personality_bias_config()["action_style_thresholds"]
    if bravery >= thresholds["aggressive_at_or_above"]:
        return int(ActionStyle.AGGRESSIVE)
    if bravery <= thresholds["evasive_at_or_below"]:
        return int(ActionStyle.EVASIVE)
    return int(ActionStyle.BALANCED)


def build_personality_for_entity(entity_id: int, faction_id: Optional[str], seed: int) -> "PersonalityComponent":
    """
    Real, per-entity, race/faction-correlated PersonalityComponent, deterministic given
    (entity_id, faction_id, seed). Shared by both real entity-construction paths
    (WorldCompiler.compile(), ArchetypeEntityFactory.build_entity() and WorldEntitySpawner's own
    legacy-guard path) so bravery-bias/ActionStyle logic lives in exactly one place
    (TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY). Uses the same DeterministicRNG/
    Domain.WORLD/sub_id convention WorldCompiler.compile() originated (10=greed, 11=bravery,
    12=sociability, 13=industry).
    """
    from src.core.enums import Domain
    from src.core.state import PersonalityComponent
    from src.platform.rng import DeterministicRNG

    rng = DeterministicRNG(seed)
    bravery_bias = get_bravery_bias(faction_id or "")
    return PersonalityComponent(
        greed=rng.get_float(Domain.WORLD, 0, entity_id, sub_id=10),
        bravery=min(1.0, max(0.0, rng.get_float(Domain.WORLD, 0, entity_id, sub_id=11) + bravery_bias)),
        sociability=rng.get_float(Domain.WORLD, 0, entity_id, sub_id=12),
        industry=rng.get_float(Domain.WORLD, 0, entity_id, sub_id=13),
    )
