import pytest
from src.domains.motivation.resolver import DoctrineResolver
from src.core.cognition import IdentityDoctrine

def test_doctrine_resolver_warrior():
    doctrine = DoctrineResolver.resolve("warrior")
    assert doctrine.class_id == "warrior"
    assert doctrine.preferred_route_tags.get("melee", 0) > 0.0
    assert doctrine.preferred_route_tags.get("heavy_armor", 0) > 0.0
    assert doctrine.avoided_route_tags.get("spells", 0) > 0.0

def test_doctrine_resolver_ranger():
    doctrine = DoctrineResolver.resolve("ranger")
    assert doctrine.class_id == "ranger"
    assert doctrine.preferred_route_tags.get("ranged", 0) > 0.0
    assert doctrine.preferred_route_tags.get("scouting", 0) > 0.0

def test_doctrine_resolver_mage():
    doctrine = DoctrineResolver.resolve("mage")
    assert doctrine.class_id == "mage"
    assert doctrine.preferred_route_tags.get("spells", 0) > 0.0
    assert doctrine.preferred_route_tags.get("intel", 0) > 0.0
    assert doctrine.avoided_route_tags.get("heavy_armor", 0) > 0.0

def test_doctrine_resolver_unknown():
    doctrine = DoctrineResolver.resolve("unknown")
    assert doctrine.class_id == "unknown"
    assert len(doctrine.preferred_route_tags) == 0
