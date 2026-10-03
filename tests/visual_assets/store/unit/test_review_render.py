"""The store's own render of the source vs the producer's preview: `review` records it, `adopt` re-does it and never trusts a stored file."""

from __future__ import annotations

import json

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store import builders as b
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config, rendering
from visual_assets.store import review as review_mod
from visual_assets.store.contracts import ReviewRenderCheck, canonical_json, parse_record
from visual_assets.store.contracts.review import RenderVerdict
from visual_assets.store.errors import GateError, IntakeError, RenderError
from visual_assets.store.intake import intake
from visual_assets.store.intake.validator import file_hash

LATER = "2026-05-05T05:05:05Z"


@pytest.fixture(autouse=True)
def _reset():
    s.CALLS.clear()


def fresh(env, width=16):
    return s.make_intake(env.tmp, width, reviewed=False)


def stored_check(env, result):
    return env.quarantine / result.intake_id / "review_render.json"


def test_a_matching_render_is_recorded_and_the_human_is_shown_the_store_image(env):
    result = fresh(env)
    outcome = review_mod.review(result.intake_id, created_at=LATER, renderer=s.FakeRenderer())
    assert outcome.verdict is RenderVerdict.MATCH and outcome.note == review_mod.MATCH_NOTE
    check = parse_record(ReviewRenderCheck, stored_check(env, result).read_bytes())
    staged = env.quarantine / result.intake_id
    assert check.verdict is RenderVerdict.MATCH and check.scale == 8 and check.created_at == LATER
    assert check.source_hash == file_hash((staged / "source.aseprite").read_bytes())
    assert check.producer_preview_hash == file_hash((staged / "preview.png").read_bytes())
    assert (check.tool_name, check.tool_version) == ("Aseprite", "1.3.test")
    assert sorted(p.name for p in outcome.directory.iterdir()) == ["preview.png", "store_render.png", "summary.txt"]
    summary = (outcome.directory / "summary.txt").read_text()
    assert summary.startswith("Store render: MATCH") and "NOT adopted" in summary
    assert file_hash((outcome.directory / "store_render.png").read_bytes()) == check.rendered_png_hash


def test_a_mismatch_is_shown_prominently_and_recorded(env):
    result = fresh(env)
    outcome = review_mod.review(result.intake_id, created_at=LATER, renderer=s.MismatchRenderer())
    assert outcome.verdict is RenderVerdict.MISMATCH
    summary = (outcome.directory / "summary.txt").read_text()
    assert summary.startswith("!!! THE PREVIEW DOES NOT MATCH THE SOURCE !!!") and "store_render.png" in summary.splitlines()[0]
    assert parse_record(ReviewRenderCheck, stored_check(env, result).read_bytes()).verdict is RenderVerdict.MISMATCH


def test_without_a_renderer_it_says_plainly_that_nothing_was_verified_and_records_no_check(env):
    result = fresh(env)
    outcome = review_mod.review(result.intake_id, created_at=LATER, renderer=None)
    assert outcome.verdict is None and "UNVERIFIED" in outcome.note and "will refuse until the review is done" in outcome.note
    assert not stored_check(env, result).exists()
    assert sorted(p.name for p in outcome.directory.iterdir()) == ["preview.png", "summary.txt"]
    assert (outcome.directory / "summary.txt").read_text().startswith("The preview is producer-supplied and UNVERIFIED")


def test_the_comparison_is_by_decoded_pixels_not_by_how_the_png_was_encoded(env):
    class Reencoder(s.FakeRenderer):
        def render(self, source, *, scale):
            facts = rendering.aseprite.read_facts(source)[0]
            width, height = facts.width * scale, facts.height * scale
            return b.png_encode(width, height, [(0x20, 0x40, 0x60, 255)] * (width * height), filters=[1, 2, 3, 4], level=0)

    result = fresh(env)
    assert (env.quarantine / result.intake_id / "preview.png").read_bytes() != Reencoder().render(
        (env.quarantine / result.intake_id / "source.aseprite").read_bytes(), scale=8)
    assert review_mod.review(result.intake_id, created_at=LATER, renderer=Reencoder()).verdict is RenderVerdict.MATCH


def test_reviewing_again_is_idempotent_and_a_later_clock_does_not_rewrite_the_record(env):
    result = fresh(env)
    review_mod.review(result.intake_id, created_at=LATER, renderer=s.FakeRenderer())
    before = snapshot(env.quarantine)
    again = review_mod.review(result.intake_id, created_at="2026-06-06T06:06:06Z", renderer=s.FakeRenderer())
    assert again.verdict is RenderVerdict.MATCH and snapshot(env.quarantine) == before


