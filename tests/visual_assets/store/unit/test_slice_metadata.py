"""Slice metadata read from an Aseprite source (`TCK-20261010-VISUAL-ASSETS-SLICE-SOURCE-FIELDS`; ADR D25).

Slices are DERIVED from the source bytes (the slice chunk 0x2022), carried per source revision on the `SourceRecord` and nowhere else. This is a new parser path over untrusted bytes, so the
security cases are planted here: a truncated, oversized or lying slice chunk and a hostile name are QUARANTINE findings, never an exception, and the walk never runs past the bounds. No Aseprite
is needed here; the real-file oracle is in `tests/visual_assets/store/integration/test_real_aseprite.py`.
"""

from __future__ import annotations

import struct
import time

import pytest
from pydantic import ValidationError

from tests.visual_assets.store import builders as b
from visual_assets.store import config, slices
from visual_assets.store.contracts import SourceRecord, canonical_json, parse_record
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.contracts.intake import IntakeFindingCode as Code
from visual_assets.store.contracts.animation import SourceAnimation
from visual_assets.store.contracts.slices import SliceKey, SlicePivot, SliceRect, SourceSlice
from visual_assets.store.intake import aseprite
from visual_assets.store.intake.service import intake

REAL = config.CATALOG_ROOT


def record_args(**over) -> dict:
    """The fields of a real committed source record (no slices, no animation), with `over` applied."""
    data = parse_record(SourceRecord, next(iter(sorted((REAL / "sources").glob("*/r0001.source.json")))).read_bytes()).model_dump()
    data.pop("animation", None)
    data.pop("slices", None)
    return {**data, **over}


PLAIN = b.slice_chunk("body", [(0, 2, 3, 8, 6)])
NINE = b.slice_chunk("panel", [(0, 0, 0, 16, 16, 4, 4, 8, 8)], nine=True)
FULL = b.slice_chunk("hand", [(0, 1, 1, 8, 8, 2, 2, 4, 4, 3, 7), (2, 2, 2, 8, 8, 2, 2, 4, 4, 8, 8)], nine=True, pivot=True)


def codes(source: bytes) -> set[Code]:
    _, problems = aseprite.read_facts(source)
    return {code for code, _ in problems}


def some(source: bytes, prefix: str = "SLICE_") -> bool:
    return any(c.value.startswith(prefix) for c in codes(source))


# ---- the parser reads what the file holds ----

def test_the_parser_reads_plain_nine_slice_and_pivot_slices_exactly_as_written():
    facts, problems = aseprite.read_facts(b.aseprite(frames=3, slice_chunks=[PLAIN, NINE, FULL]))
    assert problems == []
    by_name = {s_.name: s_ for s_ in facts.slices}
    assert set(by_name) == {"body", "panel", "hand"}
    assert by_name["body"].keys == (aseprite.RawSliceKey(0, 2, 3, 8, 6, None, None),)
    assert by_name["panel"].keys[0].center == (4, 4, 8, 8) and by_name["panel"].keys[0].pivot is None
    assert [(k.frame, k.center, k.pivot) for k in by_name["hand"].keys] == [(0, (2, 2, 4, 4), (3, 7)), (2, (2, 2, 4, 4), (8, 8))]


def test_a_source_without_slices_has_no_slices_field_and_its_record_is_unchanged():
    assert slices.slices_from_source(b.aseprite()) is None
    record = canonical_json(SourceRecord(**record_args(slices=None)))
    assert b'"slices"' not in record


def test_the_derived_records_are_sorted_by_name_and_round_trip_through_the_source_record():
    derived = slices.slices_from_source(b.aseprite(frames=3, slice_chunks=[PLAIN, NINE, FULL]))
    assert [x.name for x in derived] == ["body", "hand", "panel"]
    record = SourceRecord(**record_args(width=16, height=16, slices=derived, animation=SourceAnimation(frame_durations_ms=(100, 100, 100))))
    assert parse_record(SourceRecord, canonical_json(record)) == record


