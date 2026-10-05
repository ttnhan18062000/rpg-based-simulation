"""codebase/structure/package_registry.jsonl: one row per tracked top-level `src/` package.

Answers which packages are live, which layer each sits in, and which files agents must not imitate.
It makes the standard's rule M5 (no new top-level `src/` package without an owner decision) checkable:
a tracked top-level package with no row is reported. Blocking in CI since
TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING: a problem (exit 1) or a failure to run (exit 2) fails the
`Code health` job.

After seeding from `docs/plans/codebase_health/src_package_structure_audit.md` (a dated 2026-10-04
snapshot) this file is the source of truth; the audit table is not updated.

Row fields, all required except `system` (may be null); unknown fields are rejected:

    package, purpose, layer, status, strictness_tier, exemplar_modules, do_not_imitate, system,
    audit_decision, added_date, reviewed

`strictness_tier` names a future per-package gate level; nothing reads it yet. `baseline` is the
current state of every package (ratchet only); `strict` and `exemplar` are reserved.

Problems come in two classes so a later ticket can promote one without rewriting the other:

    schema        the file itself: JSON, fields, types, enums, duplicates, cited paths, `system`,
                  `merge-candidate into X` resolving to a row
    completeness  the file against the tree: a tracked package without a row, or a row for a
                  package that is not tracked or not on disk

    python3 -m codebase.structure.packages validate [--root DIR] [--schema-only] [--summary-out PATH] [--annotate]

Exit 0 clean, 1 problems, 2 could not run. `--summary-out` appends the result (and each problem) to a
Markdown file and `--annotate` prints one `::error::` line, as the code-health ratchet does, so a failing
step is never silent in CI.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_REL_PATH = Path("codebase/structure/package_registry.jsonl")
SYSTEM_REGISTRY_REL_PATH = Path("registries/system_registry.jsonl")

SCHEMA = "schema"
COMPLETENESS = "completeness"

REQUIRED_FIELDS = (
    "package", "purpose", "layer", "status", "strictness_tier", "exemplar_modules", "do_not_imitate",
    "system", "audit_decision", "added_date", "reviewed",
)
NULLABLE_FIELDS = frozenset({"system"})
LAYERS = frozenset(
    {"foundation", "content-pipeline", "domain", "engine", "simulation-systems", "consumer"}
)
STATUSES = frozenset({"active", "legacy", "frozen"})
TIERS = frozenset({"baseline", "strict", "exemplar"})
DECISIONS = frozenset({"keep", "retire-candidate", "investigate"})
MERGE_PREFIX = "merge-candidate into "
MAX_EXEMPLARS = 3


class Problem(NamedTuple):
    """One defect: `kind` is `schema` or `completeness`."""

    kind: str
    message: str

    def __str__(self) -> str:
        return f"[{self.kind}] {self.message}"


class RegistryError(ValueError):
    """The registry file is malformed. `problems` lists every defect found."""

    def __init__(self, problems: Sequence[Problem]) -> None:
        super().__init__("; ".join(str(p) for p in problems))
        self.problems = list(problems)


def registry_path(root: Path | str | None = None) -> Path:
    """Where the registry lives under `root` (default: this repository)."""
    return (Path(root) if root is not None else REPO_ROOT) / REGISTRY_REL_PATH


def tracked_packages(root: Path, notes: list[str] | None = None) -> set[str]:
    """Top-level `src/` directories holding a tracked file.

    If `git ls-files` fails (not a repository, "dubious ownership" in a CI container) the on-disk
    directories holding a `.py` file are used instead, and a one-line notice is appended to `notes`
    so a wrong package set can be explained.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "src"], capture_output=True, text=True, check=True
        ).stdout
        return {p.split("/")[1] for p in out.splitlines() if p.count("/") >= 2}
    except (OSError, subprocess.CalledProcessError) as exc:
        if notes is not None:
            notes.append(f"git ls-files failed ({exc.__class__.__name__}); package set taken from directories on disk")
        src = root / "src"
        return {d.name for d in src.iterdir() if d.is_dir() and any(d.rglob("*.py"))} if src.is_dir() else set()


