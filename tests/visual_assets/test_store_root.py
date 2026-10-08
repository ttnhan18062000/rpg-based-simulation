"""Root resolution of the store (`TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT`): the default is the checkout the module lives in, `VISUAL_ASSETS_CHECKOUT` names another one,
and anything that is not a store checkout is refused, never corrected. The server's behaviour over stdio is in `drawing/test_store_root_stdio.py`."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from visual_assets.store import config

REPO = Path(__file__).resolve().parents[2]


def fake_checkout(tmp_path: Path, name: str = "wt", *, worktree: bool = True, branch: str = "feature-x") -> Path:
    root = tmp_path / name
    (root / "visual_assets" / "catalog").mkdir(parents=True)
    (root / "visual_assets" / "catalog" / "STORE_FORMAT").write_text("store_format_version: 1\n")
    if worktree:
        gitdir = tmp_path / f"{name}.gitdir"
        gitdir.mkdir()
        (gitdir / "HEAD").write_text(f"ref: refs/heads/{branch}\n")
        (root / ".git").write_text(f"gitdir: {gitdir}\n")
    else:
        (root / ".git").mkdir()
        (root / ".git" / "HEAD").write_text(f"ref: refs/heads/{branch}\n")
    return root


def test_without_the_variable_the_root_is_the_checkout_the_module_lives_in():
    directory, source = config.resolve_visual_assets_dir({})
    assert source == "module" and directory == Path(config.__file__).resolve().parents[1]
    assert config.resolve_visual_assets_dir({config.ENV_CHECKOUT: "   "})[1] == "module"  # an empty value (what `${VAR:-}` passes through) counts as unset


def test_the_variable_names_another_checkout_and_every_root_follows_it(tmp_path):
    root = fake_checkout(tmp_path)
    directory, source = config.resolve_visual_assets_dir({config.ENV_CHECKOUT: str(root)})
    assert (directory, source) == (root / "visual_assets", "env")
    # the roots are derived from it in a fresh interpreter (they are module constants, read at import)
    code = "import json; from visual_assets.store import config as c; print(json.dumps([str(c.CATALOG_ROOT), str(c.QUARANTINE_ROOT), str(c.REVIEW_ROOT), str(c.DRAFTS_ROOT)]))"
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True, check=True, env={"VISUAL_ASSETS_CHECKOUT": str(root), "PATH": "/usr/bin:/bin"}).stdout
    base = str(root.resolve() / "visual_assets")
    assert json.loads(out) == [f"{base}/catalog", f"{base}/catalog/.quarantine", f"{base}/catalog/.review", f"{base}/drafts"]


@pytest.mark.parametrize("make, fragment", [
    (lambda tmp: "relative/path", "absolute"),
    (lambda tmp: str(tmp / "missing"), "existing directory"),
    (lambda tmp: str(_without(fake_checkout(tmp, "nogit"), ".git")), "not a git checkout"),
    (lambda tmp: str(_without(fake_checkout(tmp, "nocatalog"), "visual_assets/catalog/STORE_FORMAT")), "not a store checkout"),
])
def test_anything_that_is_not_a_store_checkout_is_refused_with_a_reason(tmp_path, make, fragment):
    with pytest.raises(config.StoreRootError, match=fragment):
        config.resolve_visual_assets_dir({config.ENV_CHECKOUT: make(tmp_path)})


def _without(root: Path, relative: str) -> Path:
    target = root / relative
    if target.is_dir():
        import shutil

        shutil.rmtree(target)
    else:
        target.unlink()
    return root


def test_a_refused_root_stops_a_fresh_interpreter_instead_of_falling_back(tmp_path):
    out = subprocess.run([sys.executable, "-c", "import visual_assets.store.config"], cwd=REPO, capture_output=True, text=True,
                         env={"VISUAL_ASSETS_CHECKOUT": str(tmp_path / "missing"), "PATH": "/usr/bin:/bin"})
    assert out.returncode != 0 and "StoreRootError" in out.stderr


def test_the_label_is_path_free_and_names_checkout_branch_kind_and_source(tmp_path):
    linked = fake_checkout(tmp_path, "wt", branch="visual-asset-x")
    plain = fake_checkout(tmp_path, "main", worktree=False, branch="main")
    assert config.describe_root(linked / "visual_assets", "env") == {"checkout": "wt", "branch": "visual-asset-x", "source": "env", "linked_worktree": True}
    assert config.describe_root(plain / "visual_assets", "module") == {"checkout": "main", "branch": "main", "source": "module", "linked_worktree": False}
    assert "/" not in json.dumps(config.describe_root(linked / "visual_assets", "env"))
    (linked / ".git").write_text("gitdir: /nonexistent\n")
    assert config.describe_root(linked / "visual_assets", "env")["branch"] == "unknown"  # a broken .git degrades the label, never the store
