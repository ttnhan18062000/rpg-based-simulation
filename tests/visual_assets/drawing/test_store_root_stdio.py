"""The drawing server serves the checkout `VISUAL_ASSETS_CHECKOUT` names, and says which one (`TCK-20261008-VISUAL-ASSETS-MCP-WORKTREE-STORE-ROOT`).

The server process runs the REAL package from the repo root (as a Claude session started in the main checkout does) while the variable points at a private fake worktree: `submit_candidate` must stage
into THAT worktree's quarantine, leave the real one untouched, and every store tool result must carry the root label. No Aseprite is needed.
"""

from __future__ import annotations

import pytest

from tests.visual_assets.drawing.stdio_support import REPO_ROOT, data, isolated_repo, run, session
from tests.visual_assets.drawing.test_store_tools_stdio import make_handoff
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config as store_config


@pytest.fixture
def world(tmp_path):
    from types import SimpleNamespace

    root = isolated_repo(tmp_path)
    (root / ".git").mkdir()  # a checkout marker: this copy now passes the root check
    (root / ".git" / "HEAD").write_text("ref: refs/heads/the-worktree-branch\n")
    return SimpleNamespace(root=root, workspace=tmp_path / "ws", quarantine=root / "visual_assets" / "catalog" / ".quarantine", catalog=root / "visual_assets" / "catalog")


def call_served(world, name, args=None, *, extra_env=None):
    async def go():
        async with session(world.workspace, REPO_ROOT, extra_env=extra_env if extra_env is not None else {"VISUAL_ASSETS_CHECKOUT": str(world.root)}) as s:
            return await s.call_tool(name, args or {})

    return run(go())


def test_submit_candidate_stages_into_the_named_worktree_and_not_into_the_checkout_the_server_runs_from(world):
    handoff_id = make_handoff(world)
    real_before = snapshot(store_config.QUARANTINE_ROOT) if store_config.QUARANTINE_ROOT.exists() else None
    result = call_served(world, "submit_candidate", {"handoff_id": handoff_id})
    assert not result.isError
    body = data(result)
    assert body["verdict"] == "PASSED" and (world.quarantine / f"{body['intake_id']}").exists()  # staged in the named worktree
    assert not (store_config.QUARANTINE_ROOT / body["intake_id"]).exists()  # and not in the real checkout's quarantine
    if real_before is not None:
        assert snapshot(store_config.QUARANTINE_ROOT) == real_before
    assert body["store_root"] == {"checkout": "repo", "branch": "the-worktree-branch", "source": "env", "linked_worktree": False}


def test_every_store_tool_result_carries_the_root_label(world):
    for name, args in (("store_list", {"kind": "source"}), ("store_show", {"kind": "source", "id": "terrain_forest/r0001"})):
        result = call_served(world, name, args)
        assert not result.isError, name
        assert data(result)["store_root"]["source"] == "env" and data(result)["store_root"]["branch"] == "the-worktree-branch", name


def test_without_the_variable_the_label_names_the_checkout_the_server_runs_from(world):
    result = call_served(world, "store_list", {"kind": "source"}, extra_env={})
    root = data(result)["store_root"]
    assert root["source"] == "module" and root["checkout"] == REPO_ROOT.name


def test_a_variable_that_is_not_a_store_checkout_stops_the_server_with_a_reason(tmp_path):
    import subprocess
    import sys

    out = subprocess.run([sys.executable, "-m", "visual_assets.drawing.server"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
                         env={"VISUAL_ASSETS_CHECKOUT": str(tmp_path / "missing"), "PATH": "/usr/bin:/bin"})
    assert out.returncode != 0 and "StoreRootError" in out.stderr and "existing directory" in out.stderr


def test_the_root_is_printed_to_stderr_at_startup(world):
    import subprocess
    import sys

    out = subprocess.run([sys.executable, "-m", "visual_assets.drawing.server"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL,
                         env={"VISUAL_ASSETS_CHECKOUT": str(world.root), "PATH": "/usr/bin:/bin"})
    assert "visual_assets store root: {'checkout': 'repo', 'branch': 'the-worktree-branch', 'source': 'env'" in out.stderr and out.stdout == ""
