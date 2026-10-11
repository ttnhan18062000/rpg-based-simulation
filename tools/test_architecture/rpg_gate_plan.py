"""Plan an rpg gate report run from rpg's config: does it exist, and which worlds are there to shard over.

TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW. The workflow's ``plan`` job runs this and writes ``have_config`` and the ``worlds`` matrix to
``$GITHUB_OUTPUT``. The config (``tests/simulation_quality/rpg_gate/config.yaml``) is rpg's and may not exist yet; then ``have_config=false`` and the workflow
stops after saying so in the step summary (green; nothing was tested).

CLI::

    python -m tools.test_architecture.rpg_gate_plan --config FILE
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from tools.test_architecture.rpg_gate_baseline import BaselineError, load_config

DEFAULT_CONFIG = Path("tests/simulation_quality/rpg_gate/config.yaml")
# GitHub rejects a matrix vector with no values, so "no config" still yields a one-value matrix; the shard job's own `if` keeps it from running.
PLACEHOLDER_MATRIX = {"world": ["none"]}


def plan(config_path: Path) -> dict:
    """``{"have_config", "worlds", "matrix", "message"}``; an unreadable or invalid config is reported, not raised."""
    if not Path(config_path).is_file():
        return {"have_config": False, "worlds": [], "matrix": json.dumps(PLACEHOLDER_MATRIX), "message": f"rpg's config {config_path} does not exist yet: nothing was run"}
    try:
        config = load_config(config_path)
    except (BaselineError, OSError, ValueError) as exc:
        return {"have_config": False, "worlds": [], "matrix": json.dumps(PLACEHOLDER_MATRIX), "message": f"rpg's config {config_path} is invalid ({exc}): nothing was run"}
    return {
        "have_config": True,
        "worlds": list(config.worlds),
        "matrix": json.dumps({"world": list(config.worlds)}),
        "message": f"{len(config.worlds)} world(s) x {len(config.seeds)} seed(s) x {config.ticks} ticks",
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    result = plan(parser.parse_args(argv).config)
    print(f"have_config={'true' if result['have_config'] else 'false'}")
    print(f"matrix={result['matrix']}")
    print(f"message={result['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
