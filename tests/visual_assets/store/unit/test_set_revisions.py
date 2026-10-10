"""Set-level revisions, draft drop and the tightened `adopt --parent` (ADR D22, `TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP`).

A draft entry may declare `parent_revision` (`draft keep --revises`): the next revision of an existing source asset. `adopt-set` adopts new and revision entries in one decision with the same records
`adopt --parent` writes; a stale parent or a changed slot is refused with nothing written. `draft drop` removes a draft and records it; an adopted set or entry is never altered. The human gate is
the existing one (tests in `test_drafts.py`); here its properties are re-checked for mixed sets.
"""

from __future__ import annotations

import builtins
import json
import shutil

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import catalogwrite, cli, config, drafts, records, setadoption
from visual_assets.store.contracts import AdoptionRecord, DraftSet, SetAdoptionRecord, SourceRecord, canonical_json, parse_record
from visual_assets.store.errors import DraftError, GateError
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.revoke import revoke

HERO, ROCK, OTHER = s.key_for("hero"), s.key_for("rock"), s.key_for("other")
SET = "revisions-v1"


@pytest.fixture
def world(env, monkeypatch, tmp_path):
    """The isolated catalog and drafts root; ROCK (no axis) already adopted as `rock_src` r0001; HERO declares a detail axis (plain default, bush) and is adopted as `hero_src` for [bush]."""
    s.CALLS.clear()
    monkeypatch.setattr(config, "DRAFTS_ROOT", tmp_path / "drafts")
    env.drafts = tmp_path / "drafts"
    env.registry = s.detail_registry(HERO, values=("plain", "bush"))
    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    env.registry = _with_keys(env, [ROCK, OTHER])
    s.do_adopt(s.make_intake(env.tmp, 30).intake_id, source_asset_id="rock_src", visual_key=ROCK, registry=env.registry)
    s.do_adopt(s.make_intake(env.tmp, 31).intake_id, source_asset_id="hero_src", visual_key=HERO, detail_value="bush", registry=env.registry)
    s.CALLS.clear()  # the two setup adoptions above each asked for a confirmation; the tests count only their own
    return env


def _with_keys(env, extra):
    """The detail registry plus plain keys, written to the catalog (so verify and the loaders agree) and loaded."""
    from visual_assets.store.catalog.registry import load_registry

    s.write_registry(env.catalog, [HERO, *extra], detail={HERO: (("plain", "bush"), "plain")})
    return load_registry(env.catalog / "definitions" / "visual_keys.yaml", allow_fixture_namespace=True)


def keep(env, width, **kw):
    kw.setdefault("set_id", SET)
    return drafts.keep(s.make_intake(env.tmp, width).intake_id, registry=env.registry, **kw)


def adopt_set(env, **over):
    args = dict(approver="Pat Approver", approver_role="art lead", licence_state="CLEARED", licence_evidence_ref="licence-note-7",
                review_evidence_ref="the review folder of revisions-v1", decided_at=s.NOW, confirm=s.yes, registry=env.registry, renderer=s.FakeRenderer())
    args.update(over)
    return setadoption.adopt_set(SET, **args)


def refused_set(env, code, **over):
    before = snapshot(env.catalog)
    with pytest.raises(GateError) as err:
        adopt_set(env, **over)
    assert err.value.code == code, err.value
    assert snapshot(env.catalog) == before  # all or nothing


def refused_keep(env, code, width=40, **kw):
    kw.setdefault("set_id", SET)
    before = snapshot(env.drafts) if env.drafts.exists() else {}
    with pytest.raises(DraftError) as err:
        drafts.keep(s.make_intake(env.tmp, width).intake_id, registry=env.registry, **kw)
    assert err.value.code == code, err.value
    assert (snapshot(env.drafts) if env.drafts.exists() else {}) == before


# ---- draft keep --revises --------------------------------------------------------------------------------------------------------------------

