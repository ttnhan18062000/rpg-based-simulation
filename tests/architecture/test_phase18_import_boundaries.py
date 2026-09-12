from __future__ import annotations

import ast
import os
from collections import Counter


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


PinnedKey = tuple[str, str, tuple[str, ...]]


def _count_boundary_imports(root_dir: str, module_prefix: str) -> Counter[PinnedKey]:
    seen: Counter[PinnedKey] = Counter()
    for path, rel_path in _iter_py_files(root_dir):
        tree = _parse(path)
        skip_lines = _type_checking_lines(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.lineno in skip_lines:
                continue
            if not (node.module and node.module.startswith(module_prefix)):
                continue
            seen[(rel_path, node.module, _names_as_written(node))] += 1
    return seen


def _assert_pinned_exactly(
    seen: Counter[PinnedKey], pinned: dict[PinnedKey, int], boundary_label: str
) -> None:
    for key, count in seen.items():
        rel_path, module, names = key
        expected = pinned.get(key)
        assert expected is not None, (
            f"{rel_path} imports {module} ({names}) crossing the {boundary_label} boundary "
            f"but is not one of the pinned grandfathered exceptions -- if this is a "
            f"deliberate, reviewed addition, pin it in this test and in "
            f"docs/audits/D14_coupling_depth.md"
        )
        assert count == expected, (
            f"{rel_path} imports {module} ({names}) {count} time(s) but the pin expects "
            f"{expected} -- a higher count is a new duplicate of a pinned import, a lower "
            f"count is a stale pin; update the pin deliberately in this test and in "
            f"docs/audits/D14_coupling_depth.md if this is intended"
        )
    for key, expected in pinned.items():
        rel_path, module, names = key
        assert seen[key] == expected, (
            f"pinned {boundary_label} exception {rel_path} ({module}, {names}) expects "
            f"{expected} occurrence(s) but {seen[key]} were found -- a removed or changed "
            f"import must be un-pinned deliberately in this test and in "
            f"docs/audits/D14_coupling_depth.md, not left as a silent permission"
        )


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
# Keyed by (rel_path, module, names) with an exact expected count, not (rel_path, lineno):
# TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE, so an unrelated line-shifting
# edit above a pinned import no longer breaks the pin. This superseded a line-keyed re-pin that
# landed on `main` after this branch diverged (orchestrator.py's import moved 487->498 during
# the "Dormant-mechanism follow-ups" Batch C arc, commit ef3ac48f) -- the content key below
# doesn't care, since the module/names pair is unchanged.
_DOMAINS_OBSERVABILITY_PINNED: dict[PinnedKey, int] = {
    ("src/domains/campaigns/narrative_ledger.py", "src.observability.events", ("SimulationEvent",)): 1,
    ("src/domains/campaigns/orchestrator.py", "src.observability.events", ("SimulationEvent",)): 1,
}


def test_domains_do_not_import_observability_outside_pinned_exceptions():
    seen = _count_boundary_imports("src/domains", "src.observability")
    _assert_pinned_exactly(seen, _DOMAINS_OBSERVABILITY_PINNED, "domains -> observability")


# TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC: pinned grandfathered exceptions to the
# `systems -> engine` boundary, confirmed exhaustively by direct read of the 5 files below.
# Expanding this set requires updating both this test and
# docs/audits/D14_coupling_depth.md's Coupling Inventory together -- not a silent addition.
# Keyed by (rel_path, module, names) with an exact expected count, not (rel_path, lineno):
# TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE, so an unrelated line-shifting
# edit above a pinned import no longer breaks the pin. Two keys are genuinely duplicated
# within intelligence.py and carry expected_count 2, not 1 -- do not "fix" these back to 1:
# `SystemCadence as DefaultCadence, should_run` at lines 832 and 904, and `SimulationDomainLogic`
# from src.engine.domain_logic at lines 84 and 828.
_SYSTEMS_ENGINE_PINNED: dict[PinnedKey, int] = {
    ("src/systems/strategic_systems/intelligence.py", "src.engine.policy", ("GovernorPolicy",)): 1,
    ("src/systems/strategic_systems/intelligence.py", "src.engine.spatial_query", ("SpatialQueryService",)): 1,
    ("src/systems/strategic_systems/intelligence.py", "src.engine.cadence", ("SystemCadence", "should_run")): 1,
    ("src/systems/strategic_systems/intelligence.py", "src.engine.domain_logic", ("SimulationDomainLogic",)): 2,
    ("src/systems/strategic_systems/intelligence.py", "src.engine.cadence", ("should_run",)): 1,
    ("src/systems/strategic_systems/intelligence.py", "src.engine.cadence", ("SystemCadence as DefaultCadence", "should_run")): 2,
    ("src/systems/strategic_systems/intelligence.py", "src.engine.cognition", ("AppraisalSystem",)): 1,
    ("src/systems/strategic_systems/detour.py", "src.engine.domain.lead_routing", ("LeadRoutingSystem",)): 1,
    ("src/systems/strategic_systems/redirection.py", "src.engine.cadence", ("SystemCadence", "should_run")): 1,
    ("src/systems/economy_systems/market.py", "src.engine.legality", ("LegalityServiceV2",)): 1,
    ("src/systems/world_systems/routine.py", "src.engine.legality", ("LegalityServiceV2",)): 1,
}


def test_systems_do_not_import_engine_outside_pinned_exceptions():
    seen = _count_boundary_imports("src/systems", "src.engine")
    _assert_pinned_exactly(seen, _SYSTEMS_ENGINE_PINNED, "systems -> engine")


# TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE: the tests below prove the new
# content-keyed scheme against synthetic tmp_path trees, never against src/. Each builds a
# minimal python file, chdir's into the tmp tree so _iter_py_files' os.path.relpath() produces
# clean src/... rel_paths, and exercises _count_boundary_imports/_assert_pinned_exactly directly.


def test_domains_observability_pin_survives_line_shift(tmp_path, monkeypatch):
    pkg = tmp_path / "src" / "domains" / "campaigns"
    pkg.mkdir(parents=True)
    (pkg / "narrative_ledger.py").write_text(
        "\n".join(f"# unrelated collateral line {i}" for i in range(20)) + "\n"
        "def emit_chronicle_event(self):\n"
        "    from src.observability.events import SimulationEvent\n"
        "    return SimulationEvent\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/domains", "src.observability")
    pinned: dict[PinnedKey, int] = {
        ("src/domains/campaigns/narrative_ledger.py", "src.observability.events", ("SimulationEvent",)): 1,
    }
    _assert_pinned_exactly(seen, pinned, "domains -> observability")


def test_systems_engine_pin_survives_line_shift(tmp_path, monkeypatch):
    pkg = tmp_path / "src" / "systems" / "strategic_systems"
    pkg.mkdir(parents=True)
    (pkg / "intelligence.py").write_text(
        "\n".join(f"# unrelated collateral line {i}" for i in range(40)) + "\n"
        "from src.engine.policy import GovernorPolicy\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/systems", "src.engine")
    pinned: dict[PinnedKey, int] = {
        ("src/systems/strategic_systems/intelligence.py", "src.engine.policy", ("GovernorPolicy",)): 1,
    }
    _assert_pinned_exactly(seen, pinned, "systems -> engine")


def test_domains_new_unpinned_observability_import_fails(tmp_path, monkeypatch):
    pkg = tmp_path / "src" / "domains" / "campaigns"
    pkg.mkdir(parents=True)
    (pkg / "narrative_ledger.py").write_text(
        "from src.observability.events import SimulationEvent\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/domains", "src.observability")
    try:
        _assert_pinned_exactly(seen, {}, "domains -> observability")
    except AssertionError:
        return
    assert False, "expected an unpinned src.observability import to fail"


def test_domains_pinned_import_content_change_fails(tmp_path, monkeypatch):
    pkg = tmp_path / "src" / "domains" / "campaigns"
    pkg.mkdir(parents=True)
    (pkg / "narrative_ledger.py").write_text(
        "from src.observability.events import OtherEvent\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/domains", "src.observability")
    pinned: dict[PinnedKey, int] = {
        ("src/domains/campaigns/narrative_ledger.py", "src.observability.events", ("SimulationEvent",)): 1,
    }
    try:
        _assert_pinned_exactly(seen, pinned, "domains -> observability")
    except AssertionError:
        return
    assert False, "expected a changed import target to fail as unpinned"


def test_domains_pinned_import_copied_to_different_file_fails(tmp_path, monkeypatch):
    campaigns = tmp_path / "src" / "domains" / "campaigns"
    other = tmp_path / "src" / "domains" / "other_domain"
    campaigns.mkdir(parents=True)
    other.mkdir(parents=True)
    (campaigns / "narrative_ledger.py").write_text(
        "from src.observability.events import SimulationEvent\n"
    )
    (other / "copycat.py").write_text(
        "from src.observability.events import SimulationEvent\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/domains", "src.observability")
    pinned: dict[PinnedKey, int] = {
        ("src/domains/campaigns/narrative_ledger.py", "src.observability.events", ("SimulationEvent",)): 1,
    }
    try:
        _assert_pinned_exactly(seen, pinned, "domains -> observability")
    except AssertionError:
        return
    assert False, (
        "expected the same (module, names) copied into a different file to fail -- rel_path "
        "must stay part of the key"
    )


def test_systems_engine_duplicate_beyond_expected_count_fails(tmp_path, monkeypatch):
    pkg = tmp_path / "src" / "systems" / "strategic_systems"
    pkg.mkdir(parents=True)
    (pkg / "intelligence.py").write_text(
        "def a():\n"
        "    from src.engine.cadence import SystemCadence as DefaultCadence, should_run\n"
        "def b():\n"
        "    from src.engine.cadence import SystemCadence as DefaultCadence, should_run\n"
        "def c():\n"
        "    from src.engine.cadence import SystemCadence as DefaultCadence, should_run\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/systems", "src.engine")
    pinned: dict[PinnedKey, int] = {
        (
            "src/systems/strategic_systems/intelligence.py",
            "src.engine.cadence",
            ("SystemCadence as DefaultCadence", "should_run"),
        ): 2,
    }
    try:
        _assert_pinned_exactly(seen, pinned, "systems -> engine")
    except AssertionError:
        return
    assert False, "expected a third copy of a count-2 pinned import to fail"


def test_systems_engine_removed_duplicate_copy_fails(tmp_path, monkeypatch):
    pkg = tmp_path / "src" / "systems" / "strategic_systems"
    pkg.mkdir(parents=True)
    (pkg / "intelligence.py").write_text(
        "def a():\n"
        "    from src.engine.cadence import SystemCadence as DefaultCadence, should_run\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/systems", "src.engine")
    pinned: dict[PinnedKey, int] = {
        (
            "src/systems/strategic_systems/intelligence.py",
            "src.engine.cadence",
            ("SystemCadence as DefaultCadence", "should_run"),
        ): 2,
    }
    try:
        _assert_pinned_exactly(seen, pinned, "systems -> engine")
    except AssertionError:
        return
    assert False, (
        "expected a pinned count-2 import with only 1 remaining occurrence to fail as a stale "
        "pin, not silently pass"
    )


def test_systems_engine_second_copy_of_count_one_pin_fails(tmp_path, monkeypatch):
    pkg = tmp_path / "src" / "systems" / "strategic_systems"
    pkg.mkdir(parents=True)
    (pkg / "intelligence.py").write_text(
        "from src.engine.policy import GovernorPolicy\n"
        "from src.engine.policy import GovernorPolicy\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/systems", "src.engine")
    pinned: dict[PinnedKey, int] = {
        ("src/systems/strategic_systems/intelligence.py", "src.engine.policy", ("GovernorPolicy",)): 1,
    }
    try:
        _assert_pinned_exactly(seen, pinned, "systems -> engine")
    except AssertionError:
        return
    assert False, "expected a second copy of a count-1 pinned import to fail"


def test_domains_observability_type_checking_import_still_skipped(tmp_path, monkeypatch):
    pkg = tmp_path / "src" / "domains" / "campaigns"
    pkg.mkdir(parents=True)
    (pkg / "narrative_ledger.py").write_text(
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from src.observability.event_recorder import EventRecorder\n"
    )
    monkeypatch.chdir(tmp_path)
    seen = _count_boundary_imports("src/domains", "src.observability")
    _assert_pinned_exactly(seen, {}, "domains -> observability")
