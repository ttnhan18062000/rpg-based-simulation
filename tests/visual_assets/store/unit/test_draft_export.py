"""`draft export`: the draft preview manifest the isolated preview page loads (`TCK-20261004-VISUAL-ASSETS-DRAFT-PREVIEW-PAGE`).

It is read-only on the drafts and the catalog, writes a NEW directory, is deterministic, carries the DraftSet file hash `adopt-set` prints, and is a record type that a runtime
manifest and a release can never be confused with. Pure Python; no Aseprite.
"""

from __future__ import annotations

import json
import re

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import FIXTURES, fixture_dict, snapshot
from tests.visual_assets.store.unit.test_drafts import HERO, ROCK, SET, adopt_set, drafting, keep, tamper, two  # noqa: F401  (fixtures)
from visual_assets.store import cli, config, draftexport, drafts
from visual_assets.store.contracts import DraftPreviewManifest, RuntimeManifest, SetAdoptionRecord, canonical_json, parse_record
from visual_assets.store.errors import ContractError, DraftError
from visual_assets.store.intake.validator import file_hash
from visual_assets.store.revoke import revoke


def export(env, name="out", **kw):
    return draftexport.export_draft_preview(SET, env.tmp / name, registry=env.registry, **kw)


def test_the_export_writes_the_manifest_and_one_png_per_distinct_preview_and_changes_nothing_else(two):
    before_catalog, before_drafts = snapshot(two.catalog), snapshot(two.drafts)
    manifest = export(two)
    out = two.tmp / "out"
    assert sorted(p.name for p in out.iterdir()) == sorted(["draft_preview_manifest.json", *{e.file for e in manifest.entries}])
    assert parse_record(DraftPreviewManifest, (out / "draft_preview_manifest.json").read_bytes()) == manifest
    assert [(e.visual_key, e.detail) for e in manifest.entries] == [(HERO, "bush"), (ROCK, None)]
    assert [(d.visual_key, d.values, d.default) for d in manifest.details] == [(HERO, ("plain", "bush"), "plain")]  # the declared axis, as in the runtime manifest
    for entry in manifest.entries:
        draft = two.drafts / SET / entry.draft_id / "preview.png"
        assert (out / entry.file).read_bytes() == draft.read_bytes()  # the very image the human reviews, byte for byte
        assert entry.file == entry.pixel_hash.split(":", 1)[1] + ".png" and entry.scale == 8 and entry.width % entry.scale == 0  # the previews are 8x
        assert entry.family == "sample" and entry.source_asset_id in {two.a.source_asset_id, two.b.source_asset_id}
    assert snapshot(two.catalog) == before_catalog and snapshot(two.drafts) == before_drafts


def test_the_export_is_deterministic(two):
    export(two, "first")
    export(two, "second")
    assert snapshot(two.tmp / "first") == snapshot(two.tmp / "second")


def test_the_page_shows_the_same_set_hash_as_the_adopt_set_notice_and_the_adoption_record(two):
    """The hash is computed three ways: the export's `draft_set_hash`, the hash `adopt-set` prints in its confirmation, and the one it stores."""
    manifest = export(two)
    expected = file_hash((two.drafts / SET / "draft_set.json").read_bytes())
    assert manifest.draft_set_hash == expected
    record = adopt_set(two)
    notices = "\n".join(s.CALLS[-1][1])
    assert re.search(r"DraftSet file hash is (sha256:[0-9a-f]{64})", notices).group(1) == manifest.draft_set_hash
    assert record.draft_set_hash == manifest.draft_set_hash
    stored = parse_record(SetAdoptionRecord, next((two.catalog / "provenance" / "set-adoptions").glob("*.json")).read_bytes())
    assert stored.draft_set_hash == manifest.draft_set_hash


def test_a_changed_set_changes_the_hash_so_a_review_of_the_old_set_does_not_cover_it(two):
    first = export(two, "first")
    keep(two, 18, visual_key=s.key_for("other"), source_asset_id="other_asset")
    assert export(two, "second").draft_set_hash != first.draft_set_hash


def refused(env, code, name="out", **kw):
    before = snapshot(env.tmp)
    with pytest.raises(DraftError) as err:
        draftexport.export_draft_preview(SET, env.tmp / name, registry=env.registry, **kw)
    assert err.value.code == code, err.value
    assert snapshot(env.tmp) == before  # no output directory, no .tmp-* leftover