def test_keep_revises_records_the_parent_and_a_new_draft_does_not(world):
    revision = keep(world, 40, visual_key=ROCK, source_asset_id="rock_src", parent_revision="r0001")
    fresh = keep(world, 41, visual_key=OTHER)
    assert (revision.parent_revision, fresh.parent_revision) == ("r0001", None)
    record, data = drafts.load_set(SET)
    assert json.loads(data)["entries"][1]["parent_revision"] == "r0001" and "parent_revision" not in json.loads(data)["entries"][0]  # absent, not null, for a new asset
    assert data == canonical_json(record) and drafts.verify_set(SET, registry=world.registry) == []


def test_keep_without_revises_still_refuses_an_existing_source_asset_id(world):
    refused_keep(world, "source_asset_exists", visual_key=ROCK, source_asset_id="rock_src")


def test_keep_revises_refuses_a_missing_source_a_stale_or_bad_parent_and_a_changed_slot(world):
    refused_keep(world, "unknown_source_asset", visual_key=ROCK, source_asset_id="nobody", parent_revision="r0001")
    refused_keep(world, "invalid_parent", visual_key=ROCK, source_asset_id="rock_src", parent_revision="one")
    refused_keep(world, "parent_not_latest_unrevoked", visual_key=ROCK, source_asset_id="rock_src", parent_revision="r0002")
    refused_keep(world, "revision_changes_slot", visual_key=OTHER, source_asset_id="rock_src", parent_revision="r0001")
    refused_keep(world, "revision_changes_slot", visual_key=HERO, detail="plain", source_asset_id="hero_src", parent_revision="r0001")  # the hero was adopted for [bush]
    keep(world, 42, visual_key=HERO, detail="bush", source_asset_id="hero_src", parent_revision="r0001")  # the same slot is fine


