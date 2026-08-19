from src.core.dirty import DirtySet, DirtyDependencyGraph


def test_dirty_dependency_movement_marks_strategic_and_social():
    """
    Movement dirty should imply strategic (proximity/pathfinding) and social (encounters).
    """
    initial = DirtySet(movement_entities={1, 2})
    expanded = DirtyDependencyGraph.expand(initial)

    assert expanded.movement_entities == {1, 2}
    assert expanded.strategic_entities == {1, 2}
    assert expanded.social_entities == {1, 2}


def test_dirty_dependency_inventory_marks_strategic():
    """
    Inventory dirty should trigger strategic systems (capacity evaluation/shop).
    """
    initial = DirtySet(inventory_entities={3})
    expanded = DirtyDependencyGraph.expand(initial)

    assert expanded.inventory_entities == {3}
    assert expanded.strategic_entities == {3}


def test_dirty_dependency_combat_marks_lifecycle_social_and_strategic():
    """
    Combat dirty should trigger lifecycle (health checks), social (morale), and strategic evaluation.
    """
    initial = DirtySet(combat_entities={4, 5})
    expanded = DirtyDependencyGraph.expand(initial)

    assert expanded.combat_entities == {4, 5}
    assert expanded.lifecycle_entities == {4, 5}
    assert expanded.social_entities == {4, 5}
    assert expanded.strategic_entities == {4, 5}


def test_dirty_dependency_biological_and_attributes_mark_strategic_and_lifecycle():
    """
    Biological or attribute changes must trigger strategic and lifecycle passes.
    """
    initial = DirtySet(biological_entities={6}, attribute_entities={7})
    expanded = DirtyDependencyGraph.expand(initial)

    assert expanded.biological_entities == {6}
    assert expanded.attribute_entities == {7}
    assert expanded.strategic_entities == {6, 7}
    assert expanded.lifecycle_entities == {6, 7}


def test_dirty_dependency_expansion_is_idempotent():
    """
    expand(expand(dirty)) must equal expand(dirty).
    """
    initial = DirtySet(
        movement_entities={1},
        combat_entities={2},
        inventory_entities={3},
        biological_entities={4},
    )

    expanded_once = DirtyDependencyGraph.expand(initial)
    expanded_twice = DirtyDependencyGraph.expand(expanded_once)

    assert expanded_once == expanded_twice


def test_dirty_dependency_expansion_is_deterministic():
    """
    Same input must always produce identical output across multiple runs.
    """
    initial = DirtySet(movement_entities={10, 5, 1}, combat_entities={8, 3})

    run1 = DirtyDependencyGraph.expand(initial)
    run2 = DirtyDependencyGraph.expand(initial)

    assert run1 == run2
    assert sorted(run1.strategic_entities) == [1, 3, 5, 8, 10]
