"""The D56 name-literal scan finds content-id literals by AST and classifies them against the loaded catalogs (TCK-20261014-NAME-LITERALS-IN-SRC-SCAN)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("name_literal_scan", ROOT / "tools" / "name_literal_scan.py")
scan_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_mod)

SOURCE = '''
import logging
logger = logging.getLogger(__name__)
HIGH = {"HILL", "mountain"}

def check(state, tile, pos):
    """A docstring that says forest."""
    logger.info("tile is forest")
    if tile == "forest":
        return 1
    if state.terrain.get(pos, "PLAIN") in HIGH:
        return 2
    if state.terrain[pos] == "WALL":
        return 3
    return 0
'''


def _scan(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sample.py").write_text(SOURCE, encoding="utf-8")
    findings, presenter, cats = scan_mod.scan(tmp_path)
    return {(f.literal, f.match, f.role) for f in findings}, cats


def test_the_scan_classifies_exact_case_missing_and_default_literals(tmp_path):
    rows, cats = _scan(tmp_path)
    assert "terrain" in cats and "forest" in cats["terrain"]
    assert ("forest", "exact", "decision") in rows
    assert ("mountain", "exact", "decision") in rows
    assert ("PLAIN", "case", "default") in rows
    assert ("WALL", "missing", "decision") in rows


def test_the_scan_skips_logging_and_docstrings(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sample.py").write_text(SOURCE, encoding="utf-8")
    findings, _, _ = scan_mod.scan(tmp_path)
    assert all(f.line not in (7, 8) for f in findings)  # the docstring and the logger call
