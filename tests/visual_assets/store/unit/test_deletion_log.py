"""ADR D24: `gc --delete` appends one chained typed record per removal BEFORE removing it; `audit_chain` verifies the log; a full log refuses and archives."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import audit, cli, config, deletionlog, gc as gc_mod, lock
from visual_assets.store.contracts.base import canonical_json, parse_record
from visual_assets.store.contracts.deletion import ZERO_HASH, DeletionRecord
from visual_assets.store.errors import ContractError, GateError
from visual_assets.store.intake.validator import file_hash

AT = "2026-02-01T00:00:00Z"
CUTOFF = "2026-01-02T00:00:00Z"


@pytest.fixture
def garbage(env):
    """Three QUARANTINED, never adopted intakes: three garbage items."""
    s.CALLS.clear()
    env.ids = sorted(s.make_intake(env.tmp, width, passed=False).intake_id for width in (18, 19, 20))
    return env


def delete(**kw):
    return gc_mod.gc(delete=True, expire_before=CUTOFF, decided_at=AT, **kw)


def log_lines(env):
    return [json.loads(line) for line in (env.catalog / ".deletions.jsonl").read_text().splitlines()]


def test_each_removal_gets_one_chained_typed_record(garbage):
    items = delete()
    assert len(items) == 3 and not any(p.exists() for p in (i.path for i in items))
    records = log_lines(garbage)
    assert [r["path"] for r in records] == [f"quarantine/{i.path.name}" for i in items]
    assert all(r["record_type"] == "deletion_record" and r["kind"] == "quarantine" and r["decided_at"] == AT for r in records)
    assert records[0]["prev_hash"] == ZERO_HASH
    lines = (garbage.catalog / ".deletions.jsonl").read_bytes().splitlines(keepends=True)
    assert [r["prev_hash"] for r in records[1:]] == [file_hash(line) for line in lines[:-1]]
    assert all(canonical_json(parse_record(DeletionRecord, line)) == line for line in lines)  # canonical, strict, round-trips
    assert audit.audit_chain(garbage.catalog).ok


def test_the_recorded_hash_is_the_hash_of_what_was_removed(garbage):
    victim = garbage.quarantine / garbage.ids[0]
    expected = deletionlog.content_hash(victim)
    delete()
    assert next(r for r in log_lines(garbage) if r["path"] == f"quarantine/{garbage.ids[0]}")["content_hash"] == expected
    assert expected.startswith("sha256:") and expected != ZERO_HASH


def test_a_dry_run_writes_no_log_and_a_second_delete_appends_nothing(garbage):
    gc_mod.gc(expire_before=CUTOFF)
    assert not (garbage.catalog / ".deletions.jsonl").exists()
    delete()
    size = (garbage.catalog / ".deletions.jsonl").stat().st_size
    assert delete() == []  # nothing left to remove: the log is unchanged
    assert (garbage.catalog / ".deletions.jsonl").stat().st_size == size


def test_the_record_is_written_before_the_item_is_removed(garbage, monkeypatch):
    seen = {}
    real = shutil.rmtree

    def spy(path, *a, **k):
        seen.setdefault(Path(path).name, any(Path(path).name in line["path"] for line in log_lines(garbage)))
        real(path, *a, **k)

    monkeypatch.setattr(gc_mod.shutil, "rmtree", spy)
    delete()
    assert seen and all(seen.values())


def test_a_kill_between_the_record_and_the_removal_leaves_a_note_not_a_break(garbage, monkeypatch):
    def boom(path, *a, **k):
        raise KeyboardInterrupt  # stands in for a kill right after the append

    with monkeypatch.context() as patch:
        patch.setattr(gc_mod.shutil, "rmtree", boom)
        with pytest.raises(KeyboardInterrupt):
            delete()
    report = audit.audit_chain(garbage.catalog)
    assert report.ok and any("still exists" in n for n in report.notes)
    delete()  # a re-run removes it again and records it again: still a valid chain
    assert audit.audit_chain(garbage.catalog).ok


def test_gc_never_lists_the_lock_the_log_or_an_archive(garbage):
    with lock.store_write_lock("gc", started_at=AT):
        pass
    delete()
    deletionlog.archive()
    (garbage.catalog / ".deletions.jsonl").write_text("")
    names = {i.path.name for i in gc_mod.collect("2999-01-01T00:00:00Z")}
    assert not names & {".store.lock", ".deletions.jsonl", ".deletions-0001.jsonl"}
    delete()
    assert {p.name for p in garbage.catalog.iterdir()} >= {".store.lock", ".deletions-0001.jsonl"}


def test_a_symlinked_log_is_refused_and_nothing_is_deleted(garbage):
    target = garbage.tmp / "elsewhere"
    target.write_text("")
    (garbage.catalog / ".deletions.jsonl").symlink_to(target)
    before = snapshot(garbage.quarantine)
    with pytest.raises(GateError):
        delete()
    assert snapshot(garbage.quarantine) == before and target.read_text() == ""


def test_an_unreadable_item_refuses_before_anything_is_deleted(garbage, monkeypatch):
    real = deletionlog.content_hash
    monkeypatch.setattr(deletionlog, "content_hash", lambda p: (_ for _ in ()).throw(OSError("denied")) if p.name == garbage.ids[-1] else real(p))
    before = snapshot(garbage.quarantine)
    with pytest.raises(GateError) as err:
        delete()
    assert err.value.code == "deletion_unreadable" and snapshot(garbage.quarantine) == before


def test_delete_without_a_decided_at_is_refused(garbage):
    with pytest.raises(GateError):
        gc_mod.gc(delete=True, expire_before=CUTOFF)


# ---- audit: a damaged log is a BREAK ----

def broken_codes(env):
    return {b.code for b in audit.audit_chain(env.catalog).breaks}


def rewrite(env, edit):
    path = env.catalog / ".deletions.jsonl"
    edit(path)
    return broken_codes(env)


def test_a_tampered_line_is_a_break(garbage):
    delete()
    codes = rewrite(garbage, lambda p: p.write_bytes(p.read_bytes().replace(b'"reason":"QUARANTINED', b'"reason":"quarantined', 1)))
    assert "DELETION_LOG_CHAIN" in codes  # editing a record's text changes its hash, so the NEXT line's prev_hash no longer matches


def test_a_removed_middle_line_is_a_break(garbage):
    delete()
    path = garbage.catalog / ".deletions.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    path.write_bytes(lines[0] + lines[2])
    assert "DELETION_LOG_CHAIN" in broken_codes(garbage)


def test_reordered_lines_are_a_break(garbage):
    delete()
    path = garbage.catalog / ".deletions.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    path.write_bytes(lines[1] + lines[0] + lines[2])
    assert {"DELETION_LOG_CHAIN", "DELETION_LOG_ANCHOR"} & broken_codes(garbage)


def test_a_forged_first_record_anchor_is_a_break(garbage):
    delete()
    path = garbage.catalog / ".deletions.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    forged = json.loads(lines[0])
    forged["prev_hash"] = "sha256:" + "1" * 64
    path.write_bytes(canonical_json_line(forged) + b"".join(lines[1:]))
    assert "DELETION_LOG_ANCHOR" in broken_codes(garbage)


def canonical_json_line(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"


@pytest.mark.parametrize("bad_path", ["sources/a/r0001.aseprite", "quarantine/../sources/x", "/etc/passwd", "quarantine", "review//x"])
def test_a_record_naming_a_path_outside_the_three_roots_is_a_break(garbage, bad_path):
    delete()
    path = garbage.catalog / ".deletions.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    forged = json.loads(lines[-1])
    forged["path"] = bad_path
    path.write_bytes(b"".join(lines[:-1]) + canonical_json_line(forged))
    assert "DELETION_LOG_RECORD" in broken_codes(garbage)  # the strict contract refuses it, so the line cannot be chained either


def test_garbage_and_non_canonical_lines_are_breaks(garbage):
    delete()
    path = garbage.catalog / ".deletions.jsonl"
    good = path.read_bytes()
    path.write_bytes(good + b"not json\n")
    assert "DELETION_LOG_RECORD" in broken_codes(garbage)
    path.write_bytes(good[:-1])  # torn: no final newline
    assert "DELETION_LOG_RECORD" in broken_codes(garbage)
    lines = good.splitlines(keepends=True)
    spaced = json.dumps(json.loads(lines[0]), sort_keys=True).encode() + b"\n"  # valid JSON, not the canonical bytes
    path.write_bytes(spaced + b"".join(lines[1:]))
    assert {"DELETION_LOG_RECORD", "DELETION_LOG_CHAIN"} & broken_codes(garbage)


def test_a_missing_log_is_fine_and_an_oversize_log_is_a_break(garbage):
    assert audit.audit_chain(garbage.catalog).ok
    (garbage.catalog / ".deletions.jsonl").write_bytes(b"x" * (config.MAX_DELETION_LOG_BYTES + 1))
    assert "DELETION_LOG_UNREADABLE" in broken_codes(garbage)


# ---- budget: a full log refuses, archives, and the chain continues ----

def test_a_full_log_refuses_before_deleting_anything(garbage, monkeypatch):
    monkeypatch.setattr(config, "MAX_DELETION_LOG_BYTES", 600)
    before = snapshot(garbage.quarantine)
    with pytest.raises(GateError) as err:
        delete()
    assert err.value.code == "deletion_log_full" and "deletions --archive" in str(err.value)
    assert snapshot(garbage.quarantine) == before and not (garbage.catalog / ".deletions.jsonl").exists()


def test_archive_then_continue_keeps_one_valid_chain(garbage, monkeypatch):
    first = gc_mod.gc(delete=True, expire_before=CUTOFF, decided_at=AT)
    assert len(first) == 3
    old_last = file_hash((garbage.catalog / ".deletions.jsonl").read_bytes().splitlines(keepends=True)[-1])
    archived = deletionlog.archive()
    assert archived.name == ".deletions-0001.jsonl" and not (garbage.catalog / ".deletions.jsonl").exists()
    assert deletionlog.last_hash() == old_last  # the chain head survives the move
    s.make_intake(garbage.tmp, 21, passed=False)
    delete()
    new = log_lines(garbage)
    assert new[0]["prev_hash"] == old_last != ZERO_HASH  # anchored on the old log's last hash, not zeros
    assert audit.audit_chain(garbage.catalog).ok
    deletionlog.archive()
    assert {p.name for p in garbage.catalog.glob(".deletions-*.jsonl")} == {".deletions-0001.jsonl", ".deletions-0002.jsonl"}
    assert audit.audit_chain(garbage.catalog).ok


def test_a_wrong_anchor_after_an_archive_is_a_break(garbage):
    delete()
    deletionlog.archive()
    s.make_intake(garbage.tmp, 22, passed=False)
    delete()
    path = garbage.catalog / ".deletions.jsonl"
    forged = json.loads(path.read_bytes().splitlines()[0])
    forged["prev_hash"] = ZERO_HASH  # pretends to start a fresh chain
    path.write_bytes(canonical_json_line(forged))
    assert "DELETION_LOG_ANCHOR" in broken_codes(garbage)


def test_a_missing_middle_archive_is_a_break(garbage):
    delete()
    deletionlog.archive()
    s.make_intake(garbage.tmp, 23, passed=False)
    delete()
    deletionlog.archive()
    s.make_intake(garbage.tmp, 24, passed=False)
    delete()
    (garbage.catalog / ".deletions-0001.jsonl").unlink()
    assert "DELETION_LOG_ANCHOR" in broken_codes(garbage)


def test_archiving_an_empty_or_absent_log_is_refused(garbage):
    with pytest.raises(GateError):
        deletionlog.archive()


def test_the_cli_deletes_lists_and_archives(garbage, capsys):
    assert cli.main(["gc", "--delete"]) == 0
    capsys.readouterr()
    assert cli.main(["deletions"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 3 and all("quarantine/in-" in line for line in out)
    assert cli.main(["deletions", "--archive"]) == 0
    assert "archived" in capsys.readouterr().out and (garbage.catalog / ".deletions-0001.jsonl").is_file()
    assert cli.main(["deletions", "--archive"]) == 2
    assert cli.main(["audit"]) == 0


def test_directory_hash_covers_names_and_contents_and_does_not_follow_links(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d, name in ((a, "f"), (b, "g")):
        d.mkdir()
        (d / name).write_bytes(b"same")
    assert deletionlog.content_hash(a) != deletionlog.content_hash(b)  # a renamed file changes the hash
    (a / "link").symlink_to(tmp_path / "missing")
    assert deletionlog.content_hash(a)  # a dangling link is hashed by its target text, never followed


def test_a_torn_log_tail_refuses_before_anything_is_deleted(garbage):
    delete()
    path = garbage.catalog / ".deletions.jsonl"
    path.write_bytes(path.read_bytes()[:-1])  # a torn last line
    s.make_intake(garbage.tmp, 25, passed=False)
    before = snapshot(garbage.quarantine)
    with pytest.raises(GateError) as err:
        delete()
    assert err.value.code == "deletion_log" and "torn" in str(err.value) and snapshot(garbage.quarantine) == before


def test_an_oversize_log_is_refused_not_read(garbage):
    (garbage.catalog / ".deletions.jsonl").write_bytes(b"x" * (config.MAX_DELETION_LOG_BYTES + 1))
    with pytest.raises(GateError):
        delete()
    with pytest.raises(GateError):
        deletionlog.archive()


def test_log_text_cannot_carry_terminal_escapes(garbage):
    delete()
    path = garbage.catalog / ".deletions.jsonl"
    lines = path.read_bytes().splitlines(keepends=True)
    forged = json.loads(lines[-1])
    forged["reason"] = "x\x1b[2Jy"
    path.write_bytes(b"".join(lines[:-1]) + canonical_json_line(forged))
    assert "DELETION_LOG_RECORD" in broken_codes(garbage)  # the strict text type refuses a control character, so listing never prints one
