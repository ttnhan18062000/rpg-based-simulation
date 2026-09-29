"""
Architecture guard for TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING (Card J,
J1 -- `calamity_intensity`).

Pins the ticket's Level-1 finding: `CalamityService.apply_calamity_consequences()`
(src/world/calamity.py:80) has zero real callers anywhere under `src/`. This is the deeper,
2026-09-20 finding on top of `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`'s original
composition-gap framing -- the producer is not merely starved of a satisfying trigger condition,
it is never invoked at all, making it dead code (`orphan`), not `STARVED` code.

Recorded exit claim: DEFECT (a recommendation only -- the registry write for `calamity_intensity`
belongs to TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION, not this ticket).

This test is a "welcome failure" by design: the moment a real caller is wired in, it starts
failing -- that failure is the signal that J1's DEFECT classification needs to be re-examined and
the registry label correction (owned by the other ticket) picked up, not a bug in the test.

Follows the same inspect.getsource()/source-text-scan technique as
tests/architecture/test_displacement_write_paths.py.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")
_PRODUCER_MODULE = Path("src/world/calamity.py")
_CALL_PATTERN = re.compile(r"\bapply_calamity_consequences\(")


def test_calamity_producer_has_zero_real_callers():
    call_sites: dict[str, list[int]] = {}
    for path in sorted(_SRC_ROOT.rglob("*.py")):
        if path == _PRODUCER_MODULE:
            continue
        text = path.read_text(encoding="utf-8")
        lines = [
            lineno
            for lineno, line in enumerate(text.splitlines(), start=1)
            if _CALL_PATTERN.search(line) and not line.lstrip().startswith("#")
        ]
        if lines:
            call_sites[str(path)] = lines

    assert call_sites == {}, (
        "CalamityService.apply_calamity_consequences() was found to have a real caller "
        f"outside its own defining module: {call_sites}. This test pins the 2026-09-20 "
        "zero-callers finding (TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING, J1). "
        "A new caller is a welcome change, but it means J1's DEFECT classification must be "
        "re-examined and the registry label correction routed through "
        "TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION, not silently absorbed here."
    )


def test_calamity_producer_still_defined_at_its_known_location():
    text = _PRODUCER_MODULE.read_text(encoding="utf-8")
    assert "def apply_calamity_consequences(" in text, (
        "CalamityService.apply_calamity_consequences() moved or was removed from "
        f"{_PRODUCER_MODULE} -- update this guard's module reference if the move was intentional."
    )
