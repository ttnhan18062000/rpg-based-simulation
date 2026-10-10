"""Animation metadata read from an Aseprite source (`TCK-20261010-VISUAL-ASSETS-ANIMATION-METADATA-FIELDS`; planner design approved 2026-10-10).

Frame durations and tags are DERIVED from the source bytes (intake reads the frame header words and the tags chunk), carried per source revision on the `SourceRecord` (no registry field, no
manifest change) and exported only by the opt-in `export-runtime --animation`. This is a new parser path over untrusted bytes, so the security cases are planted here: a truncated, oversized or
lying tags chunk and a hostile name are QUARANTINE findings, never an exception, and the walk never runs past the bounds. No Aseprite is needed here; the real-file oracle is in
`tests/visual_assets/store/integration/test_real_aseprite.py`.
"""

from __future__ import annotations

import json
import random
import struct
import time

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store import builders as b
from visual_assets.drawing import config as drawing_config
from visual_assets.store import animation, cli, config, records, verify
from visual_assets.store.build import exporter
from visual_assets.store.contracts import SourceRecord, canonical_json, parse_record
from visual_assets.store.contracts.animation import AnimationTag, RuntimeAnimation, SourceAnimation
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.contracts.intake import IntakeFindingCode as Code
from visual_assets.store.errors import ContractError
from visual_assets.store.intake import aseprite, validator
from visual_assets.store.intake.service import intake
from visual_assets.store.release import assemble_release
from visual_assets.store.runtime_export import export_runtime

DURATIONS = [50, 100, 150, 200]
TAGS = [("idle", 0, 1, 0, 0), ("walk", 1, 3, 2, 3)]  # name, from, to, direction (0 forward .. 3 ping-pong reverse), repeat (0 = forever)
ANIMATED = dict(frames=4, durations=DURATIONS, tag_specs=TAGS)
REAL = config.CATALOG_ROOT


def codes(source: bytes) -> set[Code]:
    _, problems = aseprite.read_facts(source)
    return {code for code, _ in problems}


# ---- the parser reads what the file holds ----

def test_the_parser_reads_frame_durations_and_tags_exactly_as_written():
    facts, problems = aseprite.read_facts(b.aseprite(**ANIMATED))
    assert problems == []
    assert facts.frames == 4 and facts.tags == 2
    assert facts.frame_durations_ms == tuple(DURATIONS)
    assert [(t.name, t.from_frame, t.to_frame, t.direction, t.repeat) for t in facts.animation_tags] == TAGS


def test_a_one_frame_source_is_not_animation_and_its_record_has_no_animation_field():
    assert animation.animation_from_source(b.aseprite()) is None
    assert animation.animation_from_source(b.aseprite(tag_specs=[("only", 0, 0, 0, 0)])) is None  # a tag on one frame is valid but carries no animation


def test_the_derived_record_maps_directions_in_aseprites_order():
    source = b.aseprite(frames=4, durations=DURATIONS, tag_specs=[("a", 0, 0, 0, 0), ("b", 1, 1, 1, 0), ("c", 2, 2, 2, 5), ("d", 3, 3, 3, 65535)])
    derived = animation.animation_from_source(source)
    assert [t.direction for t in derived.tags] == ["forward", "reverse", "ping_pong", "ping_pong_reverse"]
    assert [t.repeat for t in derived.tags] == [0, 0, 5, 65535]


# ---- each planted bad case is quarantined with its own code ----

