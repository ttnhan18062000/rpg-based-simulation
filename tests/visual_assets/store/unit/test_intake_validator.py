"""The independent validator: every acceptance case has its own finding code; one policy for every producer."""

from __future__ import annotations

import json
import struct
import time

import pytest

from tests.visual_assets.store import builders as b
from visual_assets.store import config
from visual_assets.store.contracts.intake import IntakeFindingCode as Code
from visual_assets.store.intake import aseprite
from visual_assets.store.intake.validator import UNSUPPORTED_LIMITATIONS, VALIDATOR_VERSION, file_hash, validate


def codes(package: bytes, source: bytes, preview: bytes) -> list[Code]:
    return [f.code for f in validate(package, source, preview).findings]


def only(package: bytes, source: bytes, preview: bytes) -> Code:
    found = codes(package, source, preview)
    assert len(found) == 1, found
    return found[0]


def base(**source_kw):
    source = b.aseprite(**source_kw)
    preview = b.png(source_kw.get("width", 16) * 8, source_kw.get("height", 16) * 8)
    return source, preview


def test_a_consistent_candidate_passes():
    package, source, preview = b.good_files(frames=2, layers=3, tags=2, palette=6)
    result = validate(package, source, preview)
    assert result.findings == () and result.package is not None and VALIDATOR_VERSION


@pytest.mark.parametrize("producer", ["MANUAL", "CAP_A"])
def test_manual_and_cap_a_candidates_pass_under_the_same_policy(producer):
    source, preview = base()
    marked = dict(producer_class=producer, creator="UNAVAILABLE", editor="NOT_APPLICABLE", adapter="UNAVAILABLE",
                  tool="NOT_APPLICABLE", tool_version="UNAVAILABLE", brief_id="UNAVAILABLE")
    assert validate(b.package_bytes(source, preview, **marked), source, preview).findings == ()
    named = dict(producer_class=producer, creator="A Person", adapter="adapter 0.1.0", tool="Aseprite", tool_version="1.3.18.6")
    assert validate(b.package_bytes(source, preview, **named), source, preview).findings == ()


# claims that disagree with a source of 16x16, 1 frame, 2 layers, 2 cels, 2 tags, palette 8
CLAIM_DEFECTS = [
    ("width", dict(width=17), Code.WIDTH_MISMATCH),
    ("height", dict(height=9), Code.HEIGHT_MISMATCH),
    ("frames", dict(frame_count=2), Code.FRAME_COUNT_MISMATCH),
    ("layers", dict(layer_count=3), Code.LAYER_COUNT_MISMATCH),
    ("cels", dict(cel_count=5), Code.CEL_COUNT_MISMATCH),
    ("tags", dict(tag_count=1), Code.TAG_COUNT_MISMATCH),
    ("palette", dict(palette_size=9), Code.PALETTE_SIZE_MISMATCH),
    ("licence withdrawn", dict(licence_state="WITHDRAWN"), Code.LICENCE_WITHDRAWN),
    ("producer revoked", dict(producer_state="REVOKED"), Code.PRODUCER_NOT_ACTIVE),
    ("producer quarantined", dict(producer_state="QUARANTINED"), Code.PRODUCER_NOT_ACTIVE),
    ("producer validation failed", dict(producer_validation="FAILED"), Code.PRODUCER_VALIDATION_FAILED),
    ("unsupported limitation", dict(declared_limitations=["unsupported:tilemap"]), Code.UNSUPPORTED_LIMITATION),
]


@pytest.mark.parametrize("label,overrides,expected", CLAIM_DEFECTS, ids=[c[0] for c in CLAIM_DEFECTS])
def test_each_claim_defect_gets_its_own_finding_code(label, overrides, expected):
    source, preview = base(tags=2, layers=2)
    assert validate(b.package_bytes(source, preview), source, preview).findings == ()  # the baseline is clean
    package = b.package_bytes(source, preview, **overrides)
    assert only(package, source, preview) == expected


def _rehashed(package: bytes, source: bytes, preview: bytes) -> bytes:
    """Keep the claimed hashes honest so only the structural defect in the bytes is in play."""
    data = json.loads(package)
    data["source_hash"], data["preview_hash"] = file_hash(source), file_hash(preview)
    return json.dumps(data).encode()


