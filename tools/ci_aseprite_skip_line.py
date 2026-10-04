"""One job-summary line stating how many real-Aseprite tests CI skipped (ADR D10).

Real Aseprite runs only on the licence holder's machine (`make visual-assets-aseprite-local`), so every
`needs_aseprite` test skips on a hosted runner. The skip reason written by `tests/visual_assets/conftest.py` carries
`SKIP_MARKER`, which is how the skips are counted from the pytest JUnit XML. Never raises; always exits 0 (it is a
reporting step, not a gate), same as `tools/ci_junit_summary.py`.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SKIP_MARKER = "requires aseprite and bwrap"


def count_aseprite_skips(path: Path) -> int | None:
    """Skipped `needs_aseprite` tests in a JUnit XML file; None when it is missing or unparseable."""
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    return sum(
        1
        for skipped in root.iter("skipped")
        if SKIP_MARKER in (skipped.get("message") or "")
    )


def render_line(skips: int | None) -> str:
    if skips is None:
        return "Real-Aseprite tests: no JUnit results available (local only, ADR D10)\n"
    return f"Real-Aseprite tests: {skips} `needs_aseprite` skipped: local only, ADR D10 (`make visual-assets-aseprite-local`)\n"


def main(argv: list[str]) -> int:
    try:
        sys.stdout.write(render_line(count_aseprite_skips(Path(argv[0]))))
    except Exception as exc:  # a reporting step never becomes a second CI failure
        sys.stdout.write(f"Real-Aseprite tests: summary failed: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