def test_a_pivot_on_the_far_edge_and_a_centre_filling_the_slice_are_accepted():
    source = b.aseprite(slice_chunks=[b.slice_chunk("edge", [(0, 0, 0, 16, 16, 0, 0, 16, 16, 16, 16)], nine=True, pivot=True)])
    assert not some(source) and slices.slices_from_source(source)[0].keys[0].pivot == SlicePivot(x=16, y=16)


# ---- each planted bad case is quarantined with its own code ----

@pytest.mark.parametrize(("name", "source", "expected"), [
    ("more slices than the bound", b.aseprite(slice_chunks=[b.slice_chunk(f"s{i}", [(0, 0, 0, 1, 1)]) for i in range(config.MAX_SOURCE_SLICES + 1)]), Code.SLICE_OUT_OF_BOUNDS),
    ("more keys than the bound", b.aseprite(frames=2, slice_chunks=[b.slice_chunk("many", [(0, 0, 0, 1, 1)] * (config.MAX_SLICE_KEYS + 1))]), Code.SLICE_OUT_OF_BOUNDS),
    ("two slices with one name", b.aseprite(slice_chunks=[PLAIN, b.slice_chunk("body", [(0, 0, 0, 1, 1)])]), Code.SLICE_INVALID),
    ("a slice with no keys", b.aseprite(slice_chunks=[b.slice_chunk("none", [])]), Code.SLICE_INVALID),
    ("an empty name", b.aseprite(slice_chunks=[b.slice_chunk("", [(0, 0, 0, 1, 1)])]), Code.SLICE_INVALID),
    ("a name over 32 characters", b.aseprite(slice_chunks=[b.slice_chunk("x" * 33, [(0, 0, 0, 1, 1)])]), Code.SLICE_INVALID),
    ("a control character in a name", b.aseprite(slice_chunks=[b.slice_chunk("a\x07b", [(0, 0, 0, 1, 1)])]), Code.SLICE_INVALID),
    ("unknown flag bits", b.aseprite(slice_chunks=[b.slice_chunk("odd", [(0, 0, 0, 1, 1)], flags=4)]), Code.SLICE_INVALID),
    ("a key frame past the last frame", b.aseprite(frames=2, slice_chunks=[b.slice_chunk("late", [(2, 0, 0, 1, 1)])]), Code.SLICE_INVALID),
    ("keys not in increasing frame order", b.aseprite(frames=3, slice_chunks=[b.slice_chunk("back", [(2, 0, 0, 1, 1), (1, 0, 0, 1, 1)])]), Code.SLICE_INVALID),
    ("two keys on one frame", b.aseprite(frames=3, slice_chunks=[b.slice_chunk("twice", [(1, 0, 0, 1, 1), (1, 0, 0, 2, 2)])]), Code.SLICE_INVALID),
    ("a rectangle past the right edge", b.aseprite(slice_chunks=[b.slice_chunk("wide", [(0, 10, 0, 7, 1)])]), Code.SLICE_GEOMETRY_INVALID),
    ("a rectangle past the bottom edge", b.aseprite(slice_chunks=[b.slice_chunk("tall", [(0, 0, 10, 1, 7)])]), Code.SLICE_GEOMETRY_INVALID),
    ("a negative origin", b.aseprite(slice_chunks=[b.slice_chunk("neg", [(0, -2, 0, 1, 1)])]), Code.SLICE_GEOMETRY_INVALID),
    ("a rectangle without width", b.aseprite(slice_chunks=[b.slice_chunk("flat", [(0, 0, 0, 0, 4)])]), Code.SLICE_GEOMETRY_INVALID),
    ("a centre past its slice", b.aseprite(slice_chunks=[b.slice_chunk("c", [(0, 0, 0, 8, 8, 4, 4, 5, 1)], nine=True)]), Code.SLICE_GEOMETRY_INVALID),
    ("a centre without area", b.aseprite(slice_chunks=[b.slice_chunk("c", [(0, 0, 0, 8, 8, 4, 4, 0, 1)], nine=True)]), Code.SLICE_GEOMETRY_INVALID),
    ("a centre before its slice", b.aseprite(slice_chunks=[b.slice_chunk("c", [(0, 0, 0, 8, 8, -1, 0, 2, 2)], nine=True)]), Code.SLICE_GEOMETRY_INVALID),
    ("a pivot past its slice", b.aseprite(slice_chunks=[b.slice_chunk("p", [(0, 0, 0, 8, 8, 9, 0)], pivot=True)]), Code.SLICE_GEOMETRY_INVALID),
    ("a negative pivot", b.aseprite(slice_chunks=[b.slice_chunk("p", [(0, 0, 0, 8, 8, -1, 0)], pivot=True)]), Code.SLICE_GEOMETRY_INVALID),
])
def test_each_planted_bad_case_is_reported_with_its_code(name, source, expected):
    assert expected in codes(source), name