def _with_chunk_size(source: bytes, size: int) -> bytes:
    # overwrite the size of the LAST chunk of the file (it is a cel chunk: 0x2005)
    for pos in range(len(source) - 6, 128, -1):
        if struct.unpack_from("<H", source, pos + 4)[0] == 0x2005 and struct.unpack_from("<I", source, pos)[0] >= 6:
            return source[:pos] + struct.pack("<I", size) + source[pos + 4 :]
    raise AssertionError("no cel chunk found")


STRUCTURAL_DEFECTS = [
    ("bad magic", lambda s: s[:4] + b"\x00\x00" + s[6:], Code.SOURCE_BAD_MAGIC),
    ("header size", lambda s: struct.pack("<I", len(s) + 1) + s[4:], Code.SOURCE_HEADER_SIZE_MISMATCH),
    ("truncated chunk", lambda s: _with_chunk_size(s, 0xFFFF), Code.SOURCE_TRUNCATED_CHUNK),
    ("cut inside the last frame", lambda s: s[:-3], Code.SOURCE_HEADER_SIZE_MISMATCH),
    ("trailing bytes", lambda s: s + b"\x00" * 4, Code.SOURCE_HEADER_SIZE_MISMATCH),
]


@pytest.mark.parametrize("label,mutate,expected", STRUCTURAL_DEFECTS, ids=[c[0] for c in STRUCTURAL_DEFECTS])
def test_each_structural_defect_gets_its_own_finding_code(label, mutate, expected):
    source, preview = base(tags=2, layers=2)
    bad = mutate(source)
    package = _rehashed(b.package_bytes(source, preview), bad, preview)
    found = codes(package, bad, preview)
    assert expected in found, (label, found)
    assert Code.SOURCE_HASH_MISMATCH not in found


def test_an_unsupported_colour_depth_is_a_finding():
    source, preview = base(depth=8)
    package = b.package_bytes(source, preview)
    assert only(package, source, preview) == Code.SOURCE_UNSUPPORTED_COLOR_DEPTH


def test_source_hash_mismatch_is_its_own_code():
    package, source, preview = b.good_files()
    # an appended byte also breaks the header size and leaves trailing data, so several findings are expected
    assert Code.SOURCE_HASH_MISMATCH in codes(package, source + b"\x00", preview)
    # a one-byte change inside the file that keeps it parseable still trips the hash and nothing else
    flipped = bytearray(source)
    flipped[-1] ^= 0x01
    assert only(package, bytes(flipped), preview) == Code.SOURCE_HASH_MISMATCH


def test_preview_hash_mismatch_is_its_own_code():
    package, source, preview = b.good_files()
    # a DIFFERENT but perfectly valid PNG of the same size: only the claimed hash is wrong
    other = b.png_encode(128, 128, b.sample_pixels(128, 128))
    assert other != preview and only(package, source, other) == Code.PREVIEW_HASH_MISMATCH
    # a flipped byte inside the file is a different defect: the chunk checksum no longer matches (and the hash differs too)
    flipped = bytearray(preview)
    flipped[40] ^= 0x01
    assert set(codes(package, source, bytes(flipped))) == {Code.PREVIEW_HASH_MISMATCH, Code.PNG_BAD_CRC}


def test_dimensions_over_the_bound_are_a_finding(monkeypatch):
    package, source, preview = b.good_files()  # 16x16 source, claims match; built while MAX_DIM is still 128
    monkeypatch.setattr(config, "MAX_DIM", 8)
    result = validate(package, source, preview)
    assert Code.DIMENSION_OUT_OF_BOUNDS in [f.code for f in result.findings]


def test_a_source_over_128_is_out_of_bounds_even_with_matching_claims_impossible():
    source, preview = base(width=129, height=129)
    package = b.package_dict(source, preview, width=128, height=128)
    found = codes(json.dumps(package).encode(), source, preview)
    assert Code.DIMENSION_OUT_OF_BOUNDS in found and Code.WIDTH_MISMATCH in found


def test_truncation_at_every_length_never_raises_and_always_reports():
    source = b.aseprite(frames=2, layers=2, tags=2, palette=6)
    preview = b.png(16 * 8, 16 * 8)
    package = b.package_bytes(source, preview)
    for length in range(0, len(source)):
        cut = source[:length]
        result = validate(package, cut, preview)
        assert result.findings, length  # a cut file is never PASSED


