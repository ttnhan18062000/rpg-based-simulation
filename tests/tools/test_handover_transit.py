"""Tests for tools/handover_transit.py and the hook's transit notice.

TCK-20261004-HANDOVER-CROSS-MACHINE-TRANSIT. All paths are injected into tmp_path; nothing touches
the real `.claude/handover/` or the real memory dir.
"""
from __future__ import annotations

import json
import os
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


# ---- pruning: only OPEN handover state is exported ------------------------------------------------

def _drafts_world(tmp: Path):
    h, m = tmp / "h", tmp / "m"
    d = h / "drafts"
    (d / "done-folder").mkdir(parents=True)
    (d / "open-folder").mkdir()
    (d / "m0" / "evidence").mkdir(parents=True)
    (d / "merged-notes").mkdir()
    m.mkdir()
    (h / "role-a.md").write_text("# Handover — role-a\n- Branch: `my-branch` · PR: none\n")
    (d / "done-folder" / "TCK-1-DONE.md").write_text("completed draft\n")
    (d / "done-folder" / "README.md").write_text("notes of a finished folder\n")
    (d / "open-folder" / "TCK-2-OPEN.md").write_text("not yet activated\n")
    (d / "m0" / "probe.md").write_text("live probe notes\n")
    (d / "m0" / "evidence" / "raw.txt").write_text("evidence\n")
    (d / "merged-notes" / "x.md").write_text("already on main byte for byte\n")
    (d / "TCK-3-ROOT-DONE.md").write_text("root level completed draft\n")
    (m / "MEMORY.md").write_text("- idx\n")
    return h, m


def _flt(tmp: Path):
    blob = ht._blob_id(tmp / "h" / "drafts" / "merged-notes" / "x.md")
    return ht.DraftFilter(done_ids=frozenset({"TCK-1-DONE"}), main_ids=frozenset({"TCK-3-ROOT-DONE"}),
                          main_blobs=frozenset({blob}))


def _paths(root):
    return {json.loads(x)["path"] for x in (root / "hostA" / ht.MANIFEST).read_text().splitlines()}


def test_completed_unactivated_evidence_and_merged_drafts(tmp_path):
    h, m = _drafts_world(tmp_path)
    ht.export_bundle(root=tmp_path / "t", handover_dir=h, memory_dir=m, host="hostA", draft_filter=_flt(tmp_path))
    kept = _paths(tmp_path / "t")
    assert kept == {"role-a.md", "drafts/open-folder/TCK-2-OPEN.md", "drafts/m0/probe.md", "MEMORY.md"}
    # skipped: done ticket (and its folder's README), evidence dir, byte-identical merged file, root-level main ticket


def test_include_all_restores_everything(tmp_path):
    h, m = _drafts_world(tmp_path)
    ht.export_bundle(root=tmp_path / "t", handover_dir=h, memory_dir=m, host="hostA", draft_filter=None)
    assert len(_paths(tmp_path / "t")) == 9


def test_reexport_deletes_the_stale_files_of_the_rolling_bundle(tmp_path):
    h, m = _drafts_world(tmp_path)
    root = tmp_path / "t"
    ht.export_bundle(root=root, handover_dir=h, memory_dir=m, host="hostA", draft_filter=None)
    assert "drafts/done-folder/TCK-1-DONE.md" in _paths(root)
    ht.export_bundle(root=root, handover_dir=h, memory_dir=m, host="hostA", draft_filter=_flt(tmp_path))
    assert "drafts/done-folder/TCK-1-DONE.md" not in _paths(root)
    assert not list((root / "hostA" / "files").rglob("TCK-1-DONE*"))


def test_memory_stays_and_no_memory_still_opts_out_under_pruning(tmp_path):
    h, m = _drafts_world(tmp_path)
    ht.export_bundle(root=tmp_path / "a", handover_dir=h, memory_dir=m, host="hostA", draft_filter=_flt(tmp_path))
    assert "MEMORY.md" in _paths(tmp_path / "a")
    ht.export_bundle(root=tmp_path / "b", handover_dir=h, memory_dir=m, host="hostA", memory=False, draft_filter=_flt(tmp_path))
    assert "MEMORY.md" not in _paths(tmp_path / "b")


def test_load_draft_filter_reads_local_done_and_origin_main(tmp_path):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}
    def git(*a): subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True, env=env)
    (tmp_path / "agent-working/tickets/done/sub").mkdir(parents=True)
    (tmp_path / "agent-working/tickets/done/sub/TCK-DONE-LOCAL.md").write_text("x")
    (tmp_path / "tracked.md").write_text("main content\n")
    (tmp_path / "TCK-ON-MAIN.md").write_text("y")
    git("init", "-q", "-b", "main"); git("add", "tracked.md", "TCK-ON-MAIN.md"); git("commit", "-q", "-m", "m")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    flt = ht.load_draft_filter(tmp_path)
    assert flt.ticket_closed("TCK-DONE-LOCAL") and flt.ticket_closed("TCK-ON-MAIN") and not flt.ticket_closed("TCK-NEW")
    assert ht._blob_id(tmp_path / "tracked.md") in flt.main_blobs
    assert ht.load_draft_filter(tmp_path, ref="origin/nope").done_ids == {"TCK-DONE-LOCAL"}  # no ref: local done only


# ---- belongs_to --------------------------------------------------------------------------------

from tools.sessions.roster import load_roster  # noqa: E402

_ROSTER = load_roster(_REPO_ROOT)
_WRITER = "agent-working-implementer"


def _rows(root, host="hostA"):
    return [json.loads(x) for x in (root / host / ht.MANIFEST).read_text().splitlines()]