@pytest.mark.parametrize("name, source, expected", [
    ("a zero duration", b.aseprite(frames=3, durations=[100, 0, 100]), Code.ANIMATION_FRAME_DURATION_INVALID),
    ("a tag past the last frame", b.aseprite(frames=2, tag_specs=[("late", 0, 2, 0, 0)]), Code.ANIMATION_TAG_RANGE_INVALID),
    ("a tag whose from is after its to", b.aseprite(frames=3, tag_specs=[("back", 2, 1, 0, 0)]), Code.ANIMATION_TAG_RANGE_INVALID),
    ("a tag outside a one-frame source", b.aseprite(frames=1, tag_specs=[("far", 0, 1, 0, 0)]), Code.ANIMATION_TAG_RANGE_INVALID),
    ("more frames than the bound", b.aseprite(frames=config.MAX_ANIMATION_FRAMES + 1), Code.ANIMATION_OUT_OF_BOUNDS),
    ("more tags than the bound", b.aseprite(frames=2, tag_specs=[(f"t{i}", 0, 1, 0, 0) for i in range(config.MAX_ANIMATION_TAGS + 1)]), Code.ANIMATION_OUT_OF_BOUNDS),
    ("two tags with one name", b.aseprite(frames=2, tag_specs=[("same", 0, 0, 0, 0), ("same", 1, 1, 0, 0)]), Code.ANIMATION_TAG_INVALID),
    ("an empty tag name", b.aseprite(frames=2, tag_specs=[("", 0, 1, 0, 0)]), Code.ANIMATION_TAG_INVALID),
    ("a tag name over 32 characters", b.aseprite(frames=2, tag_specs=[("x" * 33, 0, 1, 0, 0)]), Code.ANIMATION_TAG_INVALID),
    ("an unknown direction", b.aseprite(frames=2, tag_specs=[("odd", 0, 1, 4, 0)]), Code.ANIMATION_TAG_INVALID),
    ("a control character in a name", b.aseprite(frames=2, tag_specs=[("a\x07b", 0, 1, 0, 0)]), Code.ANIMATION_TAG_INVALID),
])
def test_each_planted_bad_case_is_reported_with_its_code(name, source, expected):
    assert expected in codes(source), name


def test_a_tag_name_that_is_not_utf8_is_reported_not_raised():
    good = b.aseprite(frames=2, tag_specs=[("abc", 0, 1, 0, 0)])
    bad = good.replace(b"abc", b"\xff\xfe\xfd")
    assert bad != good and bad.count(b"\xff\xfe\xfd") == 1
    assert Code.ANIMATION_TAG_INVALID in codes(bad)


def test_a_bad_animation_quarantines_the_candidate_at_intake(env):
    for number, source in enumerate([b.aseprite(frames=3, durations=[100, 0, 100]), b.aseprite(frames=2, tag_specs=[("late", 0, 9, 0, 0)])]):
        preview = b.png(16 * 8, 16 * 8)
        directory = b.write_dir(env.tmp / f"bad-{number}", b.package_bytes(source, preview, candidate_id=f"cand-0000000000000a{number:02x}"), source, preview)
        result = intake(directory, created_at="2026-01-01T00:00:00Z")
        assert result.verdict is IntakeVerdict.QUARANTINED
        assert any(f.code.value.startswith("ANIMATION_") for f in result.findings)


def test_every_accepted_source_builds_a_valid_contract_record_and_the_parser_and_contract_agree():
    for source in (b.aseprite(**ANIMATED), b.aseprite(frames=2), b.aseprite(frames=16, durations=[1] * 16, tag_specs=[(f"t{i}", i, i, i % 4, i) for i in range(16)])):
        assert not any(c.value.startswith("ANIMATION_") for c in codes(source))
        derived = animation.animation_from_source(source)
        assert isinstance(derived, SourceAnimation) and len(derived.tags) == aseprite.read_facts(source)[0].tags


def test_a_source_that_failed_intake_is_never_turned_into_a_record():
    with pytest.raises(animation.AnimationError):
        animation.animation_from_source(b.aseprite(frames=3, durations=[100, 0, 100]))


# ---- hostile bytes: a finding, never an exception, never a long loop ----

def test_a_tags_chunk_cut_at_every_length_is_reported_never_raised():
    source = b.aseprite(**ANIMATED)
    start = source.index(struct.pack("<H", 2) + b"\x00" * 8)  # the tags chunk body (count 2, 8 reserved bytes)
    chunk_start = start - 6
    chunk_len = struct.unpack_from("<I", source, chunk_start)[0]
    assert source[chunk_start + 4 : chunk_start + 6] == struct.pack("<H", 0x2018)
    for keep in range(chunk_len):
        cut = bytearray(source)
        struct.pack_into("<I", cut, chunk_start, keep)  # the chunk now CLAIMS to be shorter than its tags need
        _, problems = aseprite.read_facts(bytes(cut))  # must not raise
        assert problems or keep >= chunk_len, f"chunk claimed {keep} bytes and nothing was reported"


