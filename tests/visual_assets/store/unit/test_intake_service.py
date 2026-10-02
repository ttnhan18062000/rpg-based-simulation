"""intake / review / list / show: idempotence, immutability, write confinement, review gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.visual_assets.store import builders as b
from tests.visual_assets.store.unit.conftest import snapshot
from visual_assets.store import config
from visual_assets.store.contracts import canonical_json, parse_record
from visual_assets.store.contracts.base import IntakeVerdict
from visual_assets.store.contracts.intake import IntakeFindingCode as Code
from visual_assets.store.contracts.intake import IntakeResult
from visual_assets.store.errors import IntakeError
from visual_assets.store.intake import intake, list_results, quarantine, review, show

NOW = "2026-01-01T00:00:00Z"
LATER = "2026-02-02T00:00:00Z"


@pytest.fixture
def pkg(tmp_path):
    package, source, preview = b.good_files(tags=1)
    return b.write_dir(tmp_path / "pkg", package, source, preview)


@pytest.fixture
def bad_pkg(tmp_path):
    return b.write_dir(tmp_path / "bad", *b.bad_files())


@pytest.fixture
def untouched(tmp_path):
    """Snapshots of everything intake must never modify: the real tracked catalog and a stand-in workspace."""
    workspace = tmp_path / "workspace"
    (workspace / "sprites" / "x").mkdir(parents=True)
    (workspace / "sprites" / "x" / "r0001.aseprite").write_bytes(b"sprite")
    state = lambda: (snapshot(config.CATALOG_ROOT), snapshot(workspace))  # noqa: E731
    return state, state()


def test_a_passing_package_is_staged_and_recorded(pkg, roots, untouched):
    state, before = untouched
    result = intake(pkg, created_at=NOW)
    assert result.verdict is IntakeVerdict.PASSED and result.findings == ()
    assert result.intake_id.startswith("in-") and len(result.intake_id) == 19
    staged = roots[0] / result.intake_id
    on_disk = parse_record(IntakeResult, (staged / "intake_result.json").read_bytes())
    assert on_disk == result and canonical_json(result) == (staged / "intake_result.json").read_bytes()
    for name in quarantine.STAGED_NAMES:
        assert (staged / name).read_bytes() == (pkg / name).read_bytes()
    assert [f.name for f in result.staged_files] == list(quarantine.STAGED_NAMES)
    assert state() == before  # tracked catalog and workspace byte-identical
    assert not roots[1].exists()  # intake never touches the review area


def test_a_defective_package_is_quarantined_with_findings(bad_pkg, roots):
    result = intake(bad_pkg, created_at=NOW)
    assert result.verdict is IntakeVerdict.QUARANTINED
    assert Code.SOURCE_BAD_MAGIC in [f.code for f in result.findings]
    assert (roots[0] / result.intake_id / "intake_result.json").is_file()  # the evidence is kept


def test_an_unparseable_package_has_no_candidate_id(tmp_path, roots):
    _, source, preview = b.good_files()
    directory = b.write_dir(tmp_path / "junk", b"{not json", source, preview)
    result = intake(directory, created_at=NOW)
    assert result.candidate_id == "UNAVAILABLE" and result.verdict is IntakeVerdict.QUARANTINED
    assert Code.PACKAGE_UNREADABLE in [f.code for f in result.findings]


def test_resubmitting_an_identical_package_returns_the_same_result_and_writes_nothing(pkg, roots):
    first = intake(pkg, created_at=NOW)
    staged = roots[0] / first.intake_id
    before = snapshot(roots[0])
    mtimes = {p.name: p.stat().st_mtime_ns for p in staged.iterdir()}
    second = intake(pkg, created_at=LATER)  # a later timestamp must not rewrite the recorded one
    assert second == first and second.created_at == NOW
    assert snapshot(roots[0]) == before
    assert {p.name: p.stat().st_mtime_ns for p in staged.iterdir()} == mtimes


def test_an_existing_result_is_never_overwritten(pkg, roots):
    first = intake(pkg, created_at=NOW)
    result_path = roots[0] / first.intake_id / "intake_result.json"
    original = result_path.read_bytes()
    for _ in range(3):
        intake(pkg, created_at=LATER)
    assert result_path.read_bytes() == original


def test_the_same_package_json_with_different_bytes_is_a_different_intake(pkg, roots):
    """asset-planner R1: wrong bytes under a genuine package.json must not take the id for the genuine package."""
    package = (pkg / "package.json").read_bytes()
    genuine_preview = (pkg / "preview.png").read_bytes()
    (pkg / "preview.png").write_bytes(genuine_preview + b"\x00")  # same package.json, wrong preview bytes
    wrong = intake(pkg, created_at=NOW)
    assert wrong.verdict is IntakeVerdict.QUARANTINED and Code.PREVIEW_HASH_MISMATCH in [f.code for f in wrong.findings]
    (pkg / "preview.png").write_bytes(genuine_preview)  # now the genuine package arrives
    right = intake(pkg, created_at=LATER)
    assert right.verdict is IntakeVerdict.PASSED and right.intake_id != wrong.intake_id
    assert (pkg / "package.json").read_bytes() == package
    results, problems = list_results()
    assert {r.intake_id for r in results} == {wrong.intake_id, right.intake_id} and problems == []
    assert show(wrong.intake_id) == wrong  # the first record is untouched


def test_an_id_collision_is_refused_and_writes_nothing(pkg, tmp_path, roots, monkeypatch):
    from visual_assets.store.intake import service

    monkeypatch.setattr(service, "_intake_id", lambda files: "in-0123456789abcdef")
    first = intake(pkg, created_at=NOW)
    other = b.write_dir(tmp_path / "other", *b.bad_files())
    before = snapshot(roots[0])
    with pytest.raises(IntakeError) as err:
        intake(other, created_at=LATER)
    assert err.value.code == "intake_id_collision"
    assert snapshot(roots[0]) == before and show(first.intake_id) == first


def test_the_intake_id_is_derived_from_all_three_files(pkg, tmp_path, roots):
    a = intake(pkg, created_at=NOW)
    same = b.write_dir(tmp_path / "same", (pkg / "package.json").read_bytes(), (pkg / "source.aseprite").read_bytes(),
                       (pkg / "preview.png").read_bytes())
    assert intake(same, created_at=LATER).intake_id == a.intake_id  # identical files, identical id
    import hashlib
    from visual_assets.store.intake.validator import file_hash

    joined = "\n".join(file_hash((pkg / n).read_bytes()) for n in ("package.json", "source.aseprite", "preview.png"))
    assert a.intake_id == "in-" + hashlib.sha256(joined.encode()).hexdigest()[:16]
    for name, new in (("source.aseprite", b"x"), ("preview.png", b"y")):
        changed = b.write_dir(tmp_path / f"c-{name}", (pkg / "package.json").read_bytes(), (pkg / "source.aseprite").read_bytes(),
                              (pkg / "preview.png").read_bytes())
        (changed / name).write_bytes(new)
        assert intake(changed, created_at=LATER).intake_id != a.intake_id, name


def test_a_killed_process_leaves_only_an_ignored_temporary_directory(pkg, roots):
    """asset-planner R2: staging is atomic, so a kill never blocks a later intake of the same package."""
    quarantine_root = roots[0]
    quarantine_root.mkdir(parents=True)
    leftover = quarantine_root / f"{quarantine.TEMP_PREFIX}in-0123456789abcdef-deadbeef"
    leftover.mkdir()
    (leftover / "package.json").write_bytes(b"half")  # what a killed writer would leave behind
    assert list_results() == ([], [])  # ignored by list
    for fn in (show, review):
        with pytest.raises(IntakeError) as err:
            fn(leftover.name)
        assert err.value.code == "bad_intake_id"
    result = intake(pkg, created_at=NOW)  # a fresh intake of the package succeeds
    assert result.verdict is IntakeVerdict.PASSED
    assert leftover.is_dir() and (leftover / "package.json").read_bytes() == b"half"  # never touched
    assert [r.intake_id for r in list_results()[0]] == [result.intake_id]
    assert review(result.intake_id).is_dir()
    import shutil

    shutil.rmtree(leftover)  # safe to delete
    assert show(result.intake_id) == result


def test_the_final_directory_only_ever_appears_complete(pkg, roots, monkeypatch):
    seen: list[list[str]] = []
    real_rename = quarantine.os.rename

    def spy(src, dst):
        seen.append(sorted(p.name for p in Path(src).iterdir()))  # what the directory holds at the moment it is published
        real_rename(src, dst)

    monkeypatch.setattr(quarantine.os, "rename", spy)
    intake(pkg, created_at=NOW)
    assert seen == [["intake_result.json", "package.json", "preview.png", "source.aseprite"]]


def test_a_failed_publish_leaves_no_temporary_directory(pkg, roots, monkeypatch):
    def boom(src, dst):
        raise OSError("cross-device")

    monkeypatch.setattr(quarantine.os, "rename", boom)
    from visual_assets.store.errors import StageError

    with pytest.raises(StageError):
        intake(pkg, created_at=NOW)
    assert list(roots[0].iterdir()) == []


def test_an_oversize_preview_has_its_own_finding_code(monkeypatch):
    package, source, preview = b.good_files()
    monkeypatch.setattr(config, "MAX_PREVIEW_DIM", 64)  # the 128x128 preview is now over the bound
    from visual_assets.store.intake.validator import validate

    codes = [f.code for f in validate(package, source, preview).findings]
    assert Code.PREVIEW_OUT_OF_BOUNDS in codes and Code.PNG_MALFORMED not in codes


def test_a_stage_directory_without_a_result_is_reported_not_adopted_or_deleted(pkg, roots):
    result = intake(pkg, created_at=NOW)
    (roots[0] / result.intake_id / "intake_result.json").unlink()
    with pytest.raises(IntakeError) as err:
        intake(pkg, created_at=LATER)
    assert err.value.code == "incomplete_stage"
    assert (roots[0] / result.intake_id / "package.json").is_file()  # nothing we did not finish is deleted


def test_a_failed_write_removes_the_partial_stage(pkg, roots, monkeypatch):
    real = quarantine.write_new
    calls = {"n": 0}

    def flaky(path, data):
        calls["n"] += 1
        if calls["n"] == 3:
            raise OSError("disk full")
        real(path, data)

    monkeypatch.setattr(quarantine, "write_new", flaky)
    with pytest.raises(OSError):
        intake(pkg, created_at=NOW)
    assert list(roots[0].iterdir()) == []
    monkeypatch.setattr(quarantine, "write_new", real)
    assert intake(pkg, created_at=NOW).verdict is IntakeVerdict.PASSED  # and a retry works


@pytest.mark.parametrize("bad", ["", "2026-01-01", "2026-02-30T00:00:00Z", "2026-01-01T00:00:00+00:00", None, 5])
def test_created_at_must_be_a_real_utc_timestamp(pkg, roots, bad):
    with pytest.raises(IntakeError) as err:
        intake(pkg, created_at=bad)
    assert err.value.code == "bad_created_at"
    assert not roots[0].exists()


def test_library_code_never_reads_the_clock():
    import ast

    for path in Path(config.__file__).parent.rglob("*.py"):
        if path.name == "cli.py":
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, (ast.Import, ast.ImportFrom)) else []
            module = node.module if isinstance(node, ast.ImportFrom) else None
            assert "datetime" not in names and module != "datetime" and "time" not in names, path


# --------------------------------------------------------------------------- review


def test_review_exports_the_preview_and_a_summary(pkg, roots, untouched):
    state, before = untouched
    result = intake(pkg, created_at=NOW)
    target = review(result.intake_id)
    assert target == roots[1] / result.intake_id
    assert sorted(p.name for p in target.iterdir()) == ["preview.png", "summary.txt"]
    assert (target / "preview.png").read_bytes() == (pkg / "preview.png").read_bytes()
    text = (target / "summary.txt").read_text()
    assert "NOT adopted" in text and result.intake_id in text and "cand-0123456789abcdef" in text
    assert state() == before


def test_review_is_idempotent_and_refuses_a_changed_review_area(pkg, roots):
    result = intake(pkg, created_at=NOW)
    first = review(result.intake_id)
    snap = snapshot(roots[1])
    assert review(result.intake_id) == first and snapshot(roots[1]) == snap
    (first / "summary.txt").write_text("tampered")
    with pytest.raises(IntakeError) as err:
        review(result.intake_id)
    assert err.value.code == "review_exists_differs"
    (first / "summary.txt").unlink()  # a half-removed review directory is refused too, never silently repaired
    with pytest.raises(IntakeError):
        review(result.intake_id)


def test_review_refuses_a_quarantined_intake(bad_pkg, roots):
    result = intake(bad_pkg, created_at=NOW)
    with pytest.raises(IntakeError) as err:
        review(result.intake_id)
    assert err.value.code == "not_passed"
    assert not roots[1].exists()


@pytest.mark.parametrize("bad", ["in-0000000000000000", "nope", "", "../x", "in-" + "g" * 16, "IN-0000000000000000", "in-0000000000000000/.."])
def test_review_and_show_refuse_unknown_or_malformed_ids(roots, bad):
    for fn in (review, show):
        with pytest.raises(IntakeError) as err:
            fn(bad)
        assert err.value.code in {"unknown_intake", "bad_intake_id"}
    assert not roots[1].exists()


@pytest.mark.parametrize("name", ["package.json", "source.aseprite", "preview.png"])
def test_review_refuses_when_staged_bytes_no_longer_match(pkg, roots, name):
    result = intake(pkg, created_at=NOW)
    staged = roots[0] / result.intake_id / name
    staged.write_bytes(staged.read_bytes() + b"\x00")
    with pytest.raises(IntakeError) as err:
        review(result.intake_id)
    assert err.value.code == "staged_bytes_changed"
    assert not roots[1].exists()


def test_review_refuses_a_symlinked_staged_file(pkg, roots, tmp_path):
    result = intake(pkg, created_at=NOW)
    staged = roots[0] / result.intake_id / "preview.png"
    copy = tmp_path / "copy.png"
    copy.write_bytes(staged.read_bytes())
    staged.unlink()
    staged.symlink_to(copy)
    from visual_assets.store.errors import StageError

    with pytest.raises(StageError):
        review(result.intake_id)
    assert not roots[1].exists()


def test_review_refuses_a_corrupt_result(pkg, roots):
    result = intake(pkg, created_at=NOW)
    (roots[0] / result.intake_id / "intake_result.json").write_text("{}")
    with pytest.raises(IntakeError) as err:
        review(result.intake_id)
    assert err.value.code == "corrupt_result"


def test_review_does_not_follow_a_symlinked_stage_directory(pkg, roots, tmp_path):
    result = intake(pkg, created_at=NOW)
    moved = tmp_path / "moved"
    (roots[0] / result.intake_id).rename(moved)
    (roots[0] / result.intake_id).symlink_to(moved, target_is_directory=True)
    with pytest.raises(IntakeError) as err:
        review(result.intake_id)
    assert err.value.code == "unknown_intake"


# --------------------------------------------------------------------------- list / show


def test_list_and_show_read_quarantine_results_only(pkg, bad_pkg, roots):
    assert list_results() == ([], [])
    one = intake(pkg, created_at=NOW)
    two = intake(bad_pkg, created_at=NOW)
    results, problems = list_results()
    assert {r.intake_id for r in results} == {one.intake_id, two.intake_id} and problems == []
    assert show(one.intake_id) == one and show(two.intake_id) == two


def test_list_reports_unreadable_directories_and_ignores_strangers(pkg, roots):
    one = intake(pkg, created_at=NOW)
    (roots[0] / "in-ffffffffffffffff").mkdir()
    (roots[0] / "stray.txt").write_text("x")
    (roots[0] / "not-an-intake").mkdir()
    results, problems = list_results()
    assert [r.intake_id for r in results] == [one.intake_id] and problems == ["in-ffffffffffffffff"]
