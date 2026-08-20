#!/usr/bin/env python3
"""Live LoC/churn/dependency baseline snapshot, reproducing the shape of
`docs/audits/D24_codebase_health_observatory.md` §C's "Current Health Baseline"
table on demand, computed fresh from the repo's real current state every run.

Built for TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET, item 1 of
`TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC`. D24 §C's own numbers are
a one-time, now-stale snapshot (measured before `src_legacy/`/`tests_legacy/`
deletion, several test-file relocations, and dependency cleanup) — this module
never hardcodes or echoes those numbers; every value below is recomputed from
`git ls-files`/`git log` and the live filesystem each time it runs.

**Churn exclusion (the one non-negotiable requirement this tool exists to
satisfy)**: `agent-monitoring/*.jsonl`, `tickets/working_log.csv`, and
`docs/REGISTRY.yaml` are append-only bookkeeping files touched on nearly every
ticket close (405/263/248/248/198 raw commit-touches respectively per D24 §D) —
a naive churn/hotspot measurement is dominated by this expected process noise,
not real architectural instability signal. `compute_churn_lines_changed` below
excludes them via a real `git log --shortstat -- . ':!path' ...` pathspec
exclusion, so their history is never walked into the computation in the first
place — not a post-hoc filter over already-collected results. Do not swap this
for a filter-after-the-fact; that would still pay the cost of walking (and risk
of double-counting) the excluded files' commit history.

`docs/REGISTRY.yaml` itself is still counted in the plain *size* metric (its own
row in the table, matching D24 §C's own inclusion) — the exclusion is specific
to the churn dimension only, per investigation.md's explicit clarification.

"Docs (.md)" counts only `docs/**/*.md` (not the whole repo) — a repo-wide `*.md`
count is dominated by `stored_artifacts/`/`tickets/` process-doc corpora (6,230
repo-wide vs. 806 under `docs/` alone at the time this was written), which is not
what D24 §C's own ~776 figure was measuring.

"Test subdirectories" counts unique parent directories of git-tracked
`tests/**/*.py` files (excluding the `tests/` root itself) — deliberately
git-tracked-content-based, not a raw filesystem walk, because the filesystem
has stale near-empty directories left over from history (e.g. `tests/ai/`
contains only a `__pycache__/`, no tracked source) that a raw `find` would
wrongly count as real test structure.

"Dead bytecode files" reproduces D24 §A's finding (`src_legacy/`/`tests_legacy/`
contained only `.pyc` remnants with zero surviving `.py` source) generically: any
`.pyc` file anywhere in the live tree whose corresponding `.py` source does not
exist. Normal `__pycache__/foo.cpython-312.pyc` next to a live `foo.py` is not
dead; nothing produced by ordinary `python -m compileall` on live source counts.

"Declared-but-unused core dependencies" mirrors D23's own methodology exactly
(`docs/audits/D23_architecture_resilience.md` line 87): a repo-wide grep (not
scoped to `src/`) for `import <name>` / `from <name>`, over every git-tracked
`.py` file, not just `src/`'s — D23 found `pika`/`confluent-kafka` this way, and
this tool's own live run found `python-json-logger`'s only user lives in
`scripts/turbo_run.py`, outside `src/` — confirming a `src/`-only scope would
have produced a false positive.
"""

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TOOLS_DIR.parent

CHURN_EXCLUDE_PATHSPECS = [
    ":!agent-monitoring/*.jsonl",
    ":!tickets/working_log.csv",
    ":!docs/REGISTRY.yaml",
]

CORE_DEPENDENCY_IMPORT_OVERRIDES = {
    "python-json-logger": "pythonjsonlogger",
}

_SKIP_DIR_NAMES = {
    ".git", ".venv", "venv", "node_modules", ".pytest_cache",
    "build", "dist", "__pycache__",
}