def test_a_negative_pivot_is_read_as_signed_not_as_a_huge_unsigned_number():
    facts, _ = aseprite.read_facts(b.aseprite(slice_chunks=[b.slice_chunk("p", [(0, 0, 0, 8, 8, -3, 0)], pivot=True)]))
    assert facts.slices[0].keys[0].pivot == (-3, 0)


def test_a_slice_name_that_is_not_utf8_is_reported_not_raised():
    good = b.aseprite(slice_chunks=[b.slice_chunk("abc", [(0, 0, 0, 1, 1)])])
    bad = good.replace(b"abc", b"\xff\xfe\xfd")
    assert bad != good and bad.count(b"\xff\xfe\xfd") == 1
    assert Code.SLICE_INVALID in codes(bad)


def test_the_contract_refuses_keys_that_disagree_about_the_centre_or_the_pivot():
    nine, plain = SliceKey(frame=0, bounds=SliceRect(x=0, y=0, w=8, h=8), center=SliceRect(x=1, y=1, w=2, h=2)), SliceKey(frame=1, bounds=SliceRect(x=0, y=0, w=8, h=8))
    with pytest.raises(ValidationError):
        SourceSlice(name="mixed", keys=(nine, plain))
    pivoted = SliceKey(frame=0, bounds=SliceRect(x=0, y=0, w=8, h=8), pivot=SlicePivot(x=1, y=1))
    with pytest.raises(ValidationError):
        SourceSlice(name="mixed", keys=(pivoted, plain))


def test_the_source_record_refuses_slices_outside_its_canvas_or_frames_or_out_of_order():
    base = record_args(width=16, height=16)
    outside = SourceSlice(name="out", keys=(SliceKey(frame=0, bounds=SliceRect(x=10, y=0, w=7, h=1)),))
    late = SourceSlice(name="late", keys=(SliceKey(frame=1, bounds=SliceRect(x=0, y=0, w=1, h=1)),))
    ok = lambda n: SourceSlice(name=n, keys=(SliceKey(frame=0, bounds=SliceRect(x=0, y=0, w=1, h=1)),))  # noqa: E731
    for bad in ((outside,), (late,), (ok("b"), ok("a")), (ok("a"), ok("a")), ()):
        with pytest.raises(ValidationError):
            SourceRecord(**{**base, "slices": bad})
    SourceRecord(**{**base, "slices": (ok("a"), ok("b"))})


def test_a_bad_slice_quarantines_the_candidate_at_intake(env):
    for number, source in enumerate([b.aseprite(slice_chunks=[b.slice_chunk("wide", [(0, 10, 0, 7, 1)])]), b.aseprite(slice_chunks=[PLAIN, PLAIN])]):
        preview = b.png(16 * 8, 16 * 8)
        directory = b.write_dir(env.tmp / f"bad-{number}", b.package_bytes(source, preview, candidate_id=f"cand-0000000000000b{number:02x}"), source, preview)
        result = intake(directory, created_at="2026-01-01T00:00:00Z")
        assert result.verdict is IntakeVerdict.QUARANTINED
        assert any(f.code.value.startswith("SLICE_") for f in result.findings)


