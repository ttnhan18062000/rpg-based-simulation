"""Tests for tools/test_architecture/mutation_selection.py (import-based-one-hop selection rule)."""

from pathlib import Path

from tools.test_architecture import mutation_selection as ms

T = "src.core.conservation"


def _w(root: Path, rel: str, text: str) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(text, encoding="utf-8")


def test_direct_one_hop_lazy_and_from_package_imports_are_selected(tmp_path):
    _w(tmp_path, "src/core/conservation.py", "")
    _w(tmp_path, "src/engine/economy.py", "from src.core.conservation import f\n")
    _w(tmp_path, "tests/unit/test_direct.py", "import src.core.conservation\n")
    _w(tmp_path, "tests/unit/test_hop.py", "from src.engine.economy import g\n")
    _w(tmp_path, "tests/unit/test_lazy.py", "def t():\n    from src.core import conservation\n")
    _w(tmp_path, "tests/unit/test_none.py", "import os\n")
    r = ms.resolve(tmp_path, T)
    assert r["one_hop_src_modules"] == ["src.engine.economy"]
    assert r["rule_files"] == ["tests/unit/test_direct.py", "tests/unit/test_hop.py", "tests/unit/test_lazy.py"]


def test_mutation_dir_and_non_test_files_are_not_selected_and_curated_additions_are_listed_separately(tmp_path):
    _w(tmp_path, "src/core/conservation.py", "")
    _w(tmp_path, "tests/mutation/test_m.py", "import src.core.conservation\n")
    _w(tmp_path, "tests/unit/helper.py", "import src.core.conservation\n")
    _w(tmp_path, "tests/unit/test_extra.py", "import os\n")
    r = ms.resolve(tmp_path, T, ["tests/unit/test_extra.py"])
    assert r["rule_files"] == [] and r["curated_additions"] == ["tests/unit/test_extra.py"]
    assert r["files"] == ["tests/unit/test_extra.py"]


def test_hash_is_order_independent_and_changes_with_the_list():
    assert ms.files_hash(["b", "a"]) == ms.files_hash(["a", "b"]) != ms.files_hash(["a"])
