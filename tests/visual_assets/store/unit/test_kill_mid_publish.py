"""ADR D24: a SIGKILL at fixed points inside `catalogwrite.publish` and `runtime_export` leaves the store readable, `audit_chain` names the orphans, and a re-run completes or refuses cleanly."""

from __future__ import annotations

import shutil
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store import runtime_fixture as fx
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import audit, lock, verify
from visual_assets.store.errors import GateError

REPO = Path(__file__).resolve().parents[4]


@pytest.fixture
def real_layout(env, monkeypatch):
    """The real layout: the quarantine and review areas live INSIDE the catalog root (the kill helper uses it too)."""
    from visual_assets.store import config

    monkeypatch.setattr(config, "QUARANTINE_ROOT", env.catalog / ".quarantine")
    monkeypatch.setattr(config, "REVIEW_ROOT", env.catalog / ".review")
    return env


def run_killed(env, *args) -> str:
    child = subprocess.run([sys.executable, "-m", "tests.visual_assets.store.kill_helper", *args, str(env.tmp)], cwd=REPO, capture_output=True, text=True)
    assert child.returncode == -signal.SIGKILL, child.stderr
    return child.stdout.strip()


def tracked_files(catalog: Path) -> set[str]:
    return {str(p.relative_to(catalog)) for p in catalog.rglob("*") if (p.is_file() or p.is_symlink()) and not str(p.relative_to(catalog)).startswith((".quarantine", ".review", ".store.lock"))}


def covered(path: str, reported: set[str]) -> bool:
    return any(path == r or path.startswith(r + "/") for r in reported)


# the five links of an adoption, in order: source, intake copy, review copy, adoption record, SourceRecord. Point `n` = killed before link n (n = 0: only the
# empty directories exist); `end` = all five landed, killed before the staging directory was removed.
POINTS = ["0", "1", "3", "4", "end"]


def created_paths(catalog: Path) -> set[str]:
    """What the killed adoption created in the tracked tree: every file and directory under `sources/` and `provenance/`."""
    return {str(p.relative_to(catalog)) for base in ("sources", "provenance") for p in (catalog / base).rglob("*")}


def recover(env) -> None:
    """The documented manual recovery (store_contract.md): remove the staging directory, remove exactly the paths `audit` prints, repeat until `chain ok`."""
    for leftover in (env.catalog / ".quarantine").glob(".tmp-publish-*"):
        shutil.rmtree(leftover)
    for _ in range(5):
        report = audit.audit_chain(env.catalog)
        if report.ok:
            return
        for item in report.breaks:
            target = env.catalog / item.path
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
    raise AssertionError(report.breaks)


@pytest.mark.parametrize("point", POINTS)
def test_a_kill_inside_publish_leaves_a_readable_store_and_audit_names_the_orphans(real_layout, point):
    env = real_layout
    run_killed(env, "publish", point)
    leftovers = list((env.catalog / ".quarantine").glob(".tmp-publish-*"))
    assert len(leftovers) == 1  # the staging directory the kill left behind
    report = audit.audit_chain(env.catalog)  # the store stays readable: audit and verify run to the end
    verify.verify()
    assert any(leftovers[0].name in note for note in report.notes)  # the exact leftover directory is named, safe to delete
    reported = {b.path for b in report.breaks}
    assert reported  # something is wrong and audit says so: orphans (or, after the last link, files that are hard links to the staging directory)
    if point != "end":
        files = {p for p in created_paths(env.catalog) if (env.catalog / p).is_file()}
        assert len(files) == int(point) and all(covered(f, reported) for f in files), (files, reported)  # the exact orphan paths are printed
        assert all((env.catalog / p).exists() for p in reported)


@pytest.mark.parametrize("point", POINTS)
def test_a_rerun_after_a_kill_refuses_cleanly_and_changes_nothing(real_layout, point):
    env = real_layout
    intake_id = run_killed(env, "publish", point).splitlines()[0]
    before = snapshot(env.catalog)
    with pytest.raises(GateError) as err:
        s.do_adopt(intake_id)
    assert err.value.code and snapshot(env.catalog) == before  # a coded refusal; never an overwrite


@pytest.mark.parametrize("point", POINTS)
def test_the_manual_recovery_in_the_contract_works(real_layout, point):
    env = real_layout
    intake_id = run_killed(env, "publish", point).splitlines()[0]
    recover(env)
    assert audit.audit_chain(env.catalog).ok
    if point == "end":
        return  # the adoption had fully landed: after the staging directory is gone it is simply complete
    s.do_adopt(intake_id)
    assert audit.audit_chain(env.catalog).ok and not list((env.catalog / ".quarantine").glob(".tmp-publish-*"))


def test_gc_also_removes_the_leftover_staging_directory(real_layout):
    from visual_assets.store import gc as gc_mod

    env = real_layout
    run_killed(env, "publish", "end")
    gc_mod.gc(delete=True, expire_before="2026-01-02T00:00:00Z", decided_at="2026-02-01T00:00:00Z")
    assert audit.audit_chain(env.catalog).ok  # the files lost their second link: the complete adoption reads again


@pytest.mark.parametrize("point", ["first-write", "second-write", "before-rename"])
def test_a_kill_inside_runtime_export_leaves_the_catalog_untouched_and_no_output(env, point):
    fx.build_catalog(env.tmp)
    out_parent = env.tmp / "out"
    out_parent.mkdir()
    before = snapshot(env.catalog)
    run_killed(env, "export", point)
    assert snapshot(env.catalog) == before
    assert not (out_parent / "runtime").exists()  # the output appears only by one rename
    assert [p.name for p in out_parent.iterdir() if not p.name.startswith(".tmp-")] == []
    assert len(list(out_parent.glob(".tmp-*"))) == 1  # the leftover staging directory beside the output; delete it by hand
    verify.verify()
    from visual_assets.store.runtime_export import export_runtime

    for leftover in out_parent.glob(".tmp-*"):
        shutil.rmtree(leftover)
    export_runtime(fx.CATALOG_ID, fx.RELEASE_ID, out_parent / "runtime", allow_fixture_namespace=True)  # the re-run completes
    assert (out_parent / "runtime" / "runtime_manifest.json").is_file()


def test_the_lock_is_free_after_a_kill_mid_publish(real_layout):
    run_killed(real_layout, "publish", "1")
    with lock.store_write_lock("gc", started_at="2026-02-01T00:00:00Z"):
        pass
