"""Baseline promotion and the baselines-directory check (TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE)."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from src.perf.benchmark_record import COST_ACCOUNTING_VERSION, BenchmarkRecord, ModeRun
from tests.unit.perf.test_benchmark_record import make_record
from tools.perf import baseline_lifecycle as lifecycle

TICKET = "TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE"


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A minimal repo root: one ticket, one divergence."""
    ticket_dir = tmp_path / "agent-working" / "tickets" / "done"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / f"{TICKET}.md").write_text("# ticket\n", encoding="utf-8")
    doc = tmp_path / "docs" / "guidelines"
    doc.mkdir(parents=True)
    (doc / "intentional_divergences.md").write_text("### DEV-021 — a change (TCK-1)\n", encoding="utf-8")
    return tmp_path


@pytest.fixture()
def baselines(tmp_path: Path) -> Path:
    directory = tmp_path / "baselines"
    directory.mkdir()
    return directory


def candidate(**changes: Any) -> Dict[str, Any]:
    """A promotable candidate dict; ``changes`` edits the record's identity/result via dotted keys."""
    record = make_record()
    if "dirty_src" in changes:
        record = dataclasses.replace(record, identity=dataclasses.replace(record.identity, engine=dataclasses.replace(record.identity.engine, dirty_src=changes["dirty_src"])))
    if "modes" in changes:
        record = dataclasses.replace(record, result=dataclasses.replace(record.result, runtime_mode_sequence=changes["modes"]))
    if "cost" in changes:
        record = dataclasses.replace(record, result=dataclasses.replace(record.result, cost_accounting_version=changes["cost"]))
    return record.to_dict()


def promote(data: Dict[str, Any], baselines: Path, repo: Path, cause: Optional[str] = TICKET, name: str = "idle_100_local") -> Path:
    return lifecycle.promote(data, name, cause, baselines, "unit", repo)


def listing(directory: Path) -> Dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir())}


# ── refusals ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "data, code",
    [
        (candidate(dirty_src=True), "dirty_src"),
        (candidate(modes=(ModeRun("NORMAL", 10), ModeRun("DEGRADED", 10))), "mode_not_normal"),
        (candidate(modes=()), "mode_sequence_empty"),
        (candidate(cost=None), "cost_accounting_version_missing"),
        (candidate(cost="DEV-016"), "cost_accounting_version_stale"),
    ],
)
def test_a_bad_candidate_is_refused_with_a_named_reason_and_nothing_is_written(data, code, baselines, repo, capsys) -> None:
    before = listing(baselines)
    with pytest.raises(ValueError, match=code):
        promote(data, baselines, repo)
    assert listing(baselines) == before == {}


@pytest.mark.parametrize(
    "cause, code",
    [(None, "no_cause"), ("", "no_cause"), ("because", "no_cause"), ("TCK-20260101-NOT-A-TICKET", "unknown_cause"), ("DEV-999", "unknown_cause")],
)
def test_a_missing_or_unknown_cause_is_refused(cause, code, baselines, repo) -> None:
    with pytest.raises(ValueError, match=code):
        promote(candidate(), baselines, repo, cause=cause)
    assert listing(baselines) == {}


@pytest.mark.parametrize("cause", [TICKET, "DEV-021", "PR #483", "PR 483", "#483"])
def test_a_ticket_a_divergence_or_a_pull_request_is_an_accepted_cause(cause, baselines, repo) -> None:
    assert promote(candidate(), baselines, repo, cause=cause).exists()


def test_every_reason_is_reported_together(baselines, repo) -> None:
    with pytest.raises(ValueError) as caught:
        promote(candidate(dirty_src=True, modes=(ModeRun("SURVIVAL", 3),), cost=None), baselines, repo, cause=None)
    message = str(caught.value)
    for code in ("dirty_src", "mode_not_normal", "cost_accounting_version_missing", "no_cause"):
        assert f"REFUSED: {code}:" in message


def test_an_invalid_candidate_and_a_bad_name_are_refused(baselines, repo) -> None:
    with pytest.raises(ValueError, match="invalid_candidate"):
        promote({"schema_version": "1.0"}, baselines, repo)
    with pytest.raises(ValueError, match="bad_name"):
        promote(candidate(), baselines, repo, name="../escape")
    assert listing(baselines) == {}


# ── versioned promotion ───────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_the_first_promotion_writes_version_one_and_records_the_cause(baselines, repo) -> None:
    path = promote(candidate(), baselines, repo)
    assert path.name == "idle_100_local.v0001.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    record = BenchmarkRecord.from_dict(data)  # the promotion object is ignored by from_dict
    assert record.identity.baseline_ref is None
    assert data["promotion"]["cause"] == {"kind": "ticket", "id": TICKET}
    assert data["promotion"]["before"] is None
    assert data["promotion"]["after"]["identity"] == record.to_dict()["identity"]
    assert lifecycle.check(baselines) == []