def test_keep_revises_refuses_a_parent_whose_revisions_are_all_revoked(world, monkeypatch):
    revoke("rock_src/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    refused_keep(world, "parent_not_latest_unrevoked", visual_key=ROCK, source_asset_id="rock_src", parent_revision="r0001")


def test_a_set_without_revisions_or_drops_serialises_exactly_as_before(world):
    keep(world, 41, visual_key=OTHER)
    _, data = drafts.load_set(SET)
    body = json.loads(data)
    assert set(body) == {"record_type", "schema_version", "set_id", "entries"} and "parent_revision" not in body["entries"][0]


# ---- adopt-set with revisions ----------------------------------------------------------------------------------------------------------------

@pytest.fixture
def mixed(world):
    world.rev = keep(world, 40, visual_key=ROCK, source_asset_id="rock_src", parent_revision="r0001")
    world.new = keep(world, 41, visual_key=OTHER)
    return world


def test_a_mixed_set_adopts_a_new_asset_and_a_revision_in_one_decision(mixed):
    record = adopt_set(mixed)
    assert len(s.CALLS) == 1 and s.CALLS[0][0] == SET  # ONE typed confirmation
    notices = "\n".join(s.CALLS[0][1])
    assert "2 entries (1 new, 1 revisions), ALL or NONE" in notices
    assert f"NEW source asset {mixed.new.source_asset_id} r0001 for {OTHER}" in notices
    assert f"REVISION of rock_src: r0001 -> r0002 (parent r0001 is the latest unrevoked) for {ROCK}" in notices
    assert file_hash((mixed.drafts / SET / "draft_set.json").read_bytes()) in notices and "MATCHES" in notices
    assert sorted((e.visual_key, e.parent_revision) for e in record.entries) == sorted([(ROCK, "r0001"), (OTHER, None)])
    assert parse_record(SetAdoptionRecord, (mixed.catalog / "provenance" / "set-adoptions" / f"{record.set_adoption_id}.json").read_bytes()) == record
    assert records.list_revisions("rock_src") == ["r0001", "r0002"] and records.list_revisions(mixed.new.source_asset_id) == ["r0001"]
    adoption = records.load_adoption(records.load_source("rock_src", "r0002").adoption_id)
    assert (adoption.parent_revision, adoption.visual_key, adoption.source_revision, adoption.intake_id) == ("r0001", ROCK, "r0002", mixed.rev.draft_id)
    assert records.slot_holders(mixed.registry.keys[ROCK], None) == ["rock_src"]  # still held by the same asset, now at r0002


def test_a_set_adoption_of_new_assets_only_writes_the_records_it_always_wrote(world):
    keep(world, 41, visual_key=OTHER)
    record = adopt_set(world)
    body = json.loads(canonical_json(record))
    assert all("parent_revision" not in e for e in body["entries"])


def test_the_lineage_records_are_identical_to_those_of_adopt_parent(mixed):
    """The same revision adopted by `adopt-set` and by per-slot `adopt --parent` from the same catalog state: equal records and source bytes (the review check differs by construction)."""
    before = tmp_copy = mixed.tmp / "catalog-before"
    shutil.copytree(mixed.catalog, tmp_copy, symlinks=True)
    adopt_set(mixed)
    via_set = _revision_records(mixed, mixed.rev.draft_id)
    shutil.rmtree(mixed.catalog)
    shutil.copytree(before, mixed.catalog, symlinks=True)
    s.do_adopt(mixed.rev.draft_id, source_asset_id="rock_src", visual_key=ROCK, parent="r0001", registry=mixed.registry)
    via_adopt = _revision_records(mixed, mixed.rev.draft_id)
    assert via_set == via_adopt


def _revision_records(env, intake_id):
    adoption = parse_record(AdoptionRecord, (env.catalog / "provenance" / "adoptions" / f"{records.adoption_id_for(intake_id, 'rock_src', 'r0002')}.json").read_bytes())
    source = parse_record(SourceRecord, records.source_paths("rock_src", "r0002")[1].read_bytes())
    a, src = json.loads(canonical_json(adoption)), json.loads(canonical_json(source))
    for volatile in ("review_hash",):
        a.pop(volatile)
    src.pop("adoption_hash")  # derived from the adoption bytes, which hold the review hash
    return a, src, records.source_paths("rock_src", "r0002")[0].read_bytes()


def test_a_stale_parent_is_refused_and_nothing_is_written(mixed):
    s.do_adopt(s.make_intake(mixed.tmp, 50).intake_id, source_asset_id="rock_src", visual_key=ROCK, parent="r0001", registry=mixed.registry)  # r0002 now exists
    s.CALLS.clear()
    refused_set(mixed, "parent_not_latest_unrevoked")
    assert s.CALLS == []  # refused before the human is asked to type anything


def test_a_revision_whose_slot_changed_since_keeping_is_refused(mixed):
    record, _ = drafts.load_set(SET)
    entries = tuple(e.model_copy(update={"visual_key": OTHER}) if e.draft_id == mixed.rev.draft_id else e for e in record.entries)
    entries = tuple(sorted(entries, key=lambda e: (e.visual_key, e.detail or "")))
    # two entries now claim OTHER: give the NEW one another key so the set itself stays valid and only the revision's slot is wrong
    entries = tuple(e.model_copy(update={"visual_key": HERO, "detail": "plain"}) if e.draft_id == mixed.new.draft_id else e for e in entries)
    entries = tuple(sorted(entries, key=lambda e: (e.visual_key, e.detail or "")))
    (mixed.drafts / SET / "draft_set.json").write_bytes(canonical_json(DraftSet(record_type="draft_set", schema_version=1, set_id=SET, entries=entries)))
    refused_set(mixed, "revision_changes_slot")
    assert s.CALLS == []


def test_one_bad_revision_among_good_entries_writes_nothing(mixed):
    s.do_adopt(s.make_intake(mixed.tmp, 51).intake_id, source_asset_id="holder", visual_key=OTHER, registry=mixed.registry)  # the NEW entry's slot is taken: the revision before it must not land
    s.CALLS.clear()
    refused_set(mixed, "visual_key_taken")
    assert s.CALLS == [] and records.list_revisions("rock_src") == ["r0001"]


def test_a_concurrent_adoption_colliding_at_publish_time_rolls_the_whole_mixed_set_back(mixed, monkeypatch):
    """The parent check and the publish are not one step, so another adoption may take `rock_src` r0002 in between: the exclusive links refuse it and every earlier file of the set is removed."""
    real = catalogwrite._link
    calls = {"n": 0}

    def link(src, dst):
        calls["n"] += 1
        if calls["n"] == 8:  # part-way through the second entry's files
            raise FileExistsError(dst)
        return real(src, dst)

    monkeypatch.setattr(catalogwrite, "_link", link)
    refused_set(mixed, "already_exists")
    assert calls["n"] >= 8 and records.list_revisions("rock_src") == ["r0001"]


def test_the_revision_needs_the_same_checks_as_any_entry_and_a_revoked_parent_chain_is_refused(mixed):
    refused_set(mixed, "preview_mismatch", renderer=s.MismatchRenderer())
    revoke("rock_src/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    s.CALLS.clear()
    refused_set(mixed, "all_revisions_revoked")


def test_every_human_gate_property_still_holds_for_a_mixed_set(mixed, monkeypatch, capsys):
    refused_set(mixed, "not_confirmed", confirm=s.no)
    refused_set(mixed, "licence_not_cleared", licence_state="UNREVIEWED")
    refused_set(mixed, "review_evidence_missing", review_evidence_ref="  ")
    refused_set(mixed, "renderer_unavailable", renderer=None)
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: False)
    monkeypatch.setattr(builtins, "input", lambda prompt="": pytest.fail("must not prompt without a terminal"))
    before = snapshot(mixed.catalog)
    assert cli.main(["adopt-set", SET, "--approver", "Pat", "--approver-role", "lead", "--licence", "CLEARED", "--licence-evidence", "n", "--review-evidence", "r"]) == 2
    assert "no_terminal" in capsys.readouterr().err and snapshot(mixed.catalog) == before
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: True)
    monkeypatch.setattr(builtins, "input", lambda prompt="": "wrong-id")
    monkeypatch.setattr(cli, "_renderer", lambda: s.FakeRenderer())
    monkeypatch.setattr("visual_assets.store.adoption.load_registry", lambda *a, **k: mixed.registry)  # the CLI reads the real registry otherwise; this one holds the fixture keys
    monkeypatch.setattr("visual_assets.store.drafts.load_registry", lambda *a, **k: mixed.registry)
    assert cli.main(["adopt-set", SET, "--approver", "Pat", "--approver-role", "lead", "--licence", "CLEARED", "--licence-evidence", "n", "--review-evidence", "r"]) == 2
    assert "not_confirmed" in capsys.readouterr().err and snapshot(mixed.catalog) == before  # a wrong typed id adopts nothing


