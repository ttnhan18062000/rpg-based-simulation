"""
Architecture guards for TCK-20260905-BELIEF-INSTITUTION-DESIGN (idea 63,
"Belief Grows Around Real History").

AC5: campaign_state.belief_institutions may only be written by
BeliefInstitutionExporter.export() (direct-dict-mutation pattern, matching
CultureDriftExporter/FidelityExporter/FameExporter's own established pattern --
NOT src/engine/patches.py, which has no CampaignState write path at all).

AC5: this ticket introduces zero references to BeliefEntry or KnowledgeFact,
and zero writes to ClanState/AuthoritativeState (final_state.clans is
read-only input).

AC6: no new SimQ scoring pillar or CHURCH BLESSING/RESURRECTION wiring is
added by this ticket.

Also guards the Mechanics/Engine constraint that
src/domains/belief_institution/model.py and deriver.py stay pure/stateless
(no src.engine or src.core.state import), matching the sibling Fame/Fidelity
modules' own constraint.

Follows the same inspect.getsource()/source-text-scan technique as
tests/architecture/test_fidelity_write_paths.py.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import FrozenSet

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")

_BELIEF_INSTITUTIONS_WRITE_PATTERN = re.compile(r"\bbelief_institutions\s*\[")

ALLOWED_BELIEF_INSTITUTIONS_WRITE_FILES: FrozenSet[str] = frozenset({
    "src/domains/belief_institution/exporter.py",
})

_BELIEF_OR_KNOWLEDGE_PATTERN = re.compile(r"\b(BeliefEntry|KnowledgeFact)\s*\(")

_CLAN_STATE_MUTATION_PATTERN = re.compile(r"\bclans\s*\[\s*\S+\s*\]\s*=")

_CHURCH_SERVICE_PATTERN = re.compile(r'"BLESSING"|"RESURRECTION"')

_BELIEF_INSTITUTION_MODULE_FILES = (
    Path("src/domains/belief_institution/model.py"),
    Path("src/domains/belief_institution/deriver.py"),
)

def _iter_src_py_files():
    return sorted(_SRC_ROOT.rglob("*.py"))


def test_belief_institutions_written_only_through_belief_institution_exporter():
    violations = []

    for path in _iter_src_py_files():
        rel_path = path.as_posix()
        if rel_path in ALLOWED_BELIEF_INSTITUTIONS_WRITE_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        if _BELIEF_INSTITUTIONS_WRITE_PATTERN.search(text):
            violations.append(rel_path)

    assert not violations, (
        "Found belief_institutions[...] index-assignment outside "
        "BeliefInstitutionExporter.export() (the sole authoritative writer):\n"
        + "\n".join(f"  {path}" for path in violations)
    )


def test_belief_institution_module_no_belief_entry_or_knowledge_fact_references():
    violations = {}

    files_to_check = list(_BELIEF_INSTITUTION_MODULE_FILES) + [
        Path("src/domains/belief_institution/exporter.py"),
        Path("src/domains/belief_institution/__init__.py"),
    ]
    for path in files_to_check:
        text = path.read_text(encoding="utf-8")
        matches = _BELIEF_OR_KNOWLEDGE_PATTERN.findall(text)
        if matches:
            violations[path.as_posix()] = sorted(set(matches))

    assert not violations, (
        "Found BeliefEntry(...)/KnowledgeFact(...) construction in the new "
        "belief_institution module -- this ticket must not repurpose either class:\n"
        + "\n".join(f"  {path}: {matches}" for path, matches in violations.items())
    )


def test_belief_institution_exporter_does_not_mutate_clan_state():
    text = Path("src/domains/belief_institution/exporter.py").read_text(encoding="utf-8")
    deriver_text = Path("src/domains/belief_institution/deriver.py").read_text(encoding="utf-8")

    assert not _CLAN_STATE_MUTATION_PATTERN.search(text), (
        "BeliefInstitutionExporter must not write to the clans dict it receives "
        "read-only (final_state.clans) -- found a clans[...] = assignment."
    )
    assert not _CLAN_STATE_MUTATION_PATTERN.search(deriver_text), (
        "BeliefInstitutionDeriver must not write to the clans dict it receives "
        "read-only -- found a clans[...] = assignment."
    )


def test_belief_institution_module_adds_no_church_service_or_simq_wiring():
    violations = {}

    files_to_check = list(_BELIEF_INSTITUTION_MODULE_FILES) + [
        Path("src/domains/belief_institution/exporter.py"),
    ]
    for path in files_to_check:
        text = path.read_text(encoding="utf-8")
        matches = _CHURCH_SERVICE_PATTERN.findall(text)
        if matches:
            violations[path.as_posix()] = matches

    assert not violations, (
        "Found BLESSING/RESURRECTION references in the belief_institution module -- "
        "this ticket does not wire the CHURCH building's services:\n"
        + "\n".join(f"  {path}: {matches}" for path, matches in violations.items())
    )