def test_hostile_size_fields_are_bounded_and_fast():
    started = time.monotonic()
    zero_chunk = b.aseprite(extra_first_frame=[struct.pack("<IH", 0, 0x2004)])
    giant = b.aseprite(extra_first_frame=[struct.pack("<IH", 0xFFFFFFFF, 0x2005)])
    many_frames = bytearray(b.aseprite())
    many_frames[6:8] = struct.pack("<H", 65535)  # claims 65535 frames but holds one
    for blob in (zero_chunk, giant, bytes(many_frames), b"\x00" * 128, b"\xff" * 5000):
        facts, problems = aseprite.read_facts(blob)
        assert problems, blob[:8]
    assert time.monotonic() - started < 2


def test_unknown_chunks_are_skipped_by_declared_size():
    source = b.aseprite(extra_first_frame=[b.unknown_chunk(37), b.unknown_chunk(0)])
    facts, problems = aseprite.read_facts(source)
    assert problems == [] and facts is not None and facts.layers == 1


def facts_of(**kw):
    return aseprite.read_facts(b.aseprite(**kw))


def test_palette_size_is_the_size_aseprite_reports_after_loading():
    assert facts_of(palette=6)[0].palette_size == 6
    assert facts_of(palette=6, palette_chunks=[b.palette_chunk(6, named=True)])[0].palette_size == 6  # named entries
    assert facts_of(palette=7, palette_chunks=[b.palette_chunk(4), b.palette_chunk(7)])[0].palette_size == 7  # last wins
    # the 1-entry transparent-black chunk Aseprite itself writes for a collapsed palette is exact
    single = facts_of(palette=1, palette_chunks=[b.palette_chunk(1, transparent=True)])
    assert single[1] == [] and single[0].palette_size == 1
    old = facts_of(palette=9, palette_chunks=[b.old_palette_chunk([(0, 4), (2, 3)])])
    assert old[1] == [] and old[0].palette_size == 9  # 4 colours, skip 2, 3 more
    assert facts_of(palette=256, palette_chunks=[b.old_palette_chunk([(0, 256)])])[0].palette_size == 256


def test_an_all_black_stored_palette_is_unverifiable_not_guessed():
    # Aseprite rebuilds such a palette from the pixels, so its loaded size cannot be known without decoding them
    for chunk, size in ((b.palette_chunk(6, black=True), 6), (b.palette_chunk(1, black=True), 1),
                        (b.old_palette_chunk([(0, 9)], black=True), 9)):
        facts, problems = facts_of(palette=size, palette_chunks=[chunk])
        assert facts.palette_size is None
        assert [c for c, _ in problems] == [Code.PALETTE_UNVERIFIABLE], size


def test_an_unverifiable_palette_quarantines_the_candidate_without_a_second_finding():
    source = b.aseprite(palette=6, palette_chunks=[b.palette_chunk(6, black=True)])
    preview = b.png(16 * 8, 16 * 8)
    for claimed in (1, 2, 6, 256):  # whatever the producer claims, the size cannot be confirmed
        package = b.package_bytes(source, preview, palette_size=claimed)
        assert only(package, source, preview) == Code.PALETTE_UNVERIFIABLE, claimed


def test_a_palette_Aseprite_would_not_write_is_malformed_not_guessed():
    # header colour count disagrees with the stored old-style entries
    facts, problems = facts_of(header_colors=7, palette_chunks=[b.old_palette_chunk([(0, 4), (2, 3)])])
    assert [c for c, _ in problems] == [Code.SOURCE_MALFORMED]
    # no palette chunk at all
    facts, problems = facts_of(palette_chunks=[])
    assert Code.SOURCE_MALFORMED in [c for c, _ in problems]