# ---- adopt --parent keeps the slot (the per-slot gate, tightened by the owner's approval) ----------------------------------------------------

def test_adopt_parent_refuses_a_revision_that_moves_the_source_to_another_key_or_detail(world):
    before = snapshot(world.catalog)
    with pytest.raises(GateError) as err:
        s.do_adopt(s.make_intake(world.tmp, 60).intake_id, source_asset_id="rock_src", visual_key=OTHER, parent="r0001", registry=world.registry)
    assert err.value.code == "revision_changes_slot" and snapshot(world.catalog) == before
    with pytest.raises(GateError) as err:
        s.do_adopt(s.make_intake(world.tmp, 61).intake_id, source_asset_id="hero_src", visual_key=HERO, detail_value="plain", parent="r0001", registry=world.registry)
    assert err.value.code == "revision_changes_slot" and snapshot(world.catalog) == before


def test_adopt_parent_still_accepts_a_revision_of_the_same_slot_including_the_default_detail_spelled_either_way(world):
    s.do_adopt(s.make_intake(world.tmp, 62).intake_id, source_asset_id="rock_src", visual_key=ROCK, parent="r0001", registry=world.registry)
    s.do_adopt(s.make_intake(world.tmp, 63).intake_id, source_asset_id="hero_src", visual_key=HERO, detail_value="bush", parent="r0001", registry=world.registry)
    assert records.list_revisions("rock_src") == ["r0001", "r0002"] and records.list_revisions("hero_src") == ["r0001", "r0002"]
    # an asset adopted for the key's DEFAULT detail may be revised naming the default explicitly or leaving it out
    s.do_adopt(s.make_intake(world.tmp, 64).intake_id, source_asset_id="plain_src", visual_key=HERO, registry=world.registry)
    s.do_adopt(s.make_intake(world.tmp, 65).intake_id, source_asset_id="plain_src", visual_key=HERO, detail_value="plain", parent="r0001", registry=world.registry)
    s.do_adopt(s.make_intake(world.tmp, 66).intake_id, source_asset_id="plain_src", visual_key=HERO, parent="r0002", registry=world.registry)
    assert records.list_revisions("plain_src") == ["r0001", "r0002", "r0003"]