def test_a_source_that_failed_intake_is_never_turned_into_a_record():
    with pytest.raises(slices.SliceError):
        slices.slices_from_source(b.aseprite(slice_chunks=[b.slice_chunk("wide", [(0, 10, 0, 7, 1)])]))


def test_every_accepted_source_builds_a_valid_contract_record_and_the_parser_and_contract_agree():
    full = [b.slice_chunk(f"s{i:02d}", [(f, 0, 0, 4, 4, 1, 1, 2, 2, 2, 2) for f in range(config.MAX_SLICE_KEYS)], nine=True, pivot=True) for i in range(config.MAX_SOURCE_SLICES)]
    for source in (b.aseprite(slice_chunks=[PLAIN, NINE]), b.aseprite(frames=16, slice_chunks=full)):
        assert not some(source)
        derived = slices.slices_from_source(source)
        assert len(derived) == len(aseprite.read_facts(source)[0].slices)


# ---- hostile bytes: a finding, never an exception, never a long loop ----

def _chunk_start(source: bytes) -> int:
    marker = struct.pack("<H", 0x2022)
    index = source.index(marker)
    assert source.count(marker) == 1
    return index - 4


def test_a_slice_chunk_cut_at_every_length_is_reported_never_raised():
    source = b.aseprite(frames=3, slice_chunks=[FULL])
    start = _chunk_start(source)
    length = struct.unpack_from("<I", source, start)[0]
    for keep in range(6, length):
        cut = bytearray(source)
        struct.pack_into("<I", cut, start, keep)  # the chunk now CLAIMS to be shorter than its keys need
        _, problems = aseprite.read_facts(bytes(cut))  # must not raise
        assert problems, f"chunk claimed {keep} bytes and nothing was reported"


def test_a_slice_chunk_that_declares_far_more_keys_than_it_holds_is_reported_without_reading_them():
    source = bytearray(b.aseprite(slice_chunks=[PLAIN]))
    body = _chunk_start(bytes(source)) + 6
    for declared in (config.MAX_SLICE_KEYS + 1, 2, 0xFFFFFFFF):
        struct.pack_into("<I", source, body, declared)
        found = codes(bytes(source))
        assert found & {Code.SLICE_OUT_OF_BOUNDS, Code.SOURCE_TRUNCATED_CHUNK}, declared


def test_a_name_length_that_runs_past_the_chunk_is_reported():
    source = bytearray(b.aseprite(slice_chunks=[PLAIN]))
    struct.pack_into("<H", source, _chunk_start(bytes(source)) + 6 + 12, 0xFFFF)
    assert Code.SOURCE_TRUNCATED_CHUNK in codes(bytes(source))


def test_a_hostile_slice_name_cannot_blow_up_a_finding(env):
    hostile = "‮" * 40 + "\x00" + "<" * 300
    source = b.aseprite(slice_chunks=[b.slice_chunk(hostile, [(0, 0, 0, 1, 1)])])
    preview = b.png(16 * 8, 16 * 8)
    directory = b.write_dir(env.tmp / "hostile", b.package_bytes(source, preview, candidate_id="cand-0000000000000c01"), source, preview)
    result = intake(directory, created_at="2026-01-01T00:00:00Z")
    assert result.verdict is IntakeVerdict.QUARANTINED
    assert all(hostile[:5] not in f.detail for f in result.findings)  # findings name a slice by position


def test_a_file_stuffed_with_slice_chunks_stops_at_the_bound_and_is_fast():
    chunks = [b.slice_chunk(f"s{i}", [(0, 0, 0, 1, 1)]) for i in range(2000)]
    source = b.aseprite(slice_chunks=chunks)
    started = time.perf_counter()
    facts, problems = aseprite.read_facts(source)
    assert time.perf_counter() - started < 0.5
    assert Code.SLICE_OUT_OF_BOUNDS in {code for code, _ in problems}
    assert len(facts.slices) == config.MAX_SOURCE_SLICES  # never walked past the bound


