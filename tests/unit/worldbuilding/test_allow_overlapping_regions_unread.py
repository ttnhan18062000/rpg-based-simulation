"""Pin that no production code reads ``ValidationSpec.allow_overlapping_regions``.

The field is declared, not enforced, and reserved (Mechanics Bible 06, Overlap Policy; owner
decision 11 declines enforcement). A reader would implement a rule the owner has refused, and a
field that looks enforced is the false promise that produced the Bible's earlier "strictly
disjoint, enforced" claim. If this test fails, the new reader needs an owner decision first.
"""

from __future__ import annotations

from pathlib import Path

FIELD = "allow_overlapping_regions"
SRC = Path(__file__).resolve().parents[3] / "src"

# Occurrences that are declarations or writes, never reads.
ALLOWED = {
    # The field declaration itself, and its own description text.
    "worldbuilding/schema.py",
    # Writes `allow_overlapping_regions=False` into a generated ValidationSpec.
    "lab/workflows/generate_simulation_setup.py",
}


def _occurrences() -> dict[str, list[int]]:
    found: dict[str, list[int]] = {}
    for path in sorted(SRC.rglob("*.py")):
        lines = [
            number
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
            if FIELD in line
        ]
        if lines:
            found[path.relative_to(SRC).as_posix()] = lines
    return found


def test_no_production_module_outside_the_allowlist_mentions_the_field() -> None:
    unexpected = set(_occurrences()) - ALLOWED
    assert not unexpected, f"{FIELD} is reserved and unread; new references in: {sorted(unexpected)}"


def test_allowlisted_lab_module_only_writes_the_field() -> None:
    path = SRC / "lab/workflows/generate_simulation_setup.py"
    for line in path.read_text(encoding="utf-8").splitlines():
        if FIELD in line:
            assert f"{FIELD}=" in line and f".{FIELD}" not in line, line


def test_schema_module_only_declares_the_field() -> None:
    path = SRC / "worldbuilding/schema.py"
    for line in path.read_text(encoding="utf-8").splitlines():
        if FIELD in line:
            assert f".{FIELD}" not in line, line


def test_positive_control_scanner_finds_the_known_occurrences() -> None:
    assert set(_occurrences()) == ALLOWED
