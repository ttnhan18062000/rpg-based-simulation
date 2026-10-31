"""Every terrain has a display name: every catalog terrain declares one, and every terrain a corpus world paints is a catalog terrain.

Sources: data/content/world/terrain.yaml via CatalogRepository.terrain, src/api/presenters/manifest_presenter.py (ManifestPresenter._terrain_display_name).
"""
from pathlib import Path

import pytest

from src.api.presenters.manifest_presenter import ManifestPresenter
from src.content.paths import ContentPathConfig
from src.content.repository import CatalogRepository
from tests.helpers.scenario import compile_world


def _catalog():
    repo = CatalogRepository(ContentPathConfig().content_root)
    repo.load_all()
    return repo


def _corpus_worlds():
    return sorted(p.name for p in Path("data/worlds").iterdir() if p.is_dir())


def test_every_catalog_terrain_declares_a_non_empty_display_name():
    terrain = dict(_catalog().terrain.items())
    assert terrain, "the terrain catalog is empty"
    nameless = [tid for tid, definition in terrain.items() if not (definition.display_name or "").strip()]
    assert nameless == []


@pytest.mark.parametrize("world_id", _corpus_worlds())
def test_every_terrain_a_corpus_world_paints_is_a_named_catalog_terrain(world_id):
    catalog = _catalog()
    painted = set(compile_world(world_id, 42).terrain.values())
    for raw in painted:
        assert catalog.terrain.get(raw.lower()) is not None, f"{world_id}: terrain {raw!r} is not in the catalog"
        assert ManifestPresenter._terrain_display_name(raw, catalog).strip()
