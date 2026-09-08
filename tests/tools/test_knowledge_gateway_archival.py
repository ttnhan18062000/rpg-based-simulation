"""Architecture guard for TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE's own archival step: the
Knowledge Gateway MCP package no longer lives at its original `tools/` paths, and each module has
a mirror file under `tools/archive/`.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_ARCHIVE_DIR = _TOOLS_DIR / "archive"

_ARCHIVED_FILENAMES = [
    "knowledge_gateway_mcp.py",
    "knowledge_gateway_router.py",
    "knowledge_gateway_packet_assembly.py",
    "knowledge_gateway_cache.py",
    "knowledge_gateway_redaction.py",
    "start_knowledge_gateway_mcp.sh",
]


def test_gateway_modules_archived_not_present_at_old_paths():
    for filename in _ARCHIVED_FILENAMES:
        old_path = _TOOLS_DIR / filename
        assert not old_path.exists(), f"expected {old_path} to no longer exist (archived)"


def test_gateway_modules_exist_at_archive_location():
    for filename in _ARCHIVED_FILENAMES:
        archived_path = _ARCHIVE_DIR / filename
        assert archived_path.exists(), f"expected archived file at {archived_path}"


def test_write_path_guard_exists_and_is_not_archived():
    """The extracted, gateway-independent module must exist at a stable, non-archived location."""
    assert (_TOOLS_DIR / "write_path_guard.py").exists()
    assert not (_ARCHIVE_DIR / "write_path_guard.py").exists()
