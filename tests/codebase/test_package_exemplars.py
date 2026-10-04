"""Tests for `codebase.structure.exemplars` (TCK-20261004-EXEMPLAR-MODULES).

The pin test at the bottom asserts only "no exceptions row for an exemplar". It must not assert that the
file exists: this module runs in the blocking tools-a-e job, so an existence check would fail the PR of a
domain that renames or deletes an exemplar in `src/`. The advisory package validator covers existence.
"""
from __future__ import annotations

import json
from pathlib import Path

from codebase.structure.exemplars import (
    EXCEPTIONS_REL_PATH,
    apply,
    importer_counts,
    measure,
)
from codebase.structure.packages import REGISTRY_REL_PATH

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _body(lines: int = 80, doc: bool = True) -> str:
    head = '"""Docstring."""\n' if doc else ""
    return head + "".join(f"x{i} = {i}\n" for i in range(lines - bool(doc)))


def _row(package: str, **over: object) -> dict:
    row = {
        "package": package, "purpose": f"{package} purpose", "layer": "domain", "status": "active",
        "strictness_tier": "baseline", "exemplar_modules": [], "do_not_imitate": [], "system": None,
        "audit_decision": "keep", "added_date": "2026-10-04", "reviewed": False,
    }
    row.update(over)
    return row


def _tree(tmp_path: Path, files: dict[str, str], rows: list[dict], debt: list[str] = ()) -> Path:
    for rel, text in files.items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    reg = tmp_path / REGISTRY_REL_PATH
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    exc = tmp_path / EXCEPTIONS_REL_PATH
    exc.parent.mkdir(parents=True, exist_ok=True)
    exc.write_text("".join(
        json.dumps({"added_date": "2026-10-02", "ceiling": 1, "file": f, "rule": "X1", "symbol": None,
                    "tool": "ruff", "value": 1}) + "\n" for f in debt))
    return tmp_path


def test_qualification_boundaries_and_exclusions(tmp_path: Path) -> None:
    """Qualification boundaries and exclusions."""
    files = {
        "src/alpha/__init__.py": _body(80),
        "src/alpha/ok.py": _body(80),
        "src/alpha/short.py": _body(59),
        "src/alpha/long.py": _body(401),
        "src/alpha/edge_lo.py": _body(60),
        "src/alpha/edge_hi.py": _body(400),
        "src/alpha/nodoc.py": _body(80, doc=False),
        "src/alpha/debt.py": _body(80),
        "src/alpha/avoid.py": _body(80),
        "src/alpha/sub/deep.py": _body(80),
    }
    row = _row("alpha", do_not_imitate=[{"path": "src/alpha/avoid.py", "reason": "r"}])
    root = _tree(tmp_path, files, [row], debt=["src/alpha/debt.py"])
    picks = measure(root)["alpha"]
    assert len(picks) == 3
    assert set(picks) <= {"src/alpha/ok.py", "src/alpha/edge_lo.py", "src/alpha/edge_hi.py", "src/alpha/sub/deep.py"}
    for bad in ("short", "long", "nodoc", "debt", "avoid", "__init__"):
        assert not any(p.endswith(f"/{bad}.py") for p in picks)


def test_path_banner_docstring_does_not_qualify(tmp_path: Path) -> None:
    """A docstring whose first line is a path, not a sentence (standard rule D2), is not an exemplar."""
    files = {
        "src/alpha/banner_src.py": '"""src/alpha/banner_src.py\n\nDoes a thing."""\n' + _body(80, doc=False),
        "src/alpha/banner_py.py": '"""alpha/banner_py.py"""\n' + _body(80, doc=False),
        "src/alpha/sentence.py": '"""Does a thing in alpha."""\n' + _body(80, doc=False),
    }
    root = _tree(tmp_path, files, [_row("alpha")])
    assert measure(root)["alpha"] == ["src/alpha/sentence.py"]


def test_legacy_and_no_qualifier_give_empty(tmp_path: Path) -> None:
    """Legacy and no qualifier give empty."""
    files = {"src/old/m.py": _body(80), "src/tiny/m.py": _body(10)}
    root = _tree(tmp_path, files, [_row("old", status="legacy"), _row("tiny")])
    assert measure(root) == {"old": [], "tiny": []}


def test_ranking_by_importers_then_path_and_cap(tmp_path: Path) -> None:
    """Ranking by importers then path and cap."""
    files = {f"src/alpha/m{c}.py": _body(80) for c in "abcd"}
    files["src/alpha/user1.py"] = "from src.alpha import md\n"
    files["src/alpha/user2.py"] = "from src.alpha import md, mc\n"
    root = _tree(tmp_path, files, [_row("alpha")])
    picks = measure(root)["alpha"]
    assert picks == ["src/alpha/md.py", "src/alpha/mc.py", "src/alpha/ma.py"]
    assert measure(root) == measure(root)


