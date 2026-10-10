"""The committed proof of the last strict local run of the real-Aseprite tests (ADR D10, `TCK-20261010-VISUAL-ASSETS-ASEPRITE-LOCAL-PROOF-RECORD`).

Real Aseprite never runs on a hosted runner, so CI cannot run those tests. Instead `make visual-assets-aseprite-local` writes
`docs/assets/aseprite_local_proof.json` after a clean, strict, complete run: the Aseprite version, the commit it ran on, the counts and a hash over the
files those tests exercise (the guarded set). CI recomputes that hash and fails when a guarded file changed since the record. The record states what
the licence holder ran; it does not authenticate who ran it, and it must never be edited by hand.

Everything here is pure over injected facts (a list of tracked paths, file bytes) so the rules are proven on planted violations without Aseprite.
The guarded set is deliberately broad (all of `store/**` and `drawing/**` minus docs): a record goes stale on any code edit there, which is the
intent, and costs one fresh local run per store change.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
from collections.abc import Iterable, Mapping
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RECORD_PATH = REPO / "docs" / "assets" / "aseprite_local_proof.json"
MAKE_TARGET = "visual-assets-aseprite-local"
RECORD_TYPE = "aseprite_local_proof"
SCHEMA_VERSION = 1
# The marker is built from parts so that this module and its own tests are not "marked" files merely by naming it.
MARKER = "needs_" + "aseprite"
SUPPORT = (
    "tests/visual_assets/conftest.py",
    "tests/visual_assets/strict_aseprite.py",
    "tests/visual_assets/drawing/conftest.py",
    "tests/visual_assets/store/builders.py",
    "tests/visual_assets/store/adoption_support.py",
    "tests/visual_assets/store/runtime_fixture.py",
)
TOOLS = ("tools/visual_assets_aseprite_local.py", "tools/visual_assets_aseprite_proof.py")
GUARDED_TREES = ("visual_assets/drawing/", "visual_assets/store/", "visual_assets/catalog/build-config/")
REFRESH = (
    f"the only fix is a real `make {MAKE_TARGET}` run on the licence holder's machine (ADR D10), which rewrites "
    "docs/assets/aseprite_local_proof.json; never edit that record by hand"
)
RECORD_KEYS = frozenset({
    "record_type", "schema_version", "make_target", "run_commit", "run_at_utc", "aseprite_version", "strict",
    "counts", "release_rebuild", "guarded_hash", "guarded_files",
})
COUNT_KEYS = frozenset({"passed", "failed", "errors", "skipped", "total"})
REBUILD_KEYS = frozenset({"release", "entries", "identical", "bytes_differ_pixels_match"})
# pytest options that cannot narrow the selection; anything else in extra arguments or PYTEST_ADDOPTS means "not the full target".
HARMLESS_OPTIONS = frozenset({"-q", "-qq", "-v", "-vv", "-s", "--tb=short", "--tb=long", "--tb=line", "--tb=no", "-p", "no:cacheprovider", "-ra", "--color=no", "--color=yes"})


def is_guarded(path: str, marked_tests: Iterable[str] = ()) -> bool:
    if path.endswith(".md") or "__pycache__" in path:
        return False
    if path.startswith(GUARDED_TREES):
        return True
    return path in SUPPORT or path in TOOLS or path in set(marked_tests)


def guarded_paths(tracked: Iterable[str], marked_tests: Iterable[str]) -> list[str]:
    marked = set(marked_tests)
    return sorted({p for p in tracked if is_guarded(p, marked)})


def file_sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def guarded_hash(files: Iterable[Mapping[str, str]]) -> str:
    lines = "".join(f"{f['path']}\0{f['sha256'].split(':', 1)[1]}\n" for f in sorted(files, key=lambda f: f["path"]))
    return file_sha256(lines.encode())


def compare(recorded: Iterable[Mapping[str, str]], current: Iterable[Mapping[str, str]]) -> tuple[list[str], list[str], list[str]]:
    """(changed, added, removed) paths of `current` against `recorded`."""
    before = {f["path"]: f["sha256"] for f in recorded}
    after = {f["path"]: f["sha256"] for f in current}
    return (
        sorted(p for p in before.keys() & after.keys() if before[p] != after[p]),
        sorted(after.keys() - before.keys()),
        sorted(before.keys() - after.keys()),
    )


def staleness_message(changed: list[str], added: list[str], removed: list[str]) -> str:
    named = [f"changed: {changed}" if changed else "", f"added: {added}" if added else "", f"removed: {removed}" if removed else ""]
    return f"the guarded files differ from the committed proof record ({'; '.join(n for n in named if n)}); {REFRESH}"


def record_problems(record: object) -> list[str]:
    """Everything wrong with a proof record's shape and internal consistency (empty = a clean, strict, complete run)."""
    if not isinstance(record, dict):
        return ["the record is not a JSON object"]
    problems = []
    if set(record) != RECORD_KEYS:
        return [f"record keys differ: missing {sorted(RECORD_KEYS - set(record))}, unexpected {sorted(set(record) - RECORD_KEYS)}"]
    if (record["record_type"], record["schema_version"], record["make_target"]) != (RECORD_TYPE, SCHEMA_VERSION, MAKE_TARGET):
        problems.append("record_type, schema_version or make_target is not the expected value")
    if record["strict"] is not True:
        problems.append("the run was not strict")
    counts = record["counts"]
    if not isinstance(counts, dict) or set(counts) != COUNT_KEYS or not all(type(v) is int and v >= 0 for v in counts.values()):
        problems.append("counts must be exactly passed, failed, errors, skipped, total (non-negative integers)")
    else:
        if counts["failed"] or counts["errors"] or counts["skipped"]:
            problems.append(f"the run was not clean: {counts}")
        if counts["total"] <= 0 or counts["passed"] != counts["total"]:
            problems.append(f"passed must equal a positive total: {counts}")
    rebuild = record["release_rebuild"]
    if not isinstance(rebuild, dict) or set(rebuild) != REBUILD_KEYS or not isinstance(rebuild["release"], str) or not all(type(rebuild[k]) is int and rebuild[k] >= 0 for k in REBUILD_KEYS - {"release"}):
        problems.append("release_rebuild must be exactly release, entries, identical, bytes_differ_pixels_match")
    elif rebuild["entries"] <= 0 or rebuild["identical"] + rebuild["bytes_differ_pixels_match"] != rebuild["entries"]:
        problems.append(f"the release rebuild does not account for every entry: {rebuild}")
    for key in ("run_commit", "run_at_utc", "aseprite_version"):
        if not isinstance(record[key], str) or not record[key].strip():
            problems.append(f"{key} must be a non-empty string")
    files = record["guarded_files"]
    shaped = isinstance(files, list) and bool(files) and all(isinstance(f, dict) and set(f) == {"path", "sha256"} and all(isinstance(v, str) for v in f.values()) for f in files)
    if not shaped:
        problems.append("guarded_files must be a non-empty list of {path, sha256}")
    elif guarded_hash(files) != record["guarded_hash"]:
        problems.append("guarded_hash does not match guarded_files")
    elif [f["path"] for f in files] != sorted(f["path"] for f in files) or len({f["path"] for f in files}) != len(files):
        problems.append("guarded_files must be sorted and unique")
    return problems


