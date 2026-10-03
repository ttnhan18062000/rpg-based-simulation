"""The read model behind `store_list` / `store_show`: shaped, bounded, read-only, no absolute paths, nothing raw."""

from __future__ import annotations

import json

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import readmodel
from visual_assets.store.errors import ReadError
from visual_assets.store.release import assemble_release
from visual_assets.store.revoke import revoke

HERO, ROCK = s.key_for("hero"), s.key_for("rock")


@pytest.fixture
def tree(env):
    s.CALLS.clear()
    env.adoptions, env.built = s.adopted_tree(env)
    s.write_registry(env.catalog, [HERO, ROCK])
    assemble_release("main", allow_fixture_namespace=True)
    env.pending = s.make_intake(env.tmp, 18)
    env.bad = s.make_intake(env.tmp, 19, passed=False)
    return env


def absolute_paths(value) -> list[str]:
    found = []
    if isinstance(value, str):
        if value.startswith("/") or "/tmp/" in value or "/home/" in value or "pytest-of-" in value:
            found.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            found += absolute_paths(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            found += absolute_paths(v)
    return found


def test_every_kind_lists_what_exists(tree):
    intakes = readmodel.list_items("intake")
    assert intakes["kind"] == "intake" and intakes["count"] == 4 and not intakes["truncated"] and intakes["unreadable"] == 0
    states = {i["intake_id"]: (i["verdict"], i["adopted"], i["revoked"]) for i in intakes["items"]}
    assert states[tree.pending.intake_id] == ("PASSED", False, False) and states[tree.bad.intake_id] == ("QUARANTINED", False, False)
    assert states[tree.adoptions[0].intake_id] == ("PASSED", True, False)
    sources = readmodel.list_items("source")["items"]
    assert [(i["source_asset_id"], i["revision"], i["build_eligible"]) for i in sources] == [("hero", "r0001", True), ("rock", "r0001", True)]
    artifacts = readmodel.list_items("artifact")["items"]
    assert [(a["artifact_id"], a["source_revision"]) for a in artifacts] == [("hero--x1", "r0001"), ("rock--x1", "r0001")]
    assert artifacts[0]["pixel_hash"] == tree.built[0].pixel_hash
    releases = readmodel.list_items("release")["items"]
    assert releases == [{"catalog_id": "main", "release_id": "rc-0001", "entries": 2, "readable": True, "status": "CANDIDATE"}]


def test_listing_is_bounded_and_says_when_it_truncated(tree):
    page = readmodel.list_items("intake", limit=2)
    assert page["count"] == 2 and page["truncated"] is True and len(page["items"]) == 2
    assert readmodel.list_items("intake", limit=4)["truncated"] is False
    for bad in (0, -1, 201, 1.5, "5", None, True):
        with pytest.raises(ReadError) as err:
            readmodel.list_items("intake", limit=bad)
        assert err.value.code == "invalid_limit", bad
    for kind in ("adopt", "", "INTAKE", "sources", None, "../x"):
        with pytest.raises(ReadError) as err:
            readmodel.list_items(kind)
        assert err.value.code == "unknown_kind", kind


def test_a_revoked_revision_and_a_revoked_intake_are_visible(tree):
    revoke("rock/r0001", reason="withdrawn", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    revoke(tree.pending.intake_id, reason="not wanted", approver="Pat", approver_role="lead", decided_at=s.NOW, confirm=s.yes)
    sources = {(i["source_asset_id"]): i["build_eligible"] for i in readmodel.list_items("source")["items"]}
    assert sources == {"hero": True, "rock": False}
    assert {i["intake_id"]: i["revoked"] for i in readmodel.list_items("intake")["items"]}[tree.pending.intake_id] is True
    shown = readmodel.show_item("source", "rock/r0001")
    assert shown["revoked"] is True and shown["build_eligible"] is False


def test_show_returns_shaped_summaries_of_each_kind(tree):
    intake = readmodel.show_item("intake", tree.pending.intake_id)
    assert intake["verdict"] == "PASSED" and intake["findings"] == [] and [f["name"] for f in intake["staged_files"]] == ["package.json", "source.aseprite", "preview.png"]
    claims = intake["claimed_by_producer"]
    assert "unverified" in claims["note"] and claims["licence_state"] == "CLEARED"  # a producer statement, labelled as a claim
    bad = readmodel.show_item("intake", tree.bad.intake_id)
    assert bad["verdict"] == "QUARANTINED" and bad["findings"][0]["code"]
    source = readmodel.show_item("source", "hero/r0001")
    assert source["adoption"]["approver_name"] == "Pat Approver" and source["adoption"]["licence_note"] == "stated by the approver at adoption"
    assert source["adoption"]["visual_key"] == HERO and source["parent_revision"] is None
    artifact = readmodel.show_item("artifact", "hero--x1")
    assert artifact["records"][0]["pixel_hash"] == tree.built[0].pixel_hash and artifact["records"][0]["tool"] == "Aseprite 1.3.test"
    release = readmodel.show_item("release", "main/rc-0001")
    assert release["status"] == "CANDIDATE" and release["entry_count"] == 2 and "nothing is active" in release["note"]
    assert [e["visual_key"] for e in release["entries"]] == [HERO, ROCK]


def test_nothing_is_raw_and_nothing_is_an_absolute_path(tree):
    shown = [readmodel.show_item("intake", tree.pending.intake_id), readmodel.show_item("intake", tree.bad.intake_id),
             readmodel.show_item("source", "hero/r0001"), readmodel.show_item("artifact", "hero--x1"), readmodel.show_item("release", "main/rc-0001")]
    listed = [readmodel.list_items(k) for k in readmodel.KINDS]
    for value in shown + listed:
        assert absolute_paths(value) == [], value
        text = json.dumps(value)
        assert len(text) < 20_000 and "\\x" not in text and "BEGIN" not in text
    # no record is dumped wholesale: a summary never carries a record_type / schema_version envelope
    for value in shown:
        assert "record_type" not in value and "schema_version" not in value


def test_listing_and_showing_change_no_file(tree):
    before = (snapshot(tree.catalog), snapshot(tree.quarantine), snapshot(tree.review))
    for kind in readmodel.KINDS:
        readmodel.list_items(kind)
        readmodel.list_items(kind, limit=1)
    readmodel.show_item("intake", tree.pending.intake_id)
    readmodel.show_item("source", "hero/r0001")
    readmodel.show_item("artifact", "rock--x1")
    readmodel.show_item("release", "main/rc-0001")
    assert (snapshot(tree.catalog), snapshot(tree.quarantine), snapshot(tree.review)) == before  # byte-identical


@pytest.mark.parametrize("kind,item_id,code", [
    ("intake", "nope", "invalid_id"), ("intake", "../x", "invalid_id"), ("intake", "", "invalid_id"), ("intake", "in-0000000000000000", "unknown_id"),
    ("source", "hero", "invalid_id"), ("source", "hero/latest", "invalid_id"), ("source", "../x/r0001", "invalid_id"), ("source", "hero/r0099", "unknown_id"),
    ("source", "ghost/r0001", "unknown_id"),
    ("artifact", "../etc", "invalid_id"), ("artifact", "", "invalid_id"), ("artifact", "ghost--x1", "unknown_id"), ("artifact", "Hero", "invalid_id"),
    ("release", "main", "invalid_id"), ("release", "main/latest", "invalid_id"), ("release", "../x/rc-0001", "invalid_id"),
    ("release", "main/rc-0009", "unknown_id"), ("release", "ghost/rc-0001", "unknown_id"),
    ("adoption", "ad-1", "unknown_kind"), (None, "x", "unknown_kind"),
])
def test_bad_or_unknown_ids_are_refused_with_a_code(tree, kind, item_id, code):
    before = snapshot(tree.catalog)
    with pytest.raises(ReadError) as err:
        readmodel.show_item(kind, item_id)
    assert err.value.code == code and snapshot(tree.catalog) == before and absolute_paths(err.value.message) == []


def test_unreadable_records_are_reported_not_hidden(tree):
    (tree.catalog / "sources" / "hero" / "r0001.source.json").write_text("{}")
    item = [i for i in readmodel.list_items("source")["items"] if i["source_asset_id"] == "hero"][0]
    assert item["readable"] is False and item["build_eligible"] is False
    with pytest.raises(ReadError) as err:
        readmodel.show_item("source", "hero/r0001")
    assert err.value.code == "unreadable"
    manifest = tree.catalog / "manifests" / "candidates" / "main" / "rc-0001.json"
    manifest.write_text("garbage")
    assert readmodel.list_items("release")["items"][0]["readable"] is False


def test_an_empty_store_lists_nothing(env):
    for kind in readmodel.KINDS:
        page = readmodel.list_items(kind)
        assert page["count"] == 0 and page["items"] == [] and page["truncated"] is False


def test_a_large_release_is_bounded_in_show_and_counted_in_full(tree):
    from visual_assets.store.contracts import ReleaseCandidateManifest, canonical_json
    from visual_assets.store.contracts.release import ReleaseEntry

    entry = readmodel.show_item("release", "main/rc-0001")["entries"][0]
    entries = tuple(ReleaseEntry(visual_key=f"fixture.sample.k{i}", artifact_id="hero--x1", pixel_hash=entry["pixel_hash"]) for i in range(250))
    manifest = ReleaseCandidateManifest(record_type="release_candidate_manifest", schema_version=1, catalog_id="main", release_id="rc-0002",
                                        registry_hash="sha256:" + "0" * 64, entries=entries, status="CANDIDATE")
    (tree.catalog / "manifests" / "candidates" / "main" / "rc-0002.json").write_bytes(canonical_json(manifest))
    shown = readmodel.show_item("release", "main/rc-0002")
    assert shown["entry_count"] == 250 and len(shown["entries"]) == readmodel.MAX_LIMIT == 200 and shown["truncated"] is True
    listed = {i["release_id"]: i["entries"] for i in readmodel.list_items("release")["items"]}
    assert listed == {"rc-0001": 2, "rc-0002": 250}