def test_a_second_promotion_is_a_new_version_and_leaves_the_first_byte_identical(baselines, repo) -> None:
    first = promote(candidate(), baselines, repo)
    first_bytes = first.read_bytes()
    second = promote(candidate(), baselines, repo, cause="DEV-021")
    assert second.name == "idle_100_local.v0002.json"
    assert first.read_bytes() == first_bytes
    data = json.loads(second.read_text(encoding="utf-8"))
    ref = BenchmarkRecord.from_dict(data).identity.baseline_ref
    assert ref is not None and ref.id == "idle_100_local.v0001"
    assert ref.record_digest == lifecycle.record_digest(BenchmarkRecord.from_dict(json.loads(first_bytes)))
    promotion = data["promotion"]
    assert promotion["cause"] == {"kind": "divergence", "id": "DEV-021"}
    assert promotion["before"]["file"] == first.name
    assert promotion["before"]["identity"] == json.loads(first_bytes)["identity"]
    assert promotion["after"]["identity"]["baseline_ref"]["id"] == "idle_100_local.v0001"
    assert lifecycle.check(baselines) == []


def test_baselines_with_different_names_version_independently(baselines, repo) -> None:
    promote(candidate(), baselines, repo, name="idle_100_local")
    assert promote(candidate(), baselines, repo, name="idle_100_concurrent").name == "idle_100_concurrent.v0001.json"


def test_an_existing_version_is_never_overwritten(baselines, repo, monkeypatch) -> None:
    promote(candidate(), baselines, repo)
    monkeypatch.setattr(lifecycle, "version_files", lambda *_: [])  # a racing writer: the next version looks free but is taken
    with pytest.raises(FileExistsError):
        promote(candidate(), baselines, repo)


# ── check() ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def test_the_committed_baselines_directory_passes_and_matches_the_allowlist() -> None:
    assert lifecycle.check() == []
    committed = {p.name for p in lifecycle.DEFAULT_BASELINES_DIR.glob("*.json")}
    assert committed <= lifecycle.LEGACY_TRIPWIRE_REFERENCES | {n for n in committed if lifecycle._VERSIONED_RE.match(n)}
    assert len(lifecycle.LEGACY_TRIPWIRE_REFERENCES) == 15


def test_a_file_that_is_neither_a_record_nor_listed_fails(baselines) -> None:
    (baselines / "mystery.json").write_text(json.dumps({"profile": "X", "avg_tick_compute_ms": 1.0}), encoding="utf-8")
    problems = lifecycle.check(baselines)
    assert len(problems) == 1 and "mystery.json" in problems[0]


def test_a_listed_legacy_file_passes_without_being_a_record(baselines) -> None:
    (baselines / "idle_100_local.json").write_text(json.dumps({"profile": "PERF_1GB_LOCAL"}), encoding="utf-8")
    assert lifecycle.check(baselines) == []


def test_a_valid_unversioned_record_passes(baselines) -> None:
    (baselines / "fresh.json").write_text(json.dumps(candidate()), encoding="utf-8")
    assert lifecycle.check(baselines) == []


def test_editing_an_earlier_version_breaks_the_chain(baselines, repo) -> None:
    first = promote(candidate(), baselines, repo)
    promote(candidate(), baselines, repo)
    data = json.loads(first.read_text(encoding="utf-8"))
    data["result"]["latency_ms"]["avg"] = 999.0
    first.write_text(json.dumps(data), encoding="utf-8")
    assert any("chain is broken" in p for p in lifecycle.check(baselines))


def test_a_version_without_its_predecessor_or_its_cause_fails(baselines, repo) -> None:
    first = promote(candidate(), baselines, repo)
    second = promote(candidate(), baselines, repo)
    first.unlink()
    assert any("previous version" in p for p in lifecycle.check(baselines))
    data = json.loads(second.read_text(encoding="utf-8"))
    del data["promotion"]
    second.write_text(json.dumps(data), encoding="utf-8")
    assert any("promotion object" in p for p in lifecycle.check(baselines))


# ── CLI ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────


def run_cli(*args: str) -> int:
    return lifecycle.main(list(args))


def test_the_cli_exit_codes(tmp_path, baselines, repo, capsys) -> None:
    good, dirty = tmp_path / "good.json", tmp_path / "dirty.json"
    good.write_text(json.dumps(candidate()), encoding="utf-8")
    dirty.write_text(json.dumps(candidate(dirty_src=True)), encoding="utf-8")
    common = ["--name", "idle_100_local", "--baselines-dir", str(baselines), "--repo-root", str(repo)]
    assert run_cli("promote", "--candidate", str(dirty), "--cause", TICKET, *common) == 2
    assert "REFUSED: dirty_src:" in capsys.readouterr().err and listing(baselines) == {}
    assert run_cli("promote", "--candidate", str(good), *common) == 2  # no cause
    assert run_cli("promote", "--candidate", str(tmp_path / "missing.json"), "--cause", TICKET, *common) == 1
    assert run_cli("promote", "--candidate", str(good), "--cause", TICKET, *common) == 0
    assert "PROMOTED:" in capsys.readouterr().out
    assert run_cli("check", "--baselines-dir", str(baselines)) == 0


def test_the_cost_accounting_constant_is_what_a_current_record_carries() -> None:
    assert candidate()["result"]["cost_accounting_version"] == COST_ACCOUNTING_VERSION