def test_a_render_that_changes_between_reviews_is_refused(env):
    result = fresh(env)
    review_mod.review(result.intake_id, created_at=LATER, renderer=s.FakeRenderer())
    with pytest.raises(IntakeError) as err:
        review_mod.review(result.intake_id, created_at=LATER, renderer=s.MismatchRenderer())
    assert err.value.code == "render_check_differs"


def test_a_corrupt_stored_check_is_reported(env):
    result = fresh(env)
    review_mod.review(result.intake_id, created_at=LATER, renderer=s.FakeRenderer())
    stored_check(env, result).write_text("{}")
    with pytest.raises(IntakeError) as err:
        review_mod.review(result.intake_id, created_at=LATER, renderer=s.FakeRenderer())
    assert err.value.code == "render_check_corrupt"


def test_renderer_problems_become_coded_errors(env):
    result = fresh(env)

    class Boom(s.FakeRenderer):
        def render(self, source, *, scale):
            raise ValueError("segfault, with /home/someone/secret in the message")

    with pytest.raises(RenderError) as err:
        review_mod.review(result.intake_id, created_at=LATER, renderer=Boom())
    assert err.value.code == "render_failed" and "secret" not in err.value.message

    class NotAPng(s.FakeRenderer):
        def render(self, source, *, scale):
            return b"not a png"

    with pytest.raises(RenderError) as err:
        review_mod.review(result.intake_id, created_at=LATER, renderer=NotAPng())
    assert err.value.code == "render_undecodable"
    assert not stored_check(env, result).exists()


def test_a_preview_scale_above_the_supported_maximum_is_refused_not_guessed(env):
    package, source, _ = b.good_files()
    big = b.png(16 * 20, 16 * 20)
    directory = b.write_dir(env.tmp / "big", b.package_bytes(source, big), source, big)
    result = intake(directory, created_at="2026-01-01T00:00:00Z")
    with pytest.raises(RenderError) as err:
        review_mod.review(result.intake_id, created_at=LATER, renderer=s.FakeRenderer())
    assert err.value.code == "scale_unsupported"


def test_review_refuses_a_quarantined_or_revoked_intake_before_rendering(env):
    bad = s.make_intake(env.tmp, 18, passed=False)
    with pytest.raises(IntakeError) as err:
        review_mod.review(bad.intake_id, created_at=LATER, renderer=s.FakeRenderer())
    assert err.value.code == "not_passed"


# --------------------------------------------------------------------------- adopt: re-render, never trust the stored file


def adopt_error(result, **kw) -> str:
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id, **kw)
    return err.value.code


def test_adopt_needs_a_renderer(env):
    result = s.make_intake(env.tmp)
    before = snapshot(env.catalog)
    assert adopt_error(result, renderer=None) == "renderer_unavailable"
    assert snapshot(env.catalog) == before and s.CALLS == []


def test_adopt_refuses_an_intake_with_no_store_rendered_review(env):
    result = s.make_intake(env.tmp, reviewed=False)
    assert adopt_error(result) == "review_render_missing" and snapshot(env.catalog) == {} and s.CALLS == []


def test_adopt_refuses_when_the_review_time_check_was_a_mismatch(env):
    result = s.make_intake(env.tmp, renderer=s.MismatchRenderer())
    assert adopt_error(result) == "preview_mismatch" and snapshot(env.catalog) == {} and s.CALLS == []


def test_a_forged_matching_check_does_not_open_the_gate(env):
    """The quarantine is writable by any local process: adopt re-renders itself and compares again."""
    result = s.make_intake(env.tmp)  # a genuine MATCH check is stored
    assert adopt_error(result, renderer=s.MismatchRenderer()) == "preview_mismatch"  # but the store's render of these bytes does not match
    assert snapshot(env.catalog) == {} and s.CALLS == []


def test_a_forged_check_for_other_bytes_is_stale(env):
    result = s.make_intake(env.tmp)
    path = stored_check(env, result)
    check = parse_record(ReviewRenderCheck, path.read_bytes())
    for field, value in (("source_hash", "sha256:" + "1" * 64), ("producer_preview_hash", "sha256:" + "2" * 64), ("intake_id", "in-ffffffffffffffff")):
        data = json.loads(path.read_bytes())
        data[field] = value
        path.write_bytes(canonical_json(parse_record(ReviewRenderCheck, json.dumps(data).encode())))
        assert adopt_error(result) == "review_render_stale", field
    path.write_bytes(canonical_json(check))
    assert s.do_adopt(result.intake_id).intake_id == result.intake_id  # the genuine record works again


