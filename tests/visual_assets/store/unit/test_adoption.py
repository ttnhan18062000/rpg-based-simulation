"""`adopt`: exact writes, lineage rules, and every refusal with its own code and an unchanged catalog."""

from __future__ import annotations

import stat

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config, records
from visual_assets.store.adoption import PREVIEW_WARNING
from visual_assets.store.contracts import AdoptionRecord, IntakeResult, ReviewRenderCheck, SourceRecord, parse_record
from visual_assets.store.errors import GateError
from visual_assets.store.intake.validator import file_hash


@pytest.fixture(autouse=True)
def _reset_calls():
    s.CALLS.clear()


def paths(env, sid="hero", rev="r0001", ad=None, intake_id=None):
    return {
        "source": env.catalog / "sources" / sid / f"{rev}.aseprite",
        "record": env.catalog / "sources" / sid / f"{rev}.source.json",
        "adoption": env.catalog / "provenance" / "adoptions" / f"{ad}.json",
        "intake": env.catalog / "provenance" / "intake" / f"{intake_id}.json",
        "review": env.catalog / "provenance" / "intake" / f"{intake_id}.review.json",
    }


def test_adopting_a_passed_intake_writes_exactly_five_consistent_files(env):
    result = s.make_intake(env.tmp)
    before = snapshot(env.catalog)
    adoption = s.do_adopt(result.intake_id)
    after = snapshot(env.catalog)
    p = paths(env, ad=adoption.adoption_id, intake_id=result.intake_id)
    new_files = {k for k, v in after.items() if v[0] == "file"}
    assert new_files == {str(path.relative_to(env.catalog)) for path in p.values()}
    assert not before
    staged = env.quarantine / result.intake_id
    source = parse_record(SourceRecord, p["record"].read_bytes())
    adopted = parse_record(AdoptionRecord, p["adoption"].read_bytes())
    copy = p["intake"].read_bytes()
    assert copy == (staged / "intake_result.json").read_bytes() and parse_record(IntakeResult, copy) == result
    assert p["source"].read_bytes() == (staged / "source.aseprite").read_bytes()
    digest = file_hash(p["source"].read_bytes())
    assert source.source_hash == adopted.source_hash == digest and result.staged_files[1].file_hash == digest
    assert adopted.intake_hash == file_hash(copy) and source.adoption_hash == file_hash(p["adoption"].read_bytes())
    check = parse_record(ReviewRenderCheck, p["review"].read_bytes())  # the store's own render check is part of the tracked provenance
    assert p["review"].read_bytes() == (staged / "review_render.json").read_bytes() and adopted.review_hash == file_hash(p["review"].read_bytes())
    assert check.verdict.value == "MATCH" and check.intake_id == result.intake_id and check.source_hash == digest
    assert (source.source_revision, source.parent_revision, source.adoption_id) == ("r0001", None, adoption.adoption_id)
    assert adopted.adoption_id == records.adoption_id_for(result.intake_id, "hero", "r0001")
    assert (adopted.approver_name, adopted.approver_role, adopted.visual_key) == ("Pat Approver", "art lead", s.KEY)
    assert adopted.licence_state.value == "CLEARED" and adopted.licence_evidence_ref == "licence-note-7"
    assert (source.width, source.height) == (16, 16) and source.source_format.value == "ASEPRITE"
    for path in p.values():
        assert stat.S_IMODE(path.stat().st_mode) == 0o644
    assert list(env.quarantine.glob(".tmp-publish-*")) == []  # the temporary directory is gone


def test_the_human_is_shown_the_warning_and_asked_once_and_last(env):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    assert len(s.CALLS) == 1
    expected, notices = s.CALLS[0]
    assert expected == result.intake_id
    text = "\n".join(notices)
    assert PREVIEW_WARNING in notices and "hero r0001" in text and "stated by you, not taken from the package" in text
    assert "recorded, not authenticated" in text
    assert "evidence 'licence-note-7'" in text and "{licence_evidence_ref" not in text  # the notice the human approves shows the real evidence ref


def test_a_second_revision_gets_r0002_with_parent_r0001_and_leaves_r0001_untouched(env):
    first = s.make_intake(env.tmp, 16)
    second = s.make_intake(env.tmp, 17)
    a1 = s.do_adopt(first.intake_id)
    before = {k: v for k, v in snapshot(env.catalog).items() if "r0001" in k or a1.adoption_id in k or first.intake_id in k}
    a2 = s.do_adopt(second.intake_id, new=False, parent="r0001")
    assert a2.source_revision == "r0002" and a2.parent_revision == "r0001"
    assert parse_record(SourceRecord, paths(env, rev="r0002")["record"].read_bytes()).parent_revision == "r0001"
    after = snapshot(env.catalog)
    assert {k: after[k] for k in before} == before  # r0001 and its records are byte-identical
    assert records.list_revisions("hero") == ["r0001", "r0002"]


