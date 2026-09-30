"""The `domain`/`level` markers registered in pyproject.toml must match the taxonomy doc's vocabulary.

docs/testing/test_taxonomy.md section 10 is the single definition; pyproject.toml only registers the
marker names, and this test fails if the two drift.
"""

import tomllib
from pathlib import Path

from tools.test_architecture import marker_check

REPO_ROOT = Path(__file__).resolve().parents[3]


def _registered_marker_names():
    cfg = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return {m.split(":", 1)[0].split("(", 1)[0].strip() for m in cfg["tool"]["pytest"]["ini_options"]["markers"]}


def test_vocabulary_block_parses_with_expected_shape():
    vocab = marker_check.load_vocabulary(REPO_ROOT)
    assert set(vocab) == {"markers", "domain", "level"}
    assert vocab["domain"] and vocab["level"]
    assert len(set(vocab["domain"])) == len(vocab["domain"])
    assert len(set(vocab["level"])) == len(vocab["level"])


def test_registered_markers_match_doc_vocabulary_exactly():
    doc_markers = set(marker_check.load_vocabulary(REPO_ROOT)["markers"])
    registered = _registered_marker_names()
    assert doc_markers <= registered, f"documented but unregistered: {sorted(doc_markers - registered)}"
    # every registered name that the vocabulary claims must be exactly the documented set
    assert {"domain", "level"} == doc_markers


def test_domain_values_cover_report_import_map():
    """Every domain the report can derive from imports is a documented domain value."""
    from tools.test_architecture import core_rpg_report as report

    vocab = marker_check.load_vocabulary(REPO_ROOT)
    assert set(report.DOMAIN_IMPORT_PREFIXES) <= set(vocab["domain"])