# ---- draft drop ------------------------------------------------------------------------------------------------------------------------------

def test_drop_removes_the_draft_records_it_and_changes_the_hash(mixed):
    old = file_hash((mixed.drafts / SET / "draft_set.json").read_bytes())
    dropped = drafts.drop(SET, visual_key=OTHER, reason="owner declined this one", registry=mixed.registry)
    record, data = drafts.load_set(SET)
    assert [e.visual_key for e in record.entries] == [ROCK] and not (mixed.drafts / SET / mixed.new.draft_id).exists()
    assert [(d.visual_key, d.draft_id, d.reason) for d in record.dropped] == [(OTHER, mixed.new.draft_id, "owner declined this one")] and dropped == record.dropped[0]
    assert file_hash(data) != old and data == canonical_json(record) and drafts.verify_set(SET, registry=mixed.registry) == []
    assert list(mixed.drafts.glob(".tmp-*")) == [] and list((mixed.drafts / SET).glob(".tmp-*")) == []


def test_drop_names_a_detail_slot_and_treats_the_default_as_the_same_slot(world):
    keep(world, 70, visual_key=HERO)  # the default detail
    drafts.drop(SET, visual_key=HERO, detail="plain", reason="spelled as the explicit default", registry=world.registry)
    assert drafts.load_set(SET)[0].entries == () and drafts.load_set(SET)[0].dropped[0].detail is None


def test_drop_refuses_an_unknown_slot_and_an_unknown_set_or_key(world):
    keep(world, 41, visual_key=OTHER)
    before = snapshot(world.drafts)
    for kwargs, code in (({"visual_key": ROCK}, "unknown_slot"), ({"visual_key": "fixture.sample.nope"}, "unknown_visual_key"), ({"visual_key": HERO, "detail": "tree"}, "unknown_detail_value")):
        with pytest.raises(DraftError) as err:
            drafts.drop(SET, reason="x", registry=world.registry, **kwargs)
        assert err.value.code == code and snapshot(world.drafts) == before
    with pytest.raises(DraftError) as err:
        drafts.drop("no-such-set", visual_key=OTHER, reason="x", registry=world.registry)
    assert err.value.code == "unknown_set"


def test_drop_refuses_an_adopted_set_and_an_adopted_entry(mixed):
    adopt_set(mixed)
    before = snapshot(mixed.drafts)
    with pytest.raises(DraftError) as err:
        drafts.drop(SET, visual_key=OTHER, reason="too late", registry=mixed.registry)
    assert err.value.code == "set_adopted" and snapshot(mixed.drafts) == before  # an adopted set is never altered


