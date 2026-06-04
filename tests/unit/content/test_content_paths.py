import pytest
from src.content.paths import ContentPathConfig
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.content.schema import MaterialDefinition, SpawnTableDefinition


def test_default_content_paths_point_to_data_content():
    config = ContentPathConfig()
    assert config.content_root == "data/content"
    assert config.world_modules_dir == "data/content/world_modules"
    assert config.world_compositions_dir == "data/content/world_compositions"
    assert config.simulation_scenarios_dir == "data/content/simulation_scenarios"


def test_world_module_repository_default_uses_content_path():
    repo = WorldModuleRepository()
    assert repo.modules_dir == "data/content/world_modules"


def test_catalog_repository_default_uses_content_path():
    repo = CatalogRepository()
    assert repo.content_dir == "data/content"


def test_old_world_modules_path_not_used_by_default():
    repo = WorldModuleRepository()
    assert repo.modules_dir != "data/world_modules"


def test_strict_load_fails_on_duplicate_id(tmp_path, monkeypatch):
    # Setup catalog with duplicate IDs
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    materials_dir = content_dir / "foundation"
    materials_dir.mkdir()
    materials_file = materials_dir / "materials.yaml"
    materials_file.write_text("""
- id: iron
  deprecated: false
- id: iron
  deprecated: false
""", encoding="utf-8")

    from src.content.repository import ContentFamilySpec
    from src.content import repository
    mock_families = [
        ContentFamilySpec("foundation.materials", "foundation/materials.yaml", MaterialDefinition, "materials")
    ]
    monkeypatch.setattr(repository, "CANONICAL_FAMILIES", mock_families)

    repo = CatalogRepository(content_dir=str(content_dir))
    with pytest.raises(ValueError) as exc_info:
        repo.load_all(strict=True)
    assert "Duplicate IDs detected" in str(exc_info.value)


def test_strict_load_fails_on_ignored_active_yaml(tmp_path, monkeypatch):
    # Setup catalog with an unknown YAML file
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    # Write a required file so it doesn't fail on missing required files
    materials_dir = content_dir / "foundation"
    materials_dir.mkdir()
    materials_file = materials_dir / "materials.yaml"
    materials_file.write_text("- id: iron\n  deprecated: false", encoding="utf-8")

    unknown_file = content_dir / "unknown.yaml"
    unknown_file.write_text("- id: something\n  deprecated: false", encoding="utf-8")

    from src.content.repository import ContentFamilySpec
    from src.content import repository
    mock_families = [
        ContentFamilySpec("foundation.materials", "foundation/materials.yaml", MaterialDefinition, "materials")
    ]
    monkeypatch.setattr(repository, "CANONICAL_FAMILIES", mock_families)

    repo = CatalogRepository(content_dir=str(content_dir))
    with pytest.raises(ValueError) as exc_info:
        repo.load_all(strict=True)
    assert "Ignored active YAML files found" in str(exc_info.value)


def test_strict_load_fails_on_empty_required_family(tmp_path, monkeypatch):
    # Setup catalog with an empty required file
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    materials_dir = content_dir / "foundation"
    materials_dir.mkdir()
    materials_file = materials_dir / "materials.yaml"
    materials_file.write_text("", encoding="utf-8")

    from src.content.repository import ContentFamilySpec
    from src.content import repository
    mock_families = [
        ContentFamilySpec("foundation.materials", "foundation/materials.yaml", MaterialDefinition, "materials")
    ]
    monkeypatch.setattr(repository, "CANONICAL_FAMILIES", mock_families)

    repo = CatalogRepository(content_dir=str(content_dir))
    with pytest.raises(ValueError) as exc_info:
        repo.load_all(strict=True)
    assert "Empty required active families found" in str(exc_info.value)


def test_optional_missing_file_is_reported_not_failed(tmp_path, monkeypatch):
    # Setup catalog with missing optional files but required files present
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    materials_dir = content_dir / "foundation"
    materials_dir.mkdir()
    materials_file = materials_dir / "materials.yaml"
    materials_file.write_text("- id: dummy\n  deprecated: false", encoding="utf-8")

    from src.content.repository import ContentFamilySpec
    from src.content import repository
    mock_families = [
        ContentFamilySpec("foundation.materials", "foundation/materials.yaml", MaterialDefinition, "materials"),
        ContentFamilySpec("spawn_tables", "spawn_tables.yaml", SpawnTableDefinition, "spawn_tables", required=False),
    ]
    monkeypatch.setattr(repository, "CANONICAL_FAMILIES", mock_families)

    repo = CatalogRepository(content_dir=str(content_dir))
    report = repo.load_all(strict=True)
    assert len(report.missing_optional_files) > 0


def test_load_report_fingerprint_changes_when_content_changes(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    materials_dir = content_dir / "foundation"
    materials_dir.mkdir()
    materials_file = materials_dir / "materials.yaml"
    materials_file.write_text("- id: iron\n  name: Iron\n  deprecated: false", encoding="utf-8")

    repo = CatalogRepository(content_dir=str(content_dir))
    report1 = repo.load_all()
    fp1 = report1.fingerprint

    # Change content
    materials_file.write_text("- id: iron\n  name: Iron Modified\n  deprecated: false", encoding="utf-8")
    report2 = repo.load_all()
    fp2 = report2.fingerprint

    assert fp1 != fp2