def test_the_licence_comes_only_from_the_humans_arguments(env):
    result = s.make_intake(env.tmp)
    package_claim = parse_record(__import__("visual_assets.store.contracts", fromlist=["CandidateHandoffPackage"]).CandidateHandoffPackage,
                                 (env.quarantine / result.intake_id / "package.json").read_bytes())
    assert package_claim.licence_evidence_ref == "fixture-licence-note"  # what the producer claimed
    adopted = s.do_adopt(result.intake_id, licence_evidence_ref="humans-own-evidence")
    assert adopted.licence_evidence_ref == "humans-own-evidence"  # never defaulted from the package


REFUSALS = {}


def refusal(code):
    def register(fn):
        REFUSALS[code] = fn
        return fn
    return register


@refusal("unknown_intake")
def _unknown(env, result, **_):
    return dict(intake_id="in-0000000000000000")


@refusal("bad_intake_id")
def _bad_id(env, result, **_):
    return dict(intake_id="../nope")


@refusal("intake_not_passed")
def _quarantined(env, result, **_):
    return dict(intake_id=s.make_intake(env.tmp, 18, passed=False).intake_id)


@refusal("staged_bytes_changed")
def _changed(env, result, **_):
    path = env.quarantine / result.intake_id / "preview.png"
    path.write_bytes(path.read_bytes() + b"\x00")
    return {}


@refusal("staged_bytes_unreadable")
def _unreadable(env, result, **_):
    (env.quarantine / result.intake_id / "extra.txt").write_text("x")
    return {}


@refusal("intake_revoked")
def _revoked(env, result, **_):
    (env.quarantine / result.intake_id / "revocation.json").write_text("{}")
    return {}


@refusal("unknown_visual_key")
def _key(env, result, **_):
    return dict(visual_key="fixture.sample.nope")


@refusal("licence_not_cleared")
def _licence(env, result, **_):
    return dict(licence_state="RESTRICTED")


@refusal("licence_evidence_missing")
def _evidence(env, result, **_):
    return dict(licence_evidence_ref="UNAVAILABLE")


@refusal("invalid_approver")
def _approver(env, result, **_):
    return dict(approver="   ")


@refusal("invalid_argument")
def _argument(env, result, **_):
    return dict(approver="Pat\nApprover")


@refusal("source_too_large")
def _large(env, result, monkeypatch, **_):
    monkeypatch.setattr(config, "MAX_SOURCE_BYTES", 10)
    return {}


@refusal("invalid_mode")
def _mode(env, result, **_):
    return dict(new=True, parent="r0001")


def test_neither_new_nor_a_parent_is_an_invalid_mode(env):
    result = s.make_intake(env.tmp)
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id, new=False, parent=None)
    assert err.value.code == "invalid_mode" and snapshot(env.catalog) == {}


@refusal("unknown_source_asset")
def _no_asset(env, result, **_):
    return dict(new=False, parent="r0001")


@refusal("invalid_parent")
def _parent(env, result, **_):
    return dict(new=False, parent="latest")


@refusal("invalid_source_asset_id")
def _sid(env, result, **_):
    return dict(source_asset_id="Hero/../x")


@refusal("bad_decided_at")
def _when(env, result, **_):
    return dict(decided_at="yesterday")


@refusal("not_confirmed")
def _unconfirmed(env, result, **_):
    return dict(confirm=s.no)


@pytest.mark.parametrize("code", sorted(REFUSALS))
def test_each_refusal_has_its_own_code_and_leaves_the_catalog_byte_identical(env, monkeypatch, code):
    result = s.make_intake(env.tmp)
    overrides = REFUSALS[code](env, result, monkeypatch=monkeypatch)
    intake_id = overrides.pop("intake_id", result.intake_id)
    before = snapshot(env.catalog)
    with pytest.raises(GateError) as err:
        s.do_adopt(intake_id, **overrides)
    assert err.value.code == code, err.value
    assert snapshot(env.catalog) == before == {}
    assert list(env.quarantine.glob(".tmp-publish-*")) == []
    if code != "not_confirmed":
        assert s.CALLS == [], "a refusal must come before the confirmation prompt"


