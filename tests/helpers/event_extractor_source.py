"""Source text of the event extractor: the facade plus every module of the extraction package, found by glob so a new module is covered."""
from __future__ import annotations

from pathlib import Path

_OBSERVABILITY = Path(__file__).resolve().parents[2] / "src" / "observability"


def extractor_source() -> str:
    """event_extractor.py and every .py file under src/observability/extraction/ (recursive), concatenated."""
    paths = [_OBSERVABILITY / "event_extractor.py", *sorted((_OBSERVABILITY / "extraction").glob("**/*.py"))]
    return "\n".join(p.read_text(encoding="utf-8") for p in paths)
