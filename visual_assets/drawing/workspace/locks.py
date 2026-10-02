"""Per-sprite exclusive file lock (flock): serialises writers of one sprite."""

from __future__ import annotations

import fcntl

from visual_assets.drawing.workspace.revisions import sprite_dir


class SpriteLock:
    def __init__(self, name: str):
        d = sprite_dir(name)
        d.mkdir(parents=True, exist_ok=True)
        self._fh = open(d / ".lock", "w")

    def __enter__(self):
        fcntl.flock(self._fh, fcntl.LOCK_EX)

    def __exit__(self, *exc):
        fcntl.flock(self._fh, fcntl.LOCK_UN)
        self._fh.close()