def test_hostile_palette_chunks_are_refused_without_allocating():
    import struct

    def new_chunk(size, first, last, entries=b""):
        body = struct.pack("<III8x", size, first, last) + entries
        return struct.pack("<IH", 6 + len(body), 0x2019) + body

    entry = struct.pack("<HBBBB", 0, 9, 9, 9, 255)
    cases = {
        "huge declared size": new_chunk(0xFFFFFFFF, 0, 5, entry * 6),
        "first after last": new_chunk(10, 7, 3, entry * 4),
        "last outside size": new_chunk(4, 0, 9, entry * 10),
        "entries missing": new_chunk(10, 0, 9, entry * 2),
        "truncated header": struct.pack("<IH", 6 + 5, 0x2019) + b"\x00" * 5,
        "name overruns": new_chunk(1, 0, 0, struct.pack("<HBBBB", 1, 9, 9, 9, 255) + struct.pack("<H", 60000)),
    }
    for label, chunk in cases.items():
        facts, problems = aseprite.read_facts(b.aseprite(palette_chunks=[chunk]))
        assert problems, label
        assert all(code is Code.SOURCE_TRUNCATED_CHUNK for code, _ in problems), (label, problems)


def test_a_validation_reports_a_palette_the_producer_got_wrong():
    source = b.aseprite(palette=6)
    preview = b.png(16 * 8, 16 * 8)
    assert only(b.package_bytes(source, preview, palette_size=256), source, preview) == Code.PALETTE_SIZE_MISMATCH


def test_missing_assertion_is_its_own_code():
    package, source, preview = b.good_files()
    data = json.loads(package)
    del data["assertion"]
    assert only(json.dumps(data).encode(), source, preview) == Code.ASSERTION_MISSING
    data["assertion"] = "HANDOFF_IS_ADOPTION"
    assert only(json.dumps(data).encode(), source, preview) == Code.ASSERTION_MISSING


def test_unknown_field_and_duplicate_key_are_their_own_codes():
    package, source, preview = b.good_files()
    data = json.loads(package)
    data["surprise"] = 1
    result = validate(json.dumps(data).encode(), source, preview)
    assert [f.code for f in result.findings] == [Code.PACKAGE_UNKNOWN_FIELD] and result.package is None
    dup = package.rstrip(b"\n")[:-1] + b',"width":16}'
    assert only(dup, source, preview) == Code.PACKAGE_DUPLICATE_KEY


@pytest.mark.parametrize("blob,code", [
    (b"", Code.PACKAGE_UNREADABLE), (b"not json", Code.PACKAGE_UNREADABLE), (b"\xff\xfe", Code.PACKAGE_UNREADABLE),
    (b"[]", Code.PACKAGE_INVALID), (b'{"record_type":"x"}', Code.PACKAGE_WRONG_RECORD_TYPE),
])
def test_unparseable_packages_are_quarantined_but_the_bytes_are_still_checked(blob, code):
    _, source, preview = b.good_files()
    result = validate(blob, source, preview)
    assert result.package is None and code in [f.code for f in result.findings]
    # claim-free checks still run: a bad source is reported alongside the package problem
    bad = validate(blob, source[:4] + b"\x00\x00" + source[6:], preview)
    assert Code.SOURCE_BAD_MAGIC in [f.code for f in bad.findings]


def test_wrong_schema_version_is_its_own_code():
    package, source, preview = b.good_files()
    data = json.loads(package)
    data["schema_version"] = 2
    assert only(json.dumps(data).encode(), source, preview) == Code.PACKAGE_UNSUPPORTED_VERSION


def test_findings_never_echo_producer_text():
    package, source, preview = b.good_files()
    data = json.loads(package)
    data["evil\x1b[31m key"] = "x"
    result = validate(json.dumps(data).encode(), source, preview)
    for finding in result.findings:
        assert "evil" not in finding.detail and "\x1b" not in finding.detail
    dup = json.dumps(json.loads(package)).encode()[:-1] + b',"evil\\u202e":1,"evil\\u202e":2}'
    for finding in validate(dup, source, preview).findings:
        assert "evil" not in finding.detail


