"""`revoke` and `is_build_eligible`: nothing is deleted, eligibility fails closed, intake revocation stays local."""

from __future__ import annotations

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config, records
from visual_assets.store.contracts import RevocationRecord, parse_record
from visual_assets.store.errors import GateError
from visual_assets.store.intake import review
from visual_assets.store.revoke import is_build_eligible, parse_target, revocation_id_for, revoke


@pytest.fixture(autouse=True)
def _reset():
    s.CALLS.clear()


def do_revoke(target, **over):
    args = dict(reason="rights withdrawn", approver="Pat Approver", approver_role="art lead", decided_at=s.NOW, confirm=s.yes)
    args.update(over)
    return revoke(target, **args)


def test_revoking_a_source_revision_makes_it_ineligible_and_deletes_nothing(env):
    result = s.make_intake(env.tmp)
    adoption = s.do_adopt(result.intake_id)
    assert is_build_eligible("hero", "r0001") is True
    before = snapshot(env.catalog)
    record = do_revoke("hero/r0001")
    assert is_build_eligible("hero", "r0001") is False
    after = snapshot(env.catalog)
    assert all(after[k] == v for k, v in before.items())  # every earlier file is still there, byte for byte
    added = set(after) - set(before)
    assert {k for k in added if after[k][0] == "file"} == {f"provenance/revocations/{record.revocation_id}.json"}
    stored = parse_record(RevocationRecord, (env.catalog / "provenance" / "revocations" / f"{record.revocation_id}.json").read_bytes())
    assert stored == record and stored.target.source_revision == "r0001" and stored.approver_name == "Pat Approver"
    assert records.find_adoption_for_intake(result.intake_id).adoption_id == adoption.adoption_id


def test_only_the_revoked_revision_is_ineligible(env):
    a, b_ = s.make_intake(env.tmp, 16), s.make_intake(env.tmp, 17)
    s.do_adopt(a.intake_id)
    s.do_adopt(b_.intake_id, new=False, parent="r0001")
    do_revoke("hero/r0002")
    assert is_build_eligible("hero", "r0001") is True and is_build_eligible("hero", "r0002") is False


@pytest.mark.parametrize("sid,rev", [("hero", "r0001"), ("ghost", "r0001"), ("hero", "r0009"), ("Hero", "r0001"), ("hero", "latest"),
                                     ("", ""), ("hero", None), (None, "r0001"), ("../x", "r0001"), ("hero", "r0000")])
def test_eligibility_is_false_for_anything_that_does_not_exist_or_is_malformed(env, sid, rev):
    assert is_build_eligible(sid, rev) is False  # nothing adopted at all


def test_eligibility_fails_closed_on_an_unreadable_revocation_file(env):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    assert is_build_eligible("hero", "r0001") is True
    base = env.catalog / "provenance" / "revocations"
    base.mkdir(parents=True, exist_ok=True)
    (base / "rv-0000000000000000.json").write_text("not json")  # we cannot prove nothing revokes it
    assert is_build_eligible("hero", "r0001") is False


def test_eligibility_fails_closed_on_a_corrupt_or_swapped_source_record(env):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    record = env.catalog / "sources" / "hero" / "r0001.source.json"
    original = record.read_bytes()
    record.write_bytes(b"{}")
    assert is_build_eligible("hero", "r0001") is False
    record.write_bytes(original.replace(b'"source_revision":"r0001"', b'"source_revision":"r0002"'))
    assert is_build_eligible("hero", "r0001") is False


def test_revoking_an_unadopted_intake_is_local_and_blocks_review_and_adoption(env):
    result = s.make_intake(env.tmp)
    before = snapshot(env.catalog)
    record = do_revoke(result.intake_id)
    assert snapshot(env.catalog) == before == {}  # nothing tracked was written
    local = env.quarantine / result.intake_id / "revocation.json"
    assert parse_record(RevocationRecord, local.read_bytes()) == record and record.target.intake_id == result.intake_id
    for call in (lambda: s.do_adopt(result.intake_id), lambda: review(result.intake_id)):
        with pytest.raises(Exception) as err:
            call()
        assert err.value.code == "intake_revoked"
    assert (env.quarantine / result.intake_id / "source.aseprite").exists()  # nothing deleted


def test_an_adopted_intake_cannot_be_revoked_as_an_intake(env):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    with pytest.raises(GateError) as err:
        do_revoke(result.intake_id)
    assert err.value.code == "intake_adopted" and "source revision" in err.value.message


def test_a_target_is_revoked_only_once(env):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    do_revoke("hero/r0001")
    before = snapshot(env.catalog)
    with pytest.raises(GateError) as err:
        do_revoke("hero/r0001")
    assert err.value.code == "already_revoked" and snapshot(env.catalog) == before
    other = s.make_intake(env.tmp, 17)
    do_revoke(other.intake_id)
    with pytest.raises(GateError) as err:
        do_revoke(other.intake_id)
    assert err.value.code == "already_revoked"


@pytest.mark.parametrize("target,code", [("hero/r0001", "unknown_target"), ("in-0000000000000000", "unknown_target"),
                                         ("nonsense", "invalid_target"), ("hero/latest", "invalid_target"), ("in-XYZ", "invalid_target"),
                                         ("Hero/r0001", "invalid_target"), ("hero/r0001/extra", "invalid_target"), ("", "invalid_target"),
                                         ("../x/r0001", "invalid_target")])
def test_bad_or_unknown_targets_are_refused_without_writing(env, target, code):
    with pytest.raises(GateError) as err:
        do_revoke(target)
    assert err.value.code == code and snapshot(env.catalog) == {} and s.CALLS == []


def test_arguments_are_checked_and_confirmation_is_last(env):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    s.CALLS.clear()
    for over, code in ((dict(decided_at="soon"), "bad_decided_at"), (dict(reason="line\nbreak"), "invalid_argument"),
                       (dict(approver=""), "invalid_argument"), (dict(approver_role="  "), "invalid_argument")):
        before = snapshot(env.catalog)
        with pytest.raises(GateError) as err:
            do_revoke("hero/r0001", **over)
        assert err.value.code == code and snapshot(env.catalog) == before and s.CALLS == []
    with pytest.raises(GateError) as err:
        do_revoke("hero/r0001", confirm=s.no)
    assert err.value.code == "not_confirmed" and is_build_eligible("hero", "r0001") is True
    expected, notices = s.CALLS[0]
    assert expected == "hero/r0001" and "never be undone" in "\n".join(notices)


def test_the_revocation_id_is_derived_from_the_target():
    assert revocation_id_for("source_revision", "hero/r0001") == revocation_id_for("source_revision", "hero/r0001")
    assert revocation_id_for("source_revision", "hero/r0001") != revocation_id_for("source_revision", "hero/r0002")
    assert parse_target("hero/r0001") == ("source_revision", "hero/r0001") and parse_target("in-0123456789abcdef")[0] == "intake"
    assert config.CATALOG_ROOT.exists()
