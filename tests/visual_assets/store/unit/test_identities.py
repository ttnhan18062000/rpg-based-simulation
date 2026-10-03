from __future__ import annotations

import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from visual_assets.store import identities as ids
from visual_assets.store.errors import IdentityError

H = "a" * 64

OPAQUE = [ids.SourceAssetId, ids.ArtifactId, ids.CatalogId, ids.CandidateId, ids.IntakeId, ids.AdoptionId,
          ids.RevocationId]

GOOD = {
    ids.VisualKey: ["a.b", "terrain.grass.tile", "a.b.c.d", "fixture.x_1.y"],
    ids.SourceRevision: ["r0001", "r0042", "r9999"],
    ids.FileHash: [f"sha256:{H}"],
    ids.PixelHash: [f"pixels-v1:{H}"],
    ids.UtcTimestamp: ["2024-02-29T23:59:59Z", "2000-02-29T00:00:00Z", "0001-01-01T00:00:00Z"],
}
BAD = {
    ids.VisualKey: ["A.b", "a", "a.b.c.d.e", " a.b", "a.b ", "a.b\n", "", "a..b", "a.1b", "a/b.c", "a.b/../c",
                    "a.b.." , "a." + "x" * 33, ".".join(["a" * 32] * 4) + "x"],
    ids.SourceRevision: ["r0000", "R0001", "r001", "r00001", "1", " r0001", "r0001\n", "", "r000a"],
    ids.FileHash: [f"sha256:{H.upper()}", f"SHA256:{H}", f"sha256:{H[:-1]}", f"sha256:{H}0", f" sha256:{H}",
                   f"sha256:{H}\n", f"pixels-v1:{H}", H, ""],
    ids.PixelHash: [f"pixels-v1:{H.upper()}", f"pixels-v1:{H[:-1]}", f"sha256:{H}", f"pixels-v1:{H}\n", ""],
    ids.UtcTimestamp: ["2023-02-29T00:00:00Z", "1900-02-29T00:00:00Z", "2024-13-01T00:00:00Z", "2024-00-10T00:00:00Z",
                       "2024-04-31T00:00:00Z", "2024-01-01T24:00:00Z", "2024-01-01T00:60:00Z", "2024-01-01T00:00:60Z",
                       "0000-01-01T00:00:00Z", "2024-01-01T00:00:00+00:00", "2024-01-01 00:00:00Z",
                       " 2024-01-01T00:00:00Z", "2024-01-01T00:00:00Z\n", ""],
}


@pytest.mark.parametrize("tp", OPAQUE, ids=lambda t: t.__name__)
def test_opaque_ids_accept_canonical_and_reject_non_canonical(tp):
    for good in ("a", "0", "abc-1_x", "a" * 64):
        assert ids.check(tp, good) == good
    for bad in ("", "A", "Abc", "-a", "_a", " a", "a ", "a\n", "a" * 65, "a/b", "a\\b", "..", "a..b", "a.b", "a b",
                "é", "../x", "x/../y"):
        with pytest.raises(IdentityError):
            ids.check(tp, bad)


@pytest.mark.parametrize("tp", list(GOOD), ids=lambda t: t.__name__ if hasattr(t, "__name__") else str(t))
def test_structured_identities(tp):
    for good in GOOD[tp]:
        assert ids.check(tp, good) == good
    for bad in BAD[tp]:
        with pytest.raises(IdentityError):
            ids.check(tp, bad)


def test_non_string_values_are_rejected_without_coercion():
    for tp in (ids.SourceAssetId, ids.VisualKey, ids.FileHash, ids.SourceRevision, ids.UtcTimestamp):
        for bad in (1, None, b"abc", ["a"], True):
            with pytest.raises(IdentityError):
                ids.check(tp, bad)


def test_identities_never_normalise():
    # a value is returned unchanged or rejected; it is never lowercased or trimmed
    for bad in ("ABC", " abc", "abc "):
        with pytest.raises(IdentityError):
            ids.check(ids.SourceAssetId, bad)


class _Hashes(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    file: ids.FileHash
    pixel: ids.PixelHash


def test_file_hash_and_pixel_hash_are_not_interchangeable():
    _Hashes(file=f"sha256:{H}", pixel=f"pixels-v1:{H}")
    with pytest.raises(ValidationError):
        _Hashes(file=f"pixels-v1:{H}", pixel=f"pixels-v1:{H}")
    with pytest.raises(ValidationError):
        _Hashes(file=f"sha256:{H}", pixel=f"sha256:{H}")


def test_sibling_id_shapes_that_differ_are_rejected():
    # an opaque id is never a visual key, a revision, a hash or a timestamp, and the reverse
    assert ids.check(ids.SourceAssetId, "abc")
    for tp, value in ((ids.VisualKey, "abc"), (ids.SourceRevision, "abc"), (ids.FileHash, "abc"),
                      (ids.UtcTimestamp, "abc")):
        with pytest.raises(IdentityError):
            ids.check(tp, value)
    for value in ("a.b", f"sha256:{H}", "2024-01-01T00:00:00Z"):
        with pytest.raises(IdentityError):
            ids.check(ids.SourceAssetId, value)


def test_visual_key_length_bound():
    longest = ".".join(["a" * 24] * 4)  # 24*4+3 = 99 > 96
    with pytest.raises(IdentityError):
        ids.check(ids.VisualKey, longest)
    assert ids.check(ids.VisualKey, ".".join(["a" * 23] * 4)) == ".".join(["a" * 23] * 4)  # 95 chars


def test_revision_helpers():
    assert ids.revision_number("r0001") == 1
    assert ids.revision_number("r9999") == 9999
    assert ids.next_revision("r0001") == "r0002"
    assert ids.next_revision("r0099") == "r0100"
    assert ids.next_revision("r9998") == "r9999"
    with pytest.raises(IdentityError):
        ids.next_revision("r9999")
    for bad in ("r0000", "x", ""):
        with pytest.raises(IdentityError):
            ids.revision_number(bad)


def test_fixture_namespace_helper():
    assert ids.is_fixture_key("fixture.a.b")
    assert not ids.is_fixture_key("fixtures.a.b")
    assert not ids.is_fixture_key("a.fixture.b")


def test_release_ids_are_ordered_rc_numbers():
    for good in ("rc-0001", "rc-0042", "rc-9999"):
        assert ids.check(ids.ReleaseId, good) == good
    for bad in ("rc-0000", "RC-0001", "rc-1", "rc-00001", "rc_0001", "rc-000a", "fixture-rc-0001", " rc-0001", "rc-0001\n", "", "0001"):
        with pytest.raises(IdentityError):
            ids.check(ids.ReleaseId, bad)
    assert ids.release_number("rc-0007") == 7
    assert ids.next_release_id([]) == "rc-0001"
    assert ids.next_release_id(["rc-0001", "rc-0010", "rc-0002"]) == "rc-0011"  # numeric, not string, order
    assert ids.next_release_id(["rc-0009"]) == "rc-0010"
    with pytest.raises(IdentityError):
        ids.next_release_id(["rc-9999"])
    with pytest.raises(IdentityError):
        ids.release_number("nope")