def build_record(*, run_commit: str, run_at_utc: str, aseprite_version: str, counts: Mapping[str, int], rebuild: Mapping[str, object], files: list[dict[str, str]]) -> dict:
    ordered = sorted(files, key=lambda f: f["path"])
    return {
        "record_type": RECORD_TYPE, "schema_version": SCHEMA_VERSION, "make_target": MAKE_TARGET, "run_commit": run_commit,
        "run_at_utc": run_at_utc, "aseprite_version": aseprite_version, "strict": True, "counts": dict(counts),
        "release_rebuild": dict(rebuild), "guarded_hash": guarded_hash(ordered), "guarded_files": ordered,
    }


def dumps(record: dict) -> str:
    return json.dumps(record, sort_keys=True, indent=2) + "\n"


def selection_problem(extra_args: Iterable[str], env: Mapping[str, str]) -> str | None:
    """Why this run is not the full make target (so it must not write a record), or None. A subset run could otherwise produce a clean strict record."""
    extra = [a for a in extra_args if a not in HARMLESS_OPTIONS]
    if extra:
        return f"pytest was given extra arguments {extra} (a selection such as -k, -m, a path or a node id narrows the run)"
    try:
        addopts = shlex.split(env.get("PYTEST_ADDOPTS", ""))
    except ValueError:
        return "PYTEST_ADDOPTS cannot be parsed, so it may carry a selection"
    unknown = [a for a in addopts if a not in HARMLESS_OPTIONS]
    if unknown:
        return f"PYTEST_ADDOPTS carries {unknown}, which may select a subset"
    return None


# ---- the file-system side (thin; the rules above are what is tested) ----

def tracked_files(repo: Path = REPO) -> list[str]:
    """`git ls-files`, so CI and the local run see the same set; a plain walk when this is not a git checkout."""
    done = subprocess.run(["git", "ls-files", "-z"], cwd=repo, capture_output=True, check=False)
    if done.returncode == 0 and done.stdout:
        return sorted(p for p in done.stdout.decode().split("\0") if p)
    found = []
    for root, dirs, names in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", ".venv"}]
        found += [os.path.relpath(os.path.join(root, n), repo) for n in names]
    return sorted(found)


def marked_test_files(paths: Iterable[str], repo: Path = REPO) -> list[str]:
    out = []
    for path in paths:
        if path.startswith("tests/visual_assets/") and path.endswith(".py"):
            try:
                if MARKER in (repo / path).read_text(encoding="utf-8", errors="replace"):
                    out.append(path)
            except OSError:
                continue
    return out


def current_files(repo: Path = REPO) -> list[dict[str, str]]:
    tracked = tracked_files(repo)
    paths = guarded_paths(tracked, marked_test_files(tracked, repo))
    return [{"path": p, "sha256": file_sha256((repo / p).read_bytes())} for p in paths if (repo / p).is_file()]


def load_record(path: Path = RECORD_PATH) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def describe(repo: Path = REPO, path: Path = RECORD_PATH) -> str:
    """One report sentence about the committed record for the CI job summary; never raises."""
    try:
        record = load_record(path)
        if record is None or record_problems(record):
            return "proof record: missing or invalid"
        changed, added, removed = compare(record["guarded_files"], current_files(repo))
        state = "DIFFER" if changed or added or removed else "match"
        return f"proof record: {record['run_commit'][:9]}, {record['aseprite_version']}, run {record['run_at_utc']}, guarded files {state}"
    except Exception as exc:  # a reporting step never becomes a second CI failure
        return f"proof record: unreadable ({exc})"