def test_preview_checks():
    source, preview = base()
    package = b.package_bytes(source, preview)

    def only_preview(blob: bytes, expected: Code):
        pk = json.dumps({**json.loads(package), "preview_hash": file_hash(blob)}).encode()
        assert only(pk, source, blob) == expected

    only_preview(b"GIF89a" + b"\x00" * 40, Code.PNG_SIGNATURE_INVALID)
    damaged = bytearray(preview)
    damaged[29] ^= 0xFF  # the IHDR checksum
    only_preview(bytes(damaged), Code.PNG_BAD_CRC)
    only_preview(preview + b"\x00", Code.PNG_TRAILING_DATA)
    only_preview(preview[:-20], Code.PNG_TRUNCATED)
    only_preview(b.png_encode(128, 128, b.sample_pixels(128, 128), ctype=6)[:0] + _png16(128, 128), Code.PNG_UNSUPPORTED)
    # a 3x-wide preview of a 16x16 source is not a whole-number scale in both axes
    odd = b.png(48, 40)
    only_preview(odd, Code.PREVIEW_DIMENSION_MISMATCH)
    # 1x and 16x previews are fine, whatever filters the encoder chose
    for scale in (1, 16):
        ok = b.png(16 * scale, 16 * scale)
        pk = json.dumps({**json.loads(package), "preview_hash": file_hash(ok)}).encode()
        assert validate(pk, source, ok).findings == (), scale
    paeth = b.png_encode(128, 128, b.sample_pixels(128, 128), filters=[0, 1, 2, 3, 4])
    pk = json.dumps({**json.loads(package), "preview_hash": file_hash(paeth)}).encode()
    assert validate(pk, source, paeth).findings == ()


def _png16(width: int, height: int) -> bytes:
    """A syntactically valid 16-bit RGBA PNG (a kind the store does not accept)."""
    import struct
    import zlib

    raw = b"".join(b"\x00" + b"\x00" * (width * 8) for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + b.png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 16, 6, 0, 0, 0)) \
        + b.png_chunk(b"IDAT", zlib.compress(raw)) + b.png_chunk(b"IEND", b"")


def test_every_preview_defect_gets_its_own_distinct_code():
    from visual_assets.store.contracts.intake import IntakeFindingCode

    for name in ("PNG_SIGNATURE_INVALID", "PNG_BAD_CRC", "PNG_UNSUPPORTED", "PNG_TRUNCATED", "PNG_TOO_LARGE_DECODED",
                 "PNG_TRAILING_DATA", "PNG_MALFORMED", "PREVIEW_OUT_OF_BOUNDS", "PREVIEW_DIMENSION_MISMATCH"):
        assert IntakeFindingCode[name].value == name


def test_every_unsupported_limitation_token_is_enforced():
    source, preview = base()
    for token in sorted(UNSUPPORTED_LIMITATIONS):
        package = b.package_bytes(source, preview, declared_limitations=[token, "just a note"])
        assert only(package, source, preview) == Code.UNSUPPORTED_LIMITATION
    informational = b.package_bytes(source, preview, declared_limitations=["unsupported:something_else"])
    assert validate(informational, source, preview).findings == ()


def test_manual_and_cap_a_get_identical_findings_for_every_defect():
    source, preview = base(tags=2)
    for overrides in ({"width": 17}, {"licence_state": "WITHDRAWN"}, {"producer_state": "REVOKED"}, {"tag_count": 0}):
        results = []
        for producer in ("MANUAL", "CAP_A"):
            package = b.package_bytes(source, preview, producer_class=producer, **overrides)
            results.append([(f.code, f.detail) for f in validate(package, source, preview).findings])
        assert results[0] == results[1] and results[0], overrides


def test_a_damaged_frame_header_is_malformed():
    import struct

    source = b.aseprite(frames=2)
    preview = b.png(16 * 8, 16 * 8)
    first = 128  # the first frame header starts right after the 128-byte file header
    bad_magic = source[: first + 4] + b"\x00\x00" + source[first + 6 :]
    too_small = source[:first] + struct.pack("<I", 8) + source[first + 4 :]
    for label, blob in (("magic", bad_magic), ("size", too_small)):
        facts, problems = aseprite.read_facts(blob)
        assert Code.SOURCE_MALFORMED in [c for c, _ in problems], label
        package = b.package_bytes(source, preview)
        assert Code.SOURCE_MALFORMED in codes(_rehashed(package, blob, preview), blob, preview), label


def test_a_second_frame_is_walked_too():
    import struct

    source = b.aseprite(frames=3, layers=2)
    facts, problems = aseprite.read_facts(source)
    assert problems == [] and facts.frames == 3 and facts.cels == 6
    # damage the SECOND frame's magic: the walk must notice it, not stop after the first frame
    first_size = struct.unpack_from("<I", source, 128)[0]
    second = 128 + first_size
    broken = source[: second + 4] + b"\x00\x00" + source[second + 6 :]
    assert Code.SOURCE_MALFORMED in [c for c, _ in aseprite.read_facts(broken)[1]]
