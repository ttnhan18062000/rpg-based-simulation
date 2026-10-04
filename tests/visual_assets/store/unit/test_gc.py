"""`gc`: lists by default, deletes only on request, and only what it lists, only under the quarantine, the review area and generated/."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config
from visual_assets.store import gc as gc_mod
from visual_assets.store import review as review_mod
from visual_assets.store.errors import IdentityError
from visual_assets.store.release import assemble_release
from visual_assets.store.revoke import revoke

# `make_intake` stamps its intakes 2026-01-01; `AT` is a day later, so the retention rule does not fire unless a test moves the clock
CREATED = datetime(2026, 1, 1, tzinfo=timezone.utc)
AT = CREATED + timedelta(days=1)
DAY = timedelta(days=1)


def run_gc(*, delete: bool = False, now: datetime):
    """`gc` as the CLI calls it: the library takes a cutoff timestamp (it never reads the clock), so the test computes it from `now`."""
    cutoff = (now - timedelta(days=config.MAX_UNADOPTED_INTAKE_AGE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return gc_mod.gc(delete=delete, expire_before=cutoff)


@pytest.fixture
def messy(env):
    """Adopted (kept), pending-review PASSED (kept), QUARANTINED, revoked-local, a leftover temp dir, and an orphan generated PNG."""
    s.CALLS.clear()
    adoptions, built = s.adopted_tree(env, widths=(16,))
    env.adopted = adoptions[0].intake_id
    env.pending = s.make_intake(env.tmp, 17).intake_id
    env.quarantined = s.make_intake(env.tmp, 18, passed=False).intake_id
    env.revoked = s.make_intake(env.tmp, 19).intake_id
    revoke(env.revoked, reason="not wanted", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    (env.quarantine / ".tmp-in-0123456789abcdef-deadbeef").mkdir()
    (env.catalog / "generated" / "hero--x1" / ("e" * 64 + ".png")).write_bytes(b"orphan")
    review_mod.review(env.adopted, created_at=s.NOW, renderer=s.FakeRenderer())  # a review export whose intake is adopted
    review_mod.review(env.pending, created_at=s.NOW, renderer=s.FakeRenderer())  # a review export that is still wanted
    return env


def names(items):
    return sorted((i.kind, i.path.name) for i in items)


def test_the_garbage_list_is_exactly_what_nothing_needs(messy):
    expected = sorted([
        ("quarantine", messy.quarantined), ("quarantine", messy.revoked), ("quarantine", ".tmp-in-0123456789abcdef-deadbeef"),
        ("review", messy.adopted), ("review", messy.revoked), ("generated", "e" * 64 + ".png"),
    ])  # make_intake also exported a review for the adopted, pending and revoked intakes: the adopted and revoked ones are garbage
    assert names(run_gc(now=AT)) == expected
    kept = {p.name for p in messy.quarantine.iterdir()}
    assert messy.adopted in kept and messy.pending in kept  # adopted evidence and a pending review are never garbage
    assert (messy.review / messy.pending).exists()


def test_a_dry_run_changes_nothing(messy):
    before = (snapshot(messy.catalog), snapshot(messy.quarantine), snapshot(messy.review))
    run_gc(now=AT)
    run_gc(delete=False, now=AT)
    assert (snapshot(messy.catalog), snapshot(messy.quarantine), snapshot(messy.review)) == before


def test_delete_removes_only_what_was_listed_and_never_tracked_history(messy):
    listed = run_gc(now=AT)
    tracked_before = {k: v for k, v in snapshot(messy.catalog).items() if not k.startswith("generated/hero--x1/" + "e" * 64)}
    removed = run_gc(delete=True, now=AT)
    assert names(removed) == names(listed)
    for item in listed:
        assert not item.path.exists()
    assert snapshot(messy.catalog) == tracked_before  # sources/, provenance/, manifests/ and every referenced artifact are untouched
    assert {p.name for p in messy.quarantine.iterdir()} == {messy.adopted, messy.pending}
    assert {p.name for p in messy.review.iterdir()} == {messy.pending}
    assert run_gc(now=AT) == []  # and a second run finds nothing


def test_deleting_a_locally_revoked_intake_also_deletes_its_local_revocation(messy):
    revocation = messy.quarantine / messy.revoked / "revocation.json"
    assert revocation.exists()
    run_gc(delete=True, now=AT)
    assert not revocation.exists() and not (messy.quarantine / messy.revoked).exists()  # stated in the docs


def test_delete_never_follows_a_symlink(messy):
    outside = messy.tmp / "precious"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    link = messy.quarantine / ".tmp-in-ffffffffffffffff-00000000"
    link.symlink_to(outside, target_is_directory=True)
    run_gc(delete=True, now=AT)
    assert (outside / "keep.txt").read_text() == "keep"
    assert link.is_symlink()  # a symlink is not removed through, and not followed


def test_an_unreadable_intake_is_not_ours_to_judge(env):
    result = s.make_intake(env.tmp, passed=False)
    (env.quarantine / result.intake_id / "intake_result.json").write_text("garbage")
    assert run_gc(delete=True, now=AT) == [] and (env.quarantine / result.intake_id).exists()


def test_a_png_that_a_record_refers_to_is_kept(env):
    s.adopted_tree(env, widths=(16,))
    assert [i for i in run_gc(delete=True, now=AT) if i.kind == "generated"] == []  # (the adopted intake's review export is collected, the PNG is not)
    assert len(list((env.catalog / "generated" / "hero--x1").glob("*.png"))) == 1


def test_an_empty_world_has_nothing_to_collect(env):
    assert run_gc(now=AT) == [] and run_gc(delete=True, now=AT) == []


def test_an_artifact_record_without_a_png_is_not_garbage(env):
    s.adopted_tree(env, widths=(16,))
    next((env.catalog / "generated" / "hero--x1").glob("*.png")).unlink()
    assert [i for i in run_gc(delete=True, now=AT) if i.kind == "generated"] == []  # corruption is `verify`'s to report, not gc's to hide
    assert any(p.name.endswith(".artifact.json") for p in (env.catalog / "generated" / "hero--x1").iterdir())


# --------------------------------------------------------------------------- retention (TCK-20261004-VISUAL-ASSETS-RETENTION-AND-ROLLBACK)


def clock(days: float) -> datetime:
    """A moment `days` after the intakes were created."""
    return CREATED + timedelta(days=days)


def test_the_retention_bound_is_the_approved_thirty_days():
    assert config.MAX_UNADOPTED_INTAKE_AGE_DAYS == 30


def test_a_young_passed_intake_and_its_review_are_protected(env):
    pending = s.make_intake(env.tmp, 17).intake_id
    assert (env.review / pending).exists()
    for days in (0, 29, 30):  # exactly the bound is still kept
        assert run_gc(now=clock(days)) == [], days
    assert (env.quarantine / pending).exists() and (env.review / pending).exists()


def test_an_old_passed_intake_and_its_review_are_listed_and_only_those_are_deleted(env):
    old = s.make_intake(env.tmp, 17).intake_id
    other = s.make_intake(env.tmp, 18).intake_id  # a second PASSED intake (make_intake exports a review for each)
    listed = run_gc(now=clock(31))
    assert names(listed) == sorted([("quarantine", old), ("quarantine", other), ("review", old), ("review", other)])
    assert all("older than 30 days" in i.reason or "expired" in i.reason for i in listed)
    assert (env.quarantine / old).exists()  # a dry run removed nothing
    run_gc(delete=True, now=clock(31))
    assert not (env.quarantine / old).exists() and not (env.review / old).exists() and not (env.quarantine / other).exists()


def test_an_adopted_intake_is_never_expired_however_old(env):
    s.CALLS.clear()
    adoptions, _ = s.adopted_tree(env, widths=(16,))
    adopted = adoptions[0].intake_id
    before = snapshot(env.catalog)
    listed = run_gc(delete=True, now=clock(3650))
    assert (env.quarantine / adopted).exists()  # the adoption's evidence outlives any age
    assert all(i.path.name != adopted or i.kind == "review" for i in listed)
    assert snapshot(env.catalog) == before  # no tracked file changed


def test_tracked_state_is_never_listed_or_removed_at_any_age(env):
    s.CALLS.clear()
    s.adopted_tree(env, widths=(16, 17))
    s.write_registry(env.catalog, [s.key_for("hero"), s.key_for("rock")])
    assemble_release("main", allow_fixture_namespace=True)
    before = snapshot(env.catalog)
    for item in run_gc(delete=True, now=clock(100_000)):
        assert item.kind in {"quarantine", "review"}, item  # never a generated/ file here, never anything tracked
    after = snapshot(env.catalog)
    assert {k: v for k, v in after.items() if not k.startswith((".quarantine", ".review"))} == {k: v for k, v in before.items() if not k.startswith((".quarantine", ".review"))}


def test_unreferenced_tracked_artifacts_are_reported_never_deleted(env):
    s.CALLS.clear()
    s.adopted_tree(env, widths=(16, 17))  # hero and rock are built
    s.write_registry(env.catalog, [s.key_for("hero")])  # the release names only hero
    assemble_release("main", allow_fixture_namespace=True)
    reported = gc_mod.tracked_unreferenced()
    assert [p.name.endswith(".r0001.artifact.json") and p.parent.name for p in reported] == ["rock--x1"]
    before = snapshot(env.catalog)
    run_gc(delete=True, now=AT)
    assert snapshot(env.catalog) == before and reported[0].exists()  # reported only: tracked history stays


def test_nothing_is_reported_when_every_artifact_is_in_a_committed_release(env):
    s.CALLS.clear()
    s.adopted_tree(env, widths=(16, 17))
    s.write_registry(env.catalog, [s.key_for("hero"), s.key_for("rock")])
    assemble_release("main", allow_fixture_namespace=True)
    assert gc_mod.tracked_unreferenced() == []


def test_without_any_release_every_artifact_is_reported(env):
    s.CALLS.clear()
    s.adopted_tree(env, widths=(16, 17))
    assert len(gc_mod.tracked_unreferenced()) == 2


@pytest.mark.parametrize("cutoff", ["9999", "9999-12-31", "2026-10-4T00:00:00Z", "2026-10-04T00:00:00+07:00", "2026-10-04 00:00:00Z", "2026-02-30T00:00:00Z", "", "now"])
def test_a_malformed_cutoff_is_refused_and_nothing_is_listed_or_deleted(env, cutoff):
    s.make_intake(env.tmp, 17)  # a young PASSED intake that a bad cutoff such as "9999" would otherwise expire
    before = (snapshot(env.catalog), snapshot(env.quarantine), snapshot(env.review))
    for delete in (False, True):
        with pytest.raises(IdentityError):
            gc_mod.gc(delete=delete, expire_before=cutoff)
    with pytest.raises(IdentityError):
        gc_mod.collect(cutoff)
    assert (snapshot(env.catalog), snapshot(env.quarantine), snapshot(env.review)) == before


def test_a_canonical_cutoff_is_accepted(env):
    assert gc_mod.gc(expire_before="2026-01-02T00:00:00Z") == []