def test_an_intake_is_adopted_only_once(env):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    before = snapshot(env.catalog)
    for kwargs in (dict(source_asset_id="other"), dict(source_asset_id="hero", new=False, parent="r0001")):
        with pytest.raises(GateError) as err:
            s.do_adopt(result.intake_id, **kwargs)
        assert err.value.code == "already_adopted"
    assert snapshot(env.catalog) == before


def test_a_missing_registry_is_reported_not_guessed(env):
    result = s.make_intake(env.tmp)
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id, registry=None)  # this catalog root has no definitions/visual_keys.yaml
    assert err.value.code == "registry_unreadable" and snapshot(env.catalog) == {}


def test_a_fixture_key_is_refused_by_the_default_registry(env):
    result = s.make_intake(env.tmp)
    committed = (config.__file__ and __import__("pathlib").Path(config.__file__).resolve().parents[1] / "catalog" / "definitions" / "visual_keys.yaml")
    (env.catalog / "definitions").mkdir()
    (env.catalog / "definitions" / "visual_keys.yaml").write_bytes(committed.read_bytes())
    before = snapshot(env.catalog)
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id, registry=None)  # the committed registry has zero keys and refuses fixture.*
    assert err.value.code == "unknown_visual_key"
    assert snapshot(env.catalog) == before


def test_an_alias_is_not_a_visual_key_for_adoption(env):
    result = s.make_intake(env.tmp)
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id, visual_key="fixture.sample.old_hero")  # an alias of the key of "hero"
    assert err.value.code == "unknown_visual_key"


def test_a_new_asset_id_that_exists_is_refused_and_the_parent_must_exist(env):
    first, second, third = (s.make_intake(env.tmp, w) for w in (16, 17, 18))
    s.do_adopt(first.intake_id)
    with pytest.raises(GateError) as err:
        s.do_adopt(second.intake_id, new=True)
    assert err.value.code == "source_asset_exists"
    with pytest.raises(GateError) as err:
        s.do_adopt(second.intake_id, new=False, parent="r0001", source_asset_id="ghost")
    assert err.value.code == "unknown_source_asset"
    with pytest.raises(GateError) as err:
        s.do_adopt(second.intake_id, new=False, parent="r0002")  # not the latest
    assert err.value.code == "parent_not_latest_unrevoked"


