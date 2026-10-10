"""`export-runtime --slices` (`TCK-20261010-VISUAL-ASSETS-SLICE-RUNTIME-EXPORT`; ADR D25).

`slices.json` is the opt-in file with the slices of every release entry whose source has any, in the EXPORTED image's pixels (source pixels times the build scale), relative to the image. No flag, no file, and
the manifest and every PNG are byte-identical either way. The only scale class today is x1, so the scaling itself is proven against hand-computed values with a patched scale; the end-to-end path runs at x1.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from tests.visual_assets.store import adoption_support as s
from tests.visual_assets.store import builders as b
from visual_assets.store import cli, records, slices
from visual_assets.store.build import exporter
from visual_assets.store.contracts import parse_record
from visual_assets.store.contracts.slices import RuntimeSlices
from visual_assets.store.errors import BuildError
from visual_assets.store.release import assemble_release
from visual_assets.store.runtime_export import export_runtime

KEY_SLICED, KEY_PLAIN = "fixture.rehearsal.panel", "fixture.rehearsal.rock"
NINE = b.slice_chunk("panel", [(0, 2, 3, 8, 6, 1, 1, 4, 2)], nine=True)
PIVOT = b.slice_chunk("hand", [(0, 4, 5, 6, 4, 3, 2)], pivot=True)


@pytest.fixture
def catalog(env):
    s.CALLS.clear()
    s.write_export_config(env.catalog)
    s.write_store_format(env.catalog)
    lines = ["record_type: visual_key_registry", "schema_version: 1", "keys:"]
    lines += [f"  - {{key: {key}, family: terrain, description: synthetic sliced test image, variant_axes: [], optional: false}}" for key in (KEY_SLICED, KEY_PLAIN)]
    lines.append("aliases: []")
    path = env.catalog / "definitions" / "visual_keys.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    from visual_assets.store.catalog.registry import load_registry

    registry = load_registry(path, allow_fixture_namespace=True)
    panel = s.make_intake(env.tmp, 16, slice_chunks=[NINE, PIVOT])
    rock = s.make_intake(env.tmp, 17)
    s.do_adopt(panel.intake_id, source_asset_id="panel", visual_key=KEY_SLICED, registry=registry)
    s.do_adopt(rock.intake_id, source_asset_id="rock", visual_key=KEY_PLAIN, registry=registry)
    exporter.build(renderer=s.HashRenderer())
    assemble_release("pilot", release_id="rc-0001", allow_fixture_namespace=True)
    return env


def test_the_opt_in_export_writes_slices_json_with_the_values_in_the_file_and_nothing_else_changes(catalog):
    plain, with_slices = catalog.tmp / "out-plain", catalog.tmp / "out-slices"
    export_runtime("pilot", "rc-0001", plain, allow_fixture_namespace=True)
    export_runtime("pilot", "rc-0001", with_slices, allow_fixture_namespace=True, slices=True)
    assert not (plain / "slices.json").exists(), "no flag, no file"
    assert sorted(p.name for p in with_slices.iterdir()) == sorted([*(p.name for p in plain.iterdir()), "slices.json"])
    for path in plain.iterdir():
        assert (with_slices / path.name).read_bytes() == path.read_bytes(), path.name
    exported = parse_record(RuntimeSlices, (with_slices / "slices.json").read_bytes())
    assert [e.visual_key for e in exported.entries] == [KEY_SLICED]  # the source without slices is omitted
    got = {one.name: one.keys for one in exported.entries[0].slices}
    assert list(got) == ["hand", "panel"]
    assert [(k.frame, k.x, k.y, k.w, k.h, k.center, k.pivot) for k in got["panel"]][0][:5] == (0, 2, 3, 8, 6)
    assert got["panel"][0].center.model_dump() == {"x": 1, "y": 1, "w": 4, "h": 2} and got["panel"][0].pivot is None
    assert got["hand"][0].pivot.model_dump() == {"x": 3, "y": 2} and got["hand"][0].center is None
    assert b"slices" not in (with_slices / "runtime_manifest.json").read_bytes()


def test_the_export_is_byte_identical_twice(catalog):
    one, two = catalog.tmp / "o1", catalog.tmp / "o2"
    export_runtime("pilot", "rc-0001", one, allow_fixture_namespace=True, slices=True)
    export_runtime("pilot", "rc-0001", two, allow_fixture_namespace=True, slices=True)
    assert (one / "slices.json").read_bytes() == (two / "slices.json").read_bytes()


def entries_of(catalog_env):
    from visual_assets.store.contracts import ReleaseCandidateManifest

    path = records.manifests_dir() / "pilot" / "rc-0001.json"
    return parse_record(ReleaseCandidateManifest, path.read_bytes()).entries


def test_geometry_is_multiplied_by_the_build_scale_against_hand_computed_values(catalog, monkeypatch):
    real = records.load_artifact_for
    monkeypatch.setattr(records, "load_artifact_for", lambda sid, rev, cls, root=None: (SimpleNamespace(width=real(sid, rev, cls)[0].width * 3, height=real(sid, rev, cls)[0].height * 3), None))
    data = json.loads(slices.runtime_slices_bytes(entries_of(catalog), catalog_id="pilot", release_id="rc-0001", scales={"x1": 3}))
    by_name = {one["name"]: one["keys"][0] for one in data["entries"][0]["slices"]}
    assert by_name["panel"] == {"frame": 0, "x": 6, "y": 9, "w": 24, "h": 18, "center": {"x": 3, "y": 3, "w": 12, "h": 6}}
    assert by_name["hand"] == {"frame": 0, "x": 12, "y": 15, "w": 18, "h": 12, "pivot": {"x": 9, "y": 6}}


def test_an_unresolvable_scale_is_refused_and_leaves_no_output(catalog):
    for scales in ({}, {"x1": 2}, {"other": 1}):
        with pytest.raises(slices.SliceScaleError):
            slices.runtime_slices_bytes(entries_of(catalog), catalog_id="pilot", release_id="rc-0001", scales=scales)


def test_the_export_refuses_when_the_scale_cannot_be_resolved_and_writes_nothing(catalog, monkeypatch):
    from visual_assets.store import runtime_export

    monkeypatch.setattr(runtime_export, "load_export_config", lambda: SimpleNamespace(scale_classes=(SimpleNamespace(name="x1", scale=2),)))
    out = catalog.tmp / "out-bad"
    with pytest.raises(BuildError) as raised:
        export_runtime("pilot", "rc-0001", out, allow_fixture_namespace=True, slices=True)
    assert raised.value.code == "slices_scale_unresolved"
    assert not out.exists() and not [p for p in catalog.tmp.iterdir() if p.name.startswith(".tmp-")]


def test_the_cli_flag_reaches_the_export_and_is_off_by_default(monkeypatch, tmp_path):
    seen = []

    def stub(catalog_id, release_id, out, **kwargs):
        seen.append(kwargs)
        return SimpleNamespace(catalog_id=catalog_id, release_id=release_id, entries=())

    monkeypatch.setattr(cli.runtime_export, "export_runtime", stub)
    base = ["export-runtime", "--catalog-id", "pilot", "--release-id", "rc-0001", "--out", str(tmp_path / "o")]
    assert cli.main(base) == 0 and cli.main([*base, "--slices"]) == 0
    assert [k["slices"] for k in seen] == [False, True]


def test_an_export_of_a_release_without_slices_has_an_empty_entry_list(env):
    data = slices.runtime_slices_bytes([], catalog_id="pilot", release_id="rc-0001", scales={"x1": 1})
    assert json.loads(data)["entries"] == []


def test_an_artifact_whose_width_or_height_alone_disagrees_with_the_scale_is_refused(catalog, monkeypatch):
    real = records.load_artifact_for
    for wrong in ("width", "height"):
        def fake(sid, rev, cls, root=None, wrong=wrong):
            record = real(sid, rev, cls)[0]
            return SimpleNamespace(width=record.width + (wrong == "width"), height=record.height + (wrong == "height")), None

        monkeypatch.setattr(records, "load_artifact_for", fake)
        with pytest.raises(slices.SliceScaleError):
            slices.runtime_slices_bytes(entries_of(catalog), catalog_id="pilot", release_id="rc-0001", scales={"x1": 1})
