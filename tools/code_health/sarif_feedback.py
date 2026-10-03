"""Changed-line PR feedback for code scanning: SARIF for the code-health findings a PR introduced.

    python3 -m tools.code_health.sarif_feedback --changed FILE --out SARIF [--summary-out PATH] [--annotate]

`--changed` lists the paths a PR changed (one per line). Only existing `src/**/*.py` files are checked, because
the code-health registry covers `src/` only. ruff and complexipy are run on those files with `--output-format
sarif`, every result the registry already holds is dropped, and the rest are written to one SARIF 2.1.0 file
for `github/codeql-action/upload-sarif`. The registry is never changed.

SARIF results have no baseline identity, so the filter works per ratchet unit (the key in
`registries/code_health_exceptions.jsonl`):

- ruff: a (file, rule code) group is dropped when its count is at or below the row's ceiling, and kept
  **whole** when it is above the ceiling or has no row. The SARIF cannot say which finding of an over-ceiling
  group is the new one, so older findings of that code in the same file are shown too; the job summary says so.
- complexipy: a function is dropped when its cognitive complexity is at or below its row's ceiling.

With no changed `src` Python file, a valid SARIF with an empty `results` array is still written, so the upload
path (permission, code-scanning acceptance) is exercised on every same-repository PR.

If a tool cannot run, its SARIF is malformed, or the registry is unusable, no SARIF is written, one "could not
run" summary line and warning are, and the exit code is 2: a broken tool must not look like a clean result,
and an empty upload would wrongly clear existing alerts. Advisory for the roadmap M4 soak: findings never fail
the command (exit 0).

Trust boundary: in CI this runs in a same-repository PR job that holds `security-events: write`, so the PR's own
`uv.lock`, `pyproject.toml` and `tools/` run with that token. That is accepted because a same-repository author
already has write access (forks are excluded by the job's `if`), and the token can only upload code-scanning data
and read contents. Untrusted input: the changed paths come from a PR, so only paths matching `src/<name>/.../<name>.py` with no
`..` segment, no leading `-` and no shell-significant characters are used, and no shell is involved.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from tools.code_health import registry, scan
from tools.code_health.adapters import RULE_COGNITIVE
from tools.code_health.findings import TOOL_COMPLEXIPY, TOOL_RUFF
from tools.code_health.registry import Row

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
RESULT_CAP = 1000
"""Results kept per upload. Code scanning accepts at most 5,000 per run; the rest are counted, not sent."""
SAFE_PATH = re.compile(r"src/(?:[A-Za-z0-9_][A-Za-z0-9_.-]*/)*[A-Za-z0-9_][A-Za-z0-9_.-]*\.py")
_COMPLEXITY = re.compile(r"cognitive complexity of (\d+)")


class SarifError(Exception):
    """SARIF that is malformed, or a tool that could not produce any."""


def changed_python_files(paths: Iterable[str], root: Path) -> list[str]:
    """The existing, safe `src/**/*.py` paths among `paths`, sorted and without duplicates."""
    keep = {
        path.strip()
        for path in paths
        if SAFE_PATH.fullmatch(path.strip()) and ".." not in path.strip().split("/") and _is_plain_file(root, path.strip())
    }
    return sorted(keep)


def _is_plain_file(root: Path, path: str) -> bool:
    """A regular file inside the checkout: a symlink (possibly pointing outside it) is never linted."""
    target = root / path
    return target.is_file() and not target.is_symlink() and target.resolve().is_relative_to(root.resolve())


def parse_sarif(text: str, label: str) -> dict[str, Any]:
    """Parse one tool's SARIF and check the shape this module relies on; raise `SarifError` otherwise."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SarifError(f"{label}: not valid JSON ({exc})") from exc
    if not isinstance(data, dict) or data.get("version") != SARIF_VERSION or not isinstance(data.get("runs"), list):
        raise SarifError(f"{label}: not SARIF {SARIF_VERSION} with a runs array")
    for run in data["runs"]:
        if not isinstance(run, dict) or not isinstance(run.get("results", []), list):
            raise SarifError(f"{label}: a run has no results array")
        for result in run.get("results", []):
            if not isinstance(result, dict) or not isinstance(result.get("ruleId"), str):
                raise SarifError(f"{label}: a result has no ruleId")
            if not isinstance(result.get("message", {}), dict) or not isinstance(result.get("locations", []), list):
                raise SarifError(f"{label}: a result has a malformed message or locations")
    return data