def test_a_check_whose_pixel_hashes_were_forged_is_stale(env):
    result = s.make_intake(env.tmp)
    path = stored_check(env, result)
    data = json.loads(path.read_bytes())
    fake = "pixels-v1:" + "3" * 64
    data["producer_pixel_hash"] = data["rendered_pixel_hash"] = fake  # still internally consistent: a MATCH of made-up pixels
    path.write_bytes(canonical_json(parse_record(ReviewRenderCheck, json.dumps(data).encode())))
    assert adopt_error(result) == "review_render_stale" and snapshot(env.catalog) == {}


def test_a_corrupt_or_unsafe_stored_check_is_refused(env):
    result = s.make_intake(env.tmp)
    path = stored_check(env, result)
    original = path.read_bytes()
    path.write_text("not json")
    assert adopt_error(result) == "review_render_corrupt"
    path.unlink()
    elsewhere = env.tmp / "elsewhere.json"
    elsewhere.write_bytes(original)
    path.symlink_to(elsewhere)
    assert adopt_error(result) == "review_render_corrupt"  # a symlinked check is not read


def test_a_renderer_failure_at_adoption_is_a_coded_refusal(env):
    result = s.make_intake(env.tmp)

    class Boom(s.FakeRenderer):
        def render(self, source, *, scale):
            raise RuntimeError("boom")

    assert adopt_error(result, renderer=Boom()) == "render_failed" and snapshot(env.catalog) == {}


def test_the_confirmation_says_the_store_rerendered_the_source(env):
    result = s.make_intake(env.tmp)
    s.do_adopt(result.intake_id)
    assert any("re-rendered the source just now" in n for n in s.CALLS[0][1])


def test_the_stored_check_is_published_and_bound_by_hash(env):
    result = s.make_intake(env.tmp)
    adoption = s.do_adopt(result.intake_id)
    copy = env.catalog / "provenance" / "intake" / f"{result.intake_id}.review.json"
    assert copy.read_bytes() == stored_check(env, result).read_bytes() and adoption.review_hash == file_hash(copy.read_bytes())
    assert config.CATALOG_ROOT == env.catalog


# --------------------------------------------------------------------------- one asset per visual key


def test_a_second_asset_cannot_take_a_key_a_live_asset_holds(env):
    a, c = s.make_intake(env.tmp, 16), s.make_intake(env.tmp, 17)
    s.do_adopt(a.intake_id)
    before = snapshot(env.catalog)
    s.CALLS.clear()
    for kwargs in (dict(source_asset_id="rock"), dict(source_asset_id="rock", new=True)):
        with pytest.raises(GateError) as err:
            s.do_adopt(c.intake_id, visual_key=s.KEY, **kwargs)
        assert err.value.code == "visual_key_taken" and "hero" in err.value.message
    assert snapshot(env.catalog) == before and s.CALLS == []