def _run_git(args: list, repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def _git_ls_files(repo_root: Path, pathspec: str) -> list:
    output = _run_git(["ls-files", pathspec], repo_root)
    return [line for line in output.splitlines() if line]


def measure_py_tree(repo_root: Path, prefix: str) -> tuple:
    """Return (loc, file_count) for git-tracked `<prefix>*.py` files.

    Mirrors D24 §B/§C's methodology of counting `.py` files/lines only (not
    every file under the prefix).
    """
    files = _git_ls_files(repo_root, f"{prefix}*.py")
    loc = 0
    for rel_path in files:
        path = repo_root / rel_path
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                loc += sum(1 for _ in handle)
        except OSError:
            continue
    return loc, len(files)


def count_top_level_src_packages(repo_root: Path) -> int:
    files = _git_ls_files(repo_root, "src/*")
    packages = set()
    for rel_path in files:
        parts = rel_path.split("/")
        if len(parts) > 2:
            packages.add(parts[1])
    return len(packages)


def count_test_subdirectories(repo_root: Path) -> int:
    files = _git_ls_files(repo_root, "tests/*.py")
    subdirs = set()
    for rel_path in files:
        parts = rel_path.split("/")
        if len(parts) > 2:
            subdirs.add("/".join(parts[:-1]))
    return len(subdirs)


def count_commits(repo_root: Path) -> int:
    output = _run_git(["log", "--oneline"], repo_root)
    return len([line for line in output.splitlines() if line])


def count_docs(repo_root: Path) -> int:
    return len(_git_ls_files(repo_root, "docs/*.md"))


def measure_registry_size(repo_root: Path) -> tuple:
    registry_path = repo_root / "docs" / "REGISTRY.yaml"
    if not registry_path.exists():
        return 0, 0
    size_bytes = registry_path.stat().st_size
    with registry_path.open("r", encoding="utf-8", errors="ignore") as handle:
        line_count = sum(1 for _ in handle)
    return size_bytes, line_count


def find_dead_bytecode_files(repo_root: Path) -> int:
    dead = 0
    for pyc_path in repo_root.rglob("*.pyc"):
        if any(part in _SKIP_DIR_NAMES for part in pyc_path.parts[:-1] if part != "__pycache__"):
            continue
        if pyc_path.parent.name == "__pycache__":
            module_name = pyc_path.name.split(".")[0]
            expected_source = pyc_path.parent.parent / f"{module_name}.py"
        else:
            expected_source = pyc_path.with_suffix(".py")
        if not expected_source.exists():
            dead += 1
    return dead


def _dependency_import_name(spec: str) -> str:
    name = re.split(r"[<>=!~;\[\s]", spec, maxsplit=1)[0].strip()
    return CORE_DEPENDENCY_IMPORT_OVERRIDES.get(name, name.replace("-", "_"))


def _parse_core_dependencies(repo_root: Path) -> list:
    pyproject_path = repo_root / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return list(data.get("project", {}).get("dependencies", []))


def find_unused_core_dependencies(repo_root: Path) -> list:
    specs = _parse_core_dependencies(repo_root)
    py_files = _git_ls_files(repo_root, "*.py")
    combined_source = []
    for rel_path in py_files:
        path = repo_root / rel_path
        try:
            combined_source.append(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    haystack = "\n".join(combined_source)

    unused = []
    for spec in specs:
        import_name = _dependency_import_name(spec)
        pattern = re.compile(
            r"(?m)^\s*(?:import|from)\s+" + re.escape(import_name) + r"\b"
        )
        if not pattern.search(haystack):
            unused.append(import_name)
    return unused


def compute_churn_lines_changed(repo_root: Path, exclude_pathspecs: list = None) -> int:
    """Total insertions+deletions across full history, excluding bookkeeping paths.

    Uses a real git pathspec exclusion (`-- . ':!path' ...`), not a post-hoc
    filter — the excluded files' commit history is never walked at all.
    """
    if exclude_pathspecs is None:
        exclude_pathspecs = CHURN_EXCLUDE_PATHSPECS
    args = ["log", "--shortstat", "--pretty=format:", "--", "."] + exclude_pathspecs
    output = _run_git(args, repo_root)
    total = 0
    for line in output.splitlines():
        line = line.strip()
        if not line or "changed" not in line:
            continue
        insertions = re.search(r"(\d+) insertion", line)
        deletions = re.search(r"(\d+) deletion", line)
        if insertions:
            total += int(insertions.group(1))
        if deletions:
            total += int(deletions.group(1))
    return total


def build_report(repo_root: Path) -> dict:
    source_loc, source_files = measure_py_tree(repo_root, "src/")
    test_loc, test_files = measure_py_tree(repo_root, "tests/")
    ratio = (test_loc / source_loc) if source_loc else 0.0
    registry_bytes, registry_lines = measure_registry_size(repo_root)
    return {
        "source_loc": source_loc,
        "source_files": source_files,
        "test_loc": test_loc,
        "test_files": test_files,
        "test_source_ratio": ratio,
        "top_level_src_packages": count_top_level_src_packages(repo_root),
        "test_subdirectories": count_test_subdirectories(repo_root),
        "commit_count": count_commits(repo_root),
        "doc_count": count_docs(repo_root),
        "registry_size_bytes": registry_bytes,
        "registry_size_lines": registry_lines,
        "dead_bytecode_files": find_dead_bytecode_files(repo_root),
        "unused_core_dependencies": find_unused_core_dependencies(repo_root),
        "churn_lines_changed_excl_bookkeeping": compute_churn_lines_changed(repo_root),
    }


def format_report(report: dict) -> str:
    unused_deps = ", ".join(report["unused_core_dependencies"]) or "none"
    lines = [
        "Codebase Health Baseline (live, computed fresh — not a cached snapshot)",
        "=" * 74,
        f"{'Source LoC / files':<50} {report['source_loc']:,} / {report['source_files']:,}",
        f"{'Test LoC / files':<50} {report['test_loc']:,} / {report['test_files']:,}",
        f"{'Test:source ratio (LoC)':<50} {report['test_source_ratio']:.2f} : 1",
        f"{'Top-level src/ packages':<50} {report['top_level_src_packages']:,}",
        f"{'Test subdirectories':<50} {report['test_subdirectories']:,}",
        f"{'Commits (full history)':<50} {report['commit_count']:,}",
        f"{'Docs (.md, under docs/)':<50} {report['doc_count']:,}",
        f"{'docs/REGISTRY.yaml size':<50} {report['registry_size_bytes']:,} bytes / {report['registry_size_lines']:,} lines",
        f"{'Dead bytecode files (.pyc w/ no source)':<50} {report['dead_bytecode_files']:,}",
        f"{'Declared-but-unused core dependencies':<50} {unused_deps}",
        f"{'Churn (lines changed, excl. bookkeeping)':<50} {report['churn_lines_changed_excl_bookkeeping']:,}",
        "=" * 74,
        "Churn excludes agent-monitoring/*.jsonl, tickets/working_log.csv, and",
        "docs/REGISTRY.yaml via a git pathspec exclusion (append-only bookkeeping",
        "files, not architectural instability signal).",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=_REPO_ROOT,
        help="Repo root to measure (default: this repo).",
    )
    args = parser.parse_args(argv)

    report = build_report(args.repo_root)
    print(format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
