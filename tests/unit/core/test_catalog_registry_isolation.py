"""Guard: tests/conftest.py restores the catalog-backed registries between tests.

Enemy/Recipe/Service/Region registries are class-level state that catalog-mode and content-mode
tests re-bootstrap. Without the autouse restore fixture, a later test sees the mutated contents
(tests/unit/domains/progression/ failed after any of 8 such files).

Order-robust: the expected contents are snapshotted at import (collection) time, before any test
has run. One test re-bootstraps every registry to empty; the other asserts the registries still
hold the snapshot. The pair detects a leak whenever the mutating test runs first, and never fails
spuriously when the order is shuffled. No absolute counts are asserted, so content changes do not
break it.
"""

from src.core.registries import (
    EnemyRegistry,
    RecipeRegistry,
    RegionRegistry,
    ServiceRegistry,
)

_REGISTRIES = (EnemyRegistry, RecipeRegistry, ServiceRegistry, RegionRegistry)
_AT_COLLECTION = {registry: registry.all() for registry in _REGISTRIES}


def test_bootstrap_inside_a_test_empties_the_registries():
    for registry in _REGISTRIES:
        registry.bootstrap({})
        assert registry.all() == {}


def test_registries_hold_their_canonical_contents_at_test_start():
    for registry in _REGISTRIES:
        assert _AT_COLLECTION[registry], f"{registry.__name__} was empty at collection"
        assert registry.all() == _AT_COLLECTION[registry], (
            f"{registry.__name__} differs from its canonical contents; a previous test's "
            f"bootstrap leaked"
        )
