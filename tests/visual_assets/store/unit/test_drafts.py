"""Draft sets (`draft keep`, `draft verify`) and the reviewed-set adoption (`adopt-set`): `TCK-20261004-VISUAL-ASSETS-DRAFT-SETS-AND-SET-ADOPTION`.

Drafts live in git outside the catalog and record no approval; `adopt-set` is the one human decision. Every refusal has a stable code and writes nothing.
Pure Python plus a deterministic stand-in for Aseprite; no real Aseprite needed.
"""

from __future__ import annotations

import builtins
import json
import shutil
import stat

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import cli, config, drafts, gc, records, setadoption
from visual_assets.store.contracts import AdoptionRecord, DraftSet, SetAdoptionRecord, canonical_json, parse_record
from visual_assets.store.errors import DraftError, GateError
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.revoke import revoke
from visual_assets.store.verify import verify

HERO, ROCK, OTHER = s.key_for("hero"), s.key_for("rock"), s.key_for("other")
SET = "terrain-v1"


@pytest.fixture
def drafting(env, monkeypatch, tmp_path):
    """The isolated catalog plus an isolated drafts root, and a registry where HERO declares a detail axis (plain default, bush)."""
    s.CALLS.clear()
    root = tmp_path / "drafts"
    monkeypatch.setattr(config, "DRAFTS_ROOT", root)
    env.drafts = root
    env.registry = s.detail_registry(HERO, values=("plain", "bush"))
    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    return env


def keep(env, width, **kw):
    kw.setdefault("set_id", SET)
    kw.setdefault("visual_key", ROCK)
    return drafts.keep(s.make_intake(env.tmp, width).intake_id, registry=env.registry, **kw)


def refused_keep(env, code, intake_id, **kw):
    before = snapshot(env.drafts) if env.drafts.exists() else {}
    kw.setdefault("set_id", SET)
    kw.setdefault("visual_key", ROCK)
    with pytest.raises(DraftError) as err:
        drafts.keep(intake_id, registry=env.registry, **kw)
    assert err.value.code == code, err.value
    assert (snapshot(env.drafts) if env.drafts.exists() else {}) == before


def codes(env, set_id=SET):
    return sorted(f.code for f in drafts.verify_set(set_id, registry=env.registry))


# ---- draft keep ------------------------------------------------------------------------------------------------------------------------

def test_keep_writes_the_entry_files_and_a_sorted_set_record_outside_the_catalog(drafting):
    a = keep(drafting, 17, visual_key=ROCK)
    b = keep(drafting, 16, visual_key=HERO, detail="bush")
    record, data = drafts.load_set(SET)
    assert [(e.visual_key, e.detail) for e in record.entries] == [(HERO, "bush"), (ROCK, None)]  # sorted by slot, not by keep order
    assert data == canonical_json(record) and not str(drafting.drafts).startswith(str(config.CATALOG_ROOT))
    for entry in (a, b):
        folder = drafting.drafts / SET / entry.draft_id
        assert sorted(p.name for p in folder.iterdir()) == ["intake_result.json", "package.json", "preview.png", "source.aseprite"]
        assert all(stat.S_IMODE(p.stat().st_mode) == 0o644 for p in folder.iterdir())
        assert entry.intake_hash == file_hash((folder / "intake_result.json").read_bytes())
    assert a.source_asset_id == "fixture_sample_rock" and b.source_asset_id == "fixture_sample_hero_bush"  # the documented default
    assert codes(drafting) == [] and list(drafting.drafts.glob(".tmp-*")) == [] and list((drafting.drafts / SET).glob(".tmp-*")) == []


