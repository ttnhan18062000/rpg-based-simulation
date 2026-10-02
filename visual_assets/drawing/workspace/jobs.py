"""Per-call job directories under <workspace>/.jobs, always removed afterwards."""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

from visual_assets.drawing import config

log = logging.getLogger("aseprite_mcp")


class Job:
    def __enter__(self) -> Path:
        jobs = config.WORKSPACE / ".jobs"
        jobs.mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(dir=jobs))
        return self.path

    def __exit__(self, *exc) -> None:
        try:
            shutil.rmtree(self.path)
        except OSError as err:
            # never mask the real outcome, but never be silent about a leaked job dir either
            log.warning("could not remove job dir %s: %s", self.path.name, err)
