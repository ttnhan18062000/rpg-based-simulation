"""Tests for tools/handover_transit.py and the hook's transit notice.

TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT. All paths are injected into tmp_path; nothing touches
the real `.claude/handover/` or the real memory dir.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
for _d in (_REPO_ROOT / "tools", _REPO_ROOT / "tools" / "agent-monitoring"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import handover_transit as ht  # noqa: E402
from session_start_handover_hook import build_transit_notice  # noqa: E402

HOOK = _REPO_ROOT / "tools" / "agent-monitoring" / "session_start_handover_hook.py"


def _src(tmp: Path):
    h, m = tmp / "src" / "handover", tmp / "src" / "memory"
    (h / "drafts" / "x").mkdir(parents=True)
    m.mkdir(parents=True)
    (h / "role-a.md").write_text("# A\nbody\n")
    (h / "role-b.md").write_text("# B\n")
    (h / "drafts" / "x" / "d.md").write_text("draft\n")
    (m / "MEMORY.md").write_text("- idx\n")
    return h, m


def _export(tmp: Path, **kw):
    h, m = _src(tmp)
    root = tmp / "transit"
    ht.export_bundle(root=root, handover_dir=h, memory_dir=m, host="hostA", **kw)
    return root, h, m


def test_round_trip_is_byte_identical_and_manifest_matches(tmp_path):
    root, h, m = _export(tmp_path)
    rows = [json.loads(x) for x in (root / "hostA" / ht.MANIFEST).read_text().splitlines()]
    assert {r["path"] for r in rows} == {"role-a.md", "role-b.md", "drafts/x/d.md", "MEMORY.md"}
    h2, m2 = tmp_path / "dst" / "handover", tmp_path / "dst" / "memory"
    ht.import_bundle("hostA", root=root, handover_dir=h2, memory_dir=m2, local_host="hostB")
    for rel in ("role-a.md", "role-b.md", "drafts/x/d.md"):
        assert (h2 / rel).read_bytes() == (h / rel).read_bytes()
    assert (m2 / "MEMORY.md").read_bytes() == (m / "MEMORY.md").read_bytes()
    assert (root / "hostA" / ".imported-hostB").exists()


def test_stored_files_carry_txt_suffix_and_import_strips_it(tmp_path):
    root, *_ = _export(tmp_path)
    stored = {p.name for p in (root / "hostA" / "files").rglob("*") if p.is_file()}
    assert stored == {"role-a.md.txt", "role-b.md.txt", "d.md.txt", "MEMORY.md.txt"}
    assert not list((root / "hostA").rglob("*.md"))


def test_export_flags_select_roles_and_opt_out(tmp_path):
    h, m = _src(tmp_path)
    root = tmp_path / "t"
    ht.export_bundle(roles=["role-a"], drafts=False, memory=False, root=root,
                     handover_dir=h, memory_dir=m, host="hostA")
    rows = [json.loads(x) for x in (root / "hostA" / ht.MANIFEST).read_text().splitlines()]
    assert [r["path"] for r in rows] == ["role-a.md"]


def test_export_replaces_previous_bundle_of_same_host(tmp_path):
    root, h, m = _export(tmp_path)
    (root / "hostA" / "stale.txt").write_text("old")
    ht.export_bundle(root=root, handover_dir=h, memory_dir=m, host="hostA")
    assert not (root / "hostA" / "stale.txt").exists()


def test_export_with_nothing_raises(tmp_path):
    with pytest.raises(ht.TransitError):
        ht.export_bundle(root=tmp_path / "t", handover_dir=tmp_path / "none",
                         memory_dir=tmp_path / "nomem", host="h")


def test_sha_mismatch_aborts_before_any_write(tmp_path):
    root, *_ = _export(tmp_path)
    tampered = next((root / "hostA" / "files" / "memory").glob("*.txt"))
    tampered.write_text("tampered")
    h2, m2 = tmp_path / "dst" / "handover", tmp_path / "dst" / "memory"
    with pytest.raises(ht.TransitError, match="sha256"):
        ht.import_bundle("hostA", root=root, handover_dir=h2, memory_dir=m2, local_host="b")
    assert not h2.exists() and not m2.exists()
    assert not (root / "hostA" / ".imported-b").exists()


def test_differing_local_file_is_backed_up_and_reported(tmp_path):
    root, *_ = _export(tmp_path)
    h2, m2 = tmp_path / "dst" / "handover", tmp_path / "dst" / "memory"
    h2.mkdir(parents=True)
    (h2 / "role-a.md").write_text("local edits\n")
    actions = ht.import_bundle("hostA", root=root, handover_dir=h2, memory_dir=m2, local_host="b")
    assert any(a.startswith("replace") and "role-a.md" in a for a in actions)
    backups = list(h2.glob("role-a.md.local-backup-*"))
    assert len(backups) == 1 and backups[0].read_text() == "local edits\n"
    assert (h2 / "role-a.md").read_text() == "# A\nbody\n"


def test_dry_run_writes_nothing(tmp_path):
    root, *_ = _export(tmp_path)
    h2, m2 = tmp_path / "dst" / "handover", tmp_path / "dst" / "memory"
    actions = ht.import_bundle("hostA", dry_run=True, root=root, handover_dir=h2,
                               memory_dir=m2, local_host="b")
    assert actions and all(a.startswith("create") for a in actions)
    assert not h2.exists() and not m2.exists()
    assert not (root / "hostA" / ".imported-b").exists()


def test_reimport_is_idempotent(tmp_path):
    root, *_ = _export(tmp_path)
    h2, m2 = tmp_path / "dst" / "handover", tmp_path / "dst" / "memory"
    kw = dict(root=root, handover_dir=h2, memory_dir=m2, local_host="b")
    ht.import_bundle("hostA", **kw)
    again = ht.import_bundle("hostA", **kw)
    assert all(a.startswith("unchanged") for a in again)
    assert not list(h2.rglob("*.local-backup-*"))


def test_unsafe_manifest_path_is_refused(tmp_path):
    root, *_ = _export(tmp_path)
    mf = root / "hostA" / ht.MANIFEST
    row = json.loads(mf.read_text().splitlines()[0])
    row["path"] = "../escape.md"
    mf.write_text(json.dumps(row) + "\n")
    with pytest.raises(ht.TransitError, match="unsafe"):
        ht.import_bundle("hostA", root=root, handover_dir=tmp_path / "h",
                         memory_dir=tmp_path / "m", local_host="b")


def test_default_memory_dir_slug_maps_checkout_path():
    p = ht.default_memory_dir()
    assert p.name == "memory" and p.parent.parent.name == "projects"
    assert "/" not in p.parent.name


def test_discard_refuses_without_marker_then_force_works(tmp_path):
    root, *_ = _export(tmp_path)
    with pytest.raises(ht.TransitError, match="marker"):
        ht.discard_bundle("hostA", root=root)
    assert (root / "hostA").exists()
    ht.discard_bundle("hostA", force=True, root=root)
    assert not (root / "hostA").exists()


def test_discard_after_import_marker(tmp_path):
    root, *_ = _export(tmp_path)
    (root / "hostA" / ".imported-b").write_text("x")
    ht.discard_bundle("hostA", root=root)
    assert not (root / "hostA").exists()


def test_status_and_pending(tmp_path):
    root, *_ = _export(tmp_path)
    assert ht.pending_bundles(root, "hostA") == []  # own bundle is never pending
    assert ht.pending_bundles(root, "b") == ["hostA"]
    assert "NOT imported here" in ht.status_lines(root, "b")[0]
    (root / "hostA" / ".imported-b").write_text("x")
    assert ht.pending_bundles(root, "b") == []
    assert "imported here" in ht.status_lines(root, "b")[0]


def test_hook_notice_present_and_absent(tmp_path):
    root, *_ = _export(tmp_path)
    note = build_transit_notice(root, "b")
    assert "hostA" in note and "handover_transit.py import hostA" in note
    (root / "hostA" / ".imported-b").write_text("x")
    assert build_transit_notice(root, "b") == ""
    assert build_transit_notice(tmp_path / "missing", "b") == ""


def test_hook_notice_fails_open_on_corrupt_bundle(tmp_path):
    (tmp_path / "t" / "hostA").mkdir(parents=True)
    assert build_transit_notice(tmp_path / "t", "b") == ""


@pytest.mark.parametrize("source", ["startup", "resume", "clear"])
def test_hook_main_emits_notice_for_each_source(tmp_path, source):
    cwd = tmp_path / "repo"
    bundle = cwd / "agent-working" / "handover-transit" / "otherhost"
    (bundle / "files" / "memory").mkdir(parents=True)
    (bundle / ht.MANIFEST).write_text("{}\n")
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"source": source}),
                         capture_output=True, text=True, cwd=str(cwd), timeout=10)
    assert out.returncode == 0
    ctx = json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "otherhost" in ctx


def test_hook_main_silent_when_no_bundle(tmp_path):
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({"source": "startup"}),
                         capture_output=True, text=True, cwd=str(tmp_path), timeout=10)
    assert out.returncode == 0 and out.stdout == ""