def test_the_worst_case_slice_json_fits_a_source_record():
    full = tuple(
        SourceSlice(name=f"{i:02d}" + "x" * 30, keys=tuple(
            SliceKey(frame=f, bounds=SliceRect(x=100, y=100, w=28, h=28), center=SliceRect(x=10, y=10, w=8, h=8), pivot=SlicePivot(x=28, y=28)) for f in range(config.MAX_SLICE_KEYS)))
        for i in range(config.MAX_SOURCE_SLICES)
    )
    record = canonical_json(SourceRecord(**record_args(width=128, height=128, slices=full, animation=SourceAnimation(frame_durations_ms=(100,) * 16))))
    assert len(record) < config.MAX_RECORD_BYTES // 2, len(record)


# ---- every committed record is byte-identical ----

def test_every_committed_source_record_round_trips_byte_for_byte_and_carries_no_slices():
    files = sorted((REAL / "sources").glob("*/r*.source.json"))
    assert len(files) >= 77
    for path in files:
        data = path.read_bytes()
        record = parse_record(SourceRecord, data)
        assert record.slices is None and canonical_json(record) == data, path
        assert b"slices" not in data, path


def test_every_committed_source_reads_with_no_new_finding_and_derives_no_slices():
    for path in sorted((REAL / "sources").glob("*/r*.aseprite")):
        source = path.read_bytes()
        assert not some(source), path
        assert slices.slices_from_source(source) is None, path


# ---- intake -> adoption -> SourceRecord ----

KEY_SLICED, KEY_PLAIN = "fixture.rehearsal.panel", "fixture.rehearsal.rock"


def test_adoption_derives_the_slices_from_the_bytes_and_leaves_a_plain_source_without_them(env):
    from tests.visual_assets.store import adoption_support as s
    from visual_assets.store import records, verify
    from visual_assets.store.catalog.registry import load_registry

    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    lines = ["record_type: visual_key_registry", "schema_version: 1", "keys:"]
    lines += [f"  - {{key: {key}, family: terrain, description: synthetic sliced test image, variant_axes: [], optional: false}}" for key in (KEY_SLICED, KEY_PLAIN)]
    lines.append("aliases: []")
    path = env.catalog / "definitions" / "visual_keys.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    registry = load_registry(path, allow_fixture_namespace=True)
    panel = s.make_intake(env.tmp, 16, frames=3, slice_chunks=[NINE, FULL])
    rock = s.make_intake(env.tmp, 17)
    s.do_adopt(panel.intake_id, source_asset_id="panel", visual_key=KEY_SLICED, registry=registry)
    s.do_adopt(rock.intake_id, source_asset_id="rock", visual_key=KEY_PLAIN, registry=registry)
    got = records.load_source("panel", "r0001")
    assert [x.name for x in got.slices] == ["hand", "panel"]
    assert got.slices[0].keys[1].pivot == SlicePivot(x=8, y=8) and got.slices[1].keys[0].center == SliceRect(x=4, y=4, w=8, h=8)
    assert records.load_source("rock", "r0001").slices is None
    assert b'"slices"' not in records.source_paths("rock", "r0001")[1].read_bytes()
    assert [f for f in verify.verify(allow_fixture_namespace=True) if f.blocking] == []  # the catalog still verifies with a sliced record in it


def test_a_finding_names_its_slice_by_chunk_position_even_after_a_rejected_one():
    source = b.aseprite(slice_chunks=[b.slice_chunk("", [(0, 0, 0, 1, 1)]), b.slice_chunk("a", [(0, 0, 0, 1, 1)]), b.slice_chunk("b", [(0, 0, 0, 1, 1)]), b.slice_chunk("c", [(0, 0, 0, 1, 1)] * 0)])
    _, problems = aseprite.read_facts(source)
    assert [m for c, m in problems if c is Code.SLICE_INVALID] == ["the name of slice 1 is empty, over 32 characters, not plain text or not UTF-8", "slice 4 has no keys"]
