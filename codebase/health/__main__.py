"""Command line for the code-health registry and ratchet.

    python3 -m codebase.health check [--from DIR]    scan (or reuse a scan) and run the ratchet
    python3 -m codebase.health scan [--out DIR]      run the tools, keep their raw JSON
    python3 -m codebase.health seed [--from DIR] [--force] [--tool TOOL]
    python3 -m codebase.health validate
    python3 -m codebase.health list [--tool T] [--file PREFIX]
    python3 -m codebase.health delete FILE TOOL RULE [--symbol S]
    python3 -m codebase.health tighten [--from DIR] [--yes]

`check` exits 1 if a violation is new or worse than its row, 2 if a tool or the registry is
unusable, 0 otherwise. This is the entry point behind `make code-health` and the advisory
`code-health` CI job (which turns the exit code into a job summary and a warning annotation, and
never fails the PR). `check` also takes `--summary-for FILE` (paths the PR changed, one per line),
`--summary-out PATH` (append a Markdown summary, changed files first) and `--annotate` (print a
GitHub `::warning::` line when the exit code is non-zero). If the check cannot run (a tool or the
registry is unusable) it still writes one "could not run" summary line and warning, then exits 2.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Callable, Sequence

from codebase.health import ratchet, registry, scan
from codebase.health.findings import Finding

DEFAULT_SCAN_DIR = Path("reports/code_health/scan")


def _findings(args: argparse.Namespace, root: Path, tools: Sequence[str] = scan.ALL_TOOLS) -> list[Finding]:
    out_dir = args.source if args.source else root / DEFAULT_SCAN_DIR
    if not args.source:
        scan.run_scan(root, out_dir) if tools == scan.ALL_TOOLS else scan.run_scan(root, out_dir, tools)
    return scan.collect_findings(out_dir, root, args.scan_root, tools)


def _report_could_not_run(args: argparse.Namespace, exc: Exception) -> None:
    """Say so in the job summary and with a warning when `check` cannot run, then let the error propagate.

    Without this a broken tool (npx, a missing complexipy, a bad registry) would exit 2 with only stderr, and
    the advisory CI job, whose step is `continue-on-error`, would look exactly like a clean pass.
    """
    reason = " ".join(f"{exc}".split())[:300] or type(exc).__name__
    if args.summary_out:
        with args.summary_out.open("a", encoding="utf-8") as handle:
            handle.write(f"**Code health (advisory):** could not run: {reason}\n")
    if args.annotate:
        print(f"::warning::code-health could not run (advisory): {reason}")


def _cmd_check(args: argparse.Namespace, root: Path, path: Path) -> int:
    try:
        rows = registry.load_rows(path, root, check_files=False)
        findings = _findings(args, root)
    except Exception as exc:
        _report_could_not_run(args, exc)
        raise
    result = ratchet.compare(findings, rows)
    print(ratchet.format_report(result, args.limit))
    if args.summary_out:
        changed = args.summary_for.read_text(encoding="utf-8").split() if args.summary_for else []
        with args.summary_out.open("a", encoding="utf-8") as handle:
            handle.write(ratchet.format_summary(result, changed, args.limit) + "\n")
    if args.annotate and result.failed:
        print(f"::warning::code-health: {len(result.new) + len(result.worse)} new/worse violations (advisory); see job summary")
    return 1 if result.failed else 0


def _cmd_scan(args: argparse.Namespace, root: Path, path: Path) -> int:
    out_dir = args.out or root / DEFAULT_SCAN_DIR
    scan.run_scan(root, out_dir)
    print(f"raw tool output written to {out_dir}")
    return 0


def _seed_one_tool(args: argparse.Namespace, root: Path, path: Path) -> int:
    """Seed only `--tool`'s rows; every row of another tool is kept exactly as it is."""
    everything = registry.load_rows(path, root, check_files=False) if path.exists() else []
    own = [row for row in everything if row.tool == args.tool]
    if own and not args.force:
        print(f"error: {path} already has {len(own)} {args.tool} rows; use --force to reseed them", file=sys.stderr)
        return 2
    others = [row for row in everything if row.tool != args.tool]
    rows = others + registry.seed_rows(_findings(args, root, (args.tool,)), previous=own)
    registry.write_rows(path, rows)
    print(f"seeded {len(rows) - len(others)} {args.tool} rows into {path}; {len(others)} rows of other tools left untouched")
    return 0


