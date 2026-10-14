"""The graph-html JS dependencies live beside the tool and resolve from the tool's own location
(TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL). No network and no npm: only paths and a fake tree."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools import graphify_to_html as g

_REPO = Path(__file__).resolve().parents[2]


def test_js_deps_dir_is_beside_the_tool_and_holds_the_manifest():
    assert g.JS_DEPS_DIR == _REPO / "tools" / "graphify_html"
    assert (g.JS_DEPS_DIR / "package.json").is_file()
    assert (g.JS_DEPS_DIR / "package-lock.json").is_file()
    assert g.SIGMA_JS == g.JS_DEPS_DIR / "node_modules/sigma/dist/sigma.min.js"
    assert g.GRAPHOLOGY_JS == g.JS_DEPS_DIR / "node_modules/graphology/dist/graphology.umd.min.js"


def test_paths_do_not_depend_on_the_working_directory(monkeypatch, tmp_path):
    before = (g.SIGMA_JS, g.GRAPHOLOGY_JS)
    monkeypatch.chdir(tmp_path)
    assert (g.SIGMA_JS, g.GRAPHOLOGY_JS) == before
    assert g.SIGMA_JS.is_absolute() and g.GRAPHOLOGY_JS.is_absolute()


def test_no_package_json_at_the_repo_root():
    tracked = subprocess.run(["git", "ls-files", "package.json", "package-lock.json"], cwd=_REPO,
                             capture_output=True, text=True, check=True).stdout.split()
    assert tracked == []


def test_missing_assets_fail_with_the_install_command(tmp_path):
    with pytest.raises(SystemExit) as exc:
        g.require_js_assets(tmp_path / "sigma.min.js", tmp_path / "graphology.umd.min.js")
    message = str(exc.value)
    assert "missing JS libraries" in message and "sigma.min.js" in message
    assert "npm ci" in message and "tools/graphify_html" in message


def test_present_assets_pass(tmp_path):
    sigma, graphology = tmp_path / "sigma.min.js", tmp_path / "graphology.umd.min.js"
    sigma.write_text("//", encoding="utf-8")
    graphology.write_text("//", encoding="utf-8")
    g.require_js_assets(sigma, graphology)
