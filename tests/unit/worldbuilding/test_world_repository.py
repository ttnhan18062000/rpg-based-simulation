# Compliance IDs: WORLD-060, WORLD-061, WORLD-062
import pytest
import json
import yaml
from pathlib import Path
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.repository import WorldRepository, WorldRepositoryError

def create_valid_world_dict(world_id: str, name: str) -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": world_id,
        "name": name,
        "topology": {
            "width": 50,
            "height": 50,
            "coordinate_system": "grid"
        }
    }

def test_repository_lists_worlds(tmp_path):
    repo = WorldRepository(tmp_path)
    
    # 1. Listing empty repository should return empty list
    assert repo.list_worlds() == []

    # 2. Create two valid world folders
    w1_dir = tmp_path / "valley_zone"
    w1_dir.mkdir()
    w1_yaml = w1_dir / "world.yaml"
    with open(w1_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(create_valid_world_dict("valley_zone", "Valley Zone"), f)

    w2_dir = tmp_path / "mountain_arena"
    w2_dir.mkdir()
    w2_yaml = w2_dir / "world.yaml"
    with open(w2_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(create_valid_world_dict("mountain_arena", "Mountain Arena"), f)

    # A folder without world.yaml should be ignored
    ignored_dir = tmp_path / "ignored_folder"
    ignored_dir.mkdir()

    # Listing should return sorted valid world IDs
    assert repo.list_worlds() == ["mountain_arena", "valley_zone"]

def test_repository_loads_world_by_id(tmp_path):
    repo = WorldRepository(tmp_path)
    
    w_dir = tmp_path / "valley_zone"
    w_dir.mkdir()
    w_yaml = w_dir / "world.yaml"
    
    spec_data = create_valid_world_dict("valley_zone", "Valley Zone")
    spec_data["description"] = "A quiet testing valley."
    with open(w_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(spec_data, f)

    # Load and assert Pydantic fields
    spec = repo.load_world("valley_zone")
    assert isinstance(spec, WorldSpec)
    assert spec.world_id == "valley_zone"
    assert spec.name == "Valley Zone"
    assert spec.description == "A quiet testing valley."

def test_repository_missing_world_raises_error(tmp_path):
    repo = WorldRepository(tmp_path)
    with pytest.raises(WorldRepositoryError) as exc_info:
        repo.load_world("non_existent_world")
    assert "not found" in str(exc_info.value).lower()

def test_repository_duplicate_world_id_rejected(tmp_path):
    repo = WorldRepository(tmp_path)
    
    # Create dir_a with world_id: duplicate_world
    dir_a = tmp_path / "dir_a"
    dir_a.mkdir()
    with open(dir_a / "world.yaml", "w") as f:
        yaml.safe_dump(create_valid_world_dict("duplicate_world", "World A"), f)

    # Create dir_b with same world_id: duplicate_world
    dir_b = tmp_path / "dir_b"
    dir_b.mkdir()
    with open(dir_b / "world.yaml", "w") as f:
        yaml.safe_dump(create_valid_world_dict("duplicate_world", "World B"), f)

    # Rebuilding the index should raise a duplicate world ID rejection error
    with pytest.raises(WorldRepositoryError) as exc_info:
        repo.rebuild_index()
    assert "duplicate world_id" in str(exc_info.value).lower()

def test_repository_path_traversal_blocked(tmp_path):
    repo = WorldRepository(tmp_path)
    
    # 1. Unsafe/Invalid ID checks
    invalid_ids = ["../../etc/passwd", "..", "valley/zone", "valley.yaml"]
    for bad_id in invalid_ids:
        with pytest.raises(WorldRepositoryError) as exc_info:
            repo.load_world(bad_id)
        assert "secure path resolution failed" in str(exc_info.value).lower()

    # 2. Asset traversal check
    # Create world_dir
    w_dir = tmp_path / "valley"
    w_dir.mkdir()
    with open(w_dir / "world.yaml", "w") as f:
        yaml.safe_dump(create_valid_world_dict("valley", "Valley"), f)

    # Resolving path traversal asset should raise PermissionError
    with pytest.raises(PermissionError) as exc_info:
        repo.resolve_asset_path("valley", "../secret.txt")
    assert "traversal" in str(exc_info.value).lower()

def test_repository_invalid_yaml_raises_error(tmp_path):
    repo = WorldRepository(tmp_path)
    
    w_dir = tmp_path / "bad_world"
    w_dir.mkdir()
    w_yaml = w_dir / "world.yaml"
    
    # Write corrupt syntax
    with open(w_yaml, "w") as f:
        f.write("schema_version: worldspec.v1\n  invalid_indentation: yes")

    with pytest.raises(WorldRepositoryError) as exc_info:
        repo.load_world("bad_world")
    assert "failed to load" in str(exc_info.value).lower()

def test_repository_index_rebuild(tmp_path):
    repo = WorldRepository(tmp_path)
    
    # Create first valid world
    w1_dir = tmp_path / "w1"
    w1_dir.mkdir()
    with open(w1_dir / "world.yaml", "w") as f:
        yaml.safe_dump(create_valid_world_dict("w1", "World One"), f)

    # Create a second broken world folder
    w2_dir = tmp_path / "w2_broken"
    w2_dir.mkdir()
    with open(w2_dir / "world.yaml", "w") as f:
        f.write("corrupted: yaml")

    # Rebuild index
    index_data = repo.rebuild_index()
    
    assert "worlds" in index_data
    assert "w1" in index_data["worlds"]
    assert index_data["worlds"]["w1"]["status"] == "VALIDATED"
    assert index_data["worlds"]["w1"]["schema_version"] == "worldspec.v1"
    
    assert "w2_broken" in index_data["worlds"]
    assert index_data["worlds"]["w2_broken"]["status"] == "BROKEN"

    # Index path should be written
    assert repo.index_path.is_file()
    with open(repo.index_path, "r") as f:
        saved_index = json.load(f)
    assert saved_index["worlds"]["w1"]["status"] == "VALIDATED"

def test_repository_index_rebuild_classifies_composition_worlds(tmp_path):
    """
    Regression guard: rebuild_index() must classify worldcomposition.v1 worlds as
    COMPOSITION and worldspec.v1 worlds as VALIDATED after the worldtemplate.v1
    branch was removed (TCK-20260701-WORLDTEMPLATE-REMOVE).
    """
    repo = WorldRepository(tmp_path)

    # worldspec.v1 world
    w1_dir = tmp_path / "w1"
    w1_dir.mkdir()
    with open(w1_dir / "world.yaml", "w") as f:
        yaml.safe_dump(create_valid_world_dict("w1", "World One"), f)

    # worldcomposition.v1 world
    w2_dir = tmp_path / "w2_composition"
    w2_dir.mkdir()
    composition_data = {
        "schema_version": "worldcomposition.v1",
        "world_id": "w2_composition",
        "name": "Composition World",
        "module_refs": []
    }
    with open(w2_dir / "world.yaml", "w") as f:
        yaml.safe_dump(composition_data, f)

    index_data = repo.rebuild_index()

    assert index_data["worlds"]["w1"]["status"] == "VALIDATED"
    assert index_data["worlds"]["w1"]["schema_version"] == "worldspec.v1"

    assert index_data["worlds"]["w2_composition"]["status"] == "COMPOSITION"
    assert index_data["worlds"]["w2_composition"]["schema_version"] == "worldcomposition.v1"

def _write_composition_with_resolved(tmp_path, world_id: str, with_compile_context: bool = True):
    """Shared fixture builder: a worldcomposition.v1 world.yaml plus its resolved/
    world.resolved.yaml, and (unless with_compile_context=False) a real compile_context.json
    carrying a role->EntityRole mapping -- mirrors the real, on-disk shape every corpus world
    under data/worlds/ already has (confirmed via TCK-20260808-MONSTER-ROLE-MISTAGGING-
    INVESTIGATION's own direct inspection)."""
    w_dir = tmp_path / world_id
    w_dir.mkdir()
    composition_data = {
        "schema_version": "worldcomposition.v1",
        "world_id": world_id,
        "name": "Composition World",
        "module_refs": [],
    }
    with open(w_dir / "world.yaml", "w") as f:
        yaml.safe_dump(composition_data, f)

    resolved_dir = w_dir / "resolved"
    resolved_dir.mkdir()
    with open(resolved_dir / "world.resolved.yaml", "w") as f:
        yaml.safe_dump(create_valid_world_dict(world_id, "Composition World"), f)

    if with_compile_context:
        from src.worldassembly.context import CompileContext
        from src.core.enums import EntityRole

        ctx = CompileContext()
        ctx.register_legacy_role("predator_hunter", EntityRole.MONSTER)
        ctx.register_legacy_role("scout", EntityRole.GUARD)
        with open(resolved_dir / "compile_context.json", "w") as f:
            json.dump(ctx.to_dict(), f)

    return w_dir


def test_load_world_with_context_non_composition_returns_none_context(tmp_path):
    """A plain worldspec.v1 world (not a composition) has no compile_context.json at all --
    load_world_with_context() must return (spec, None), matching load_world()'s own existing
    behavior for this case exactly."""
    repo = WorldRepository(tmp_path)
    w_dir = tmp_path / "plain_world"
    w_dir.mkdir()
    with open(w_dir / "world.yaml", "w") as f:
        yaml.safe_dump(create_valid_world_dict("plain_world", "Plain World"), f)

    spec, context = repo.load_world_with_context("plain_world")
    assert spec.world_id == "plain_world"
    assert context is None


def test_load_world_with_context_composition_loads_real_role_mapping(tmp_path):
    """TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION: the real bug this method fixes --
    a composition world's own compile_context.json must be loaded and returned so
    WorldCompiler.compile() can correctly resolve entity.identity.role for real, catalog-driven
    monster archetypes instead of falling back to naive keyword matching (which defaults almost
    every real monster role_id, e.g. "predator_hunter", to CITIZEN)."""
    from src.core.enums import EntityRole

    repo = WorldRepository(tmp_path)
    _write_composition_with_resolved(tmp_path, "monster_world")

    spec, context = repo.load_world_with_context("monster_world")
    assert spec.world_id == "monster_world"
    assert context is not None
    assert context.legacy_roles["predator_hunter"] == EntityRole.MONSTER
    assert context.legacy_roles["scout"] == EntityRole.GUARD


def test_load_world_with_context_composition_missing_compile_context_degrades_to_none(tmp_path):
    """Graceful degradation: a resolved composition world whose compile_context.json is
    missing (e.g. an older resolve predating this artifact) must still load successfully with
    context=None, not raise -- matching load_world()'s own existing tolerance for a resolved-
    but-context-less world."""
    repo = WorldRepository(tmp_path)
    _write_composition_with_resolved(tmp_path, "no_context_world", with_compile_context=False)

    spec, context = repo.load_world_with_context("no_context_world")
    assert spec.world_id == "no_context_world"
    assert context is None


def test_load_world_with_context_unresolved_composition_raises(tmp_path):
    """A composition world with no resolved/world.resolved.yaml at all must raise, matching
    load_world()'s own existing "Run resolve first" error for this case."""
    repo = WorldRepository(tmp_path)
    w_dir = tmp_path / "unresolved_world"
    w_dir.mkdir()
    composition_data = {
        "schema_version": "worldcomposition.v1",
        "world_id": "unresolved_world",
        "name": "Unresolved World",
        "module_refs": [],
    }
    with open(w_dir / "world.yaml", "w") as f:
        yaml.safe_dump(composition_data, f)

    with pytest.raises(WorldRepositoryError, match="has not been resolved"):
        repo.load_world_with_context("unresolved_world")


def test_repository_save_world(tmp_path):
    repo = WorldRepository(tmp_path)
    
    spec = WorldSpec(
        schema_version="worldspec.v1",
        world_id="new_sandbox",
        name="New Sandbox World",
        topology={
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        }
    )
    
    saved_path = repo.save_world(spec)
    assert saved_path.is_file()
    assert saved_path.name == "world.yaml"
    assert saved_path.parent.name == "new_sandbox"

    # Verify loading back
    loaded_spec = repo.load_world("new_sandbox")
    assert loaded_spec.name == "New Sandbox World"
    assert loaded_spec.topology.width == 100
