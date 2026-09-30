"""Tests for tools/test_architecture/marker_check.py (advisory, report-only). Fixtures are synthetic tmp repos."""

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from tools.test_architecture import core_rpg_report as report
from tools.test_architecture import marker_check

REPO_ROOT = Path(__file__).resolve().parents[3]


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")
    return path


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "docs/testing").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "docs/testing/test_taxonomy.md", root / "docs/testing/test_taxonomy.md")
    return root


def _kinds(findings):
    return sorted(f["finding"] for f in findings)


def test_consistent_markers_have_no_findings(repo):
    _write(repo / "tests/unit/combat/test_ok.py", """
        import pytest
        from src.engine.combat import resolve
        pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("unit")]
    """)
    assert marker_check.run_check(repo, ["tests/unit/combat/test_ok.py"]) == []


def test_mismatched_domain_is_flagged(repo):
    _write(repo / "tests/unit/combat/test_bad.py", """
        import pytest
        from src.engine.combat import resolve
        pytestmark = [pytest.mark.domain("economy"), pytest.mark.level("unit")]
    """)
    assert _kinds(marker_check.run_check(repo, ["tests/unit/combat/test_bad.py"])) == ["domain-mismatch"]


def test_mismatched_level_placement_is_flagged(repo):
    _write(repo / "tests/unit/combat/test_bad.py", """
        import pytest
        from src.engine.combat import resolve
        pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("mechanic_scenario")]
    """)
    assert _kinds(marker_check.run_check(repo, ["tests/unit/combat/test_bad.py"])) == ["level-placement-mismatch"]


def test_unknown_values_are_flagged(repo):
    _write(repo / "tests/unit/misc/test_unknown.py", """
        import pytest
        pytestmark = [pytest.mark.domain("party"), pytest.mark.level("huge")]
    """)
    assert _kinds(marker_check.run_check(repo, ["tests/unit/misc/test_unknown.py"])) == ["unknown-domain", "unknown-level"]


def test_unmarked_core_rpg_test_is_flagged(repo):
    _write(repo / "tests/unit/combat/test_new.py", "from src.engine.combat import resolve\n")
    assert _kinds(marker_check.run_check(repo, ["tests/unit/combat/test_new.py"])) == ["unmarked-core-rpg"]


def test_unmarked_non_core_rpg_test_is_not_flagged(repo):
    _write(repo / "tests/unit/tools/test_plain.py", "import os\n")
    assert marker_check.run_check(repo, ["tests/unit/tools/test_plain.py"]) == []


def test_marker_vocabulary_is_read_from_the_doc(repo):
    doc = repo / "docs/testing/test_taxonomy.md"
    doc.write_text(doc.read_text(encoding="utf-8").replace("  - economy\n", ""), encoding="utf-8")
    _write(repo / "tests/unit/economy/test_x.py", """
        import pytest
        from src.economy import ledger
        pytestmark = [pytest.mark.domain("economy")]
    """)
    assert "unknown-domain" in _kinds(marker_check.run_check(repo, ["tests/unit/economy/test_x.py"]))


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin"})


def test_diff_selects_only_new_or_modified_test_files(repo):
    _write(repo / "tests/unit/combat/test_old.py", "from src.engine.combat import a\n")
    _write(repo / "tests/unit/combat/test_touched.py", "from src.engine.combat import b\n")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    (repo / "tests/unit/combat/test_touched.py").write_text("from src.engine.combat import c\n", encoding="utf-8")
    _write(repo / "tests/unit/combat/test_added.py", "from src.engine.combat import d\n")
    files = marker_check.changed_test_files(repo, "main")
    assert files == ["tests/unit/combat/test_added.py", "tests/unit/combat/test_touched.py"]
    assert _kinds(marker_check.run_check(repo, files)) == ["unmarked-core-rpg", "unmarked-core-rpg"]


def test_cli_always_exits_zero_even_with_findings(repo, capsys):
    _write(repo / "tests/unit/combat/test_new.py", "from src.engine.combat import resolve\n")
    rc = marker_check.main(["--repo-root", str(repo), "--files", "tests/unit/combat/test_new.py"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "ADVISORY unmarked-core-rpg" in out


def test_report_locates_and_classifies_a_newly_marked_test(repo):
    _write(repo / "tests/unit/combat/test_marked.py", """
        import pytest
        from src.engine.combat import resolve
        pytestmark = [pytest.mark.domain("combat"), pytest.mark.level("unit")]
    """)
    layer = report.classification_layer(report.scan_tests(repo))
    entry = layer["declared_markers"]["by_file"]["tests/unit/combat/test_marked.py"]
    assert entry == {"class": "classified", "domains": ["combat"], "levels": ["unit"]}
    assert layer["declared_markers"]["files"] == 1
