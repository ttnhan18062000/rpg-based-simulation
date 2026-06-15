"""
Unit tests for pack_refs validation in WorldAssemblyResolver.assemble().

Compliance: TCK-20260614-WORLDMOD-PACKS
Tests the AssemblyPackError gate inserted at the start of assemble() before
any module resolution occurs. Uses unittest.mock to avoid touching the real
filesystem or loading real catalogs.
"""
from __future__ import annotations

import pytest
import yaml
from unittest.mock import MagicMock, patch, mock_open

from src.worldassembly.schema import WorldCompositionSpec
from src.worldassembly.resolver import WorldAssemblyResolver, AssemblyPackError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_spec(pack_refs=None) -> WorldCompositionSpec:
    """Build a minimal WorldCompositionSpec with the given pack_refs."""
    return WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="test_world",
        name="Test World",
        pack_refs=pack_refs or [],
    )


def _make_pack_yaml(pack_id: str, enabled: bool = True, dependencies=None) -> str:
    """Return a YAML string for a ContentPackManifest."""
    data = {
        "schema_version": "content_pack.v1",
        "pack_id": pack_id,
        "display_name": f"Pack {pack_id}",
        "version": "1.0.0",
        "enabled": enabled,
        "dependencies": dependencies or [],
        "included_families": {},
        "sample_compositions": ["test_composition"],
    }
    return yaml.dump(data)


def _mock_resolver() -> WorldAssemblyResolver:
    """Build a WorldAssemblyResolver with mocked catalog and module repos."""
    catalog_repo = MagicMock()
    catalog_repo.fingerprint = "test-fingerprint"
    catalog_repo.factions = []
    module_repo = MagicMock()
    return WorldAssemblyResolver(catalog_repo, module_repo)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPackValidation:

    def test_disabled_pack_raises_assembly_pack_error(self):
        """Assembly of a composition referencing a disabled pack must raise AssemblyPackError
        with the pack_id in the message."""
        spec = _make_spec(pack_refs=["frontier_extended_pack"])
        resolver = _mock_resolver()

        disabled_yaml = _make_pack_yaml("frontier_extended_pack", enabled=False)

        with patch("builtins.open", mock_open(read_data=disabled_yaml)):
            with pytest.raises(AssemblyPackError) as exc_info:
                resolver.assemble(spec)

        assert "frontier_extended_pack" in str(exc_info.value)

    def test_missing_pack_raises_assembly_pack_error(self):
        """Assembly of a composition whose pack YAML does not exist must raise
        AssemblyPackError with the pack_id in the message."""
        spec = _make_spec(pack_refs=["nonexistent_pack"])
        resolver = _mock_resolver()

        with patch("builtins.open", side_effect=FileNotFoundError("not found")):
            with pytest.raises(AssemblyPackError) as exc_info:
                resolver.assemble(spec)

        assert "nonexistent_pack" in str(exc_info.value)

    def test_unsatisfied_dependency_raises_assembly_pack_error(self):
        """Assembly of a composition whose pack has a dependency that is disabled must
        raise AssemblyPackError naming the missing/disabled dependency."""
        spec = _make_spec(pack_refs=["swamp_border_pack"])
        resolver = _mock_resolver()

        # swamp_border_pack depends on base_world_pack which is disabled
        pack_yaml = _make_pack_yaml("swamp_border_pack", enabled=True, dependencies=["base_world_pack"])
        dep_yaml = _make_pack_yaml("base_world_pack", enabled=False)

        yaml_map = {
            "data/content/packs/swamp_border_pack.yaml": pack_yaml,
            "data/content/packs/base_world_pack.yaml": dep_yaml,
        }

        def _open_side_effect(path, *args, **kwargs):
            path_str = str(path)
            for key, content in yaml_map.items():
                if key in path_str:
                    return mock_open(read_data=content)()
            raise FileNotFoundError(f"Unexpected path: {path_str}")

        with patch("builtins.open", side_effect=_open_side_effect):
            with pytest.raises(AssemblyPackError) as exc_info:
                resolver.assemble(spec)

        assert "base_world_pack" in str(exc_info.value)

    def test_empty_pack_refs_passes_without_error(self):
        """Assembly of a composition with empty pack_refs must not raise AssemblyPackError
        (no file I/O should occur for pack validation at all)."""
        spec = _make_spec(pack_refs=[])
        resolver = _mock_resolver()

        # Patch assemble's normalization path so we don't need real modules
        # We only need to confirm that pack validation itself never fires.
        with patch("builtins.open", side_effect=FileNotFoundError("should not be called")) as mock_file:
            # The FileNotFoundError would be raised if pack validation runs.
            # We expect the error to come from somewhere else (normalization or module loading),
            # NOT from AssemblyPackError.
            try:
                resolver.assemble(spec)
            except AssemblyPackError:
                pytest.fail("AssemblyPackError must not be raised when pack_refs is empty")
            except Exception:
                # Any other exception is fine — means we got past pack validation
                pass

        # Verify open was not called for any pack path (it may be called for other reasons
        # but specifically not for pack validation which only triggers when pack_refs is non-empty)
        for call in mock_file.call_args_list:
            call_path = str(call[0][0]) if call[0] else ""
            assert "data/content/packs" not in call_path, (
                f"Pack validation should not open pack files when pack_refs is empty; "
                f"got open({call_path!r})"
            )
