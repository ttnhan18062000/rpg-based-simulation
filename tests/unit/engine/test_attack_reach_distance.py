"""Attack legality and pursuit reach measure one whole-tile distance
(TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT, MOV-07 / Decision 25)."""
import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.state import AuthoritativeState
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.legality import LegalityServiceV2


def _pair(a, b, attack_range=1):
    attacker = V2EntityBuilder(1).kind("hero").identity(faction=Faction.HERO_GUILD).location(*a).combat(
        hp=100, max_hp=100, attack_range=attack_range, alive=True, readiness=100.0).build()
    target = V2EntityBuilder(2).kind("goblin").identity(faction=Faction.MONSTER_HORDE).location(*b).build()
    return attacker, target


def _both(a, b, attack_range=1):
    attacker, target = _pair(a, b, attack_range)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, AuthoritativeState(tick=1, seed=1))
    in_reach = MovementCandidateSelector._target_in_attack_reach(attacker, target)
    return legal, reason, in_reach


@pytest.mark.parametrize("a,b", [
    ((93.34, 71.06), (94.0, 70.0)),   # the ticket's float distance 1.72 (tiles (93,71) and (94,70): distance 2)
    ((10.9, 10.0), (11.0, 10.0)),     # tiles (10,10) and (11,10): distance 1
    ((10.0, 10.0), (10.99, 10.99)),   # the same tile: distance 0
    ((10.0, 10.0), (12.0, 10.0)),
    ((10.0, 10.0), (11.0, 11.0)),     # diagonal: not adjacent (MOV-07)
])
def test_legality_and_pursuit_reach_agree_on_fractional_and_integral_pairs(a, b):
    legal, reason, in_reach = _both(a, b)
    assert (reason != ReasonCode.OUT_OF_RANGE) is in_reach


def test_distance_is_the_whole_tile_distance_not_a_truncated_sum():
    assert LegalityServiceV2.get_manhattan_dist((93.34, 71.06), (94.0, 70.0)) == 2   # the old int() of 1.72 was 1
    assert LegalityServiceV2.get_manhattan_dist((10.0, 10.0), (11.0, 10.0)) == 1
    assert LegalityServiceV2.get_manhattan_dist((-0.5, 0.0), (0.0, 0.0)) == 0