def _export_with_role(tmp, role, **kw):
    h, m = _drafts_world(tmp)
    (h / f"{_WRITER}.md").write_text("# Handover\n- Branch: `feat-x` · PR: #9\n")
    root = tmp / "t"
    ht.export_bundle(root=root, handover_dir=h, memory_dir=m, host="hostA", draft_filter=_flt(tmp),
                     role=role, roster=_ROSTER, worktree="/w/path", branch="feat-x", **kw)
    return root


def test_belongs_to_is_derived_per_kind(tmp_path):
    rows = {r["path"]: r for r in _rows(_export_with_role(tmp_path, _WRITER))}
    note = rows[f"{_WRITER}.md"]["belongs_to"]
    assert note == {"role": _WRITER, "domain": "agent-working", "ticket_id": None, "branch": "feat-x", "kind": "note"}
    draft = rows["drafts/open-folder/TCK-2-OPEN.md"]["belongs_to"]
    assert draft == {"role": _WRITER, "domain": "agent-working", "ticket_id": "TCK-2-OPEN", "branch": None, "kind": "draft"}
    assert rows["MEMORY.md"]["belongs_to"] == {"role": None, "domain": None, "ticket_id": None, "branch": None, "kind": "memory"}
    assert rows["MEMORY.md"]["worktree"] == "/w/path" and rows["MEMORY.md"]["branch"] == "feat-x"


def test_exporting_role_is_explicit_or_resolved_never_guessed():
    assert ht.exporting_role(environ={}, roster=_ROSTER, explicit="rpg-designer") == "rpg-designer"
    assert ht.exporting_role(environ={"SESSION_ROLE": _WRITER}, roster=_ROSTER) == _WRITER
    assert ht.exporting_role(environ={}, roster=_ROSTER) is None
    assert ht.exporting_role(environ={"SESSION_ROLE": "no-such-role"}, roster=_ROSTER) is None


def test_unresolved_role_gives_null_role_and_the_cli_flags_it(tmp_path, monkeypatch, capsys):
    root = _export_with_role(tmp_path, None)
    draft = next(r for r in _rows(root) if r["path"].endswith("TCK-2-OPEN.md"))["belongs_to"]
    assert draft["role"] is None and draft["ticket_id"] == "TCK-2-OPEN"
    h, m = tmp_path / "h", tmp_path / "m"
    monkeypatch.setattr(ht, "HANDOVER_DIR", h)
    monkeypatch.setattr(ht, "TRANSIT_ROOT", tmp_path / "t2")
    monkeypatch.setattr(ht, "default_memory_dir", lambda: m)
    monkeypatch.setattr(ht, "load_draft_filter", lambda *a, **k: _flt(tmp_path))
    monkeypatch.delenv("SESSION_ROLE", raising=False)
    monkeypatch.setattr(ht, "host_id", lambda: "hostA")
    assert ht.main(["export"]) == 0
    cap = capsys.readouterr()
    assert "unattributed" in cap.out and "WARNING: the exporting role is unresolved" in cap.err


# ---- grouping and --role ------------------------------------------------------------------------

def test_summary_groups_by_role_with_unattributed_and_memory_listed_separately(tmp_path):
    rows = _rows(_export_with_role(tmp_path, None))
    summary = ht.summarize_groups(rows)
    assert summary == f"{_WRITER}: 1, role-a: 1, unattributed: 2, memory: 1"
    assert ht.bundle_summary("hostA", tmp_path / "t") == summary
    assert ht.bundle_summary("missing", tmp_path / "t") == ""
    assert "hostA [" in build_transit_notice(tmp_path / "t", "b") and "--role <your role>" in build_transit_notice(tmp_path / "t", "b")
    assert summary in ht.status_lines(tmp_path / "t", "b")[0]


def test_import_role_copies_only_that_roles_items_plus_memory_and_lists_the_rest(tmp_path):
    root = _export_with_role(tmp_path, _WRITER)
    h2, m2 = tmp_path / "dst" / "h", tmp_path / "dst" / "m"
    actions = ht.import_bundle("hostA", root=root, handover_dir=h2, memory_dir=m2, local_host="b", role="someone-else")
    assert (m2 / "MEMORY.md").exists()  # memory always comes along
    assert not list(h2.rglob("*.md"))
    assert any(a.startswith("skipped") and "belongs to" in a for a in actions)
    ht.import_bundle("hostA", root=root, handover_dir=h2, memory_dir=m2, local_host="b", role=_WRITER)
    assert (h2 / f"{_WRITER}.md").exists() and (h2 / "drafts/open-folder/TCK-2-OPEN.md").exists()


def test_role_import_never_silently_drops_unattributed_items(tmp_path):
    root = _export_with_role(tmp_path, None)
    actions = ht.import_bundle("hostA", root=root, handover_dir=tmp_path / "d" / "h", memory_dir=tmp_path / "d" / "m",
                               local_host="b", role=_WRITER)
    assert any("unattributed" in a and a.startswith("skipped") for a in actions)


def test_import_no_memory_skips_memory_and_a_tampered_unselected_file_still_aborts(tmp_path):
    root = _export_with_role(tmp_path, _WRITER)
    h2, m2 = tmp_path / "d2" / "h", tmp_path / "d2" / "m"
    ht.import_bundle("hostA", root=root, handover_dir=h2, memory_dir=m2, local_host="b", role=_WRITER, no_memory=True)
    assert not m2.exists()
    next((root / "hostA" / "files" / "memory").glob("*.txt")).write_text("tampered")
    with pytest.raises(ht.TransitError, match="sha256"):
        ht.import_bundle("hostA", root=root, handover_dir=tmp_path / "d3" / "h", memory_dir=tmp_path / "d3" / "m",
                         local_host="b", role=_WRITER, no_memory=True)
