"""Module refs in a composition: a disabled ref is left out and is not a missing module (ASM-COMP-001); a module listed twice is refused before any merge."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.content.repository import CatalogRepository
from src.worldassembly.resolve_io import load_composition_spec
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldassembly.schema import ModuleRefSpec
from src.worldmodules.repository import WorldModuleRepository

pytestmark = pytest.mark.worldassembly

BASE_WORLD = "urban_political"
LEFT_OUT = "wolf_den_near_forest"  # a real module this composition does not use


@pytest.fixture(scope="module")
def resolver():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mods = WorldModuleRepository()
    mods.load_all()
    return WorldAssemblyResolver(cat, mods), mods


def _composition(extra_ref):
    comp = load_composition_spec(Path("data/worlds") / BASE_WORLD / "world.yaml")
    return comp.model_copy(update={"module_refs": [*comp.module_refs, extra_ref]})


def _composition_issues(bundle):
    return bundle.assembly_report["composition_validation"]


def test_a_disabled_ref_to_a_real_module_raises_no_missing_module_error_and_adds_nothing(resolver):
    res, mods = resolver
    assert mods.get_module(LEFT_OUT) is not None
    plain = res.assemble(load_composition_spec(Path("data/worlds") / BASE_WORLD / "world.yaml"))
    with_disabled = res.assemble(_composition(ModuleRefSpec(module_id=LEFT_OUT, enabled=False)))
    assert _composition_issues(with_disabled) == []
    assert [r.id for r in with_disabled.world_spec.regions] == [r.id for r in plain.world_spec.regions]


def test_an_enabled_ref_to_an_unknown_module_is_still_refused(resolver):
    res, _mods = resolver
    with pytest.raises(ValueError, match="not found in repository"):
        res.assemble(_composition(ModuleRefSpec(module_id="no_such_module")))


def test_a_module_listed_twice_is_refused_before_any_merge_naming_the_world_the_id_and_both_refs(resolver):
    res, _mods = resolver
    comp = load_composition_spec(Path("data/worlds") / BASE_WORLD / "world.yaml")
    twice = comp.module_refs[0].module_id
    dup = comp.model_copy(update={"module_refs": [*comp.module_refs, ModuleRefSpec(module_id=twice, namespace="second")]})
    index = len(comp.module_refs)
    with pytest.raises(ValueError) as err:
        res.assemble(dup)
    msg = str(err.value)
    assert BASE_WORLD in msg and f"'{twice}'" in msg
    assert "module_refs[0]" in msg and f"module_refs[{index}]" in msg and "namespace='second'" in msg