def test_a_revoked_revision_does_not_freeze_its_asset(env):
    from visual_assets.store.revoke import revoke

    a, b_, c = (s.make_intake(env.tmp, w) for w in (16, 17, 18))
    s.do_adopt(a.intake_id)
    s.do_adopt(b_.intake_id, new=False, parent="r0001")
    revoke("hero/r0002", reason="bad pixels", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    with pytest.raises(GateError) as err:  # the revoked r0002 is no longer a valid parent
        s.do_adopt(c.intake_id, new=False, parent="r0002")
    assert err.value.code == "parent_not_latest_unrevoked"
    fixed = s.do_adopt(c.intake_id, new=False, parent="r0001")  # the repair: latest UNREVOKED revision is the parent
    assert fixed.source_revision == "r0003" and fixed.parent_revision == "r0001"  # numbering continues after the highest
    assert records.list_revisions("hero") == ["r0001", "r0002", "r0003"]


def test_when_every_revision_is_revoked_the_id_is_closed(env):
    from visual_assets.store.revoke import revoke

    a, b_ = s.make_intake(env.tmp, 16), s.make_intake(env.tmp, 17)
    s.do_adopt(a.intake_id)
    revoke("hero/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    before = snapshot(env.catalog)
    with pytest.raises(GateError) as err:
        s.do_adopt(b_.intake_id, new=False, parent="r0001")
    assert err.value.code == "all_revisions_revoked"
    assert snapshot(env.catalog) == before
    s.do_adopt(b_.intake_id, source_asset_id="hero2")  # a new id works


def test_adopting_an_already_adopted_intake_whose_revision_is_revoked_says_so(env):
    from visual_assets.store.revoke import revoke

    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    revoke("hero/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id, source_asset_id="again")
    assert err.value.code == "adoption_revoked"
    assert paths(env, ad=records.adoption_id_for(result.intake_id, "hero", "r0001"))["source"].exists()  # nothing was deleted


def test_a_symlinked_catalog_directory_is_refused_without_writing_through_it(env):
    result = s.make_intake(env.tmp)
    elsewhere = env.tmp / "elsewhere"
    elsewhere.mkdir()
    (env.catalog / "sources").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id)
    assert err.value.code == "catalog_symlink"
    assert list(elsewhere.iterdir()) == []


def test_the_committed_catalog_is_never_touched_by_these_tests():
    # The committed records are exactly the owner's: the forest's three slots (TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE, ...-FOREST-DETAIL-TILES) and the 31 sources of the adoption of terrain-v1 on
    # 2026-10-05T18:17:03Z: 34 sources, 34 adoptions, two intake files each, one set adoption, no revocations. A test adoption would add one more; the equality makes that fail.
    from tests.visual_assets import adopted_facts as af

    committed = config.CATALOG_ROOT
    for name, count in (("sources", af.ADOPTION_COUNT), ("provenance/adoptions", af.ADOPTION_COUNT), ("provenance/intake", af.INTAKE_FILE_COUNT), ("provenance/set-adoptions", 1), ("provenance/revocations", 0)):
        found = [p.name for p in (committed / name).iterdir() if p.name != ".gitkeep"] if (committed / name).exists() else []
        assert len(found) == count, (name, found)
    assert sorted(p.name for p in (committed / "sources").iterdir() if p.name != ".gitkeep") == af.ADOPTED_SOURCES


# --------------------------------------------------------------------------- R4: the same bytes through another intake


def test_a_revocation_cannot_be_sidestepped_by_a_second_intake_of_the_same_bytes(env):
    from visual_assets.store.revoke import revoke

    first = s.make_intake(env.tmp)
    s.do_adopt(first.intake_id)
    revoke("hero/r0001", reason="rights withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    again = s.make_intake_same_bytes(env.tmp, first)
    assert again.intake_id != first.intake_id and again.staged_files[1] == first.staged_files[1]
    before = snapshot(env.catalog)
    s.CALLS.clear()
    for kwargs in (dict(source_asset_id="hero-again"), dict(source_asset_id="hero", new=False, parent=None)):
        with pytest.raises(GateError) as err:
            s.do_adopt(again.intake_id, **kwargs)
        assert err.value.code in {"source_bytes_revoked", "invalid_mode"}
    with pytest.raises(GateError) as err:
        s.do_adopt(again.intake_id, source_asset_id="hero-again")
    assert err.value.code == "source_bytes_revoked" and "hero r0001" in err.value.message
    assert snapshot(env.catalog) == before and s.CALLS == []


def test_the_same_bytes_cannot_be_adopted_twice_as_two_live_assets(env):
    first = s.make_intake(env.tmp)
    s.do_adopt(first.intake_id)
    again = s.make_intake_same_bytes(env.tmp, first)
    before = snapshot(env.catalog)
    s.CALLS.clear()
    with pytest.raises(GateError) as err:
        s.do_adopt(again.intake_id, source_asset_id="rock")
    assert err.value.code == "duplicate_source" and "hero r0001" in err.value.message
    with pytest.raises(GateError) as err:  # also not as the next revision of the same asset
        s.do_adopt(again.intake_id, new=False, parent="r0001")
    assert err.value.code == "duplicate_source"
    assert snapshot(env.catalog) == before and s.CALLS == []


def test_a_genuinely_different_source_still_adopts(env):
    first = s.make_intake(env.tmp, 16)
    s.do_adopt(first.intake_id)
    different = s.make_intake(env.tmp, 17)
    assert s.do_adopt(different.intake_id, source_asset_id="rock").source_revision == "r0001"


def test_a_locally_revoked_intake_covers_its_source_bytes_for_other_intakes(env):
    from visual_assets.store.revoke import revoke

    first = s.make_intake(env.tmp)
    revoke(first.intake_id, reason="not wanted", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    again = s.make_intake_same_bytes(env.tmp, first)
    s.CALLS.clear()
    with pytest.raises(GateError) as err:
        s.do_adopt(again.intake_id)
    assert err.value.code == "source_bytes_revoked" and first.intake_id in err.value.message
    assert snapshot(env.catalog) == {} and s.CALLS == []


def test_a_revoked_revision_wins_over_a_live_duplicate_in_the_message(env):
    from visual_assets.store.revoke import revoke

    a = s.make_intake(env.tmp, 16)
    s.do_adopt(a.intake_id)
    revoke("hero/r0001", reason="x", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    again = s.make_intake_same_bytes(env.tmp, a)
    with pytest.raises(GateError) as err:
        s.do_adopt(again.intake_id, source_asset_id="other")
    assert err.value.code == "source_bytes_revoked"
