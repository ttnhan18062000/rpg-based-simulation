"""Run the existing EventExtractor unit tests under the recorder plugin, and load/compare/regenerate the committed fixtures."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_DIR = _REPO_ROOT / "tests" / "fixtures" / "event_extractor_characterization"
CORPUS_FIXTURE = FIXTURE_DIR / "unit_corpus.jsonl"
KERNEL_FIXTURE = FIXTURE_DIR / "kernel_runs.jsonl"

# The recorders run in a subprocess with this fixed hash seed. Event order no longer follows the seed (the emit-order fix sorts the set-listing
# events), and ALT_HASH_SEED lets a test prove it: a second recording at another seed must be byte-identical.
_HASH_SEED = "0"
ALT_HASH_SEED = "12345"

# (world, seed, ticks): the two seeded kernel scenarios. lifecycle_full_coverage_world exercises lifecycle, biological, social and
# progression diffs; dungeon_crawl adds combat and hazards.
KERNEL_SCENARIOS = (("lifecycle_full_coverage_world", 42, 200), ("dungeon_crawl", 42, 200))

# The three real_kernel tests run a Kernel without audit_mode, so wall-clock governors vary what they see; the kernel scenarios above replace them.
# TestAntiDriftGuards reads extract()'s source, which the recorder's wrapper hides.
_CORPUS_PYTEST_ARGS = (
    "--deselect", "tests/unit/observability/test_event_extractor_agency2.py::TestAntiDriftGuards",
    "-k", "not real_kernel",
)


def run_corpus(hash_seed: str = _HASH_SEED) -> list[dict[str, Any]]:
    """Digest rows for every extract() call made by the existing EventExtractor unit tests."""
    modules = sorted(str(p.relative_to(_REPO_ROOT)) for p in (_REPO_ROOT / "tests" / "unit" / "observability").glob("test_event_extractor_*.py") if p.stem != "test_event_extractor_characterization")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "corpus.jsonl"
        env = {**os.environ, "EXTRACTOR_RECORD_OUT": str(out), "PYTHONPATH": str(_REPO_ROOT), "PYTHONHASHSEED": hash_seed}
        env.pop("EXTRACTOR_RECORD_FULL", None)
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-p", "tests.unit.observability.extractor_characterization.recorder_plugin",
             "-q", "-p", "no:cacheprovider", "-p", "no:randomly", "--basetemp", str(Path(tmp) / "bt"), *_CORPUS_PYTEST_ARGS, *modules],
            cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=300,
        )
        assert out.exists(), f"recorder wrote nothing:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}"
        return load_rows(out)


def run_kernel_scenario(world: str, seed: int, ticks: int, hash_seed: str = _HASH_SEED) -> list[dict[str, Any]]:
    env = {**os.environ, "PYTHONPATH": str(_REPO_ROOT), "PYTHONHASHSEED": hash_seed}
    proc = subprocess.run(
        [sys.executable, "-m", "tests.unit.observability.extractor_characterization.kernel_scenario", world, str(seed), str(ticks)],
        cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    return [json.loads(line) for line in proc.stdout.splitlines() if line.startswith("{")]


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8")


def key(row: dict[str, Any]) -> tuple[str, int]:
    return row["test"], row["call"]


def differences(expected: list[dict[str, Any]], actual: list[dict[str, Any]]) -> list[str]:
    """Every pinned (test, call, config) whose count or digest moved, or whose row vanished. New rows in ``actual`` are not differences."""
    by_key = {key(r): r for r in actual}
    problems: list[str] = []
    for row in expected:
        got = by_key.get(key(row))
        if got is None:
            problems.append(f"missing {key(row)}")
            continue
        if got["mode"] != row["mode"]:
            problems.append(f"{key(row)}: mode {row['mode']} -> {got['mode']}")
        for config, pinned in row["results"].items():
            if got["results"].get(config) != pinned:
                problems.append(f"{key(row)} [{config}]: {pinned} -> {got['results'].get(config)}")
    return problems


def regenerate() -> None:
    """Rewrite both fixtures from the current code. Only for an intentional change of what extract() emits, agreed with rpg-planner."""
    write_rows(CORPUS_FIXTURE, run_corpus())
    kernel_rows: list[dict[str, Any]] = []
    for world, seed, ticks in KERNEL_SCENARIOS:
        kernel_rows.extend(run_kernel_scenario(world, seed, ticks))
    write_rows(KERNEL_FIXTURE, kernel_rows)


if __name__ == "__main__":
    regenerate()
