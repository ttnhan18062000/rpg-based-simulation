"""Static guard: every real `tests/` directory is referenced by a fast-lane CI job.

Built for TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK. `.github/workflows/test.yml` enumerates
every test directory by explicit path in each job's `pytest` invocation -- there is no glob or
auto-discovery. `TCK-20260817-CI-COVERAGE-GAP-16-ORPHANED-TEST-DIRS` found 16 directories (439
tests) that no job ever referenced; that ticket fixed the specific 16 directories but added no
lasting check against recurrence. This module is that lasting check.

Three pure, independently-testable pieces, matching `test_scope_coverage_static.py`'s shape (pure
mapping/predicate functions feeding one aggregator):

- `parse_job_pytest_paths` -- text-only parser: workflow YAML text -> `{job_name: {path_token,
  ...}}`. Deliberately line-based (no multiline/backtracking regex over the whole file) --
  the naive `pytest\\s+(...)*?` approach this replaced hung for minutes on the real ~320-line
  workflow file.
- `directories_from_test_files` -- pure path-string grouping: a flat file list (e.g. from
  `git ls-files`) -> `{directory: [file, ...]}`, one entry per directory that directly contains at
  least one `test_*.py` file (non-recursive -- a subdirectory is its own separate entry, covered
  independently, consistent with how `tests/unit/domains/campaigns` is covered by a listed
  `tests/unit/domains` *parent path*, not by `tests/unit/domains` being "the same directory").
- `file_is_fully_slow_marked` -- AST-based predicate: does every `test_*` function in this file
  carry a `slow`/`extra_slow` marker (via `pytestmark`, a function decorator, or a `Test*` class
  decorator)? Needed because the `slow` job's blanket `pytest tests/ -m "slow or extra_slow"` scan
  only legitimately covers a directory whose tests are *all* slow-marked (e.g. `tests/regression/`)
  -- a directory with even one unmarked (fast) test would silently never run if only the `slow`
  job's blanket referenced it.

`check_ci_workflow_test_coverage` is the aggregator real callers use. It accepts an injectable
`test_files` list so tests can exercise it against a synthetic `tests/` tree in `tmp_path` without
a real git repo; the default (`test_files=None`) shells out to `git ls-files` against
`repo_root`, per this project's stated preference for `git ls-files` over a raw filesystem walk
(avoids local `__pycache__`/untracked-file noise).

Deliberately narrow, and disclosed as such: `file_is_fully_slow_marked` recognizes the three
marking idioms actually used in this codebase (module-level `pytestmark`, a `@pytest.mark.slow`
-style decorator on a `test_*` function, and the same decorator on an enclosing `Test*` class) --
it does not resolve markers applied via `pyproject.toml`'s `addopts`, `pytest.ini` conftest hooks,
or dynamically-computed marker expressions. No such indirection exists in this repo's `tests/`
tree today (see `tests/conftest.py::pytest_collection_modifyitems`, which only auto-enforces
taxonomy markers under `tests/parity/`, and does not auto-apply `slow`/`extra_slow`).
"""

import ast
import subprocess
import tomllib
from pathlib import Path
from typing import Dict, List, Optional, Set

SLOW_JOB_NAME = "slow"
_SLOW_MARKER_NAMES = {"slow", "extra_slow"}

_JOB_HEADER_INDENT = "  "  # exactly 2 spaces: top-level key under `jobs:`


def parse_job_pytest_paths(workflow_text: str) -> Dict[str, Set[str]]:
    """Return `{job_name: {tests/... path token, ...}}` for every `pytest` invocation found in
    each job's body. The root blanket `pytest tests/` (used by the `slow` job) is represented as
    the single token `"tests"`. `--ignore=<path>` tokens are stripped before token collection --
    an ignored path is explicitly excluded from that invocation, never "covered" by it.
    """
    lines = workflow_text.splitlines()
    job_bodies: Dict[str, List[str]] = {}
    current_job: Optional[str] = None

    for line in lines:
        job_name = _match_job_header(line)
        if job_name is not None:
            current_job = job_name
            job_bodies[current_job] = []
            continue
        if current_job is not None:
            job_bodies[current_job].append(line)

    return {name: _extract_pytest_paths(body) for name, body in job_bodies.items()}


def _match_job_header(line: str) -> Optional[str]:
    if not line.startswith(_JOB_HEADER_INDENT):
        return None
    if line.startswith(_JOB_HEADER_INDENT + " "):
        return None  # deeper than 2 spaces -- not a top-level `jobs:` key
    if not line.endswith(":"):
        return None
    name = line[len(_JOB_HEADER_INDENT):-1]
    if not name or not (name[0].isalpha()):
        return None
    if not all(ch.isalnum() or ch in "-_" for ch in name):
        return None
    return name


