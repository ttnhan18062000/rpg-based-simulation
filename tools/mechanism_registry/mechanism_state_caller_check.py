#!/usr/bin/env python3
"""
Claims-as-tests phase 1: state-versus-caller-count mismatch detection.

TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION. Scoped deliberately as mismatch detection,
not presence/absence detection, per peer review: every one of the four real registry state errors
found by hand this epic (`camp`, `motivation_doctrine`, `causal_spatial_memory`,
`commitment_betrayal`'s mis-binding) was a WRONG state, never a missing entry. A detector that only
answers "does this mechanism exist in code" would have caught none of them. `orphan` and `gated`
in particular are OPPOSITE conclusions -- dead code versus working code switched off -- so a wrong
answer sends a reader to do the opposite of the right thing.

Reuses `implemented_by` (the real, disk-validated code binding -- `TCK-20260916-MECHANISM-
IMPLEMENTED-BY-BINDING`) as its only source of "what code is this mechanism." This means the
detector can only check the 20 of 89 mechanisms that currently have a binding -- it does NOT
attempt to re-derive bindings via prose search or a lookup table (both already rejected elsewhere
in this epic for the same reason: a second, unverifiable place the same fact would live).

Three checks (originally four -- see "Removed check" below), in the order peer named them
(cheapest payoff first):
  1. declared `orphan` with a real, non-zero caller count -- `causal_spatial_memory`'s exact shape,
     the highest-value single check (its own historical regression test uses that real defect).
  2. declared `done`/`partial` with zero real callers -- `motivation_doctrine`'s shape (though that
     specific historical case is unrepresentable here since its own implementing code was deleted
     entirely, not merely uncalled -- no `implemented_by` path can exist for deleted code. Covered
     by a synthetic fixture instead).
  3. declared `gated` with no feature-flag context found near any real caller -- weaker signal,
     labeled low-confidence in the report.

**Removed check: `skeleton` whose body looks substantial, not a stub.** Built, run once, and
deleted after its own first real test flagged `temporal_pressure` -- `skeleton` in this registry's
own taxonomy means "an early, minimal implementation," not "an empty stub," and the check's line-
count heuristic conflated the two. Per peer review: a check known to be wrong, left in at low
confidence, becomes permanent known-noise a reader learns to ignore -- exactly the attribution-
ratchet failure shape this corpus already has a precedent for. Deleted rather than downgraded;
re-add only if a real signal for this claim is found (see
`stored_artifacts/TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION/investigation.md` for the
full disposition of its own one real test).

**Symbol-level bindings, when available, check only the bound symbol's real callers -- not every
symbol in the file.** An `implemented_by` entry may be a bare path (file-level: every top-level
symbol in the file is aggregated, the original, coarser behavior) or `"<path>::<Symbol>"`
(symbol-level -- TCK-20260916-MECHANISM-IMPLEMENTED-BY-SYMBOL-LEVEL-BINDING). Symbol-level exists
because file-level aggregation produced a real misleading signal: `demographic_cohort_cycle`'s own
`cohort.py` defines both `PopulationCohort` (a data class used widely elsewhere, unrelated to this
mechanism's own claim) and `DemographicCycleService` (the actual entry point) -- aggregating
callers across both cannot distinguish "the data class is used elsewhere" from "the service itself
is invoked."

**Report-only**, same rule as every other detector in this corpus -- never fails the build. Every
mechanism this tool cannot check (no `implemented_by`) is a named, counted exclusion, not a silent
skip -- see `Report.unchecked`.

**The headline number this tool's own report leads with is its false-positive rate, not its
finding count** -- per peer review: if caller-count detection turns out unreliable in this
codebase, the honest conclusion is that phases 2/3 of the initiative need re-arguing, which is
exactly what the initiative document says should happen. Four real errors were found by hand
before this detector existed; that is the baseline this tool is measured against, not a target it
is assumed to beat. **The tool's own first real run only checked the 20 mechanisms this same
session had just hand-verified while fixing the four known errors -- the cleanest slice of the
registry, not a representative one.** A meaningful false-positive/defect-rate read requires
`implemented_by` coverage on mechanisms nobody has recently touched; that coverage-extension work
is sequenced before re-running this assessment for real (see the ticket's own Completion Summary).

Usage:
  python3 tools/mechanism_registry/mechanism_state_caller_check.py           # human-readable report
  python3 tools/mechanism_registry/mechanism_state_caller_check.py --json     # machine-readable report
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC_DIR = _REPO_ROOT / "src"
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"

sys.path.insert(0, str(_REPO_ROOT / "tools" / "mechanism_registry"))
from registry import parse_implemented_by_entry  # noqa: E402

_CLASS_RE = re.compile(r"^class\s+(\w+)", re.MULTILINE)
# Module-level functions too -- not every mechanism's real entry point is a class.
# diplomacy's own implementing module (diplomatic_state_machine.py) is pure free functions
# (compute_transitions, events_from_transitions), no class at all; a class-only symbol extractor
# finds nothing to check callers for and silently reports zero callers -- a real detector bug
# found while validating this tool's own first run, not a registry defect.
_DEF_RE = re.compile(r"^def\s+(\w+)", re.MULTILINE)
_PRIVATE_NAME_RE = re.compile(r"^_")
_FLAG_CONTEXT_RE = re.compile(r"\bENABLE_[A-Z0-9_]+\b|\brun_phase\(")

# A file counts as a backward-compat re-export shim, not a real caller, if its only non-blank,
# non-comment content is import statements -- the exact shape found throughout this epic
# (`src/systems/*.py`'s own 2-3 line shims). Excluding shims from caller counts is the same
# discipline the completeness checker's own enumeration already applies.
_IMPORT_ONLY_RE = re.compile(r"^\s*(from\s+\S+\s+import\s+.+|import\s+\S+|__all__\s*=.*)\s*$")


@dataclass(frozen=True)
class Finding:
    mechanism_id: str
    check: str
    declared_state: str
    detail: str
    confidence: str  # "high" | "low"


@dataclass
class Report:
    checked: int
    unchecked: int
    findings: List[Finding] = field(default_factory=list)


def _real_source_files() -> List[Path]:
    return [p for p in _SRC_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def _is_shim_file(path: Path) -> bool:
    try:
        lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError:
        return False
    lines = [l for l in lines if not l.strip().startswith("#")]
    if not lines or len(lines) > 4:
        return False
    return all(_IMPORT_ONLY_RE.match(l) for l in lines)


def _symbol_names(path: Path) -> List[str]:
    """Top-level classes and module-level (non-underscore-prefixed) functions -- a mechanism's
    real entry point is sometimes a free function, not a class (see module docstring)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    classes = _CLASS_RE.findall(text)
    functions = [f for f in _DEF_RE.findall(text) if not _PRIVATE_NAME_RE.match(f)]
    return classes + functions


