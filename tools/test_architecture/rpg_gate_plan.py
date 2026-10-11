"""Plan an rpg gate report run from rpg's config: does it exist, and which worlds are there to shard over.

TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW. The workflow's ``plan`` job runs this and writes ``ready`` and the ``worlds`` matrix to
``$GITHUB_OUTPUT``. The config (``tests/simulation_quality/rpg_gate/config.yaml``) is rpg's and may not exist yet; then ``ready=false`` and the workflow
stops after saying so in the step summary (green; nothing was tested). The same holds when rpg's metric module file is absent: the simulations are not run
just to produce ``metric_error``. An INVALID config is red.

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
from tools.test_architecture.rpg_gate_harness import DEFAULT_METRICS_MODULE, module_path

DEFAULT_CONFIG = Path("tests/simulation_quality/rpg_gate/config.yaml")
# GitHub rejects a matrix vector with no values, so "no config" still yields a one-value matrix; the shard job's own `if` keeps it from running.
PLACEHOLDER_MATRIX = {"world": ["none"]}


def plan(config_path: Path, metrics_module: str = DEFAULT_METRICS_MODULE, root: Optional[Path] = None) -> dict:
    """``{"ready", "invalid", "worlds", "matrix", "message"}``.

    ``ready`` only when the config is valid AND rpg's metric module file exists: running the simulations without the module would bill about 100 runner-minutes a day
    to produce ``metric_error``. An ABSENT config or module is green and nothing runs; an INVALID config is a fault (``invalid``, the CLI exits 1).
    """
    def stop(message: str, invalid: bool = False) -> dict:
        return {"ready": False, "invalid": invalid, "worlds": [], "matrix": json.dumps(PLACEHOLDER_MATRIX), "message": message}

    if not Path(config_path).is_file():
        return stop(f"rpg's config {config_path} does not exist yet: nothing was run")
    try:
        config = load_config(config_path)
    except (BaselineError, OSError, ValueError, TypeError, AttributeError) as exc:
        return stop(f"rpg's config {config_path} is invalid ({exc}): nothing was run", invalid=True)
    if module_path(metrics_module, root) is None:
        return stop("rpg's metric module is absent: nothing was run")
    return {
        "ready": True,
        "invalid": False,
        "worlds": list(config.worlds),
        "matrix": json.dumps({"world": list(config.worlds)}),
        "message": f"{len(config.worlds)} world(s) x {len(config.seeds)} seed(s) x {config.ticks} ticks",
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    result = plan(parser.parse_args(argv).config)
    print(f"ready={'true' if result['ready'] else 'false'}")
    print(f"matrix={result['matrix']}")
    print(f"message={result['message']}")
    return 1 if result["invalid"] else 0  # an invalid config is a fault (red); an absent one is not


if __name__ == "__main__":
    sys.exit(main())
