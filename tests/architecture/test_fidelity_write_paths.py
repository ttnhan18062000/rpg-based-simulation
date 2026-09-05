"""
Architecture guards for TCK-20260905-CHRONICLE-FIDELITY-DRIFT (idea 62,
"Generations Misremember" -- Chronicle fidelity drift).

AC4: campaign_state.historical_drift may only be written by
FidelityExporter.export() (direct-dict-mutation pattern, matching
CultureDriftExporter's own established pattern -- NOT src/engine/patches.py,
which has no CampaignState write path at all).

AC5: this ticket introduces zero references to BeliefEntry or KnowledgeFact,
and zero changes to CultureDeriver's own read/write behavior.

Also guards the Mechanics/Engine constraint that src/domains/fidelity/model.py
and src/domains/fidelity/deriver.py stay pure/stateless (no src.engine or
src.core.state import), matching CultureState/CultureDeriver's own constraint.

Follows the same inspect.getsource()/source-text-scan technique as
tests/architecture/test_clan_reputation_write_paths.py and
tests/architecture/test_social_write_paths.py.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import FrozenSet

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")

_HISTORICAL_DRIFT_WRITE_PATTERN = re.compile(r"\bhistorical_drift\s*\[")

# Only the authoritative exporter may index-assign into historical_drift.
ALLOWED_HISTORICAL_DRIFT_WRITE_FILES: FrozenSet[str] = frozenset({
    "src/domains/fidelity/exporter.py",
})

_BELIEF_OR_KNOWLEDGE_PATTERN = re.compile(r"\b(BeliefEntry|KnowledgeFact)\s*\(")

_FIDELITY_MODULE_FILES = (
    Path("src/domains/fidelity/model.py"),
    Path("src/domains/fidelity/deriver.py"),
)

_FORBIDDEN_TOP_LEVEL_IMPORT_PREFIXES = ("src.engine", "src.core.state")


def _iter_src_py_files():
    return sorted(_SRC_ROOT.rglob("*.py"))


def test_historical_drift_written_only_through_fidelity_exporter():
    violations = []

    for path in _iter_src_py_files():
        rel_path = path.as_posix()
        if rel_path in ALLOWED_HISTORICAL_DRIFT_WRITE_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        if _HISTORICAL_DRIFT_WRITE_PATTERN.search(text):
            violations.append(rel_path)

    assert not violations, (
        "Found historical_drift[...] index-assignment outside "
        "FidelityExporter.export() (the sole authoritative writer):\n"
        + "\n".join(f"  {path}" for path in violations)
    )


def test_fidelity_module_no_belief_entry_or_knowledge_fact_references():
    violations = {}

    for path in _FIDELITY_MODULE_FILES:
        text = path.read_text(encoding="utf-8")
        matches = _BELIEF_OR_KNOWLEDGE_PATTERN.findall(text)
        if matches:
            violations[path.as_posix()] = sorted(set(matches))

    exporter_text = Path("src/domains/fidelity/exporter.py").read_text(encoding="utf-8")
    exporter_matches = _BELIEF_OR_KNOWLEDGE_PATTERN.findall(exporter_text)
    if exporter_matches:
        violations["src/domains/fidelity/exporter.py"] = sorted(set(exporter_matches))

    assert not violations, (
        "Found BeliefEntry(...)/KnowledgeFact(...) construction in the new "
        "fidelity module -- this ticket must not repurpose either class:\n"
        + "\n".join(f"  {path}: {matches}" for path, matches in violations.items())
    )


def test_fidelity_deriver_and_model_no_engine_or_core_state_imports():
    violations = {}

    for path in _FIDELITY_MODULE_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        bad_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(_FORBIDDEN_TOP_LEVEL_IMPORT_PREFIXES):
                        bad_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(_FORBIDDEN_TOP_LEVEL_IMPORT_PREFIXES):
                    bad_imports.append(module)
        if bad_imports:
            violations[path.as_posix()] = bad_imports

    assert not violations, (
        "Found forbidden src.engine/src.core.state import(s) in a fidelity "
        "model/deriver module (must stay pure/stateless):\n"
        + "\n".join(f"  {path}: {imports}" for path, imports in violations.items())
    )
