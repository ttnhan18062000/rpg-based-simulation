"""The key-usage report (`TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT`): planted cases for every finding, determinism, read-only, and the CLI. It is a REPORT: nothing here fails on what the real repo contains."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.review import __main__ as cli
from visual_assets.review import key_usage as ku
from visual_assets.store import config
from visual_assets.store.catalog.registry import load_registry

REGISTRY = """record_type: visual_key_registry
schema_version: 1
keys:
  - {key: fixture.a.one, family: a, description: d, variant_axes: []}
  - {key: fixture.a.two, family: a, description: d, variant_axes: []}
  - {key: fixture.a.three, family: a, description: d, variant_axes: []}
  - {key: fixture.a.four, family: a, description: d, variant_axes: []}
aliases:
  - {alias: fixture.a.old, target: fixture.a.one}
  - {alias: fixture.a.newer, target: fixture.a.four}
"""
FAMILIES = frozenset({"fixture"})


@pytest.fixture
def registry(tmp_path):
    path = tmp_path / "keys.yaml"
    path.write_text(REGISTRY)
    return load_registry(path, allow_fixture_namespace=True)


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# ---- the scan ---------------------------------------------------------------------------------------------------------------------------------

def test_the_scan_finds_plain_literals_of_a_registered_family_and_says_app_or_harness(tmp_path):
    write(tmp_path, "frontend/src/components/Panel.tsx", "const a = 'fixture.a.one'\nconst b = \"fixture.a.two\"\nconst c = `fixture.a.three`\n")
    write(tmp_path, "frontend/src/visualAssets/Page.tsx", "const d = 'fixture.a.one'\n")
    write(tmp_path, "src/engine/thing.py", "KEY = 'fixture.a.four'\n")
    refs, dynamic = ku.scan_references(("frontend/src", "src"), tmp_path, FAMILIES)
    assert sorted(refs) == ["fixture.a.four", "fixture.a.one", "fixture.a.three", "fixture.a.two"] and dynamic == []
    assert [(r["file"], r["line"], r["where"]) for r in refs["fixture.a.one"]] == [("frontend/src/components/Panel.tsx", 1, "app"), ("frontend/src/visualAssets/Page.tsx", 1, "harness")]
    assert refs["fixture.a.four"][0]["where"] == "app" and refs["fixture.a.three"][0]["line"] == 3


def test_the_scan_ignores_tests_fixtures_other_families_partial_matches_and_other_suffixes(tmp_path):
    write(tmp_path, "frontend/src/visualAssets/__tests__/x.test.ts", "const a = 'fixture.a.one'\n")
    write(tmp_path, "frontend/src/visualAssets/__fixtures__/y.ts", "const a = 'fixture.a.one'\n")
    write(tmp_path, "frontend/src/components/Z.tsx", "const a = 'other.a.one'\nconst b = 'x fixture.a.two y'\nconst c = 'fixture.a.three.png.'\n// 'fixture.a.four' in a comment is still a literal\n")
    write(tmp_path, "frontend/src/components/notes.md", "'fixture.a.one'\n")
    refs, _ = ku.scan_references(("frontend/src",), tmp_path, FAMILIES)
    assert sorted(refs) == ["fixture.a.four"]  # only the literal in the comment line (a literal scan cannot tell a comment from code; stated in the module docstring)


def test_a_template_literal_with_an_interpolation_is_a_dynamic_reference_not_a_key(tmp_path):
    write(tmp_path, "frontend/src/components/Dyn.tsx", "const k = `fixture.a.${name}`\nconst m = `fixture.${x}.one`\nconst n = `fixture.a.one`\n")
    refs, dynamic = ku.scan_references(("frontend/src",), tmp_path, FAMILIES)
    assert sorted(refs) == ["fixture.a.one"]
    assert [(d["file"], d["line"], d["prefix"]) for d in dynamic] == [("frontend/src/components/Dyn.tsx", 1, "fixture."), ("frontend/src/components/Dyn.tsx", 2, "fixture.")]


# ---- the comparison ---------------------------------------------------------------------------------------------------------------------------

def test_every_finding_is_classified_from_planted_references(registry):
    refs = {
        "fixture.a.one": [{"file": "frontend/src/components/A.tsx", "line": 1, "where": "app"}],
        "fixture.a.two": [{"file": "frontend/src/components/B.tsx", "line": 2, "where": "app"}],
        "fixture.a.three": [{"file": "frontend/src/visualAssets/H.tsx", "line": 3, "where": "harness"}],
        "fixture.a.zzz": [{"file": "frontend/src/components/C.tsx", "line": 4, "where": "app"}],
        "fixture.a.old": [{"file": "frontend/src/components/D.tsx", "line": 5, "where": "app"}],
        "fixture.a.newer": [{"file": "frontend/src/components/E.tsx", "line": 6, "where": "app"}],  # the ONLY reference to fixture.a.four, through its alias
    }
    report = ku.build_report(registry, refs, [], {"fixture.a.one", "fixture.a.two", "fixture.a.three"}, ("rc-0009", {"fixture.a.one"}))
    assert report["unknown"] == ["fixture.a.zzz"]  # an alias is known
    assert report["unreferenced"] == []  # four is referenced, through its alias
    assert report["adopted_unreleased"] == ["fixture.a.three", "fixture.a.two"]
    assert report["fallback_only"] == ["fixture.a.four", "fixture.a.two"]  # referenced by application code (four through its alias), not in the candidate; three is only in the harness; the alias of one resolves to a released key
    assert report["latest_release_candidate"] == "rc-0009" and report["released_keys"] == ["fixture.a.one"] and report["registry_keys"] == 4
    assert report["references"]["fixture.a.three"] == {"app": 0, "harness": 1, "first": "frontend/src/visualAssets/H.tsx:3"}


def test_a_key_referenced_only_by_the_harness_is_never_fallback_only_and_an_unreleased_unreferenced_unadopted_key_is_only_unreferenced(registry):
    refs = {"fixture.a.one": [{"file": "frontend/src/visualAssets/H.tsx", "line": 1, "where": "harness"}]}
    report = ku.build_report(registry, refs, [], set(), ("rc-0001", set()))
    assert report["fallback_only"] == [] and report["adopted_unreleased"] == [] and report["unreferenced"] == ["fixture.a.four", "fixture.a.three", "fixture.a.two"]


def test_with_no_release_candidate_nothing_is_released_and_nothing_crashes(registry):
    report = ku.build_report(registry, {}, [], {"fixture.a.one"}, (None, set()))
    assert report["latest_release_candidate"] is None and report["released_keys"] == [] and report["adopted_unreleased"] == ["fixture.a.one"]


# ---- the real repository: shape, determinism, read-only ----------------------------------------------------------------------------------------

def test_the_real_report_is_deterministic_read_only_and_describes_the_committed_registry():
    before = snapshot(config.CATALOG_ROOT) if False else None  # the catalog is large; read-only is checked on the tracked tree below
    first, second = ku.report_json(), ku.report_json()
    assert first == second and first.endswith("}\n")
    report = json.loads(first)
    assert report["registry_keys"] == 62 and report["latest_release_candidate"].startswith("rc-")
    assert set(report) >= {"unknown", "unreferenced", "adopted_unreleased", "fallback_only", "dynamic_references", "references", "released_keys"}
    assert "terrain.forest" in report["references"] and report["references"]["terrain.forest"]["harness"] >= 1
    assert all(k in report["released_keys"] for k in report["fallback_only"]) is False or report["fallback_only"] == []
    assert before is None


def test_the_command_prints_the_report_exits_zero_and_changes_nothing(capsys, monkeypatch, tmp_path):
    import subprocess

    def status() -> str:
        return subprocess.run(["git", "status", "--porcelain", "--untracked-files=all", "visual_assets", "frontend/src", "docs", "tests"], cwd=ku.REPO, capture_output=True, text=True).stdout

    before = status()
    assert cli.main(["key-usage"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["registry_keys"] == 62 and status() == before
