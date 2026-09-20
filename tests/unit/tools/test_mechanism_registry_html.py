"""Tests for tools/mechanism_registry/generate_mechanism_registry_html.py.

TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW, Scope item 2. A generated HTML page replacing the
hand-authored artifact peer caught and reverted -- every row must come from
all_mechanisms_combined_view(), never hand-typed, and the epic's own measured findings must be
linked to, never restated.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.mechanism_registry.generate_mechanism_registry_html import render

REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = REPO_ROOT / "registries" / "mechanisms.yaml"
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


def test_render_defines_dark_theme_tokens():
    """[Load-bearing] Published Artifacts render in the viewer's theme -- a hardcoded light
    palette is unreadable on a dark host. Tokens must be redefined under both the
    prefers-color-scheme media query (guarded so an explicit light choice wins) and the explicit
    dark data-theme override, per the standard artifact theming contract."""
    content = render({"layers": {}, "mechanisms": []})
    assert '@media (prefers-color-scheme: dark)' in content
    assert ':root:not([data-theme="light"])' in content
    assert ':root[data-theme="dark"]' in content


def test_render_badges_use_css_classes_not_inline_color_styles(registry_data):
    """Inline per-cell style= colors can't vary by theme -- badges must be theme-token-driven CSS
    classes instead."""
    content = render(registry_data)
    assert "style=" not in content
    assert 'class="badge state-' in content
    assert 'class="badge evidence-' in content


def test_render_repo_target_keeps_working_relative_links(registry_data):
    content = render(registry_data, target="repo")
    assert '<a href="mechanism_priority_view.md">' in content
    assert '<a href="mechanism_verification_view.md">' in content
    assert '<a href="../../tickets/done/mechanism-registry/TCK-20260915-EPIC-MECHANISM-REGISTRY.md">' in content


def test_render_artifact_target_drops_unresolvable_links(registry_data):
    """[Load-bearing] A published artifact can't resolve repo-relative links -- artifact mode must
    not emit a dead <a href> for them. The mechanism ids/facts should still be mentioned as plain
    text, just never as a link that would 404."""
    content = render(registry_data, target="artifact")
    assert "mechanism_priority_view.md" in content
    assert "mechanism_verification_view.md" in content
    assert "TCK-20260915-EPIC-MECHANISM-REGISTRY" in content
    assert '<a href="mechanism_priority_view.md">' not in content
    assert '<a href="mechanism_verification_view.md">' not in content
    assert "../../tickets/done" not in content


def test_render_rejects_unknown_target(registry_data):
    with pytest.raises(ValueError):
        render(registry_data, target="nonexistent")


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
    # Counts only the main "All Mechanisms" table's own rows (each carries data-systems, which
    # the rollup table's own rows never do) -- distinguishes it from the rollup table's own rows,
    # which also use bare <tr>.
    assert content.count("<tr data-systems=") == total


# ---------------------------------------------------------------------------
# TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP
# ---------------------------------------------------------------------------


def test_render_shows_system_per_mechanism_row(registry_data):
    """Peer review: the system tier was built, validated, and given a markdown rollup, but the
    one artifact a person opens rendered no system membership at all. Each mechanism row must
    carry its own real systems, read straight off the mechanism -- not recomputed."""
    content = render(registry_data)
    # combat_resolution is confirmed systems: [combat] on the real registry.
    assert 'data-systems="combat"' in content or ',combat' in content or 'combat,' in content
    assert '<span class="badge system-pill">combat</span>' in content


def test_render_shows_multi_system_mechanism_with_all_its_systems(registry_data):
    """8 of 93 real mechanisms are genuinely multi-system (e.g. movement: combat + world) -- a
    row must show every system it declares, not just the first."""
    content = render(registry_data)
    assert 'data-systems="combat,world"' in content
    assert content.count('<span class="badge system-pill">') >= 2


def test_render_unassigned_mechanism_renders_as_its_own_visible_group():
    """A mechanism with no systems: [] must render as 'unassigned', never silently dropped --
    the same discipline mechanisms_by_system() itself already enforces one level down."""
    data = {
        "layers": {"entity": {"weight": 1}},
        "mechanisms": [{"id": "no_system_here", "layer": "entity", "state": "done"}],
    }
    content = render(data)
    assert 'data-systems="unassigned"' in content
    assert "system-unassigned" in content


def test_render_rollup_reports_counts_never_a_single_badge(registry_data):
    """Epic Assumptions #3, non-negotiable: a system's own numbers must be counts, never a single
    summary status collapsing many mechanisms into one symbol."""
    content = render(registry_data)
    assert "System Rollup" in content
    assert "combat" in content
    # A real count-with-denominator shape ("N/M (") must appear, not a bare status word.
    assert re.search(r">\d+/\d+ \(", content), "rollup must render real N/M counts, not a badge"


def test_render_rollup_shows_rate_against_live_baseline(registry_data):
    """A rate without its baseline isn't a finding -- every system row must be shown next to the
    whole-registry baseline, computed live, not hardcoded."""
    content = render(registry_data)
    assert "vs baseline" in content
    assert "Baseline (all" in content


def test_render_rollup_includes_unassigned_row(registry_data):
    content = render(registry_data)
    assert "<code>unassigned</code>" in content


def test_render_rollup_reuses_build_system_rollup_not_a_second_computation(registry_data):
    """One definition, one renderer reading it -- the HTML page's own rollup numbers must match
    build_system_rollup()'s own real output exactly, not an independently recomputed rate.

    Deliberately imports build_system_rollup from generate_mechanism_registry_html's own
    namespace (not tools.mechanism_registry.registry directly): that module loads `registry` as a
    bare top-level module via its own sys.path shim, a *different* module object from
    `tools.mechanism_registry.registry` -- the one this directory's autouse
    `_empty_system_registry_by_default` fixture monkeypatches. Importing the "same" function via
    the dotted path would silently pick up the patched, zero-systems version and desync from what
    render() actually calls.
    """
    from tools.mechanism_registry.generate_mechanism_registry_html import build_system_rollup

    content = render(registry_data)
    rollup = build_system_rollup(registry_data)
    combat = next(s for s in rollup["systems"] if s["system"] == "combat")
    assert f"{combat['bound']}/{combat['count']}" in content


def test_render_includes_system_filter_control(registry_data):
    """Scope item 1: it must be possible to see the registry grouped or filtered by system, not
    only the aggregate rollup."""
    content = render(registry_data)
    assert 'id="system-filter"' in content
    assert '<option value="combat">combat</option>' in content
    assert '<option value="unassigned">unassigned</option>' in content


def test_render_never_hand_edits_never_recomputes_a_second_way(registry_data):
    """Constraint: generated-only, and the page must say so."""
    content = render(registry_data)
    assert "Do not hand-edit" in content


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
        [sys.executable, "tools/mechanism_registry/generate_mechanism_registry_html.py", "--check",
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
