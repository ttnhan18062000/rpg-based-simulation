"""Structural entry-criterion check: MONITORING-WRITER-UNIFICATION must have landed
(TCK-20260721-CODEX-REPLAY-PARITY).

`tools/agent-monitoring/` is not an importable package name in Python (hyphenated) — this mirrors
`tools/agent-monitoring/manifest.py`'s own technique for importing sibling hyphenated-directory
modules elsewhere in this repo (`importlib.util.spec_from_file_location`), rather than renaming
that directory, which is out of scope and would break every existing caller.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from .errors import EntryCriterionNotMetError

_DEFAULT_TOOLS_DIR = Path(__file__).resolve().parent.parent


def assert_monitoring_writer_landed(tools_dir: Path | None = None) -> None:
    """Raise EntryCriterionNotMetError unless tools/agent-monitoring/writer.py is importable and
    defines both write_line and write_lines callables."""
    if tools_dir is None:
        tools_dir = _DEFAULT_TOOLS_DIR

    writer_path = tools_dir / "agent-monitoring" / "writer.py"
    spec = importlib.util.spec_from_file_location("agent_monitoring_writer", writer_path)
    if spec is None or spec.loader is None:
        raise EntryCriterionNotMetError(
            f"MONITORING-WRITER-UNIFICATION entry criterion not met: could not load a module "
            f"spec for {writer_path} — has tools/agent-monitoring/writer.py landed?"
        )

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError as exc:
        raise EntryCriterionNotMetError(
            f"MONITORING-WRITER-UNIFICATION entry criterion not met: {writer_path} does not "
            f"exist ({exc})"
        ) from exc

    missing = [name for name in ("write_line", "write_lines") if not callable(getattr(module, name, None))]
    if missing:
        raise EntryCriterionNotMetError(
            f"MONITORING-WRITER-UNIFICATION entry criterion not met: {writer_path} is missing "
            f"required callable(s): {missing}"
        )