def _system_names(root: Path) -> set[str]:
    path = root / SYSTEM_REGISTRY_REL_PATH
    if not path.exists():
        return set()
    return {
        json.loads(line)["system"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def _is_str(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _scalar_problems(entry: dict, where: str, systems: set[str]) -> list[str]:
    problems = [
        f"{where}: field '{name}' has an invalid value {entry[name]!r}"
        for name in ("package", "purpose", "added_date")
        if not _is_str(entry[name])
    ]
    problems += [
        f"{where}: field '{name}' has an invalid value {entry[name]!r}"
        for name, allowed in (("layer", LAYERS), ("status", STATUSES), ("strictness_tier", TIERS))
        if entry[name] not in allowed
    ]
    if not isinstance(entry["reviewed"], bool):
        problems.append(f"{where}: field 'reviewed' has an invalid value {entry['reviewed']!r}")
    if _is_str(entry["added_date"]):
        try:
            date.fromisoformat(entry["added_date"])
        except ValueError:
            problems.append(f"{where}: field 'added_date' is not an ISO date: {entry['added_date']!r}")
    decision = entry["audit_decision"]
    merge = isinstance(decision, str) and decision.startswith(MERGE_PREFIX) and decision[len(MERGE_PREFIX):]
    if decision not in DECISIONS and not merge:
        problems.append(f"{where}: field 'audit_decision' has an invalid value {decision!r}")
    system = entry["system"]
    if system is not None and (not isinstance(system, str) or system not in systems):
        problems.append(f"{where}: field 'system' names no row of {SYSTEM_REGISTRY_REL_PATH}: {system!r}")
    return problems


def _path_problems(entry: dict, where: str, root: Path) -> list[str]:
    problems: list[str] = []
    exemplars = entry["exemplar_modules"]
    if not isinstance(exemplars, list) or not all(_is_str(p) for p in exemplars) or len(exemplars) > MAX_EXEMPLARS:
        problems.append(f"{where}: field 'exemplar_modules' must be a list of at most {MAX_EXEMPLARS} paths")
        exemplars = []
    avoid = entry["do_not_imitate"]
    avoid_paths: list[str] = []
    if not isinstance(avoid, list) or not all(
        isinstance(item, dict) and set(item) == {"path", "reason"} and _is_str(item["path"]) and _is_str(item["reason"])
        for item in avoid
    ):
        problems.append(f"{where}: field 'do_not_imitate' must be a list of {{path, reason}} objects")
    else:
        avoid_paths = [item["path"] for item in avoid]
    problems += [
        f"{where}: cited path does not exist: {path}"
        for path in [*exemplars, *avoid_paths]
        if not (root / path).is_file()
    ]
    return problems


def _row_problems(entry: object, where: str, root: Path, systems: set[str]) -> list[str]:
    if not isinstance(entry, dict):
        return [f"{where}: row is not a JSON object"]
    problems = [f"{where}: unknown field '{name}'" for name in entry if name not in REQUIRED_FIELDS]
    missing = [f"{where}: missing required field '{name}'" for name in REQUIRED_FIELDS if name not in entry]
    if missing:
        return problems + missing
    return problems + _scalar_problems(entry, where, systems) + _path_problems(entry, where, root)


def _load_entries(path: Path) -> tuple[list[tuple[str, object]], list[Problem]]:
    entries: list[tuple[str, object]] = []
    problems: list[Problem] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        where = f"{path.name}:{number}"
        try:
            entries.append((where, json.loads(line)))
        except json.JSONDecodeError as exc:
            problems.append(Problem(SCHEMA, f"{where}: not valid JSON ({exc.msg})"))
    return entries, problems


def validate_file(
    path: Path,
    root: Path | None = None,
    kinds: Sequence[str] = (SCHEMA, COMPLETENESS),
    notes: list[str] | None = None,
) -> list[Problem]:
    """Every problem of the requested classes in the registry at `path`. A missing file is a `schema` problem.

    `notes` collects non-problem notices (the git fallback in `tracked_packages`).
    """
    root = root or REPO_ROOT
    problems: list[Problem] = []
    if path.exists():
        entries, schema = _load_entries(path)
    else:
        entries, schema = [], [Problem(SCHEMA, f"registry file not found: {path}")]
    systems = _system_names(root)
    seen: dict[str, str] = {}
    rows: dict[str, dict] = {}
    for where, entry in entries:
        schema += [Problem(SCHEMA, m) for m in _row_problems(entry, where, root, systems)]
        if isinstance(entry, dict) and isinstance(entry.get("package"), str):
            name = entry["package"]
            if name in seen:
                schema.append(Problem(SCHEMA, f"{where}: duplicate package {name!r}, first seen at {seen[name]}"))
            seen.setdefault(name, where)
            rows.setdefault(name, entry)
    for name, entry in rows.items():
        decision = entry.get("audit_decision")
        if isinstance(decision, str) and decision.startswith(MERGE_PREFIX) and decision[len(MERGE_PREFIX):] not in rows:
            schema.append(Problem(SCHEMA, f"{seen[name]}: merge target has no row: {decision[len(MERGE_PREFIX):]!r}"))
    if SCHEMA in kinds:
        problems += schema
    if COMPLETENESS in kinds:
        tracked = tracked_packages(root, notes)
        problems += [
            Problem(COMPLETENESS, f"tracked top-level package has no row: src/{name}")
            for name in sorted(tracked - rows.keys())
        ]
        problems += [
            Problem(COMPLETENESS, f"{seen[name]}: row for a package that is not tracked or not on disk: {name}")
            for name in sorted(rows.keys() - tracked)
        ]
    return problems


def load_rows(path: Path, root: Path | None = None, kinds: Sequence[str] = (SCHEMA,)) -> list[dict]:
    """The rows in `path`, sorted by package. Raises `RegistryError` on any problem of `kinds`."""
    problems = validate_file(path, root, kinds)
    if problems:
        raise RegistryError(problems)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return sorted(rows, key=lambda row: row["package"])


def _write_summary(path: Path | None, line: str) -> None:
    if path is not None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point; returns the process exit code (0 clean, 1 problems, 2 could not run)."""
    parser = argparse.ArgumentParser(prog="python3 -m codebase.structure.packages", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate", help="report schema and completeness problems; exit 1 if any, 2 if it could not run")
    check.add_argument("--root", type=Path, default=REPO_ROOT)
    check.add_argument("--schema-only", action="store_true", help="skip the completeness class")
    check.add_argument("--summary-out", type=Path, help="append a Markdown result to this file (GITHUB_STEP_SUMMARY)")
    check.add_argument("--annotate", action="store_true", help="print a GitHub ::error:: line on problems or a failure to run")
    args = parser.parse_args(argv)
    kinds = (SCHEMA,) if args.schema_only else (SCHEMA, COMPLETENESS)
    notes: list[str] = []
    try:
        problems = validate_file(registry_path(args.root), args.root, kinds, notes)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError) as exc:  # a crash is reported, never silent
        reason = f"{exc.__class__.__name__}: {exc}"
        _write_summary(args.summary_out, f"**Package registry:** could not run ({reason})")
        if args.annotate:
            print(f"::error::package registry could not run: {reason}")
        print(f"package registry: could not run ({reason})")
        return 2
    for problem in problems:
        print(problem)
    for note in notes:
        print(f"note: {note}")
    result = f"package registry: {len(problems)} problem(s)"
    print(result)
    lines = [f"**Package registry:** {result}"]
    lines += [f"- `{problem}`" for problem in problems]
    lines += [f"- note: {note}" for note in notes]
    _write_summary(args.summary_out, "\n".join(lines))
    if args.annotate and problems:
        print(f"::error::package registry: {len(problems)} problem(s); see job summary")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
