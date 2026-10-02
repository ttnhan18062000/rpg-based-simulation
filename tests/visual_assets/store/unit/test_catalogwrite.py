"""All-or-nothing publication: a failure at ANY position leaves the catalog tree byte-identical (files and directories)."""

from __future__ import annotations

import os

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import catalogwrite, config
from visual_assets.store.errors import GateError
from visual_assets.store.intake import quarantine


def plan(env):
    return [
        (env.catalog / "sources" / "a" / "r0001.aseprite", b"source"),
        (env.catalog / "provenance" / "intake" / "in-1.json", b"{}"),
        (env.catalog / "provenance" / "adoptions" / "ad-1.json", b"{}"),
        (env.catalog / "sources" / "a" / "r0001.source.json", b"{}"),
    ]


def test_publish_creates_every_file_and_missing_directory(env):
    catalogwrite.publish(plan(env))
    assert {k for k, v in snapshot(env.catalog).items() if v[0] == "file"} == {
        "sources/a/r0001.aseprite", "provenance/intake/in-1.json", "provenance/adoptions/ad-1.json", "sources/a/r0001.source.json"}
    assert list(env.quarantine.glob(".tmp-*")) == []


@pytest.mark.parametrize("position", range(4))
def test_a_failure_while_publishing_at_each_position_rolls_everything_back(env, monkeypatch, position):
    (env.catalog / "provenance").mkdir()  # one directory pre-exists: only the NEW ones may be removed
    before = snapshot(env.catalog)
    real = os.link
    calls = {"n": 0}

    def flaky(src, dst):
        if calls["n"] == position:
            raise OSError("disk went away")
        calls["n"] += 1
        real(src, dst)

    monkeypatch.setattr(catalogwrite, "_link", flaky)
    with pytest.raises(OSError):
        catalogwrite.publish(plan(env))
    assert snapshot(env.catalog) == before
    assert list(env.quarantine.glob(".tmp-*")) == []


@pytest.mark.parametrize("position", range(4))
def test_a_failure_while_preparing_at_each_position_writes_nothing(env, monkeypatch, position):
    before = snapshot(env.catalog)
    real = quarantine.write_new
    calls = {"n": 0}

    def flaky(path, data):
        if calls["n"] == position:
            raise OSError("no space")
        calls["n"] += 1
        real(path, data)

    monkeypatch.setattr(catalogwrite.quarantine, "write_new", flaky)
    with pytest.raises(OSError):
        catalogwrite.publish(plan(env))
    assert snapshot(env.catalog) == before and list(env.quarantine.glob(".tmp-*")) == []


def test_a_target_that_appears_during_publishing_rolls_back_and_is_not_replaced(env, monkeypatch):
    real = os.link
    calls = {"n": 0}

    def race(src, dst):
        calls["n"] += 1
        if calls["n"] == 3:
            (env.catalog / "provenance" / "adoptions" / "ad-1.json").write_bytes(b"theirs")
            raise FileExistsError
        real(src, dst)

    monkeypatch.setattr(catalogwrite, "_link", race)
    with pytest.raises(GateError) as err:
        catalogwrite.publish(plan(env))
    assert err.value.code == "already_exists"
    left = {k: v for k, v in snapshot(env.catalog).items() if v[0] == "file"}
    assert set(left) == {"provenance/adoptions/ad-1.json"}  # only the other writer's file remains, untouched
    assert (env.catalog / "provenance" / "adoptions" / "ad-1.json").read_bytes() == b"theirs"


def test_an_existing_target_is_refused_before_anything_is_written(env, monkeypatch):
    (env.catalog / "sources" / "a").mkdir(parents=True)
    (env.catalog / "sources" / "a" / "r0001.source.json").write_bytes(b"original")
    before = snapshot(env.catalog)
    monkeypatch.setattr(catalogwrite, "_link", lambda *a: pytest.fail("nothing may even be attempted"))
    monkeypatch.setattr(catalogwrite.quarantine, "write_new", lambda *a: pytest.fail("no temporary file may be written"))
    with pytest.raises(GateError) as err:
        catalogwrite.publish(plan(env))
    assert err.value.code == "already_exists" and snapshot(env.catalog) == before
    assert not env.quarantine.exists() or list(env.quarantine.iterdir()) == []


def test_a_symlinked_ancestor_inside_the_catalog_is_refused(env):
    elsewhere = env.tmp / "elsewhere"
    elsewhere.mkdir()
    (env.catalog / "provenance").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(GateError) as err:
        catalogwrite.publish(plan(env))
    assert err.value.code == "catalog_symlink" and list(elsewhere.iterdir()) == []


def test_a_target_outside_the_catalog_is_refused(env):
    with pytest.raises(GateError) as err:
        catalogwrite.publish([(env.tmp / "elsewhere.json", b"x")])
    assert err.value.code == "outside_catalog" and not (env.tmp / "elsewhere.json").exists()


def test_adopt_rolls_back_at_every_position_of_its_four_writes(env, monkeypatch):
    result = s.make_intake(env.tmp)
    real = os.link
    for position in range(4):
        calls = {"n": 0}

        def flaky(src, dst, _p=position, _c=calls):
            if _c["n"] == _p:
                raise OSError("injected")
            _c["n"] += 1
            real(src, dst)

        monkeypatch.setattr(catalogwrite, "_link", flaky)
        with pytest.raises(OSError):
            s.do_adopt(result.intake_id)
        assert snapshot(env.catalog) == {}, position
    monkeypatch.setattr(catalogwrite, "_link", real)
    assert s.do_adopt(result.intake_id).source_revision == "r0001"  # and a clean retry then works


def test_the_temporary_files_never_hold_anything_a_failed_publish_could_leave_in_the_catalog(env):
    catalogwrite.publish(plan(env))
    assert not any(p.name.startswith(".tmp-") for p in env.catalog.rglob("*"))
    assert config.CATALOG_ROOT == env.catalog


def test_adopt_publishes_the_source_record_last(env, monkeypatch):
    """The SourceRecord is what makes a revision exist, so a hard kill mid-publish leaves orphans, never a half-real revision."""
    result = s.make_intake(env.tmp)
    real = os.link
    order: list[str] = []

    def spy(src, dst):
        order.append(os.path.relpath(dst, env.catalog))
        real(src, dst)

    monkeypatch.setattr(catalogwrite, "_link", spy)
    adoption = s.do_adopt(result.intake_id)
    assert order == [
        "sources/hero/r0001.aseprite",
        f"provenance/intake/{result.intake_id}.json",
        f"provenance/adoptions/{adoption.adoption_id}.json",
        "sources/hero/r0001.source.json",
    ]