def test_the_export_refuses_a_tampered_or_revoked_draft_and_an_unsafe_output_and_leaves_no_output(two):
    (two.tmp / "exists").mkdir()
    refused(two, "out_exists", name="exists")
    refused(two, "out_parent_missing", name="no/such/out")
    with pytest.raises(DraftError) as err:
        draftexport.export_draft_preview(SET, two.catalog / "out", registry=two.registry)
    assert err.value.code == "out_inside_store"
    with pytest.raises(DraftError) as err:
        draftexport.export_draft_preview(SET, two.drafts / SET / "out", registry=two.registry)
    assert err.value.code == "out_inside_store"
    revoke(two.b.draft_id, reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    refused(two, "draft_set_invalid")
    folder = two.drafts / SET / two.a.draft_id
    tamper(two, two.a, "source.aseprite", (folder / "source.aseprite").read_bytes() + b"x")
    refused(two, "draft_set_invalid")
    with pytest.raises(DraftError) as err:
        draftexport.export_draft_preview("no-such-set", two.tmp / "n", registry=two.registry)
    assert err.value.code == "unknown_set"


def test_the_draft_export_cli_prints_the_set_hash(two, monkeypatch, capsys):
    monkeypatch.setattr("visual_assets.store.draftexport.load_registry", lambda *a, **k: two.registry)
    assert cli.main(["draft", "export", SET, str(two.tmp / "cli_out")]) == 0
    assert file_hash((two.drafts / SET / "draft_set.json").read_bytes()) in capsys.readouterr().out
    assert cli.main(["draft", "export", SET, str(two.tmp / "cli_out")]) == 2  # never overwrites


# ---- a draft preview manifest and a runtime manifest can never be loaded as each other ------------------------------------------------

def draft_bytes() -> bytes:
    return (FIXTURES / "draft_preview_manifest.json").read_bytes()


def runtime_bytes() -> bytes:
    return (FIXTURES / "runtime_manifest.json").read_bytes()


def code_of(cls, data: bytes) -> str:
    with pytest.raises(ContractError) as err:
        parse_record(cls, data)
    return err.value.code


def test_each_manifest_is_refused_by_the_others_parser_and_keeps_failing_after_the_type_is_swapped():
    assert code_of(RuntimeManifest, draft_bytes()) == "wrong_record_type"
    assert code_of(DraftPreviewManifest, runtime_bytes()) == "wrong_record_type"
    swapped_draft = json.loads(draft_bytes())
    swapped_draft["record_type"] = "runtime_manifest"
    assert code_of(RuntimeManifest, json.dumps(swapped_draft).encode()) in {"unknown_field", "missing_field"}  # set_id, draft_set_hash and the entry extras
    swapped_runtime = json.loads(runtime_bytes())
    swapped_runtime["record_type"] = "draft_preview_manifest"
    assert code_of(DraftPreviewManifest, json.dumps(swapped_runtime).encode()) in {"unknown_field", "missing_field"}


def test_a_scale_must_be_a_whole_number_dividing_the_preview_exactly():
    base = fixture_dict(DraftPreviewManifest)
    for field, value in (("scale", 0), ("scale", 3), ("scale", 17), ("width", 130)):
        data = json.loads(json.dumps(base))
        data["entries"][0][field] = value
        assert code_of(DraftPreviewManifest, json.dumps(data).encode()) == "invalid_record", (field, value)


# ---- adopted references: a live adopted slot the set does not hold is shown, labelled, never part of the set -----------------------------------------------

OTHER = s.key_for("other")


@pytest.fixture
def referenced(two):
    """`two` (HERO [bush] and ROCK drafts) plus an ADOPTED and built asset for a third key, which the set does not hold."""
    from visual_assets.store.build import exporter

    two.other = s.do_adopt(s.make_intake(two.tmp, 20).intake_id, source_asset_id="other", visual_key=OTHER, registry=two.registry)
    exporter.build(renderer=s.HashRenderer())
    return two


def test_a_live_adopted_slot_the_set_does_not_hold_is_added_as_a_labelled_reference_built_from_the_catalog_artifact(referenced):
    manifest = export(referenced)
    by_key = {e.visual_key: e for e in manifest.entries}
    ref = by_key[OTHER]
    assert ref.adopted is True and ref.scale == 1 and ref.source_asset_id == "other" and ref.draft_id == referenced.other.intake_id
    artifact_png = next((referenced.catalog / "generated" / "other--x1").glob("*.png")).read_bytes()
    assert (referenced.tmp / "out" / ref.file).read_bytes() == artifact_png  # the catalog's own artifact, byte for byte, nothing from a draft
    assert (by_key[HERO].adopted, by_key[ROCK].adopted) == (None, None)  # draft entries carry no such field
    assert b'"adopted"' not in canonical_json(manifest.model_copy(update={"entries": tuple(e for e in manifest.entries if e.adopted is None)}))


def test_a_draft_for_the_slot_always_wins_so_no_reference_is_added(referenced):
    keep(referenced, 18, visual_key=OTHER, source_asset_id="other_draft")
    manifest = export(referenced)
    entries = [e for e in manifest.entries if e.visual_key == OTHER]
    assert [(e.adopted, e.source_asset_id) for e in entries] == [(None, "other_draft")]


def test_references_never_reach_the_draft_set_draft_verify_or_adopt_set(referenced):
    set_bytes = (referenced.drafts / SET / "draft_set.json").read_bytes()
    manifest = export(referenced)
    assert any(e.adopted for e in manifest.entries)
    assert (referenced.drafts / SET / "draft_set.json").read_bytes() == set_bytes  # the set record is untouched
    assert manifest.draft_set_hash == file_hash(set_bytes)  # and the reviewed hash is the set's, not the export's
    assert drafts.verify_set(SET, registry=referenced.registry) == []  # `draft verify` never sees a reference
    record = adopt_set(referenced)
    assert sorted(e.visual_key for e in record.entries) == [HERO, ROCK]  # exactly the drafts; the adopted reference is not re-adopted
    assert OTHER not in {e.visual_key for e in record.entries}


def test_the_adopted_field_is_only_ever_the_literal_true():
    data = json.loads(draft_bytes())
    data["entries"][0]["adopted"] = True
    assert parse_record(DraftPreviewManifest, json.dumps(data).encode()).entries[0].adopted is True
    for bad in (False, 1, "true", None):
        data["entries"][0]["adopted"] = bad
        if bad is None:
            continue  # an explicit null is the same as absent
        assert code_of(DraftPreviewManifest, json.dumps(data).encode()) == "invalid_record", bad
