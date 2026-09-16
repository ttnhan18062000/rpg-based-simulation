#!/usr/bin/env python3
"""
Recurring completeness check for the mechanism registry's own node set.

TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS found the registry's node set incomplete: it
was seeded from `docs/brainstorm/rpg_feature_atlas.html` alone (75 mechanisms), never from a real
enumeration of `src/domains/`/`src/systems/`. That enumeration found 11 real, wired mechanisms the
atlas never carded. This tool makes that enumeration a standing, repeatable check instead of a
one-off pass whose method lived only in prose -- per peer review, a one-off pass this good is
worthless the moment the next module lands, since nothing re-runs it.

**This checks against `implemented_by`, not prose.** An earlier draft of this tool regex-searched
`mechanisms.yaml`'s raw text for path-shaped citations. That failed hard on its first real run: the
original 75 mechanisms have ZERO source-path citations anywhere in `mechanisms.yaml` -- their
evidence (`stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md`) cites
atlas card IDs and wiring-map node names, never real files. A prose-text checker could only ever
see the 11 mechanisms this session cited inline, producing 47 false "unmapped" results on its
first run. `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING` added a real, validated
`implemented_by: [<path>, ...]` field to the schema instead -- structured, checked to exist on
disk, and NOT a second lookup table this tool owns (a hand-authored table would be exactly the kind
of duplicated, unverifiable, second place a code<->mechanism binding could drift, the same failure
shape as the atlas citations themselves).

This encodes the two things that made the manual completeness pass trustworthy, not just its
conclusion:

1. **Re-export shim resolution.** Nearly every top-level `src/systems/*.py` file is a 2-3 line
   backward-compat re-export shim. Enumerating by real subpackage file (`economy_systems/`,
   `lifecycle_systems/`, `social_systems/`, `strategic_systems/`, `world_systems/`) rather than by
   top-level shim filename is the difference between checking the right thing and checking the
   wrong one entirely.
2. **Never conflate "not yet bound" with "gap."** `implemented_by` is populated for only 11 of 86
   mechanisms today (deliberately -- it grows organically, not backfilled all at once). A code
   target with no matching `implemented_by` entry is therefore NOT reported as a gap or a missing
   mechanism -- most such targets almost certainly already belong to one of the atlas-cited 75, just
   not yet re-cited with a real path. Reporting them as gaps would repeat, in the opposite
   direction, the exact overclaiming failure this whole epic exists to catch. They are reported
   as **unbound (not yet checkable)** -- a distinct, honest bucket from "confirmed infrastructure"
   (EXCLUSIONS, a real recorded decision with a reason) and from "confirmed bound."

**Report-only, same rule as every other detector in this corpus** (see
`tools/mechanism_registry/mechanism_registry_graphify_check.py`'s own docstring for the precedent): this script never
fails the build by itself. Drift enforcement is a separate, explicit regression test
(`tests/unit/tools/test_mechanism_registry_completeness_check.py`) that pins today's known
enumeration/binding/exclusion counts -- if a new module appears, that test fails, forcing a human
decision (bind it, exclude it with a reason, or register a new mechanism) rather than a silent skip.

Usage:
  python3 tools/mechanism_registry/mechanism_registry_completeness_check.py           # human-readable report
  python3 tools/mechanism_registry/mechanism_registry_completeness_check.py --json     # machine-readable report
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _REPO_ROOT / "src" / "domains"
_SYSTEMS_DIR = _REPO_ROOT / "src" / "systems"
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"

# Real _systems subpackages that hold the actual implementations behind the top-level
# backward-compat shims (TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS's own structural
# finding: checking a shim's bare filename against citations is close to meaningless).
_SYSTEMS_SUBPACKAGES = [
    "economy_systems", "lifecycle_systems", "social_systems", "strategic_systems", "world_systems",
]

# Confirmed infrastructure, not a gameplay mechanism -- a real, recorded decision with a reason
# each, not a silent skip (TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS's own Implementation
# Notes: "Confirmed infrastructure, not a gameplay mechanism").
EXCLUSIONS = {
    "domains/feature_packs": (
        "Content-pack loading/balancing config (balance_spec, loader, manifest, profile, "
        "registry). Configuration infrastructure, not a mechanism."
    ),
    "domains/optimization": (
        "feature_flags.py only -- the flag-gating infrastructure itself, referenced constantly "
        "by name throughout the registry as ENABLE_*. Infrastructure."
    ),
    "systems/strategic_systems/cognition_export": (
        "Its own module docstring: 'Read-Only Presenter... exposes persisted strategic state for "
        "debugging and visualization without becoming the source of truth.' A debug/presenter "
        "tool, not a gameplay mechanism."
    ),
}


@dataclass(frozen=True)
class Target:
    id: str
    real_path: Path  # the real filesystem location this target represents (dir for domains, file for systems)


def _domain_targets() -> List[Target]:
    targets = []
    for path in sorted(_DOMAINS_DIR.iterdir()):
        if not path.is_dir() or path.name.startswith("__"):
            continue
        targets.append(Target(id=f"domains/{path.name}", real_path=path))
    return targets


def _systems_targets() -> List[Target]:
    """Enumerates real implementation files directly from each _systems subpackage -- NOT from
    top-level src/systems/*.py shim filenames, which would check the wrong identity entirely (see
    module docstring, point 1)."""
    targets = []
    seen_ids = set()
    for subpkg in _SYSTEMS_SUBPACKAGES:
        subpkg_dir = _SYSTEMS_DIR / subpkg
        if not subpkg_dir.is_dir():
            continue
        for path in sorted(subpkg_dir.glob("*.py")):
            if path.stem == "__init__":
                continue
            target_id = f"systems/{subpkg}/{path.stem}"
            if target_id in seen_ids:
                continue
            seen_ids.add(target_id)
            targets.append(Target(id=target_id, real_path=path))
    return targets


def enumerate_targets() -> List[Target]:
    return _domain_targets() + _systems_targets()


def _implemented_by_paths(mechanisms: List[dict]) -> Dict[str, List[Path]]:
    """mechanism id -> list of resolved, absolute implemented_by paths."""
    result = {}
    for m in mechanisms:
        paths = m.get("implemented_by") or []
        result[m["id"]] = [(_REPO_ROOT / p).resolve() for p in paths]
    return result


def _target_binding(target: Target, bindings: Dict[str, List[Path]]) -> Optional[str]:
    """Returns the mechanism id whose implemented_by covers this target, or None. A domain target
    (a directory) is covered if any bound path lies inside it; a systems target (a file) is
    covered if any bound path resolves to exactly that file."""
    real = target.real_path.resolve()
    for mech_id, paths in bindings.items():
        for p in paths:
            if real.is_dir():
                if p == real or real in p.parents:
                    return mech_id
            else:
                if p == real:
                    return mech_id
    return None


@dataclass
class Report:
    total_mechanisms: int
    mechanisms_with_binding: int
    total_targets: int
    bound: Dict[str, str]  # target id -> mechanism id
    excluded: Dict[str, str]  # target id -> reason
    unbound: List[str]  # target ids neither bound nor excluded -- NOT asserted to be gaps


def build_report(registry_data: dict) -> Report:
    mechanisms = registry_data.get("mechanisms", []) or []
    bindings = _implemented_by_paths(mechanisms)
    mechanisms_with_binding = sum(1 for paths in bindings.values() if paths)

    targets = enumerate_targets()
    bound = {}
    unbound = []
    for target in targets:
        mech_id = _target_binding(target, bindings)
        if mech_id:
            bound[target.id] = mech_id
        elif target.id in EXCLUSIONS:
            continue
        else:
            unbound.append(target.id)

    return Report(
        total_mechanisms=len(mechanisms),
        mechanisms_with_binding=mechanisms_with_binding,
        total_targets=len(targets),
        bound=bound,
        excluded=dict(EXCLUSIONS),
        unbound=sorted(unbound),
    )


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
            "total_mechanisms": report.total_mechanisms,
            "mechanisms_with_binding": report.mechanisms_with_binding,
            "total_targets": report.total_targets,
            "bound": report.bound,
            "excluded": report.excluded,
            "unbound": report.unbound,
        }, indent=2))
        return 0

    print(f"{report.mechanisms_with_binding} of {report.total_mechanisms} mechanisms have a real "
          f"implemented_by code binding.")
    print(f"Enumerated {report.total_targets} mechanism-bearing code targets under "
          f"src/domains/ and src/systems/ (real subpackage files, shims resolved).")
    print(f"{len(report.bound)} confirmed bound to a mechanism via implemented_by.")
    print(f"{len(report.excluded)} confirmed infrastructure exclusion(s), each with a recorded "
          f"reason.")
    print(f"{len(report.unbound)} unbound (not yet checkable) -- NOT asserted to be gaps. Most "
          f"almost certainly belong to one of the atlas-cited mechanisms that has no "
          f"implemented_by yet; they become checkable as that field is backfilled.")
    if report.unbound:
        for t in report.unbound:
            print(f"  - {t}")

    # Report-only: never fails the build by itself. Drift enforcement lives in the paired
    # regression test, not here.
    return 0


if __name__ == "__main__":
    sys.exit(main())