def _strip_line_comment(line: str) -> str:
    """Crude but effective for this corpus's own style: drop everything from the first '#' not
    inside a string literal. Doesn't handle a '#' inside a string perfectly, but this codebase
    doesn't lean on that edge case in the lines that matter here."""
    in_single = in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i]
    return line


def _real_callers(symbol: str, defining_file: Path, source_files: List[Path]) -> List[Path]:
    """Files (other than the defining file and any shim) with at least one REAL code reference to
    symbol -- a mention inside a comment or docstring line doesn't count. Found necessary the hard
    way: strategic_redirection's own registered `orphan` state has exactly one repo-wide mention
    of its class name outside its own file, and that mention is a code comment
    ("Hoisted logic from StrategicRedirectionSystem") -- a naive whole-file substring match would
    have called that a real caller and produced a false 'orphan_with_callers' finding."""
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    hits = []
    for path in source_files:
        if path.resolve() == defining_file.resolve():
            continue
        if _is_shim_file(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        in_docstring = False
        for line in lines:
            stripped = line.strip()
            triple_count = stripped.count('"""') + stripped.count("'''")
            code_part = _strip_line_comment(line) if not in_docstring else ""
            if triple_count % 2 == 1:
                in_docstring = not in_docstring
            if in_docstring and triple_count == 0:
                continue
            if pattern.search(code_part):
                hits.append(path)
                break
    return hits


def _flag_context_near_callers(symbol: str, caller_files: List[Path]) -> bool:
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    for path in caller_files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            if pattern.search(line):
                window = "\n".join(lines[max(0, i - 5):i + 6])
                if _FLAG_CONTEXT_RE.search(window):
                    return True
    return False


def check_mechanism(mechanism: dict, source_files: List[Path]) -> List[Finding]:
    mid = mechanism["id"]
    state = mechanism.get("state")
    implemented_by = mechanism.get("implemented_by") or []
    if not implemented_by:
        return []

    findings: List[Finding] = []
    total_callers = 0
    any_flag_context = False

    for entry in implemented_by:
        rel_path, bound_symbol = parse_implemented_by_entry(entry)
        defining_file = _REPO_ROOT / rel_path
        if not defining_file.is_file():
            continue
        # Symbol-level binding checks only the bound symbol's own real callers; a bare
        # file-level binding falls back to aggregating every top-level symbol in the file (see
        # module docstring for why symbol-level exists and when file-level still applies).
        symbols = [bound_symbol] if bound_symbol else _symbol_names(defining_file)
        file_callers: List[Path] = []
        for symbol in symbols:
            file_callers.extend(_real_callers(symbol, defining_file, source_files))
            if _flag_context_near_callers(symbol, file_callers):
                any_flag_context = True
        total_callers += len(set(file_callers))

    if state == "orphan" and total_callers > 0:
        findings.append(Finding(
            mid, "orphan_with_callers", state,
            f"declared orphan but {total_callers} real caller file(s) found for a symbol defined "
            f"in {implemented_by} -- causal_spatial_memory's exact historical shape",
            "high",
        ))
    if state in ("done", "partial") and total_callers == 0:
        findings.append(Finding(
            mid, "state_with_zero_callers", state,
            f"declared {state} but zero real callers found for any class defined in "
            f"{implemented_by}",
            "high",
        ))
    if state == "gated" and total_callers > 0 and not any_flag_context:
        findings.append(Finding(
            mid, "gated_without_flag_context", state,
            f"declared gated but no ENABLE_* flag or run_phase() call found within 5 lines of any "
            f"real caller of {implemented_by}",
            "low",
        ))

    return findings


def build_report(registry_data: dict) -> Report:
    mechanisms = registry_data.get("mechanisms", []) or []
    source_files = _real_source_files()
    checked = 0
    unchecked = 0
    findings: List[Finding] = []
    for m in mechanisms:
        if not m.get("implemented_by"):
            unchecked += 1
            continue
        checked += 1
        findings.extend(check_mechanism(m, source_files))
    return Report(checked=checked, unchecked=unchecked, findings=findings)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON report.")
    parser.add_argument("--registry", type=Path, default=_REGISTRY_PATH)
    args = parser.parse_args(argv)

    with open(args.registry, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    report = build_report(data)

    if args.json:
        print(json.dumps({
            "checked": report.checked,
            "unchecked": report.unchecked,
            "findings": [vars(f) for f in report.findings],
        }, indent=2))
        return 0

    print(f"Checked {report.checked} mechanism(s) with a real implemented_by binding; "
          f"{report.unchecked} mechanism(s) have no binding yet and cannot be checked (not a "
          f"gap claim -- see TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING).")
    if not report.findings:
        print("No state/caller-count mismatches found among the checkable mechanisms.")
    else:
        high = [f for f in report.findings if f.confidence == "high"]
        low = [f for f in report.findings if f.confidence == "low"]
        print(f"{len(report.findings)} mismatch(es) found ({len(high)} high-confidence, "
              f"{len(low)} low-confidence). Each needs a real, direct re-check before acting on "
              f"it -- this is a report, not a verdict.")
        for f in report.findings:
            print(f"  [{f.confidence}] {f.mechanism_id} ({f.check}): {f.detail}")

    # Report-only: never fails the build by itself.
    return 0


if __name__ == "__main__":
    sys.exit(main())