def _cmd_seed(args: argparse.Namespace, root: Path, path: Path) -> int:
    if args.tool:
        return _seed_one_tool(args, root, path)
    if path.exists() and path.read_text(encoding="utf-8").strip() and not args.force:
        print(f"error: {path} already has rows; use --force to reseed", file=sys.stderr)
        return 2
    previous = registry.load_rows(path, root, check_files=False) if path.exists() else []
    rows = registry.seed_rows(_findings(args, root), previous=previous)
    registry.write_rows(path, rows)
    kept = sum(1 for row in rows if row.added_date != date.today().isoformat() or row.reviewed)
    print(f"seeded {len(rows)} rows into {path}; {len(previous)} earlier rows read, review data kept where keys persist ({kept})")
    return 0


def _cmd_validate(args: argparse.Namespace, root: Path, path: Path) -> int:
    problems = registry.validate_file(path, root)
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{path}: {'INVALID' if problems else 'valid'} ({len(problems)} problems)")
    return 2 if problems else 0


def _cmd_list(args: argparse.Namespace, root: Path, path: Path) -> int:
    for row in registry.load_rows(path, root, check_files=False):
        if (args.tool and row.tool != args.tool) or (args.file and not row.file.startswith(args.file)):
            continue
        print(f"{row.file} {row.symbol or '-'} [{row.tool} {row.rule}] value={row.value} ceiling={row.ceiling}")
    return 0


def _cmd_delete(args: argparse.Namespace, root: Path, path: Path) -> int:
    rows = registry.load_rows(path, root, check_files=False)
    try:
        remaining = registry.delete_row(rows, (args.file, args.symbol, args.tool, args.rule))
    except KeyError:
        print("error: no such row", file=sys.stderr)
        return 2
    registry.write_rows(path, remaining)
    print(f"deleted 1 row; {len(remaining)} remain")
    return 0


def _cmd_tighten(args: argparse.Namespace, root: Path, path: Path) -> int:
    rows, changes = registry.tighten(registry.load_rows(path, root, check_files=False), _findings(args, root))
    deletions = sum(1 for change in changes if change.startswith("deleted"))
    print("\n".join(changes) or "nothing to tighten")
    if deletions and not args.yes:
        print(
            f"refusing: {deletions} rows would be deleted as gone. A stale or partial scan directory looks "
            "the same as paid-off debt; check the list above, then re-run with --yes. Nothing was written.",
            file=sys.stderr,
        )
        return 2
    registry.write_rows(path, rows)
    return 0


COMMANDS: dict[str, Callable[[argparse.Namespace, Path, Path], int]] = {
    "check": _cmd_check, "scan": _cmd_scan, "seed": _cmd_seed, "validate": _cmd_validate,
    "list": _cmd_list, "delete": _cmd_delete, "tighten": _cmd_tighten,
}


def build_parser() -> argparse.ArgumentParser:
    """The argument parser; `--root` and `--registry` exist so tests can use a scratch repository."""
    parser = argparse.ArgumentParser(prog="python3 -m codebase.health", description=__doc__)
    parser.add_argument("--root", type=Path, default=registry.REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--registry", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--scan-root", default=scan.SCAN_ROOT, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "seed", "tighten"):
        sp = sub.add_parser(name)
        sp.add_argument("--from", dest="source", type=Path, help="reuse the raw output of an earlier scan")
        if name == "check":
            sp.add_argument("--limit", type=int, default=ratchet.DEFAULT_REPORT_LIMIT)
            sp.add_argument("--summary-for", type=Path, help="file listing the paths a PR changed, one per line")
            sp.add_argument("--summary-out", type=Path, help="append a Markdown summary here ($GITHUB_STEP_SUMMARY)")
            sp.add_argument("--annotate", action="store_true", help="print a GitHub ::warning:: line on a failure")
        if name == "seed":
            sp.add_argument("--force", action="store_true", help="reseed an existing registry (keeps review data)")
            sp.add_argument("--tool", choices=scan.ALL_TOOLS, help="seed only this tool's rows; other tools' rows are kept as they are")
        if name == "tighten":
            sp.add_argument("--yes", action="store_true", help="confirm deleting rows whose violation is gone")
    sub.add_parser("scan").add_argument("--out", type=Path)
    sub.add_parser("validate")
    lister = sub.add_parser("list")
    lister.add_argument("--tool")
    lister.add_argument("--file")
    deleter = sub.add_parser("delete")
    deleter.add_argument("file")
    deleter.add_argument("tool")
    deleter.add_argument("rule")
    deleter.add_argument("--symbol")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand; returns the process exit code."""
    args = build_parser().parse_args(argv)
    root = args.root
    path = args.registry or registry.registry_path(root)
    try:
        return COMMANDS[args.command](args, root, path)
    except (registry.RegistryError, scan.ToolUnavailableError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