def test_a_tags_chunk_that_declares_far_more_tags_than_it_holds_is_reported_without_walking_them():
    source = bytearray(b.aseprite(**ANIMATED))
    start = source.index(struct.pack("<H", 2) + b"\x00" * 8)
    for declared in (config.MAX_ANIMATION_TAGS + 1, 1000, 65535):
        struct.pack_into("<H", source, start, declared)
        began = time.perf_counter()
        _, problems = aseprite.read_facts(bytes(source))
        assert time.perf_counter() - began < 0.5
        assert {c for c, _ in problems} & {Code.ANIMATION_OUT_OF_BOUNDS, Code.SOURCE_TRUNCATED_CHUNK}, declared
    struct.pack_into("<H", source, start, 5)  # within the bound but more than the chunk can hold
    assert Code.SOURCE_TRUNCATED_CHUNK in {c for c, _ in aseprite.read_facts(bytes(source))[1]}


def test_a_tag_name_length_that_runs_past_the_chunk_is_reported():
    source = bytearray(b.aseprite(frames=2, tag_specs=[("abc", 0, 1, 0, 0)]))
    at = source.index(b"abc") - 2
    assert struct.unpack_from("<H", source, at)[0] == 3
    for length in (4, 100, 65535):
        struct.pack_into("<H", source, at, length)
        _, problems = aseprite.read_facts(bytes(source))
        assert Code.SOURCE_TRUNCATED_CHUNK in {c for c, _ in problems}, length


def test_no_single_byte_change_or_truncation_of_an_animated_source_raises():
    source = b.aseprite(**ANIMATED)
    rng = random.Random(20261010)
    for _ in range(1500):
        mutated = bytearray(source)
        for _ in range(rng.choice((1, 1, 2, 4))):
            mutated[rng.randrange(len(mutated))] = rng.randrange(256)
        aseprite.read_facts(bytes(mutated))
        aseprite.read_facts(bytes(mutated[: rng.randrange(len(mutated) + 1)]))


HOSTILE_NAME = "\U000e0080" * 32  # unassigned code points: plain-text valid, and `repr` expands each to a 10-character escape


@pytest.mark.parametrize("name, source", [
    ("a bad range on a hostile name", b.aseprite(frames=2, tag_specs=[(HOSTILE_NAME, 5, 9, 0, 0)])),
    ("an unknown direction on a hostile name", b.aseprite(frames=2, tag_specs=[(HOSTILE_NAME, 0, 1, 7, 0)])),
    ("sixteen hostile tags of 17 to 32 characters", b.aseprite(frames=2, tag_specs=[(HOSTILE_NAME[: 17 + i], 5, 9, 9, 0) for i in range(16)])),
])
def test_a_hostile_tag_name_quarantines_the_candidate_and_never_raises(name, source):
    """Security review of the animation parser: a name of unassigned code points made a quoted finding longer than the 256-character limit, so `validate` raised instead of quarantining."""
    result = validator.validate(b"{}", source, b"")
    assert any(f.code.value.startswith("ANIMATION_") for f in result.findings), name
    assert all(len(f.detail) <= 256 for f in result.findings)
    assert all(HOSTILE_NAME[:3] not in f.detail for f in result.findings), "findings name a tag by its position, never its text"


def test_a_finding_longer_than_its_bound_is_clamped_not_raised():
    clamped = validator._finding(Code.SOURCE_MALFORMED, "x" * 1000)
    assert len(clamped.detail) == 256 and clamped.detail.endswith("...")
    assert validator._finding(Code.SOURCE_MALFORMED, "short").detail == "short"


