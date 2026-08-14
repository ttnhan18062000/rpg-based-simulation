"""Unit tests for WorldEntitySpawner's own legacy-guard path (no archetype_id).

TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY: this path previously never set
personality at all, the same bug as the archetype-native path but confirmed separately
here since it uses a distinct code branch (_spawn_legacy_guard, V2EntityBuilder directly).
"""

from src.worldassembly.entity_spawner import WorldEntitySpawner
from src.worldassembly.models import ResolvedEntityProfile


def _profile(**overrides) -> ResolvedEntityProfile:
    defaults = dict(
        legacy_role=0,
        legacy_faction=1,
        hp=50,
        max_hp=50,
        atk=10,
        **{"def": 3},
        attack_range=1,
        readiness=100.0,
        archetype_id=None,
        race_id="human",
        role_id="citizen",
        faction_id="wild_beast_pack",
        traits=[],
    )
    defaults.update(overrides)
    return ResolvedEntityProfile(**defaults)


def test_legacy_guard_produces_real_nonzero_personality():
    spawner = WorldEntitySpawner()
    profile = _profile()
    entity = spawner._spawn_legacy_guard(1, profile, _spawn_ctx(), seed=42)
    p = entity.identity.personality
    assert p.bravery > 0.0 or p.greed > 0.0 or p.sociability > 0.0 or p.industry > 0.0


def test_legacy_guard_action_style_correlates_with_bravery():
    from src.core.enums import ActionStyle
    spawner = WorldEntitySpawner()
    styles = []
    for eid in range(1, 21):
        profile = _profile(faction_id="wild_beast_pack")
        entity = spawner._spawn_legacy_guard(eid, profile, _spawn_ctx(), seed=42)
        styles.append(entity.combat.action_style)
    assert any(s == ActionStyle.AGGRESSIVE for s in styles)


def test_legacy_guard_deterministic_given_seed():
    spawner = WorldEntitySpawner()
    profile = _profile()
    e1 = spawner._spawn_legacy_guard(5, profile, _spawn_ctx(), seed=7)
    e2 = spawner._spawn_legacy_guard(5, profile, _spawn_ctx(), seed=7)
    assert e1.identity.personality == e2.identity.personality


def test_legacy_guard_no_faction_id_does_not_crash():
    spawner = WorldEntitySpawner()
    profile = _profile(faction_id=None)
    entity = spawner._spawn_legacy_guard(1, profile, _spawn_ctx(), seed=42)
    assert entity is not None


def _spawn_ctx():
    from src.entities.archetype_factory import EntitySpawnContext
    return EntitySpawnContext(position=(0.0, 0.0))