def test_drop_refuses_an_entry_that_was_adopted_slot_by_slot_but_may_drop_its_unadopted_sibling(mixed):
    s.do_adopt(mixed.new.draft_id, source_asset_id=mixed.new.source_asset_id, visual_key=OTHER, registry=mixed.registry)  # adopted per slot, as the owner did for icons-owner-fixes-v1
    with pytest.raises(DraftError) as err:
        drafts.drop(SET, visual_key=OTHER, reason="no", registry=mixed.registry)
    assert err.value.code == "entry_adopted"
    drafts.drop(SET, visual_key=ROCK, reason="owner declined the revision", registry=mixed.registry)  # no set adoption record, this entry unadopted: allowed
    assert [e.visual_key for e in drafts.load_set(SET)[0].entries] == [OTHER]


def test_drop_validates_the_reason_and_the_count(mixed, monkeypatch):
    for bad in ("", "  ", "x" * 81, "line\nbreak", " padded "):
        with pytest.raises(DraftError) as err:
            drafts.drop(SET, visual_key=OTHER, reason=bad, registry=mixed.registry)
        assert err.value.code == "invalid_reason", bad
    drafts.drop(SET, visual_key=OTHER, reason="x" * 80, registry=mixed.registry)
    monkeypatch.setattr(config, "MAX_DROPPED_DRAFTS", 1)
    with pytest.raises(DraftError) as err:
        drafts.drop(SET, visual_key=ROCK, reason="second", registry=mixed.registry)
    assert err.value.code == "too_many_drops"


def test_keeping_a_dropped_draft_again_takes_it_out_of_the_drop_list(mixed):
    drafts.drop(SET, visual_key=OTHER, reason="changed my mind later", registry=mixed.registry)
    drafts.keep(mixed.new.draft_id, set_id=SET, visual_key=OTHER, registry=mixed.registry)
    record, _ = drafts.load_set(SET)
    assert record.dropped == () and sorted(e.visual_key for e in record.entries) == sorted([OTHER, ROCK])


def test_a_failed_write_leaves_the_set_untouched(mixed, monkeypatch):
    before = snapshot(mixed.drafts)
    monkeypatch.setattr(drafts.os, "replace", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError):
        drafts.drop(SET, visual_key=OTHER, reason="x", registry=mixed.registry)
    assert snapshot(mixed.drafts) == before


# ---- the command line ------------------------------------------------------------------------------------------------------------------------

def test_the_cli_keeps_a_revision_and_drops_a_draft_and_prints_the_new_hash(world, monkeypatch, capsys):
    monkeypatch.setattr("visual_assets.store.drafts.load_registry", lambda *a, **k: world.registry)
    revision = s.make_intake(world.tmp, 40)
    assert cli.main(["draft", "keep", revision.intake_id, "--set", SET, "--as", ROCK, "--source-asset-id", "rock_src", "--revises", "r0001"]) == 0
    assert "next revision of rock_src (parent r0001)" in capsys.readouterr().out
    assert cli.main(["draft", "keep", s.make_intake(world.tmp, 41).intake_id, "--set", SET, "--as", HERO, "--detail", "bush", "--source-asset-id", "hero_new"]) == 0
    capsys.readouterr()
    assert cli.main(["draft", "drop", SET, "--slot", f"{HERO}:bush", "--reason", "owner declined"]) == 0
    out = capsys.readouterr().out
    _, data = drafts.load_set(SET)
    assert f"the draft set hash is now {file_hash(data)}" in out and "no longer describes this set" in out and "nothing is adopted" in out
    assert cli.main(["draft", "drop", SET, "--slot", HERO + ":bush", "--reason", "again"]) == 2 and "unknown_slot" in capsys.readouterr().err
    assert cli.main(["draft", "keep", s.make_intake(world.tmp, 42).intake_id, "--set", "another-set", "--as", ROCK, "--source-asset-id", "rock_src", "--revises", "r0009"]) == 2
    assert "parent_not_latest_unrevoked" in capsys.readouterr().err


def test_no_agent_surface_gained_a_draft_or_adopt_tool():
    from visual_assets.drawing.server import mcp

    names = {t.name for t in mcp._tool_manager.list_tools()}
    assert not {n for n in names if "adopt" in n or "draft" in n or "drop" in n or "revis" in n}
