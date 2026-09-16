"""Tests for tools/generate_mechanism_registry_html.py.

TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW, Scope item 2. A generated HTML page replacing the
hand-authored artifact peer caught and reverted -- every row must come from
all_mechanisms_combined_view(), never hand-typed, and the epic's own measured findings must be
linked to, never restated.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.generate_mechanism_registry_html import render

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"
_OUTPUT_PATH = REPO_ROOT / "docs" / "brainstorm" / "mechanism_registry.html"


@pytest.fixture(scope="module")
def registry_data():
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_render_includes_every_mechanism_id(registry_data):
    content = render(registry_data)
    for m in registry_data["mechanisms"]:
        assert f"<code>{m['id']}</code>" in content, f"{m['id']!r} missing from rendered page"


def test_render_links_to_epic_ticket_rather_than_restating_findings(registry_data):
    """[Load-bearing] The governing principle this ticket exists to satisfy: epic findings are
    linked to, never restated, on this page."""
    content = render(registry_data)
    assert "TCK-20260915-EPIC-MECHANISM-REGISTRY" in content
    # None of the epic's own specific measured figures appear verbatim on this page.
    for forbidden in ("17%", "2 stale atlas badges", "camp seeding"):
        assert forbidden not in content


def test_render_escapes_mechanism_data():
    """A defensive check, not a real current risk (mechanism ids/states are a closed enum from
    mechanisms.yaml) -- confirms html.escape is actually wired in, not just imported."""
    data = {
        "layers": {"entity": {"weight": 1}},
        "mechanisms": [
            {"id": "x", "layer": "entity", "state": "done", "depends_on": []},
        ],
    }
    content = render(data)
    assert "<code>x</code>" in content


def test_render_is_not_truncated(registry_data):
    content = render(registry_data)
    total = len(registry_data["mechanisms"])
    # +1 for the single <thead><tr> header row, which also contains the literal substring "<tr>".
    assert content.count("<tr>") == total + 1


def test_make_target_generates_registry_html():
    result = subprocess.run(
        ["make", "mechanism-registry-html"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert _OUTPUT_PATH.exists()


def test_generator_check_mode_detects_staleness(tmp_path):
    stale_output = tmp_path / "mechanism_registry.html"
    stale_output.write_text("stale content that will never match", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "tools/generate_mechanism_registry_html.py", "--check",
         "--output", str(stale_output)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "STALE" in result.stdout


def test_real_registry_html_is_up_to_date():
    """The load-bearing regression check: the committed file must match a fresh render."""
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    expected = render(data)
    actual = _OUTPUT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/brainstorm/mechanism_registry.html is stale -- "
        "run `make mechanism-registry-html`"
    )