def _extract_pytest_paths(body_lines: List[str]) -> Set[str]:
    paths: Set[str] = set()
    i = 0
    n = len(body_lines)
    while i < n:
        stripped = body_lines[i].strip()
        if stripped == "pytest" or stripped.startswith("pytest ") or stripped.startswith("pytest\\"):
            statement_words: List[str] = []
            while True:
                current = body_lines[i].strip()
                continues = current.endswith("\\")
                if continues:
                    current = current[:-1].strip()
                statement_words.extend(current.split())
                i += 1
                if not continues or i >= n:
                    break
            statement_words = [w for w in statement_words if not w.startswith("--ignore=")]
            for word in statement_words:
                token = word.strip("'\"")
                if token in ("tests", "tests/"):
                    paths.add("tests")
                elif token.startswith("tests/"):
                    paths.add(token.rstrip("/"))
        else:
            i += 1
    return paths


def git_ls_test_files(repo_root: Path) -> List[str]:
    """`git ls-files` (not a raw filesystem walk) for every `test_*.py` file under `tests/`,
    avoiding local `__pycache__`/untracked-file noise."""
    result = subprocess.run(
        ["git", "ls-files", "--", "tests/*test_*.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def directories_from_test_files(file_paths: List[str]) -> Dict[str, List[str]]:
    """Group a flat file list by immediate parent directory -- one entry per directory that
    directly contains at least one `test_*.py` file (non-recursive)."""
    grouped: Dict[str, List[str]] = {}
    for file_path in file_paths:
        directory = str(Path(file_path).parent)
        grouped.setdefault(directory, []).append(file_path)
    return grouped


def is_directory_covered(directory: str, fastlane_paths: Set[str]) -> bool:
    """True iff `directory` is directly listed, or is a descendant of a listed parent path, in
    any fast-lane job's path set."""
    if "tests" in fastlane_paths:
        return True
    for listed in fastlane_paths:
        if directory == listed or directory.startswith(listed + "/"):
            return True
    return False


def directory_is_covered_by_file_listings(files_in_dir: List[str], fastlane_paths: Set[str]) -> bool:
    """True iff every `test_*.py` file directly in this directory is individually listed as its
    own path token in some fast-lane job -- pytest supports mixing directory and file arguments
    in the same invocation, so a directory can be fully (if verbosely) covered file-by-file
    without ever appearing as a directory token itself (e.g. a handful of loose files directly
    under `tests/unit/` with no themed subdirectory of their own)."""
    return bool(files_in_dir) and all(f in fastlane_paths for f in files_in_dir)


def file_is_fully_slow_marked(file_path: Path) -> bool:
    """True iff every `test_*` function in `file_path` is marked `slow` or `extra_slow` -- via a
    module-level `pytestmark`, a function decorator, or an enclosing `Test*` class decorator.
    Returns False for a file with zero test functions (nothing to legitimately call "covered")."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return False

    if _module_pytestmark_is_slow(tree):
        return True

    test_functions: List[bool] = []  # each entry: True if this function is individually marked
    for node in tree.body:
        if _is_test_function(node):
            test_functions.append(_decorators_mark_slow(node.decorator_list))
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            class_marked = _decorators_mark_slow(node.decorator_list)
            for sub in node.body:
                if _is_test_function(sub):
                    test_functions.append(class_marked or _decorators_mark_slow(sub.decorator_list))

    if not test_functions:
        return False
    return all(test_functions)


def _is_test_function(node: ast.AST) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")


def _module_pytestmark_is_slow(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "pytestmark" for target in node.targets
        ):
            if _expr_marks_slow(node.value):
                return True
    return False


def _decorators_mark_slow(decorators: List[ast.expr]) -> bool:
    return any(_expr_marks_slow(dec) for dec in decorators)


def _expr_marks_slow(expr: ast.expr) -> bool:
    if isinstance(expr, ast.Call):
        return _expr_marks_slow(expr.func)
    if isinstance(expr, ast.Attribute):
        if expr.attr in _SLOW_MARKER_NAMES:
            return True
        return _expr_marks_slow(expr.value)
    if isinstance(expr, (ast.List, ast.Tuple)):
        return any(_expr_marks_slow(elt) for elt in expr.elts)
    return False


def directory_is_slow_only_legitimate(files_in_dir: List[str], repo_root: Path) -> bool:
    """True iff every file directly in this directory is fully slow-marked -- the `slow` job's
    blanket scan is then the correct and sufficient coverage for it."""
    if not files_in_dir:
        return False
    return all(file_is_fully_slow_marked(repo_root / f) for f in files_in_dir)


def pytest_norecursedirs(pyproject_path: Path) -> Set[str]:
    """Reads `[tool.pytest.ini_options].norecursedirs` from `pyproject_path` (the same list
    `pytest` itself consults). Returns an empty set if the file or key is missing -- never raises,
    since a coverage check should not itself become a hard dependency on `pyproject.toml`'s exact
    shape."""
    if not pyproject_path.exists():
        return set()
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    entries = data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("norecursedirs", [])
    return set(entries)


def directory_is_excluded_from_pytest_collection(directory: str, norecursedirs: Set[str]) -> bool:
    """True iff any path segment of `directory` matches a `norecursedirs` basename -- mirrors
    pytest's own basename-matching semantics (`norecursedirs` matches directory basenames
    anywhere in the recursion path, not full paths, per `pyproject.toml`'s own confirmed
    convention). A directory excluded this way is never collected in ANY job (fast-lane or
    `slow`), so it cannot be a "silently orphaned, would otherwise run" gap this check exists to
    catch -- e.g. `tests/archive/`, an intentional frozen-historical-snapshot location
    (`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`), not an oversight."""
    return bool(set(Path(directory).parts) & norecursedirs)


def check_ci_workflow_test_coverage(
    workflow_path: Path,
    repo_root: Path,
    test_files: Optional[List[str]] = None,
    norecursedirs: Optional[Set[str]] = None,
) -> List[dict]:
    """Aggregate check: every real test directory (`git ls-files`-discovered, one entry per
    directory directly containing a `test_*.py` file) must be covered by at least one fast-lane
    job's explicit `pytest` path list, or be entirely `slow`/`extra_slow`-marked (in which case
    the `slow` job's blanket scan legitimately covers it), or excluded from pytest collection
    entirely via `pyproject.toml`'s `norecursedirs` (in which case it cannot silently fail to run
    in CI -- it is never collected anywhere, by design).

    Returns a flat `list[dict]` of `{"condition", "status", "evidence"}`, matching
    `done_checker_static.run_static_precheck`'s shape. `status` is `PASS` or `FAIL`.

    `test_files`: injectable file list (paths relative to `repo_root`) for fixture-based testing
    without a real git repo. `None` (the default) shells out to `git ls_test_files(repo_root)`.
    `norecursedirs`: injectable override for fixture-based testing. `None` (the default) reads
    `repo_root / "pyproject.toml"` via `pytest_norecursedirs()`.
    """
    workflow_text = workflow_path.read_text(encoding="utf-8")
    job_paths = parse_job_pytest_paths(workflow_text)

    fastlane_paths: Set[str] = set()
    for job_name, paths in job_paths.items():
        if job_name == SLOW_JOB_NAME:
            continue
        fastlane_paths |= paths

    files = test_files if test_files is not None else git_ls_test_files(repo_root)
    dir_map = directories_from_test_files(files)

    resolved_norecursedirs = (
        norecursedirs if norecursedirs is not None
        else pytest_norecursedirs(repo_root / "pyproject.toml")
    )

    results: List[dict] = []
    for directory in sorted(dir_map):
        files_in_dir = dir_map[directory]

        if directory_is_excluded_from_pytest_collection(directory, resolved_norecursedirs):
            results.append({
                "condition": f"ci_test_dir_covered:{directory}",
                "status": "PASS",
                "evidence": (
                    f"{directory} has no fast-lane job path entry, but is excluded from pytest "
                    f"collection entirely via pyproject.toml's [tool.pytest.ini_options] "
                    f"norecursedirs -- it is never collected by any job (fast-lane or slow), by "
                    f"design, so it cannot silently fail to run."
                ),
            })
            continue

        if is_directory_covered(directory, fastlane_paths):
            results.append({
                "condition": f"ci_test_dir_covered:{directory}",
                "status": "PASS",
                "evidence": f"{directory} is covered by a fast-lane job's explicit path list.",
            })
            continue

        if directory_is_covered_by_file_listings(files_in_dir, fastlane_paths):
            results.append({
                "condition": f"ci_test_dir_covered:{directory}",
                "status": "PASS",
                "evidence": (
                    f"{directory} has no directory-level fast-lane entry, but every test_*.py "
                    f"file directly in it is individually listed by file path in a fast-lane "
                    f"job."
                ),
            })
            continue

        if directory_is_slow_only_legitimate(files_in_dir, repo_root):
            results.append({
                "condition": f"ci_test_dir_covered:{directory}",
                "status": "PASS",
                "evidence": (
                    f"{directory} has no fast-lane job path entry, but every test_* function in "
                    f"it is marked slow/extra_slow -- the `slow` job's blanket `pytest tests/` "
                    f"scan legitimately covers it."
                ),
            })
            continue

        results.append({
            "condition": f"ci_test_dir_covered:{directory}",
            "status": "FAIL",
            "evidence": (
                f"{directory} contains a test_*.py file, is not referenced (directly, or as a "
                f"descendant of a listed parent) by any fast-lane job's pytest path list in "
                f"{workflow_path}, and is not exclusively slow/extra_slow-marked -- it would "
                f"never run in CI outside the nightly/manual `slow` job. Add it to the correct "
                f"fast-lane job's explicit path list."
            ),
        })

    return results