def test_keep_refuses_a_quarantined_unknown_or_revoked_intake(drafting):
    bad = s.make_intake(drafting.tmp, 16, passed=False)
    refused_keep(drafting, "intake_not_passed", bad.intake_id)
    refused_keep(drafting, "unknown_intake", "in-" + "0" * 16)
    good = s.make_intake(drafting.tmp, 17)
    revoke(good.intake_id, reason="not wanted", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    refused_keep(drafting, "intake_revoked", good.intake_id)


def test_keep_refuses_an_undeclared_key_or_value_and_a_value_on_a_key_without_an_axis(drafting):
    intake = s.make_intake(drafting.tmp, 16).intake_id
    refused_keep(drafting, "unknown_visual_key", intake, visual_key="fixture.sample.nothing")
    refused_keep(drafting, "unknown_detail_value", intake, visual_key=HERO, detail="tree")
    refused_keep(drafting, "detail_not_declared", intake, visual_key=ROCK, detail="bush")


def test_a_second_draft_for_a_slot_needs_replace_and_the_default_counts_as_the_same_slot(drafting):
    first = keep(drafting, 16, visual_key=HERO)  # None = the default value, plain
    refused_keep(drafting, "slot_taken_in_set", s.make_intake(drafting.tmp, 17).intake_id, visual_key=HERO, detail="plain", source_asset_id="hero_two")
    third = s.make_intake(drafting.tmp, 18).intake_id
    entry = drafts.keep(third, set_id=SET, visual_key=HERO, detail="plain", source_asset_id="hero_two", replace=True, registry=drafting.registry)
    record, _ = drafts.load_set(SET)
    assert [e.draft_id for e in record.entries] == [third]  # replaced, and the old entry's folder is gone
    assert not (drafting.drafts / SET / first.draft_id).exists() and entry.detail == "plain"
    assert codes(drafting) == []


def test_keep_settles_the_source_asset_id_early(drafting):
    keep(drafting, 16, visual_key=ROCK)
    other = s.make_intake(drafting.tmp, 17).intake_id
    refused_keep(drafting, "source_asset_in_set", other, visual_key=OTHER, source_asset_id="fixture_sample_rock")  # used by another entry of the set
    refused_keep(drafting, "invalid_source_asset_id", other, visual_key=OTHER, source_asset_id="Not Valid")
    refused_keep(drafting, "invalid_set_id", other, visual_key=OTHER, set_id="Bad Set")
    s.do_adopt(s.make_intake(drafting.tmp, 18).intake_id, source_asset_id="hero")  # an existing source asset in the catalog
    refused_keep(drafting, "source_asset_exists", other, visual_key=OTHER, source_asset_id="hero")


def test_the_same_intake_cannot_be_kept_twice_in_a_set_and_a_set_has_a_limit(drafting, monkeypatch):
    first = keep(drafting, 16, visual_key=ROCK)
    refused_keep(drafting, "draft_exists", first.draft_id, visual_key=OTHER, source_asset_id="other_asset")
    monkeypatch.setattr(config, "MAX_DRAFT_SET_ENTRIES", 1)
    refused_keep(drafting, "set_full", s.make_intake(drafting.tmp, 17).intake_id, visual_key=OTHER, source_asset_id="other_asset")


def test_a_failed_write_leaves_no_entry_and_no_set_record(drafting, monkeypatch):
    intake = s.make_intake(drafting.tmp, 16).intake_id
    monkeypatch.setattr(drafts.os, "replace", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        drafts.keep(intake, set_id=SET, visual_key=ROCK, registry=drafting.registry)
    assert [p.name for p in (drafting.drafts / SET).iterdir()] == []


# ---- drafts are outside everything the catalog reads ------------------------------------------------------------------------------------

def test_drafts_survive_gc_and_a_fresh_clone_and_the_catalog_never_sees_them(drafting, tmp_path):
    keep(drafting, 16, visual_key=ROCK)
    before_catalog = snapshot(drafting.catalog)
    before_drafts = snapshot(drafting.drafts)
    gc.gc(expire_before="2999-01-01T00:00:00Z", delete=True)  # the most aggressive gc there is
    assert snapshot(drafting.drafts) == before_drafts and snapshot(drafting.catalog) == before_catalog
    assert all(f.code != "UNEXPECTED_FILE" for f in verify(drafting.catalog, allow_fixture_namespace=True))
    clone = tmp_path / "clone"
    shutil.copytree(drafting.drafts, clone)  # what a fresh clone has: the tracked files only
    assert drafts.verify_set(SET, registry=drafting.registry, root=clone) == []
    for module in ("release", "runtime_export", "verify"):
        assert "drafts" not in open(f"visual_assets/store/{module}.py").read()


# ---- draft verify: one test per link of the chain, and the rest -------------------------------------------------------------------------

def tamper(env, entry, name, data=b"tampered"):
    (env.drafts / SET / entry.draft_id / name).write_bytes(data)


def test_verify_refuses_each_link_of_the_chain_when_tampered(drafting):
    entry = keep(drafting, 16, visual_key=ROCK)
    folder = drafting.drafts / SET / entry.draft_id
    originals = {n: (folder / n).read_bytes() for n in ("source.aseprite", "intake_result.json")}
    # link 1: source.aseprite -> the staged-file hash inside intake_result.json
    tamper(drafting, entry, "source.aseprite", originals["source.aseprite"] + b"x")
    assert codes(drafting) == ["staged_bytes_changed"]
    tamper(drafting, entry, "source.aseprite", originals["source.aseprite"])
    # link 2: intake_result.json -> intake_hash in the entry
    tamper(drafting, entry, "intake_result.json", originals["intake_result.json"] + b" ")
    assert codes(drafting) == ["intake_hash_mismatch"]
    tamper(drafting, entry, "intake_result.json", originals["intake_result.json"])
    # link 3: preview.png pixels -> pixel_hash in the entry (the set record is edited, the files are intact)
    record, _ = drafts.load_set(SET)
    forged = DraftSet(record_type="draft_set", schema_version=1, set_id=SET,
                      entries=(entry.model_copy(update={"pixel_hash": "pixels-v1:" + "0" * 64}),))
    (drafting.drafts / SET / "draft_set.json").write_bytes(canonical_json(forged))
    assert codes(drafting) == ["pixel_hash_mismatch"]


def test_verify_reports_stray_files_undeclared_keys_duplicate_slots_and_a_missing_entry(drafting):
    keep(drafting, 16, visual_key=ROCK)
    (drafting.drafts / SET / "notes.txt").write_text("x")
    (drafting.drafts / "loose.txt").write_text("x")
    assert codes(drafting) == ["stray_file"]
    assert sorted(f.code for f in drafts.verify_all(registry=drafting.registry)) == ["stray_file", "stray_file"]
    (drafting.drafts / SET / "notes.txt").unlink(), (drafting.drafts / "loose.txt").unlink()
    assert drafts.verify_all(registry=drafting.registry) == []
    assert "unknown_visual_key" in [f.code for f in drafts.verify_set(SET, registry=s.registry().__class__({}, {}, "sha256:" + "0" * 64))]
    record, _ = drafts.load_set(SET)
    dup = record.entries[0].model_copy(update={"visual_key": HERO, "detail": "plain", "draft_id": "in-" + "9" * 16, "source_asset_id": "second"})
    first = record.entries[0].model_copy(update={"visual_key": HERO, "detail": None})
    (drafting.drafts / SET / "draft_set.json").write_bytes(canonical_json(DraftSet(record_type="draft_set", schema_version=1, set_id=SET, entries=(first, dup))))
    assert "duplicate_slot" in codes(drafting)  # None and the explicit default are one slot
    shutil.rmtree(drafting.drafts / SET / record.entries[0].draft_id)
    assert "entry_unreadable" in codes(drafting)


# ---- adopt-set ---------------------------------------------------------------------------------------------------------------------------

def adopt_set(env, **over):
    args = dict(approver="Pat Approver", approver_role="art lead", licence_state="CLEARED", licence_evidence_ref="licence-note-7",
                review_evidence_ref="the whole-map preview page of terrain-v1", decided_at=s.NOW, confirm=s.yes, registry=env.registry,
                renderer=s.FakeRenderer())
    args.update(over)
    return setadoption.adopt_set(SET, **args)


def refused(env, code, **over):
    before = snapshot(env.catalog)
    with pytest.raises(GateError) as err:
        adopt_set(env, **over)
    assert err.value.code == code, err.value
    assert snapshot(env.catalog) == before  # all or nothing: nothing was written


@pytest.fixture
def two(drafting):
    drafting.a = keep(drafting, 16, visual_key=HERO, detail="bush")
    drafting.b = keep(drafting, 17, visual_key=ROCK)
    return drafting


def test_adopt_set_writes_one_adoption_per_entry_and_one_set_record_after_one_confirmation(two):
    record = adopt_set(two)
    assert len(s.CALLS) == 1 and s.CALLS[0][0] == SET  # ONE typed confirmation, of the set id
    notices = "\n".join(s.CALLS[0][1])
    set_bytes = (two.drafts / SET / "draft_set.json").read_bytes()
    assert file_hash(set_bytes) in notices  # the human is shown the hash of the exact set
    assert "licence-note-7" in notices and "the whole-map preview page" in notices and "MATCHES" in notices
    for entry in (two.a, two.b):
        assert entry.source_asset_id in notices and entry.draft_id in notices
    assert f"{HERO} [bush]" in notices and ROCK in notices
    assert record.draft_set_hash == file_hash(set_bytes) and len(record.entries) == 2
    path = two.catalog / "provenance" / "set-adoptions" / f"{record.set_adoption_id}.json"
    assert parse_record(SetAdoptionRecord, path.read_bytes()) == record
    adoptions = {a.source_asset_id: a for a in (parse_record(AdoptionRecord, p.read_bytes()) for p in (two.catalog / "provenance" / "adoptions").glob("*.json"))}
    assert set(adoptions) == {two.a.source_asset_id, two.b.source_asset_id}  # ordinary records, one per entry
    assert (adoptions[two.a.source_asset_id].visual_key, adoptions[two.a.source_asset_id].detail_value) == (HERO, "bush")
    assert records.slot_holders(two.registry.keys[HERO], "bush") == [two.a.source_asset_id]
    assert all(f.code != "UNEXPECTED_FILE" for f in verify(two.catalog, allow_fixture_namespace=True))
    from visual_assets.store.audit import audit_chain
    assert audit_chain(two.catalog).breaks == []  # intake copy, fresh render check, adoption and source records chain together


def test_nothing_is_written_when_the_set_is_not_confirmed(two):
    refused(two, "not_confirmed", confirm=s.no)
    assert len(s.CALLS) == 1


def test_a_render_that_does_not_match_the_draft_preview_is_a_hard_refusal(two):
    refused(two, "preview_mismatch", renderer=s.MismatchRenderer())
    assert s.CALLS == []  # refused before the human is even asked to confirm


def test_one_bad_entry_among_good_ones_writes_nothing(two):
    # the SECOND entry's slot is held by a live asset, so the whole set is refused, including the first (good) entry
    s.do_adopt(s.make_intake(two.tmp, 18).intake_id, source_asset_id="holder", visual_key=ROCK, registry=two.registry)
    before = snapshot(two.catalog)
    s.CALLS.clear()
    with pytest.raises(GateError) as err:
        adopt_set(two)
    assert err.value.code == "visual_key_taken" and snapshot(two.catalog) == before and s.CALLS == []


def test_each_link_of_the_chain_is_re_checked_at_adoption(two):
    folder_a = two.drafts / SET / two.a.draft_id
    source, result = (folder_a / "source.aseprite").read_bytes(), (folder_a / "intake_result.json").read_bytes()
    (folder_a / "source.aseprite").write_bytes(source + b"x")
    refused(two, "draft_set_invalid")
    (folder_a / "source.aseprite").write_bytes(source)
    (folder_a / "intake_result.json").write_bytes(result + b" ")
    refused(two, "draft_set_invalid")
    (folder_a / "intake_result.json").write_bytes(result)
    record, _ = drafts.load_set(SET)
    forged = record.model_copy(update={"entries": tuple(e.model_copy(update={"pixel_hash": "pixels-v1:" + "0" * 64}) if e.draft_id == two.a.draft_id else e for e in record.entries)})
    (two.drafts / SET / "draft_set.json").write_bytes(canonical_json(forged))
    refused(two, "draft_set_invalid")


def test_the_decision_arguments_are_checked_before_anything_else(two):
    refused(two, "licence_not_cleared", licence_state="UNREVIEWED")
    refused(two, "licence_evidence_missing", licence_evidence_ref="UNAVAILABLE")
    refused(two, "invalid_approver", approver=" ")
    refused(two, "review_evidence_missing", review_evidence_ref="  ")
    refused(two, "renderer_unavailable", renderer=None)
    refused(two, "bad_decided_at", decided_at="yesterday")
    with pytest.raises(GateError) as err:
        setadoption.adopt_set("no-such-set", approver="a", approver_role="b", licence_state="CLEARED", licence_evidence_ref="n", review_evidence_ref="r",
                              decided_at=s.NOW, confirm=s.yes, registry=two.registry, renderer=s.FakeRenderer())
    assert err.value.code == "unknown_set"


def plant_catalog_intake_revocation(env, intake_id):
    """A catalog RevocationRecord with an IntakeTarget for `intake_id`, as a human revoke of an intake would leave (here planted directly)."""
    from visual_assets.store.contracts import RevocationRecord

    record = RevocationRecord.model_validate_json(json.dumps({
        "record_type": "revocation_record", "schema_version": 1, "revocation_id": "rv-" + "7" * 16, "target": {"kind": "intake", "intake_id": intake_id},
        "reason": "withdrawn after it was kept", "approver_name": "Pat Approver", "approver_role": "art lead", "decided_at": s.NOW}))
    directory = env.catalog / "provenance" / "revocations"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{record.revocation_id}.json").write_bytes(canonical_json(record))


def test_an_intake_revoked_after_it_was_kept_is_flagged_by_verify_and_refused_by_adopt_set(two):
    plant_catalog_intake_revocation(two, two.a.draft_id)
    assert codes(two) == ["intake_revoked"]
    refused(two, "intake_revoked")
    assert s.CALLS == []


def test_an_intake_revoked_locally_on_this_machine_after_it_was_kept_is_refused_too(two):
    revoke(two.b.draft_id, reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)  # writes revocation.json into the quarantine
    assert codes(two) == ["intake_revoked"]
    refused(two, "intake_revoked")


def test_two_entries_with_the_same_source_bytes_are_refused(drafting):
    first = s.make_intake(drafting.tmp, 16)
    second = s.make_intake_same_bytes(drafting.tmp, first)
    drafts.keep(first.intake_id, set_id=SET, visual_key=ROCK, registry=drafting.registry)
    drafts.keep(second.intake_id, set_id=SET, visual_key=OTHER, registry=drafting.registry)
    refused(drafting, "duplicate_source")


def test_a_set_that_was_already_adopted_is_refused(two):
    adopt_set(two)
    with pytest.raises(GateError) as err:
        adopt_set(two)
    assert err.value.code in {"already_adopted", "source_asset_exists"}


# ---- the human gate at the command line, and no agent surface ----------------------------------------------------------------------------

def test_adopt_set_refuses_without_a_terminal_and_a_draft_cannot_be_adopted_by_the_drawing_server(two, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: False)
    monkeypatch.setattr(builtins, "input", lambda prompt="": pytest.fail("must not prompt without a terminal"))
    before = snapshot(two.catalog)
    assert cli.main(["adopt-set", SET, "--approver", "Pat", "--approver-role", "lead", "--licence", "CLEARED", "--licence-evidence", "n", "--review-evidence", "r"]) == 2
    assert "no_terminal" in capsys.readouterr().err and snapshot(two.catalog) == before
    from visual_assets.drawing.server import mcp

    names = {t.name for t in mcp._tool_manager.list_tools()}
    assert not {n for n in names if "adopt" in n or "draft" in n}


def test_the_draft_cli_keeps_and_verifies(drafting, monkeypatch, capsys):
    monkeypatch.setattr("visual_assets.store.drafts.load_registry", lambda *a, **k: drafting.registry)
    intake = s.make_intake(drafting.tmp, 16)
    assert cli.main(["draft", "keep", intake.intake_id, "--set", SET, "--as", ROCK]) == 0
    assert "nothing is adopted" in capsys.readouterr().out
    assert cli.main(["draft", "verify", SET]) == 0 and "drafts ok" in capsys.readouterr().out
    (drafting.drafts / SET / "stray.txt").write_text("x")
    assert cli.main(["draft", "verify"]) == 1 and "stray_file" in capsys.readouterr().out
    (drafting.drafts / SET / "stray.txt").unlink()
    assert cli.main(["draft", "keep", intake.intake_id, "--set", SET, "--as", ROCK]) == 2  # a refusal is exit 2, with its stable code
    assert "slot_taken_in_set" in capsys.readouterr().err
