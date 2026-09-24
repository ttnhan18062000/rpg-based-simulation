#!/usr/bin/env python3
"""
Report-only check: has the world moved under a Rule<->Mechanism mapping entry since a human last
reviewed it?

TCK-20260924-M2-MAPPING-DRIFT-DETECTION (`roadmap.md` M2, gated on M1's live Territory mapping).
Mirrors `tools/mechanism_registry/mechanism_registry_changed_code_check.py`'s three-entry-point
shape (pure core / git wrapper / CLI) and its report-only, never-fails-the-build convention -- but
answers a DIFFERENT axis than that tool. That tool compares two git *refs* (`--base`/`--head`),
because its question is "did this diff change cited code." This tool's question is "has cited code
or a mapped mechanism's verdict changed since **this row's own recorded date**" -- a per-row date
comparison, not a two-ref diff. Do not copy the `--base`/`--head` shape here.

`roadmap.md` M2 names three drift classes; this module implements two of them:

  1. `check_cited_code_drift` -- an `implemented_by` path cited by a row's mapped mechanism has a
     more recent last-commit date than the row's own `date`.
  3. `check_verdict_drift` -- a row's mapped mechanism's `verified.verdict` at the row's own
     review-time differs from its current value. The review-time verdict is recovered from
     `registries/mechanisms.yaml`'s own git history, pinned to the specific commit that last
     touched `registries/rule_mechanism_edges.yaml` on or before the row's `date` -- never an
     independent date search against `mechanisms.yaml`'s own history, which is same-day-ambiguous
     (as of 2026-09-24, every M1 row and `mechanisms.yaml`'s own last commit share one calendar
     date).

Drift class 2 (rename/removal/split/merge with a resolvable ID) is deliberately NOT implemented as
its own detector code -- `registries/mechanisms.yaml` carries no lineage field of any kind, and the
one real precedent (`action_pacing_readiness`, a kept-ID split) is only detectable via a full-entry
snapshot diff against a stored review-time baseline, which would duplicate
`mechanism_registry_changed_code_check.py`'s own whole-entry-equality check on a different axis, for
a scenario that has not occurred once among M1's five mapped mechanisms. See
`tickets/inprogress/TCK-20260924-M2-MAPPING-DRIFT-DETECTION.md`'s own Assumptions/Open Questions and
Implementation Notes for the recorded disposition. (Plain rename/removal is already a hard validator
failure today via `tools/semantic_control_plane/registry.py::validate_rule_mechanism_edges()`'s
unresolved-id check -- not this module's job either.)

Three entry points:
  - `check_cited_code_drift(edge_rows, mechanism_cited_paths, file_last_commit_dates)` -- pure
    core, drift class 1. Takes already-resolved data only (no `MechanismRegistry()` call, no git,
    no file I/O) so a synthetic fixture with a made-up `mechanism_id` can exercise it directly,
    mirroring `check_drift(old_data, new_data, changed_files)`'s own purity contract
    (`tools/mechanism_registry/mechanism_registry_changed_code_check.py:87-102`).
  - `check_verdict_drift(edge_rows, review_time_verdicts, current_verdicts)` -- pure core, drift
    class 3. Same purity contract.
  - `check_drift_from_git()` -- the git-backed wrapper: loads the real `edges:` list, resolves
    each mechanism's cited paths (via `MechanismRegistry` + `parse_implemented_by_entry`, reused
    rather than re-parsed), each cited path's last-commit date, and each mechanism's
    review-time/current verdict, then calls both pure-core functions.
  - `main(argv=None)` -- CLI entry point. Always returns 0 -- report-only, never fails the build,
    same convention as every other detector in this corpus. No CI wiring at this milestone.

Usage:
  python3 tools/semantic_control_plane/mapping_drift_check.py
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_EDGES_REL_PATH = "registries/rule_mechanism_edges.yaml"
_MECHANISMS_REL_PATH = "registries/mechanisms.yaml"

sys.path.insert(0, str(_REPO_ROOT / "tools" / "mechanism_registry"))
from registry import MechanismRegistry, parse_implemented_by_entry  # noqa: E402


@dataclass(frozen=True)
class CitedCodeDriftFinding:
    rule_id: str
    mechanism_id: str
    edge_type: str
    row_date: str
    changed_paths: List[str]


@dataclass(frozen=True)
class VerdictDriftFinding:
    rule_id: str
    mechanism_id: str
    row_date: str
    old_verdict: Optional[str]
    new_verdict: Optional[str]


def check_cited_code_drift(
    edge_rows: List[dict],
    mechanism_cited_paths: Dict[str, List[str]],
    file_last_commit_dates: Dict[str, str],
) -> List[CitedCodeDriftFinding]:
    """Pure core, drift class 1: no git dependency, no file I/O. `edge_rows` is
    `rule_mechanism_edges.yaml`'s own `edges:` list. `mechanism_cited_paths` is a pre-resolved
    `{mechanism_id: [bare_path, ...]}` map (the git wrapper builds it via `MechanismRegistry` +
    `parse_implemented_by_entry`, reused rather than re-parsed). `file_last_commit_dates` is a
    pre-resolved `{path: "YYYY-MM-DD"}` map the git wrapper also builds.

    A row is a finding when any of its mapped mechanism's cited paths has a resolved last-commit
    date STRICTLY AFTER the row's own `date` -- the conservative reading (a same-day code change
    counts as changed-since-review) per the ticket's own "pick the conservative reading"
    instruction.
    """
    findings: List[CitedCodeDriftFinding] = []
    for row in edge_rows:
        row_date = row["date"]
        cited_paths = mechanism_cited_paths.get(row["mechanism_id"], [])
        changed_paths = sorted(
            path for path in cited_paths
            if path in file_last_commit_dates and file_last_commit_dates[path] > row_date
        )
        if changed_paths:
            findings.append(CitedCodeDriftFinding(
                rule_id=row["rule_id"],
                mechanism_id=row["mechanism_id"],
                edge_type=row["edge_type"],
                row_date=row_date,
                changed_paths=changed_paths,
            ))
    return findings


def check_verdict_drift(
    edge_rows: List[dict],
    review_time_verdicts: Dict[str, Optional[str]],
    current_verdicts: Dict[str, Optional[str]],
) -> List[VerdictDriftFinding]:
    """Pure core, drift class 3: no git dependency. `review_time_verdicts`/`current_verdicts` are
    pre-resolved `{mechanism_id: verdict_or_None}` maps the git wrapper builds -- both drawn
    straight from `MechanismRegistry.get_verification()`'s own `verified.verdict` field, never a
    minted term.

    A row is a finding when its mapped mechanism's review-time verdict differs from its current
    verdict.
    """
    findings: List[VerdictDriftFinding] = []
    for row in edge_rows:
        mechanism_id = row["mechanism_id"]
        old_verdict = review_time_verdicts.get(mechanism_id)
        new_verdict = current_verdicts.get(mechanism_id)
        if old_verdict != new_verdict:
            findings.append(VerdictDriftFinding(
                rule_id=row["rule_id"],
                mechanism_id=mechanism_id,
                row_date=row["date"],
                old_verdict=old_verdict,
                new_verdict=new_verdict,
            ))
    return findings


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return result.stdout


def _file_last_commit_date(path: str) -> Optional[str]:
    out = _git("log", "-1", "--format=%ad", "--date=short", "--", path).strip()
    return out or None


def _anchor_commit_for_row_date(row_date: str) -> Optional[str]:
    """The last commit on/before `row_date` that touched `registries/rule_mechanism_edges.yaml`
    itself -- resolves the review-time snapshot from the citing row's OWN file history, never from
    an independent date search against `registries/mechanisms.yaml`'s own history (same-day-
    ambiguous, see module docstring). Takes the first (most recent) result of
    `git log --before=<row_date> 23:59:59`, which is git's own newest-first ordering -- the
    explicit tie-break for two commits sharing a calendar date."""
    out = _git(
        "log", f"--before={row_date} 23:59:59", "--format=%H", "--", _EDGES_REL_PATH,
    )
    shas = [line.strip() for line in out.splitlines() if line.strip()]
    return shas[0] if shas else None


def _verdict_at_commit(sha: str, mechanism_id: str) -> Optional[str]:
    out = _git("show", f"{sha}:{_MECHANISMS_REL_PATH}")
    data = yaml.safe_load(out) or {}
    for mechanism in data.get("mechanisms", []) or []:
        if mechanism.get("id") == mechanism_id:
            verified = mechanism.get("verified")
            return verified.get("verdict") if verified else None
    return None


def _load_edge_rows() -> List[dict]:
    with open(_REPO_ROOT / _EDGES_REL_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("edges", []) or []


def check_drift_from_git() -> "tuple[List[CitedCodeDriftFinding], List[VerdictDriftFinding]]":
    """Git-backed wrapper: loads the real `edges:` list off disk, resolves every mapped
    mechanism's cited paths, every cited path's last-commit date, and every mapped mechanism's
    review-time/current verdict via git, and calls both pure-core functions."""
    edge_rows = _load_edge_rows()
    registry = MechanismRegistry()
    mechanisms_by_id = {m["id"]: m for m in registry.all_mechanisms()}

    mechanism_cited_paths: Dict[str, List[str]] = {}
    all_cited_paths: set = set()
    for mechanism_id in {row["mechanism_id"] for row in edge_rows}:
        mechanism = mechanisms_by_id.get(mechanism_id)
        cited_paths = [
            parse_implemented_by_entry(entry)[0]
            for entry in ((mechanism or {}).get("implemented_by") or [])
        ]
        mechanism_cited_paths[mechanism_id] = cited_paths
        all_cited_paths.update(cited_paths)

    file_last_commit_dates = {
        path: date for path in all_cited_paths
        if (date := _file_last_commit_date(path)) is not None
    }

    review_time_verdicts: Dict[str, Optional[str]] = {}
    current_verdicts: Dict[str, Optional[str]] = {}
    for row in edge_rows:
        mechanism_id = row["mechanism_id"]
        if mechanism_id in current_verdicts:
            continue
        verification = registry.get_verification(mechanism_id)
        current_verdicts[mechanism_id] = verification.get("verdict") if verification else None
        anchor_sha = _anchor_commit_for_row_date(row["date"])
        review_time_verdicts[mechanism_id] = (
            _verdict_at_commit(anchor_sha, mechanism_id) if anchor_sha else None
        )

    cited_code_findings = check_cited_code_drift(
        edge_rows, mechanism_cited_paths, file_last_commit_dates,
    )
    verdict_findings = check_verdict_drift(edge_rows, review_time_verdicts, current_verdicts)
    return cited_code_findings, verdict_findings


def main(argv: Optional[List[str]] = None) -> int:
    try:
        cited_code_findings, verdict_findings = check_drift_from_git()
    except subprocess.CalledProcessError as e:
        print(f"Mapping drift check (report-only, never fails): SKIPPED -- "
              f"git command failed: {e.stderr.strip()}")
        return 0

    print(f"Mapping drift check (report-only, never fails): "
          f"{len(cited_code_findings)} cited-code drift finding(s), "
          f"{len(verdict_findings)} verdict drift finding(s)")
    if cited_code_findings:
        print("\nCited code changed since the mapping row's own review date:")
        for f in cited_code_findings:
            print(f"  {f.rule_id} -> {f.mechanism_id} ({f.edge_type}), reviewed {f.row_date}: "
                  f"{', '.join(f.changed_paths)}")
    if verdict_findings:
        print("\nMapped mechanism's verdict changed since the mapping row's own review date:")
        for f in verdict_findings:
            print(f"  {f.rule_id} -> {f.mechanism_id}, reviewed {f.row_date}: "
                  f"{f.old_verdict} -> {f.new_verdict}")
    return 0  # Always 0 -- this check never fails the build.


if __name__ == "__main__":
    sys.exit(main())
