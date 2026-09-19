#!/usr/bin/env python3
"""
Report-only check: flag a PR/diff that changes `implemented_by`-cited code without touching the
citing mechanism's own registry entry.

TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION. Now that `implemented_by` is a
structured, checkable fact (`TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING`), a mechanical check
can compare a diff's changed files against every mechanism's own citations: if code cited by a
mechanism changed and that mechanism's own registry entry (`state`, `depends_on`, `verified`,
`implemented_by` itself) did NOT change in the same diff, that's worth a human look -- the
mechanical version of the parity ledger's own decayed "update your entry when behavior changes"
rule (`docs/plans/mechanism_claims_as_tests_initiative.md` §6 Non-goals).

Two entry points, deliberately separated:
  - `check_drift(old_data, new_data, changed_files)` -- the pure, testable core. Takes two already-
    loaded registry dicts (old/new) and a set of changed file paths; returns every mechanism whose
    `implemented_by` citation includes a changed file, annotated with whether its own entry also
    changed. No git dependency, no subprocess -- this is what the tests exercise directly.
  - `check_drift_from_git(base_ref, head_ref)` -- the CLI's own git-diff wrapper: resolves changed
    files via `git diff --name-only`, loads the registry at both refs via `git show`, and calls
    `check_drift()`.

Report-only, same convention as every other detector in this corpus -- never fails the build.
Not wired into CI (same as `mechanism_state_caller_check.py`/`mechanism_wiring_map_classdef.py`,
neither of which is CI-wired either); invoked via `make mechanism-registry-changed-code-check`.

A second, related signal reported separately: mechanisms whose `implemented_by` was REPLACED
(already had a citation, now points somewhere different) rather than bound for the first time.
Cheap to compute from the same old/new comparison already in hand, and a replacement is a stronger
claim than a first binding -- it deserves to be visible in review on its own terms (found real,
concretely: `trauma`'s own same-session misattribution, `TCK-20260916-MECHANISM-STATUS-LANGUAGE-
DETECTION`'s own Completion Summary, was exactly an `implemented_by` replacement that a reviewer
seeing it flagged this way might have caught).

Usage:
  python3 tools/mechanism_registry/mechanism_registry_changed_code_check.py [--base REF] [--head REF]
    # defaults: --base origin/main --head HEAD
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REGISTRY_REL_PATH = "registries/mechanisms.yaml"

sys.path.insert(0, str(_REPO_ROOT / "tools" / "mechanism_registry"))
from registry import parse_implemented_by_entry  # noqa: E402


@dataclass(frozen=True)
class DriftFinding:
    mechanism_id: str
    changed_cited_files: List[str]


@dataclass(frozen=True)
class ReplacementFinding:
    mechanism_id: str
    old_implemented_by: List[str]
    new_implemented_by: List[str]


def _mechanisms_by_id(data: dict) -> Dict[str, dict]:
    return {m["id"]: m for m in data.get("mechanisms", []) or [] if m.get("id")}


def _cited_paths(mech: dict) -> List[str]:
    return [parse_implemented_by_entry(e)[0] for e in (mech.get("implemented_by") or [])]


def check_drift(
    old_data: dict, new_data: dict, changed_files: Set[str],
) -> List[DriftFinding]:
    """Pure core: which mechanisms have a changed cited file but an unchanged own entry."""
    old_mechs = _mechanisms_by_id(old_data)
    new_mechs = _mechanisms_by_id(new_data)

    findings: List[DriftFinding] = []
    for mid, mech in new_mechs.items():
        cited = _cited_paths(mech)
        changed_cited = sorted(p for p in cited if p in changed_files)
        if not changed_cited:
            continue
        if old_mechs.get(mid) == mech:
            findings.append(DriftFinding(mechanism_id=mid, changed_cited_files=changed_cited))
    return findings


def check_replacements(old_data: dict, new_data: dict) -> List[ReplacementFinding]:
    """Pure core: which mechanisms had implemented_by REPLACED (already had one, now points
    somewhere different) rather than bound for the first time. Independent of `changed_files` --
    this only compares the two registry snapshots."""
    old_mechs = _mechanisms_by_id(old_data)
    new_mechs = _mechanisms_by_id(new_data)

    findings: List[ReplacementFinding] = []
    for mid, mech in new_mechs.items():
        old_mech = old_mechs.get(mid)
        if not old_mech:
            continue
        old_ib = old_mech.get("implemented_by") or []
        new_ib = mech.get("implemented_by") or []
        if old_ib and new_ib and old_ib != new_ib:
            findings.append(ReplacementFinding(
                mechanism_id=mid, old_implemented_by=old_ib, new_implemented_by=new_ib,
            ))
    return findings


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True,
    )
    return result.stdout


def get_changed_files(base_ref: str, head_ref: str = "HEAD") -> Set[str]:
    out = _git("diff", "--name-only", f"{base_ref}...{head_ref}")
    return {line.strip() for line in out.splitlines() if line.strip()}


def load_registry_at_ref(ref: str) -> dict:
    """`ref` may be a real git ref, or the literal string "WORKTREE" to read the file straight off
    disk (uncommitted changes) instead of a committed ref."""
    if ref == "WORKTREE":
        with open(_REPO_ROOT / _REGISTRY_REL_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    out = _git("show", f"{ref}:{_REGISTRY_REL_PATH}")
    return yaml.safe_load(out) or {}


def check_drift_from_git(
    base_ref: str, head_ref: str = "HEAD",
) -> tuple[List[DriftFinding], List[ReplacementFinding]]:
    changed_files = get_changed_files(base_ref, head_ref)
    old_data = load_registry_at_ref(base_ref)
    new_data = load_registry_at_ref(head_ref if head_ref != "HEAD" else "WORKTREE")
    return check_drift(old_data, new_data, changed_files), check_replacements(old_data, new_data)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args(argv)

    try:
        drift, replacements = check_drift_from_git(args.base, args.head)
    except subprocess.CalledProcessError as e:
        print(f"Changed-code-entry-drift check (report-only, never fails): SKIPPED -- "
              f"git diff against {args.base!r} failed: {e.stderr.strip()}")
        return 0

    print(f"Changed-code-entry-drift check (report-only, never fails): "
          f"{len(drift)} drift finding(s), {len(replacements)} implemented_by replacement(s)")
    if drift:
        print("\nCode cited by a mechanism changed, but that mechanism's own entry did not:")
        for f in drift:
            print(f"  {f.mechanism_id}: {', '.join(f.changed_cited_files)}")
    if replacements:
        print("\nimplemented_by REPLACED (already had a citation, now points elsewhere) -- worth "
              "a closer look than a first binding:")
        for r in replacements:
            print(f"  {r.mechanism_id}: {r.old_implemented_by} -> {r.new_implemented_by}")
    return 0  # Always 0 -- this check never fails the build.


if __name__ == "__main__":
    sys.exit(main())