def test_the_animation_bounds_are_the_drawing_tools_own_and_a_worst_case_record_fits():
    assert config.MAX_ANIMATION_FRAMES == drawing_config.MAX_FRAMES == 16 and config.MAX_ANIMATION_TAGS == 16
    worst = SourceAnimation(
        frame_durations_ms=(65535,) * 16,
        tags=tuple(AnimationTag(name=("n" * 31) + chr(97 + i), from_frame=0, to_frame=15, direction="ping_pong_reverse", repeat=65535) for i in range(16)),
    )
    assert len(worst.model_dump_json()) < config.MAX_RECORD_BYTES // 8


# ---- the contract ----

@pytest.mark.parametrize("name, build", [
    ("one frame", lambda: SourceAnimation(frame_durations_ms=(100,))),
    ("a zero duration", lambda: SourceAnimation(frame_durations_ms=(0, 100))),
    ("a duration over a word", lambda: SourceAnimation(frame_durations_ms=(65536, 100))),
    ("too many frames", lambda: SourceAnimation(frame_durations_ms=(100,) * 17)),
    ("a tag outside the frames", lambda: SourceAnimation(frame_durations_ms=(100, 100), tags=(AnimationTag(name="a", from_frame=0, to_frame=2, direction="forward", repeat=0),))),
    ("a reversed range", lambda: SourceAnimation(frame_durations_ms=(100, 100), tags=(AnimationTag(name="a", from_frame=1, to_frame=0, direction="forward", repeat=0),))),
    ("duplicate names", lambda: SourceAnimation(frame_durations_ms=(100, 100), tags=(AnimationTag(name="a", from_frame=0, to_frame=0, direction="forward", repeat=0),) * 2)),
    ("an unknown direction", lambda: AnimationTag(name="a", from_frame=0, to_frame=0, direction="sideways", repeat=0)),
    ("an extra field", lambda: SourceAnimation(frame_durations_ms=(100, 100), loop_mode="forever")),
])
def test_the_contract_refuses_each_planted_violation(name, build):
    with pytest.raises(ValueError):
        build()


# ---- every committed record is byte-identical ----

def test_every_committed_source_record_round_trips_byte_for_byte_and_carries_no_animation():
    files = sorted((REAL / "sources").glob("*/r*.source.json"))
    assert len(files) >= 77
    for path in files:
        data = path.read_bytes()
        record = parse_record(SourceRecord, data)
        assert record.animation is None and canonical_json(record) == data, path
        assert b"animation" not in data, path


def test_every_committed_source_reads_with_no_new_finding_and_derives_no_animation():
    for path in sorted((REAL / "sources").glob("*/r*.aseprite")):
        source = path.read_bytes()
        assert not any(c.value.startswith("ANIMATION_") for c in codes(source)), path
        assert animation.animation_from_source(source) is None, path


def test_a_record_with_an_animation_serializes_it_and_parses_back_equal():
    base = parse_record(SourceRecord, next(iter(sorted((REAL / "sources").glob("*/r0001.source.json")))).read_bytes())
    animated = base.model_copy(update={"animation": animation.animation_from_source(b.aseprite(**ANIMATED))})
    again = parse_record(SourceRecord, canonical_json(animated))
    assert again == animated and again.animation.frame_durations_ms == tuple(DURATIONS)
    assert b'"animation"' in canonical_json(animated) and b'"animation"' not in canonical_json(base)


# ---- intake -> adoption -> artifact -> animation.json ----

KEY_ANIMATED, KEY_STATIC = "fixture.rehearsal.walk", "fixture.rehearsal.rock"


def build_catalog(env):
    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    lines = ["record_type: visual_key_registry", "schema_version: 1", "keys:"]
    lines += [f"  - {{key: {key}, family: terrain, description: synthetic animated test image, variant_axes: [], optional: false}}" for key in (KEY_ANIMATED, KEY_STATIC)]
    lines.append("aliases: []")
    path = env.catalog / "definitions" / "visual_keys.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    from visual_assets.store.catalog.registry import load_registry

    registry = load_registry(path, allow_fixture_namespace=True)
    walk = s.make_intake(env.tmp, 16, **ANIMATED)
    rock = s.make_intake(env.tmp, 17)
    s.do_adopt(walk.intake_id, source_asset_id="walk", visual_key=KEY_ANIMATED, registry=registry)
    s.do_adopt(rock.intake_id, source_asset_id="rock", visual_key=KEY_STATIC, registry=registry)
    exporter.build(renderer=s.HashRenderer())
    assemble_release("pilot", release_id="rc-0001", allow_fixture_namespace=True)
    return env


