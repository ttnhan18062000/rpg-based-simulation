"""Injected scratch-config rollback proof, deliberately without hook transport."""
from __future__ import annotations

from pathlib import Path

from .errors import RootAdmissionRefused


_PROJECT_CONFIG = Path(__file__).resolve().parents[2] / ".codex" / "config.toml"
_PROJECT_ROOT = _PROJECT_CONFIG.parents[1]
_CONFIG_RELATIVE = ".codex/config.toml"


def _contained_config_path(scratch_root: Path | str, relative_path: str) -> Path:
    root = Path(scratch_root).resolve()
    project = _PROJECT_ROOT.resolve()
    if root == project or project in root.parents:
        raise RootAdmissionRefused("scratch rollback adapter refuses the project root or child")
    if not root.is_dir():
        raise RootAdmissionRefused("scratch rollback root must exist")
    if not isinstance(relative_path, str) or not relative_path or Path(relative_path).is_absolute():
        raise RootAdmissionRefused("scratch config path must be a safe relative path")
    supplied = Path(relative_path)
    if any(part in {"", ".", ".."} for part in supplied.parts):
        raise RootAdmissionRefused("scratch config path must be a safe relative path")
    path = (root / supplied).resolve()
    if root not in path.parents:
        raise RootAdmissionRefused("scratch config path escapes injected root")
    if path.relative_to(root).as_posix() != _CONFIG_RELATIVE:
        raise RootAdmissionRefused("scratch rollback adapter is limited to .codex/config.toml")
    return path


class ScratchConfigAdapter:
    """Restore one captured scratch config exactly under its owning identity."""

    def __init__(self, config_path: Path, baseline: bytes, execution_id: str):
        self._path = config_path
        self._baseline = baseline
        self._execution_id = execution_id

    @classmethod
    def capture(
        cls, scratch_root: Path | str, config_relative_path: str, execution_id: str
    ) -> "ScratchConfigAdapter":
        """Capture baseline bytes through the contained adapter seam only."""
        path = _contained_config_path(scratch_root, config_relative_path)
        if not path.is_file():
            raise RootAdmissionRefused("scratch config is missing")
        return cls(path, path.read_bytes(), execution_id)

    def enable(self, enabled_bytes: bytes) -> None:
        self._path.write_bytes(enabled_bytes)

    def restore(self, execution_id: str) -> None:
        if execution_id != self._execution_id:
            raise PermissionError("only the execution identity that enabled config may restore it")
        self._path.write_bytes(self._baseline)

    def is_hook_free(self) -> bool:
        """The captured baseline is authoritative; no hook syntax is invented here."""
        return self._path.read_bytes() == self._baseline
