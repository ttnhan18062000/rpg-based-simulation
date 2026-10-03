"""`gc`: lists by default, deletes only on request, and only what it lists, only under the quarantine, the review area and generated/."""

from __future__ import annotations

import json

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import gc as gc_mod
from visual_assets.store import review as review_mod
from visual_assets.store.revoke import revoke


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
    assert names(gc_mod.gc()) == expected
    kept = {p.name for p in messy.quarantine.iterdir()}
    assert messy.adopted in kept and messy.pending in kept  # adopted evidence and a pending review are never garbage
    assert (messy.review / messy.pending).exists()


def test_a_dry_run_changes_nothing(messy):
    before = (snapshot(messy.catalog), snapshot(messy.quarantine), snapshot(messy.review))
    gc_mod.gc()
    gc_mod.gc(delete=False)
    assert (snapshot(messy.catalog), snapshot(messy.quarantine), snapshot(messy.review)) == before


def test_delete_removes_only_what_was_listed_and_never_tracked_history(messy):
    listed = gc_mod.gc()
    tracked_before = {k: v for k, v in snapshot(messy.catalog).items() if not k.startswith("generated/hero--x1/" + "e" * 64)}
    removed = gc_mod.gc(delete=True)
    assert names(removed) == names(listed)
    for item in listed:
        assert not item.path.exists()
    assert snapshot(messy.catalog) == tracked_before  # sources/, provenance/, manifests/ and every referenced artifact are untouched
    assert {p.name for p in messy.quarantine.iterdir()} == {messy.adopted, messy.pending}
    assert {p.name for p in messy.review.iterdir()} == {messy.pending}
    assert gc_mod.gc() == []  # and a second run finds nothing


def test_deleting_a_locally_revoked_intake_also_deletes_its_local_revocation(messy):
    revocation = messy.quarantine / messy.revoked / "revocation.json"
    assert revocation.exists()
    gc_mod.gc(delete=True)
    assert not revocation.exists() and not (messy.quarantine / messy.revoked).exists()  # stated in the docs


def test_delete_never_follows_a_symlink(messy):
    outside = messy.tmp / "precious"
    outside.mkdir()
    (outside / "keep.txt").write_text("keep")
    link = messy.quarantine / ".tmp-in-ffffffffffffffff-00000000"
    link.symlink_to(outside, target_is_directory=True)
    gc_mod.gc(delete=True)
    assert (outside / "keep.txt").read_text() == "keep"
    assert link.is_symlink()  # a symlink is not removed through, and not followed


def test_an_unreadable_intake_is_not_ours_to_judge(env):
    result = s.make_intake(env.tmp, passed=False)
    (env.quarantine / result.intake_id / "intake_result.json").write_text("garbage")
    assert gc_mod.gc(delete=True) == [] and (env.quarantine / result.intake_id).exists()


def test_a_png_that_a_record_refers_to_is_kept(env):
    s.adopted_tree(env, widths=(16,))
    assert [i for i in gc_mod.gc(delete=True) if i.kind == "generated"] == []  # (the adopted intake's review export is collected, the PNG is not)
    assert len(list((env.catalog / "generated" / "hero--x1").glob("*.png"))) == 1


def test_an_empty_world_has_nothing_to_collect(env):
    assert gc_mod.gc() == [] and gc_mod.gc(delete=True) == []


def test_an_artifact_record_without_a_png_is_not_garbage(env):
    s.adopted_tree(env, widths=(16,))
    next((env.catalog / "generated" / "hero--x1").glob("*.png")).unlink()
    assert [i for i in gc_mod.gc(delete=True) if i.kind == "generated"] == []  # corruption is `verify`'s to report, not gc's to hide
    assert any(p.name.endswith(".artifact.json") for p in (env.catalog / "generated" / "hero--x1").iterdir())
    assert json  # noqa: B018
