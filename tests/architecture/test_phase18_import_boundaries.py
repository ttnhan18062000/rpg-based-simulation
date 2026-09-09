from __future__ import annotations

import ast
import os


def _type_checking_lines(tree: ast.AST) -> set[int]:
    """Line numbers covered by an `if TYPE_CHECKING:` block.

    Mirrors the collect-line-ranges technique in
    tests/architecture/test_api_read_model_guard.py so real (non-type-only) imports can be
    told apart from type-checking-only ones.
    """
    lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            is_tc = (
                (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING")
                or (isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")
            )
            if is_tc:
                for child in ast.walk(node):
                    if hasattr(child, "lineno"):
                        lines.add(child.lineno)
    return lines


def _iter_py_files(root_dir: str):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                yield path, os.path.relpath(path).replace(os.sep, "/")


def _parse(path: str) -> ast.AST:
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    return ast.parse(source, filename=path)


def _names_as_written(node: ast.ImportFrom) -> tuple[str, ...]:
    return tuple(sorted(
        alias.name if alias.asname is None else f"{alias.name} as {alias.asname}"
        for alias in node.names
    ))


def test_entity_models_do_not_import_domain_services():
    # Enforce static analysis check: src/core/ must never import src/domains/
    for path, rel_path in _iter_py_files("src/core"):
        tree = _parse(path)
        skip_lines = _type_checking_lines(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if node.lineno in skip_lines:
                continue
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("src.domains"):
                    assert False, f"Violation: core file {rel_path} imports domain services! ({node.module})"
            else:
                for alias in node.names:
                    assert not alias.name.startswith("src.domains"), (
                        f"Violation: core file {rel_path} imports domain services! ({alias.name})"
                    )


def test_observability_engine_imports_go_through_kernel_facade():
    # src/observability/'s src.engine coupling must route through the Kernel facade only
    # (established by TCK-20260627-P2G-KERNEL-FACADE) -- never a lower-level engine internal
    # like WorldIndexService directly. See docs/guides/observability.md's Architecture boundary
    # note.
    for path, rel_path in _iter_py_files("src/observability"):
        tree = _parse(path)
        skip_lines = _type_checking_lines(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if node.lineno in skip_lines:
                continue
            if isinstance(node, ast.ImportFrom):
                if not (node.module and node.module.startswith("src.engine")):
                    continue
                ok = (
                    node.module == "src.engine.kernel"
                    and len(node.names) == 1
                    and node.names[0].name == "Kernel"
                    and node.names[0].asname is None
                )
                assert ok, (
                    f"{rel_path}:{node.lineno} imports directly from src.engine "
                    f"({node.module}) instead of routing through the Kernel facade "
                    f"('from src.engine.kernel import Kernel') -- see "
                    f"TCK-20260627-P2G-KERNEL-FACADE and docs/guides/observability.md's "
                    f"Architecture boundary note"
                )
            else:
                for alias in node.names:
                    assert not alias.name.startswith("src.engine"), (
                        f"{rel_path}:{node.lineno} imports directly from src.engine "
                        f"({alias.name}) instead of routing through the Kernel facade "
                        f"-- see TCK-20260627-P2G-KERNEL-FACADE and "
                        f"docs/guides/observability.md's Architecture boundary note"
                    )


_OBS_DOMAINS_SYSTEMS_ALLOWED_FILES = {
    "src/observability/event_extractor.py",
    "src/observability/event_shapers.py",
    "src/observability/cognition/recorder.py",
}

_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS = {
    ("src.domains.world_emergence.schema", ("WorldEventCategory",)),
    ("src.domains.commitment.abandonment", ("AbandonmentCategory", "AbandonmentEvaluator")),
    ("src.systems.strategic_systems.intelligence", ("_MAX_CONSECUTIVE_REJECTIONS",)),
    ("src.systems.strategic_systems.cognition_export", ("CognitionGraphExporter",)),
}


def test_observability_domains_systems_import_allowlist():
    # src/observability/'s event_extractor.py, event_shapers.py, and cognition/recorder.py
    # are the only files permitted to import from src.domains/src.systems, and only this
    # fixed, pure/stateless allowlist for read-only event classification -- see
    # docs/guides/observability.md's Architecture boundary note. Expanding this allowlist
    # requires updating both this test and that doc note together, not a silent addition.
    for path, rel_path in _iter_py_files("src/observability"):
        tree = _parse(path)
        skip_lines = _type_checking_lines(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if node.lineno in skip_lines:
                continue
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                touches = module.startswith("src.domains") or module.startswith("src.systems")
            else:
                module = ", ".join(alias.name for alias in node.names)
                touches = any(
                    alias.name.startswith("src.domains") or alias.name.startswith("src.systems")
                    for alias in node.names
                )
            if not touches:
                continue
            assert rel_path in _OBS_DOMAINS_SYSTEMS_ALLOWED_FILES, (
                f"{rel_path} imports from src.domains/src.systems but is not in the "
                f"documented allowlist (docs/guides/observability.md Architecture "
                f"boundary note) -- {module}"
            )
            assert (
                isinstance(node, ast.ImportFrom)
                and (module, _names_as_written(node)) in _OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS
            ), (
                f"{rel_path} has a new src.domains/src.systems import not in the pinned "
                f"allowlist ({module}) -- update docs/guides/observability.md's "
                f"Architecture boundary note and this test's allowlist together if this "
                f"is a deliberate, reviewed addition"
            )


# TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC: pinned grandfathered exceptions to the
# `domains -> observability` boundary. Both sites are lazy, method-body imports of the same
# pure SimulationEvent dataclass, guarded by an event-recorder-present check immediately
# above. Expanding this set requires updating both this test and
# docs/audits/D14_coupling_depth.md's Coupling Inventory together -- not a silent addition.
# Line 437->440 re-pinned by TCK-20260905-FAME-DERIVER-LEGEND-FACT: adding the
# FameExporter.export() call/import in orchestrator.py._advance_state() shifted this line
# down by 3, per the sibling Fidelity ticket's own documented collateral-drift lesson.
# Line 447->487 re-pinned by TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING: adding
# CatalogRepository/WorldModuleRepository/CatalogScenarioStateBuilder construction to
# __init__() and the entity-spawn/scatter call in _build_initial_state() shifted this line
# down by 40, same collateral-drift pattern as above -- the import itself is unchanged.
_DOMAINS_OBSERVABILITY_PINNED = {
    ("src/domains/campaigns/narrative_ledger.py", 71): (
        "src.observability.events", ("SimulationEvent",),
    ),
    ("src/domains/campaigns/orchestrator.py", 487): (
        "src.observability.events", ("SimulationEvent",),
    ),
}


def test_domains_do_not_import_observability_outside_pinned_exceptions():
    for path, rel_path in _iter_py_files("src/domains"):
        tree = _parse(path)
        skip_lines = _type_checking_lines(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.lineno in skip_lines:
                continue
            if not (node.module and node.module.startswith("src.observability")):
                continue
            key = (rel_path, node.lineno)
            pinned = _DOMAINS_OBSERVABILITY_PINNED.get(key)
            assert pinned is not None, (
                f"{rel_path}:{node.lineno} imports from src.observability ({node.module}) "
                f"but is not one of the pinned grandfathered exceptions -- domains must not "
                f"import observability; if this is a deliberate, reviewed addition, pin it "
                f"in this test and in docs/audits/D14_coupling_depth.md"
            )
            assert (node.module, _names_as_written(node)) == pinned, (
                f"{rel_path}:{node.lineno} is a pinned exception but its import target "
                f"changed to ({node.module}, {_names_as_written(node)}) -- update the pin "
                f"deliberately in this test and in docs/audits/D14_coupling_depth.md if this "
                f"is intended"
            )


# TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC: pinned grandfathered exceptions to the
# `systems -> engine` boundary, confirmed exhaustively by direct read of the 5 files below.
# Expanding this set requires updating both this test and
# docs/audits/D14_coupling_depth.md's Coupling Inventory together -- not a silent addition.
_SYSTEMS_ENGINE_PINNED = {
    ("src/systems/strategic_systems/intelligence.py", 70): (
        "src.engine.policy", ("GovernorPolicy",),
    ),
    ("src/systems/strategic_systems/intelligence.py", 76): (
        "src.engine.spatial_query", ("SpatialQueryService",),
    ),
    ("src/systems/strategic_systems/intelligence.py", 79): (
        "src.engine.cadence", ("SystemCadence", "should_run"),
    ),
    ("src/systems/strategic_systems/intelligence.py", 84): (
        "src.engine.domain_logic", ("SimulationDomainLogic",),
    ),
    ("src/systems/strategic_systems/intelligence.py", 663): (
        "src.engine.cadence", ("should_run",),
    ),
    ("src/systems/strategic_systems/intelligence.py", 828): (
        "src.engine.domain_logic", ("SimulationDomainLogic",),
    ),
    ("src/systems/strategic_systems/intelligence.py", 832): (
        "src.engine.cadence", ("SystemCadence as DefaultCadence", "should_run"),
    ),
    ("src/systems/strategic_systems/intelligence.py", 904): (
        "src.engine.cadence", ("SystemCadence as DefaultCadence", "should_run"),
    ),
    ("src/systems/strategic_systems/intelligence.py", 957): (
        "src.engine.cognition", ("AppraisalSystem",),
    ),
    ("src/systems/strategic_systems/detour.py", 22): (
        "src.engine.domain.lead_routing", ("LeadRoutingSystem",),
    ),
    ("src/systems/strategic_systems/redirection.py", 25): (
        "src.engine.cadence", ("SystemCadence", "should_run"),
    ),
    ("src/systems/economy_systems/market.py", 50): (
        "src.engine.legality", ("LegalityServiceV2",),
    ),
    ("src/systems/world_systems/routine.py", 180): (
        "src.engine.legality", ("LegalityServiceV2",),
    ),
}


def test_systems_do_not_import_engine_outside_pinned_exceptions():
    for path, rel_path in _iter_py_files("src/systems"):
        tree = _parse(path)
        skip_lines = _type_checking_lines(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.lineno in skip_lines:
                continue
            if not (node.module and node.module.startswith("src.engine")):
                continue
            key = (rel_path, node.lineno)
            pinned = _SYSTEMS_ENGINE_PINNED.get(key)
            assert pinned is not None, (
                f"{rel_path}:{node.lineno} imports from src.engine ({node.module}) but is "
                f"not one of the 13 pinned grandfathered exceptions -- systems must not "
                f"import engine; if this is a deliberate, reviewed addition, pin it in this "
                f"test and in docs/audits/D14_coupling_depth.md"
            )
            assert (node.module, _names_as_written(node)) == pinned, (
                f"{rel_path}:{node.lineno} is a pinned exception but its import target "
                f"changed to ({node.module}, {_names_as_written(node)}) -- update the pin "
                f"deliberately in this test and in docs/audits/D14_coupling_depth.md if this "
                f"is intended"
            )
