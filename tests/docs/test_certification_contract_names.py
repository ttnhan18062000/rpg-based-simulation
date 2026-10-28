"""The certification contract names only the code's names, except inside its documented "earlier name" notes (TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE).

#306 renamed the outcome and field names in ``docs/engine/contracts/certification_contract.md`` to the code's: ``FAILED_DEGRADATION_SEQUENCE``,
``FAILED_RECOVERY_TIMEOUT`` and ``override_applied``. The old names survive only in parenthetical notes that say they are earlier names. This guard
reads the contract (it never edits it) and fails if a legacy name appears anywhere else, so the rename cannot silently regress.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pytest

CONTRACT = Path(__file__).resolve().parents[2] / "docs" / "engine" / "contracts" / "certification_contract.md"

#: Legacy name -> the regex that finds it as a bare name (FAILED_RECOVERY must not match the code's FAILED_RECOVERY_TIMEOUT).
LEGACY = {
    "FAILED_DEGRADATION_ORDER": r"FAILED_DEGRADATION_ORDER",
    "FAILED_RECOVERY": r"FAILED_RECOVERY(?!_TIMEOUT)",
    "hardware_class_override_applied": r"hardware_class_override_applied",
}
NOTE_MARKERS = ("earlier name", "earlier version")


def _uses(name: str, pattern: str) -> List[str]:
    return [line for line in CONTRACT.read_text(encoding="utf-8").splitlines() if re.search(pattern, line)]


@pytest.mark.parametrize("name", LEGACY)
def test_a_legacy_name_appears_only_inside_an_earlier_name_note(name: str) -> None:
    for line in _uses(name, LEGACY[name]):
        assert any(marker in line.lower() for marker in NOTE_MARKERS), f"{name} appears outside an earlier-name note: {line.strip()[:160]}"


@pytest.mark.parametrize("current", ["FAILED_DEGRADATION_SEQUENCE", "FAILED_RECOVERY_TIMEOUT", "override_applied"])
def test_the_code_names_are_the_ones_the_contract_states(current: str) -> None:
    assert current in CONTRACT.read_text(encoding="utf-8")


def test_the_guard_pattern_does_not_match_the_code_name() -> None:
    assert re.search(LEGACY["FAILED_RECOVERY"], "FAILED_RECOVERY_TIMEOUT") is None
    assert re.search(LEGACY["FAILED_RECOVERY"], "(Earlier name `FAILED_RECOVERY`.)") is not None