@pytest.fixture
def catalog(env):
    s.CALLS.clear()
    return build_catalog(env)


def test_adoption_derives_the_animation_from_the_bytes_and_leaves_a_static_source_without_one(catalog):
    walk = records.load_source("walk", "r0001")
    assert [t.name for t in walk.animation.tags] == ["idle", "walk"] and walk.animation.frame_durations_ms == tuple(DURATIONS)
    assert records.load_source("rock", "r0001").animation is None
    assert b'"animation"' not in records.source_paths("rock", "r0001")[1].read_bytes()
    assert [f for f in verify.verify(allow_fixture_namespace=True) if f.blocking] == []  # the catalog still verifies with an animated record in it


def test_the_opt_in_export_writes_animation_json_equal_to_the_values_in_the_file_and_nothing_else_changes(catalog):
    plain, with_animation = catalog.tmp / "out-plain", catalog.tmp / "out-animation"
    export_runtime("pilot", "rc-0001", plain, allow_fixture_namespace=True)
    export_runtime("pilot", "rc-0001", with_animation, allow_fixture_namespace=True, animation=True)
    assert not (plain / "animation.json").exists(), "no flag, no file"
    assert sorted(p.name for p in with_animation.iterdir()) == sorted([*(p.name for p in plain.iterdir()), "animation.json"])
    for path in plain.iterdir():
        assert (with_animation / path.name).read_bytes() == path.read_bytes(), path.name  # the manifest and every PNG are byte-identical either way
    exported = parse_record(RuntimeAnimation, (with_animation / "animation.json").read_bytes())
    assert [e.visual_key for e in exported.entries] == [KEY_ANIMATED]  # the one-frame source is omitted
    entry = exported.entries[0]
    assert entry.frame_durations_ms == tuple(DURATIONS)
    assert [(t.name, t.from_frame, t.to_frame, t.direction, t.repeat) for t in entry.tags] == [("idle", 0, 1, "forward", 0), ("walk", 1, 3, "ping_pong", 3)]
    assert b"animation" not in (with_animation / "runtime_manifest.json").read_bytes()


def test_the_cli_flag_reaches_the_export_and_is_off_by_default(monkeypatch, tmp_path):
    from types import SimpleNamespace

    seen = []

    def stub(catalog_id, release_id, out, **kwargs):
        seen.append(kwargs)
        return SimpleNamespace(catalog_id=catalog_id, release_id=release_id, entries=())

    monkeypatch.setattr(cli.runtime_export, "export_runtime", stub)
    base = ["export-runtime", "--catalog-id", "pilot", "--release-id", "rc-0001", "--out", str(tmp_path / "o")]
    assert cli.main(base) == 0 and cli.main([*base, "--animation"]) == 0 and cli.main([*base, "--animation", "--atlas"]) == 0
    assert [(k["animation"], k["atlases"]) for k in seen] == [(False, False), (True, False), (True, True)]


def test_mutant_an_exported_duration_that_differs_from_the_file_is_caught(catalog):
    out = catalog.tmp / "out-mutant"
    export_runtime("pilot", "rc-0001", out, allow_fixture_namespace=True, animation=True)
    exported = json.loads((out / "animation.json").read_text())
    truth = list(aseprite.read_facts((records.source_paths("walk", "r0001")[0]).read_bytes())[0].frame_durations_ms)
    assert exported["entries"][0]["frame_durations_ms"] == truth
    exported["entries"][0]["frame_durations_ms"][2] += 1
    assert exported["entries"][0]["frame_durations_ms"] != truth, "the mutant must change exactly one value"


def test_the_contract_error_type_is_what_a_bad_record_raises():
    with pytest.raises(ContractError):
        parse_record(SourceRecord, b'{"record_type":"source_record","animation":{"frame_durations_ms":[1]}}')