def test_importer_forms_are_all_counted(tmp_path: Path) -> None:
    """Importer forms are all counted."""
    files = {
        "src/pkg/__init__.py": "",
        "src/pkg/target.py": _body(80),
        "src/pkg/rel_a.py": "from . import target\n",
        "src/pkg/rel_b.py": "from .target import x0\n",
        "src/pkg/sub/__init__.py": "from .. import target\n",
        "src/pkg/sub/deep.py": "from ..target import x0\n",
        "src/other/__init__.py": "",
        "src/other/abs_a.py": "from src.pkg import target\n",
        "src/other/abs_b.py": "from src.pkg.target import x0\n",
        "src/other/abs_c.py": "import src.pkg.target\n",
        "src/other/none.py": "import os\nfrom src.pkg import missing_name\n",
    }
    root = _tree(tmp_path, files, [_row("pkg")])
    assert importer_counts(root)["src/pkg/target.py"] == 7


def test_relative_import_from_package_init(tmp_path: Path) -> None:
    """Relative import from package init."""
    files = {"src/pkg/__init__.py": "from . import target\n", "src/pkg/target.py": _body(80)}
    assert importer_counts(_tree(tmp_path, files, [_row("pkg")]))["src/pkg/target.py"] == 1


def test_self_import_is_not_counted(tmp_path: Path) -> None:
    """Self import is not counted."""
    files = {"src/pkg/target.py": _body(80) + "import src.pkg.target\n"}
    assert "src/pkg/target.py" not in importer_counts(_tree(tmp_path, files, [_row("pkg")]))


def test_exceptions_row_spelled_as_the_real_file_spells_it(tmp_path: Path) -> None:
    """The real baseline keys rows by repo-relative `src/...` paths; a module with such a row never qualifies."""
    real = [json.loads(line) for line in (_REPO_ROOT / EXCEPTIONS_REL_PATH).read_text().splitlines() if line.strip()]
    assert all(r["file"].startswith("src/") and "\\" not in r["file"] for r in real if r["file"].startswith("src"))
    root = _tree(tmp_path, {"src/alpha/m.py": _body(80), "src/alpha/n.py": _body(80)}, [_row("alpha")],
                 debt=["src/alpha/m.py"])
    assert measure(root)["alpha"] == ["src/alpha/n.py"]


def test_apply_is_byte_stable_and_touches_only_changed_rows(tmp_path: Path) -> None:
    """Apply is byte stable and touches only changed rows."""
    files = {"src/alpha/m.py": _body(80), "src/beta/m.py": _body(10)}
    rows = [_row("beta", purpose="café"), _row("alpha")]
    root = _tree(tmp_path, files, rows)
    reg = root / REGISTRY_REL_PATH
    lines = reg.read_text().splitlines()
    assert apply(root) == 1
    after = reg.read_bytes()
    new_lines = after.decode().splitlines()
    assert new_lines[0] == lines[0]  # unchanged row byte-identical, file order kept
    assert json.loads(new_lines[1])["exemplar_modules"] == ["src/alpha/m.py"]
    assert json.loads(new_lines[1])["reviewed"] is False
    assert apply(root) == 0
    assert reg.read_bytes() == after


def test_apply_changes_only_exemplar_modules(tmp_path: Path) -> None:
    """Apply changes only exemplar modules."""
    root = _tree(tmp_path, {"src/alpha/m.py": _body(80)}, [_row("alpha")])
    before = json.loads((root / REGISTRY_REL_PATH).read_text())
    apply(root)
    after = json.loads((root / REGISTRY_REL_PATH).read_text())
    assert {k: v for k, v in after.items() if k != "exemplar_modules"} == {
        k: v for k, v in before.items() if k != "exemplar_modules"}


def test_real_exemplars_have_no_exceptions_row() -> None:
    """Re-pick signal. Deliberately does not check that the file exists (see module docstring)."""
    debt = {json.loads(line)["file"] for line in (_REPO_ROOT / EXCEPTIONS_REL_PATH).read_text().splitlines() if line.strip()}
    rows = [json.loads(line) for line in (_REPO_ROOT / REGISTRY_REL_PATH).read_text().splitlines() if line.strip()]
    flagged = [p for row in rows for p in row["exemplar_modules"] if p in debt]
    assert not flagged, (
        f"exemplar(s) now have a code-health exceptions row: {flagged}. Re-pick with "
        "`python3 -m codebase.structure.exemplars measure`, then `python3 -m codebase.structure.exemplars apply`."
    )


