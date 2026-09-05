"""
Architecture guards for TCK-20260905-FAME-DERIVER-LEGEND-FACT (idea 57,
"The Living Legend Feedback Loop" -- FameDeriver + LegendFact).

AC2: campaign_state.entity_fame may only be written by FameExporter.export()
(direct-dict-mutation pattern, matching CultureDriftExporter's/FidelityExporter's
own established pattern -- NOT src/engine/patches.py, which has no CampaignState
write path at all).

AC5: this ticket introduces zero references to BeliefEntry, KnowledgeFact, or
the pre-existing, unrelated LegendaryArrivalEvent/LEGENDARY_ARRIVAL
faction-reputation concept -- LegendFact must never be confused with it.

AC4: this ticket adds zero new PerceptionUpdatePhase call sites in the live
pipeline, and zero new MotivationBiasService.compute_bias_multiplier() call
sites outside its own module.

Also guards the Mechanics/Engine constraint that src/domains/fame/model.py and
src/domains/fame/deriver.py stay pure/stateless (no src.engine or
src.core.state import), matching CultureState/CultureDeriver's and
FidelityState/FidelityDeriver's own constraint.

Follows the same inspect.getsource()/source-text-scan technique as
tests/architecture/test_fidelity_write_paths.py.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import FrozenSet

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")

_ENTITY_FAME_WRITE_PATTERN = re.compile(r"\bentity_fame\s*\[")

# Only the authoritative exporter may index-assign into entity_fame.
ALLOWED_ENTITY_FAME_WRITE_FILES: FrozenSet[str] = frozenset({
    "src/domains/fame/exporter.py",
})

_BELIEF_OR_KNOWLEDGE_OR_LEGENDARY_ARRIVAL_PATTERN = re.compile(
    r"\b(BeliefEntry|KnowledgeFact|LegendaryArrivalEvent|LEGENDARY_ARRIVAL)\s*[\(=]"
)

_FAME_MODULE_FILES = (
    Path("src/domains/fame/model.py"),
    Path("src/domains/fame/deriver.py"),
    Path("src/domains/fame/exporter.py"),
    Path("src/domains/fame/legend.py"),
)

_FAME_DERIVER_AND_MODEL_FILES = (
    Path("src/domains/fame/model.py"),
    Path("src/domains/fame/deriver.py"),
)

_FORBIDDEN_TOP_LEVEL_IMPORT_PREFIXES = ("src.engine", "src.core.state")


def _iter_src_py_files():
    return sorted(_SRC_ROOT.rglob("*.py"))


def test_entity_fame_written_only_through_fame_exporter():
    violations = []

    for path in _iter_src_py_files():
        rel_path = path.as_posix()
        if rel_path in ALLOWED_ENTITY_FAME_WRITE_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        if _ENTITY_FAME_WRITE_PATTERN.search(text):
            violations.append(rel_path)

    assert not violations, (
        "Found entity_fame[...] index-assignment outside "
        "FameExporter.export() (the sole authoritative writer):\n"
        + "\n".join(f"  {path}" for path in violations)
    )


def test_fame_module_no_belief_entry_knowledge_fact_or_legendary_arrival_references():
    violations = {}

    for path in _FAME_MODULE_FILES:
        text = path.read_text(encoding="utf-8")
        matches = _BELIEF_OR_KNOWLEDGE_OR_LEGENDARY_ARRIVAL_PATTERN.findall(text)
        if matches:
            violations[path.as_posix()] = sorted(set(matches))

    assert not violations, (
        "Found BeliefEntry/KnowledgeFact/LegendaryArrivalEvent/LEGENDARY_ARRIVAL "
        "reference(s) in the new fame module -- LegendFact must never be confused "
        "with the pre-existing, unrelated LEGENDARY_ARRIVAL faction-reputation "
        "concept:\n"
        + "\n".join(f"  {path}: {matches}" for path, matches in violations.items())
    )


def test_fame_deriver_and_model_no_engine_or_core_state_imports():
    violations = {}

    for path in _FAME_DERIVER_AND_MODEL_FILES:
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
        "Found forbidden src.engine/src.core.state import(s) in a fame "
        "model/deriver module (must stay pure/stateless):\n"
        + "\n".join(f"  {path}: {imports}" for path, imports in violations.items())
    )


def test_fame_module_no_perception_update_phase_call_site_increase():
    phase_text = Path("src/domains/perception/phase.py").read_text(encoding="utf-8")
    pipeline_text = Path("src/engine/pipeline.py").read_text(encoding="utf-8")

    # PerceptionUpdatePhase( must have zero live pipeline call sites -- confirmed
    # dormant per docs/simulation/domains/perception_contract.md and
    # TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION; this ticket must not change that.
    assert "PerceptionUpdatePhase(" not in pipeline_text, (
        "AuthoritativeApplyPipeline.refine() now constructs PerceptionUpdatePhase -- "
        "this ticket must not wire PerceptionUpdatePhase into the live pipeline"
    )

    # compute_bias_multiplier( must have zero call sites outside its own module.
    motivation_service_path = Path("src/domains/motivation/service.py")
    for path in _iter_src_py_files():
        if path == motivation_service_path:
            continue
        text = path.read_text(encoding="utf-8")
        assert "compute_bias_multiplier(" not in text, (
            f"{path.as_posix()} calls compute_bias_multiplier() -- this ticket must "
            "not wire MotivationBiasService.compute_bias_multiplier() into any live "
            "call site"
        )

    # phase.py itself is read here only to confirm it still exists/is unmodified in
    # spirit -- no assertion needed beyond the pipeline.py scan above, since
    # PerceptionUpdatePhase's own definition living in phase.py is expected.
    assert "class PerceptionUpdatePhase" in phase_text


def test_coming_of_age_candidate_roles_unchanged():
    # AC4 companion guard (plan.md's own Acceptance Criteria Map cites this test name):
    # idea 34's _CANDIDATE_ROLES must stay exactly (SHOPKEEPER, WORKER, GUARD) -- this
    # ticket makes LegendFact perceivable/queryable only, it does not extend idea 34's
    # candidate-role set with an ADVENTURER/HERO option.
    from src.ai.coming_of_age import _CANDIDATE_ROLES
    from src.core.enums import EntityRole

    assert _CANDIDATE_ROLES == (EntityRole.SHOPKEEPER, EntityRole.WORKER, EntityRole.GUARD)
