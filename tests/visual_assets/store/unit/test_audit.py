"""`audit_chain`: a fresh tree passes; every planted tamper is reported with its own specific break."""

from __future__ import annotations

import json
import shutil

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config, records
from visual_assets.store.audit import audit_chain
from visual_assets.store.revoke import revoke


@pytest.fixture
def tree(env):
    """Two assets, three revisions, one revocation: a realistic adopted tree."""
    s.CALLS.clear()
    a, b_, c = (s.make_intake(env.tmp, w) for w in (16, 17, 18))
    a1 = s.do_adopt(a.intake_id)
    a2 = s.do_adopt(b_.intake_id, new=False, parent="r0001")
    other = s.do_adopt(c.intake_id, source_asset_id="rock")
    revoke("hero/r0002", reason="bad", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    env.ids = (a, b_, c)
    env.adoptions = (a1, a2, other)
    return env


def codes(report):
    return sorted(b.code for b in report.breaks)


def edit_json(path, **changes):
    data = json.loads(path.read_bytes())
    data.update(changes)
    path.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")


def p(env, *parts):
    return env.catalog.joinpath(*parts)


def test_a_freshly_adopted_tree_passes(tree):
    report = audit_chain()
    assert report.ok and report.breaks == [] and report.notes == []


def test_an_empty_or_missing_catalog_passes(env):
    assert audit_chain().ok and audit_chain(env.tmp / "does-not-exist").ok


def test_the_audit_is_read_only(tree):
    before = snapshot(tree.catalog)
    audit_chain()
    assert snapshot(tree.catalog) == before


def test_an_edited_source_byte_is_reported(tree):
    path = p(tree, "sources", "rock", "r0001.aseprite")
    data = bytearray(path.read_bytes())
    data[-1] ^= 1
    path.write_bytes(bytes(data))
    report = audit_chain()
    assert codes(report) == ["SOURCE_BYTES_HASH_MISMATCH"] and report.breaks[0].path == "sources/rock/r0001.aseprite"


def test_a_deleted_adoption_record_is_reported(tree):
    p(tree, "provenance", "adoptions", f"{tree.adoptions[2].adoption_id}.json").unlink()
    report = audit_chain()
    assert codes(report) == ["ADOPTION_MISSING"] and "sources/rock/r0001" not in report.breaks[0].detail


def test_a_deleted_intake_record_is_reported(tree):
    p(tree, "provenance", "intake", f"{tree.ids[2].intake_id}.json").unlink()
    assert codes(audit_chain()) == ["INTAKE_MISSING"]


def test_an_edited_approver_is_reported(tree):
    edit_json(p(tree, "provenance", "adoptions", f"{tree.adoptions[0].adoption_id}.json"), approver_name="Someone Else")
    assert codes(audit_chain()) == ["ADOPTION_HASH_MISMATCH"]


def test_an_edited_intake_copy_is_reported(tree):
    edit_json(p(tree, "provenance", "intake", f"{tree.ids[0].intake_id}.json"), validator_version="edited")
    assert codes(audit_chain()) == ["INTAKE_HASH_MISMATCH"]


def test_a_swapped_source_record_is_reported(tree):
    shutil.copyfile(p(tree, "sources", "hero", "r0002.source.json"), p(tree, "sources", "hero", "r0001.source.json"))
    found = codes(audit_chain())
    assert "SOURCE_RECORD_MISMATCH" in found and "SOURCE_BYTES_HASH_MISMATCH" in found
    assert audit_chain().ok is False


def test_a_source_record_swapped_across_assets_is_reported(tree):
    shutil.copyfile(p(tree, "sources", "rock", "r0001.source.json"), p(tree, "sources", "hero", "r0001.source.json"))
    assert "SOURCE_RECORD_MISMATCH" in codes(audit_chain())


def test_every_break_is_reported_not_just_the_first(tree):
    p(tree, "provenance", "adoptions", f"{tree.adoptions[2].adoption_id}.json").unlink()
    edit_json(p(tree, "provenance", "adoptions", f"{tree.adoptions[0].adoption_id}.json"), approver_name="X")
    path = p(tree, "sources", "hero", "r0002.aseprite")
    path.write_bytes(path.read_bytes() + b"\x00")
    assert codes(audit_chain()) == ["ADOPTION_HASH_MISMATCH", "ADOPTION_MISSING", "SOURCE_BYTES_HASH_MISMATCH"]


def test_source_bytes_without_a_source_record_are_orphans(tree):
    p(tree, "sources", "rock", "r0001.source.json").unlink()
    assert "ORPHAN_FILE" in codes(audit_chain())


def test_a_source_record_without_its_bytes_is_reported(tree):
    p(tree, "sources", "rock", "r0001.aseprite").unlink()
    assert codes(audit_chain()) == ["SOURCE_BYTES_MISSING"]


def test_unreferenced_provenance_and_stray_files_are_orphans(tree):
    shutil.copyfile(p(tree, "provenance", "adoptions", f"{tree.adoptions[0].adoption_id}.json"), p(tree, "provenance", "adoptions", "ad-ffffffffffffffff.json"))
    shutil.copyfile(p(tree, "provenance", "intake", f"{tree.ids[0].intake_id}.json"), p(tree, "provenance", "intake", "in-ffffffffffffffff.json"))
    (p(tree, "sources", "rock") / "notes.txt").write_text("stray")
    (p(tree, "sources") / "loose.txt").write_text("stray")
    report = audit_chain()
    assert codes(report) == ["ORPHAN_FILE"] * 4


def test_a_broken_parent_is_reported(tree):
    for name in ("r0001.source.json", "r0001.aseprite"):  # r0002's parent no longer exists
        p(tree, "sources", "hero", name).unlink()
    found = codes(audit_chain())
    assert "PARENT_BROKEN" in found
    assert found.count("PARENT_BROKEN") == 1  # reported on r0002 only


def test_a_record_that_the_contract_rejects_is_unreadable_not_a_parent_problem(tree):
    edit_json(p(tree, "sources", "hero", "r0002.source.json"), parent_revision=None)  # None is only valid for r0001
    found = codes(audit_chain())
    assert "SOURCE_RECORD_UNREADABLE" in found and "PARENT_BROKEN" not in found


def test_an_unreadable_record_does_not_cause_a_cascade_of_false_orphans(tree):
    p(tree, "sources", "rock", "r0001.source.json").write_text("garbage")
    report = audit_chain()
    assert codes(report) == ["SOURCE_RECORD_UNREADABLE"]
    assert any("not checked for orphans" in note for note in report.notes)


def test_revocation_problems_are_reported(tree):
    base = p(tree, "provenance", "revocations")
    (base / "rv-0000000000000000.json").write_text("garbage")
    assert "REVOCATION_UNREADABLE" in codes(audit_chain())
    (base / "rv-0000000000000000.json").unlink()
    only = next(base.iterdir())
    renamed = base / "rv-1111111111111111.json"
    only.rename(renamed)
    assert "REVOCATION_MISMATCH" in codes(audit_chain())
    renamed.rename(only)
    shutil.rmtree(p(tree, "sources", "rock"))
    revoke("hero/r0001", reason="x", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    for path in (p(tree, "sources", "hero", "r0001.source.json"), p(tree, "sources", "hero", "r0001.aseprite")):
        path.unlink()
    assert "REVOCATION_DANGLING" in codes(audit_chain())


def test_a_leftover_temporary_directory_is_a_note_not_a_failure(tree):
    (tree.catalog / ".quarantine").mkdir(exist_ok=True)
    (tree.catalog / ".quarantine" / ".tmp-in-0123456789abcdef-deadbeef").mkdir()
    (tree.catalog / "sources" / ".tmp-publish-abcd1234").mkdir()
    report = audit_chain()
    assert report.ok and len(report.notes) == 2 and all("safe to delete" in n for n in report.notes)


def test_the_stated_limit_a_consistent_double_edit_is_not_caught_by_the_catalog_alone(tree):
    """Documented, not hidden: edit the adoption record AND the hash in its SourceRecord and the chain still verifies."""
    from visual_assets.store.intake.validator import file_hash

    adoption_path = p(tree, "provenance", "adoptions", f"{tree.adoptions[2].adoption_id}.json")
    edit_json(adoption_path, approver_name="Forged Approver")
    edit_json(p(tree, "sources", "rock", "r0001.source.json"), adoption_hash=file_hash(adoption_path.read_bytes()))
    assert audit_chain().ok  # git history is the backstop for this one


def test_an_unreadable_symlinked_record_is_reported_not_followed(tree):
    path = p(tree, "provenance", "adoptions", f"{tree.adoptions[2].adoption_id}.json")
    copy = tree.tmp / "copy.json"
    copy.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(copy)
    assert codes(audit_chain()) == ["ADOPTION_UNREADABLE"]


def test_the_default_root_is_the_configured_catalog(tree):
    assert audit_chain().ok and config.CATALOG_ROOT == tree.catalog and records.list_source_ids() == ["hero", "rock"]


# --------------------------------------------------------------------------- the store's render check is part of the chain


def test_a_deleted_render_check_copy_is_reported(tree):
    p(tree, "provenance", "intake", f"{tree.ids[0].intake_id}.review.json").unlink()
    assert codes(audit_chain()) == ["REVIEW_MISSING"]


def test_an_edited_render_check_copy_is_reported(tree):
    edit_json(p(tree, "provenance", "intake", f"{tree.ids[0].intake_id}.review.json"), tool_version="edited")
    assert codes(audit_chain()) == ["REVIEW_HASH_MISMATCH"]


def test_a_render_check_that_did_not_match_or_describes_other_bytes_is_reported(tree):
    path = p(tree, "provenance", "intake", f"{tree.ids[0].intake_id}.review.json")
    data = json.loads(path.read_bytes())
    data["source_hash"] = "sha256:" + "4" * 64
    path.write_bytes(json.dumps(data, sort_keys=True, separators=(",", ":")).encode() + b"\n")
    assert "REVIEW_MISMATCH" in codes(audit_chain())


def test_an_unreferenced_render_check_copy_is_an_orphan(tree):
    shutil.copyfile(p(tree, "provenance", "intake", f"{tree.ids[0].intake_id}.review.json"), p(tree, "provenance", "intake", "in-ffffffffffffffff.review.json"))
    assert codes(audit_chain()) == ["ORPHAN_FILE"]