def test_the_key_is_free_again_once_every_revision_of_its_holder_is_revoked(env):
    from visual_assets.store.revoke import revoke

    a, c = s.make_intake(env.tmp, 16), s.make_intake(env.tmp, 17)
    s.do_adopt(a.intake_id)
    revoke("hero/r0001", reason="replaced", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    assert s.do_adopt(c.intake_id, source_asset_id="rock", visual_key=s.KEY).visual_key == s.KEY  # the deliberate path


def test_an_asset_keeps_its_own_key_across_revisions_but_cannot_move_onto_anothers(env):
    a, b_, c, d = (s.make_intake(env.tmp, w) for w in (16, 17, 18, 19))
    s.do_adopt(a.intake_id)
    s.do_adopt(b_.intake_id, source_asset_id="rock")
    assert s.do_adopt(c.intake_id, new=False, parent="r0001").source_revision == "r0002"  # hero stays on its own key
    with pytest.raises(GateError) as err:  # a new hero revision tries to take rock's key
        s.do_adopt(d.intake_id, new=False, parent="r0002", visual_key=s.key_for("rock"))
    assert err.value.code == "visual_key_taken" and "rock" in err.value.message


def test_a_preview_that_is_not_a_whole_number_scale_of_the_source_is_refused_by_the_comparison_itself(env):
    """Intake already refuses such a preview, but the comparison must not depend on that: it checks the scale on its own."""
    _, source, _ = b.good_files()  # a 16-wide source
    for width in (17, 47, 130):  # not multiples of 16
        with pytest.raises(RenderError) as err:
            rendering.preview_scale(b.png(width, width), source)
        assert err.value.code == "scale_unsupported", width
    assert rendering.preview_scale(b.png(16 * 3, 16 * 3), source) == 3
    with pytest.raises(RenderError) as err:
        rendering.preview_scale(b"not a png", source)
    assert err.value.code == "preview_undecodable"
    with pytest.raises(RenderError):
        rendering.preview_scale(b.png(16, 16), b"not an aseprite file")


# --------------------------------------------------------------------------- B1: the image the human actually opened


def review_image(env, result):
    return env.review / result.intake_id / "store_render.png"


def test_adopt_checks_the_image_file_the_human_opened(env):
    result = s.make_intake(env.tmp)
    image = review_image(env, result)
    original = image.read_bytes()
    assert adopt_ok_after(result, image, original) is True  # a re-encoded file with the SAME pixels is fine


def adopt_ok_after(result, image, original) -> bool:
    from visual_assets.store import pixels

    image.write_bytes(b.png_encode(128, 128, [tuple(p) for p in _pixels(original)], filters=[4], level=0))
    assert image.read_bytes() != original and pixels.pixel_hash(image.read_bytes(), max_dim=1024) == pixels.pixel_hash(original, max_dim=1024)
    return s.do_adopt(result.intake_id).intake_id == result.intake_id


def _pixels(png: bytes):
    from visual_assets.store import pixels

    rgba = pixels.decode_png(png, max_dim=1024).rgba
    return [rgba[i : i + 4] for i in range(0, len(rgba), 4)]


@pytest.mark.parametrize("how,code", [
    ("rewritten", "review_image_changed"), ("garbage", "review_image_changed"), ("truncated", "review_image_changed"),
    ("symlink", "review_image_changed"), ("deleted", "review_render_missing"), ("directory_missing", "review_render_missing"),
])
def test_a_review_image_that_was_changed_or_removed_after_the_review_is_refused(env, how, code):
    result = s.make_intake(env.tmp)
    image = review_image(env, result)
    original = image.read_bytes()
    if how == "rewritten":
        image.write_bytes(b.png_encode(128, 128, [(1, 2, 3, 255)] * (128 * 128)))  # a valid PNG of a different picture
    elif how == "garbage":
        image.write_bytes(b"not a png")
    elif how == "truncated":
        image.write_bytes(original[:-30])
    elif how == "symlink":
        elsewhere = env.tmp / "elsewhere.png"
        elsewhere.write_bytes(original)
        image.unlink()
        image.symlink_to(elsewhere)
    elif how == "deleted":
        image.unlink()
    else:
        import shutil

        shutil.rmtree(env.review / result.intake_id)
    before = snapshot(env.catalog)
    s.CALLS.clear()
    with pytest.raises(GateError) as err:
        s.do_adopt(result.intake_id)
    assert err.value.code == code and snapshot(env.catalog) == before and s.CALLS == []


def test_a_genuine_review_again_repairs_it(env):
    result = s.make_intake(env.tmp)
    review_image(env, result).write_bytes(b"not a png")
    with pytest.raises(GateError):
        s.do_adopt(result.intake_id)
    import shutil

    shutil.rmtree(env.review / result.intake_id)
    review_mod.review(result.intake_id, created_at="2026-07-07T07:07:07Z", renderer=s.FakeRenderer())
    assert s.do_adopt(result.intake_id).intake_id == result.intake_id


def test_a_large_render_is_not_blocked_by_the_producer_preview_size_limit(env, monkeypatch):
    """The store's own render can be larger than the producer preview limit; re-reviewing must still be idempotent."""

    class Uncompressed(s.FakeRenderer):  # the same pixels as the producer preview, but stored uncompressed: ~65 KB
        def render(self, source, *, scale):
            facts = rendering.aseprite.read_facts(source)[0]
            width, height = facts.width * scale, facts.height * scale
            return b.png_encode(width, height, [(0x20, 0x40, 0x60, 255)] * (width * height), level=0)

    result = s.make_intake(env.tmp, reviewed=False)
    assert review_mod.review(result.intake_id, created_at=LATER, renderer=Uncompressed()).verdict is RenderVerdict.MATCH
    assert review_image(env, result).stat().st_size > 50_000
    monkeypatch.setattr(config, "MAX_PREVIEW_BYTES", 1000)  # above the staged preview, far below the store render
    assert review_mod.review(result.intake_id, created_at=LATER, renderer=Uncompressed()).verdict is RenderVerdict.MATCH
    assert s.do_adopt(result.intake_id, renderer=Uncompressed()).intake_id == result.intake_id


def test_the_preview_bound_is_what_export_handoff_can_produce():
    assert config.MAX_PREVIEW_DIM == 128 * 8  # scale 8 of the largest sprite: the only scale export_handoff makes