def relative_uri(uri: str, root: Path) -> str:
    """A repository-relative path for a SARIF artifact uri; a uri outside the repository raises `SarifError`."""
    path = uri[len("file://"):] if uri.startswith("file://") else uri
    if path.startswith("/"):
        try:
            return Path(path).resolve().relative_to(root.resolve()).as_posix()
        except ValueError as exc:
            raise SarifError(f"artifact outside the repository: {uri}") from exc
    if ".." in path.split("/"):
        raise SarifError(f"artifact path escapes the repository: {uri}")
    return path


def _result_uri(result: Mapping[str, Any]) -> str:
    try:
        return str(result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"])
    except (KeyError, IndexError, TypeError) as exc:
        raise SarifError("a result has no physical location") from exc


def _with_uri(result: Mapping[str, Any], uri: str) -> dict[str, Any]:
    fixed = json.loads(json.dumps(result))
    location = fixed["locations"][0]["physicalLocation"]["artifactLocation"]
    location["uri"] = uri
    location.pop("uriBaseId", None)
    return fixed


def filter_ruff(run: Mapping[str, Any], rows: Mapping[tuple, Row], codes: Mapping[str, str], root: Path) -> tuple[list[dict], dict[str, int]]:
    """Keep the ruff results the registry does not hold; returns them with kept/dropped/groups counts."""
    results = [(relative_uri(_result_uri(r), root), codes.get(r["ruleId"], r["ruleId"]), r) for r in run.get("results", [])]
    totals = Counter((file, code) for file, code, _ in results)
    kept: list[dict] = []
    over: set[tuple[str, str]] = set()
    dropped = 0
    for file, code, result in results:
        row = rows.get((file, None, TOOL_RUFF, code))
        if row is not None and totals[(file, code)] <= row.ceiling:
            dropped += 1
            continue
        over.add((file, code))
        kept.append(_with_uri(result, file))
    return kept, {"kept": len(kept), "dropped": dropped, "groups": len(over)}


def filter_complexipy(run: Mapping[str, Any], rows: Mapping[tuple, Row], root: Path) -> tuple[list[dict], dict[str, int]]:
    """Keep the complexipy results the registry does not hold; returns them with kept/dropped/groups counts."""
    kept: list[dict] = []
    dropped = 0
    for result in run.get("results", []):
        file = relative_uri(_result_uri(result), root)
        try:
            symbol = str(result["locations"][0]["logicalLocations"][0]["name"]).replace("::", ".")
        except (KeyError, IndexError, TypeError) as exc:
            raise SarifError("a complexipy result has no function name") from exc
        match = _COMPLEXITY.search(str(result.get("message", {}).get("text", "")))
        if match is None:
            raise SarifError("a complexipy result has no complexity value")
        row = rows.get((file, symbol, TOOL_COMPLEXIPY, RULE_COGNITIVE))
        if row is not None and int(match.group(1)) <= row.ceiling:
            dropped += 1
            continue
        kept.append(_with_uri(result, file))
    return kept, {"kept": len(kept), "dropped": dropped, "groups": 0}


def _run_of(source: Mapping[str, Any], results: list[dict]) -> dict[str, Any]:
    base = (source.get("runs") or [{}])[0]
    return {"tool": base.get("tool", {"driver": {"name": "code-health"}}), "results": results}


def build_sarif(runs: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """One SARIF 2.1.0 document holding `runs`."""
    return {"$schema": SARIF_SCHEMA, "version": SARIF_VERSION, "runs": list(runs)}


def empty_sarif() -> dict[str, Any]:
    """A valid SARIF with one run and no results (nothing to report, but the upload still happens)."""
    return build_sarif([{"tool": {"driver": {"name": "code-health"}}, "results": []}])


def cap_results(runs: list[dict[str, Any]], limit: int = RESULT_CAP) -> int:
    """Trim the runs in place to `limit` results in total; returns how many were left out."""
    left = limit
    omitted = 0
    for run in runs:
        results = run["results"]
        run["results"] = results[:max(left, 0)]
        omitted += len(results) - len(run["results"])
        left -= len(run["results"])
    return omitted


def _run_tool(command: Sequence[str], root: Path, label: str) -> subprocess.CompletedProcess[str]:
    try:
        done = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise SarifError(f"{label}: {exc}") from exc
    if done.returncode not in (0, 1):
        raise SarifError(f"{label} exited {done.returncode}: {' '.join(done.stderr.split())[:200]}")
    return done


def ruff_rule_codes(root: Path) -> dict[str, str]:
    """ruff rule name -> code (ruff's SARIF names the rule; the registry keys on the code)."""
    listing = _run_tool([sys.executable, "-m", "ruff", "rule", "--all", "--output-format", "json"], root, "ruff rule")
    try:
        return {str(rule["name"]): str(rule["code"]) for rule in json.loads(listing.stdout)}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise SarifError(f"ruff rule: unexpected output ({exc})") from exc


def _tool_sarif(files: Sequence[str], root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    ruff = _run_tool([sys.executable, "-m", "ruff", "check", *files, "--output-format", "sarif"], root, "ruff check")
    ruff_sarif = parse_sarif(ruff.stdout, "ruff")
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "complexipy.sarif"
        try:
            command = [scan._find("complexipy"), *files, "-q", "--output-format", "sarif", "--output", str(target)]
        except scan.ToolUnavailableError as exc:
            raise SarifError(str(exc)) from exc
        _run_tool(command, root, "complexipy")
        try:
            complexipy_text = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise SarifError(f"complexipy wrote no SARIF: {exc}") from exc
    return ruff_sarif, parse_sarif(complexipy_text, "complexipy")


def _append(path: Path | None, text: str) -> None:
    if path is not None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")


def _summary(ruff: dict[str, int], complexipy: dict[str, int], omitted: int) -> str:
    kept = ruff["kept"] + complexipy["kept"]
    line = (
        f"**Code health SARIF (advisory):** {kept} findings not in the baseline in changed files "
        f"(ruff {ruff['kept']} in {ruff['groups']} over-ceiling groups; complexipy {complexipy['kept']}). "
        f"Dropped as already in the baseline: ruff {ruff['dropped']}, complexipy {complexipy['dropped']}. "
        "Groups are shown whole: an over-ceiling (file, rule) group includes its older findings, so do not read every finding "
        "of such a group as new."
    )
    return line + (f" {omitted} results were left out of the upload (cap {RESULT_CAP})." if omitted else "")


def run(root: Path, changed: Path, out: Path, summary_out: Path | None = None, annotate: bool = False,
        registry_file: Path | None = None) -> int:
    """Write the SARIF for the PR's changed files; returns 0, or 2 if it could not run (nothing written)."""
    try:
        files = changed_python_files(changed.read_text(encoding="utf-8").splitlines(), root)
        if not files:
            data = empty_sarif()
            _append(summary_out, "**Code health SARIF (advisory):** no changed `src` Python files; an empty SARIF is uploaded so the upload path is exercised.")
            kept = 0
        else:
            rows = {row.key: row for row in registry.load_rows(registry_file or registry.registry_path(root), root, check_files=False)}
            codes = ruff_rule_codes(root)
            ruff_sarif, complexipy_sarif = _tool_sarif(files, root)
            ruff_results, ruff_stats = filter_ruff((ruff_sarif["runs"] or [{}])[0], rows, codes, root)
            cx_results, cx_stats = filter_complexipy((complexipy_sarif["runs"] or [{}])[0], rows, root)
            runs = [_run_of(ruff_sarif, ruff_results), _run_of(complexipy_sarif, cx_results)]
            omitted = cap_results(runs)
            data = build_sarif(runs)
            _append(summary_out, _summary(ruff_stats, cx_stats, omitted))
            kept = ruff_stats["kept"] + cx_stats["kept"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=1), encoding="utf-8")
    except (SarifError, registry.RegistryError, OSError, KeyError, TypeError, AttributeError) as exc:
        reason = " ".join(f"{exc}".split())[:300] or type(exc).__name__
        _append(summary_out, f"**Code health SARIF (advisory):** could not run: {reason}")
        if annotate:
            print(f"::warning::code-health SARIF could not run (advisory): {reason}")
        print(f"error: {reason}", file=sys.stderr)
        return 2
    if annotate and kept:
        print(f"::warning::code-health: {kept} findings not in the baseline in changed files (advisory); see the job summary and code scanning")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(prog="python3 -m tools.code_health.sarif_feedback", description=__doc__)
    parser.add_argument("--root", type=Path, default=registry.REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--registry", type=Path, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--changed", type=Path, required=True, help="file listing the paths a PR changed, one per line")
    parser.add_argument("--out", type=Path, required=True, help="where to write the SARIF")
    parser.add_argument("--summary-out", type=Path, help="append a Markdown summary here ($GITHUB_STEP_SUMMARY)")
    parser.add_argument("--annotate", action="store_true", help="print a GitHub ::warning:: line for kept findings")
    args = parser.parse_args(argv)
    return run(args.root, args.changed, args.out, args.summary_out, args.annotate, args.registry)


if __name__ == "__main__":
    sys.exit(main())
