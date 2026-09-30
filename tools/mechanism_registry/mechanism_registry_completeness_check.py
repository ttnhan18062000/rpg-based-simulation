#!/usr/bin/env python3
"""
Recurring completeness check for the mechanism registry's own node set -- against
`src/domains/` and `src/systems/` (the original tier) plus a wider, rule-based tier over the other
non-infra `src/` directories (added 2026-09-30, see "Wider-scope tier" below), not "the codebase".

TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS found the registry's node set incomplete: it
was seeded from `docs/brainstorm/rpg_feature_atlas.html` alone (75 mechanisms), never from a real
enumeration of `src/domains/`/`src/systems/`. That enumeration found 11 real, wired mechanisms the
atlas never carded. This tool makes that enumeration a standing, repeatable check instead of a
one-off pass whose method lived only in prose -- per peer review, a one-off pass this good is
worthless the moment the next module lands, since nothing re-runs it.

**Scope note, added 2026-09-20 (`TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-
VERIFICATION`), per direct peer review -- read this before citing this tool's own "N unbound"
count as evidence the registry is complete.** This tool's enumeration is `src/domains/*` and
`src/systems/{economy_systems,lifecycle_systems,social_systems,strategic_systems,world_systems}/
*.py` ONLY. It was never widened past its original 2026-09-16 pass. A real, live, wired mechanism
(`src/world/perception/gate.py::PerceptionGate`) was found entirely outside this scope while
investigating an unrelated finding -- a manual sizing pass of the other ~20 non-infra `src/`
top-level directories found 14 more candidates clearing the same "real caller outside its own
file" bar. This tool's own clean report ("0 drift findings") is honest about what it checked, not
a claim that nothing else in `src/` is missing -- see
`docs/plans/mechanism_claims_as_tests_initiative.md` §3.4 and
`TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`, which added the wider tier described below
(the 2026-09-20 paragraph above records why the original two-root tier alone was not enough).

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
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from tools.mechanism_registry.registry import parse_implemented_by_entry

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _REPO_ROOT / "src" / "domains"
_SYSTEMS_DIR = _REPO_ROOT / "src" / "systems"
_REGISTRY_PATH = _REPO_ROOT / "registries" / "mechanisms.yaml"

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


# ---------------------------------------------------------------------------
# Wider-scope tier (TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP)
#
# The domains/systems enumeration above never looked outside those roots. This tier makes the
# one-off 2026-09-20 sizing repeatable: mechanism-shaped classes anywhere else in non-infra
# `src/` that are referenced from a different top-level package but cited by no `implemented_by`.
#
# The rule, stated so a number is never mistaken for a fact about the whole codebase:
#   scope     every `src/**/*.py` except `__init__.py`, tests, top-level files, the two roots the
#             tier above already covers, and the infrastructure top-level dirs in _WIDER_INFRA_DIRS
#   candidate a top-level class whose name ends in one of _WIDER_SUFFIXES
#   unbound   no `implemented_by` entry names the class's file with no symbol, or with this class
#   wired     the class name appears (ast Name/Attribute) in a file under a *different* top-level
#             package, `__init__.py` re-export shims excluded
# The ticket's own 2026-09-20 figure (14 wired candidates) does not reproduce under any explicit
# rule tried; this rule yields the count pinned in the paired test. It is a floor, not a ceiling:
# other naming conventions (Classifier/Filter/Builder/Detector) are not swept, and a bare name match
# can over-count. "Unbound" carries the same caveat as the tier above -- not yet checkable, not
# asserted to be a gap.
# ---------------------------------------------------------------------------
_SRC_DIR = _REPO_ROOT / "src"
_WIDER_INFRA_DIRS = {
    "api", "cli", "certification", "config", "logging", "observability", "perf", "platform",
    "rendering", "replay", "runtime", "testing", "views",
}
_WIDER_SUFFIXES = ("Service", "System", "Gate", "Phase", "Evaluator", "Resolver", "Manager")

# "<repo-relative path>::<Class>" -> reason. Confirmed infrastructure, same standard as EXCLUSIONS.
WIDER_EXCLUSIONS: Dict[str, str] = {
    "src/content/resolver.py::" + name: (
        "Catalog resolver: its module docstring says it 'provides validated, deterministic access to "
        "static catalog data without running any runtime simulation logic'. Content-catalog "
        "infrastructure, not a mechanism."
    )
    for name in (
        "BiomeResolver", "BuildingResolver", "EcologyResolver", "EntityArchetypeResolver",
        "PopulationRecipeResolver", "RegionResolver", "RelationshipResolver", "ResourceResolver",
    )
}
WIDER_EXCLUSIONS.update({
    "src/content/warmup.py::ContentWarmupService": (
        "Eagerly loads content singletons before the first tick (called once from kernel.py). "
        "Runtime start-up plumbing, no gameplay rule."
    ),
    "src/content_semantics/defaults.py::DefaultSemanticsService": (
        "Read-only lookup of fallback properties from default compile profiles; "
        "docs/content/content_semantics_contract.md calls the package advisory, not authoritative "
        "state. Catalog interpretation, not a mechanism."
    ),
    "src/content_semantics/faction.py::FactionSemanticsService": (
        "Read-only interpretation of faction catalog definitions (hostile/protector/bucket "
        "queries). Catalog interpretation, not a mechanism."
    ),
    "src/content_semantics/relation.py::RelationProjectionService": (
        "Projects relation labels from catalog definitions; no state change. Catalog projection, "
        "not a mechanism."
    ),
    "src/content_semantics/role.py::RoleSemanticsService": (
        "Role family / legacy-role mapping / profile lookup over the catalog. Catalog lookup, not a "
        "mechanism."
    ),
    "src/core/cognition.py::PerceivedService": (
        "A frozen dataclass value record (service_id, position, salience) produced by the perception "
        "filter, not a service in the behavioural sense; the name suffix is a false positive."
    ),
    "src/engine/metrics.py::MetricsService": (
        "Extracts metrics for certification reports and the engine manager. Observability plumbing."
    ),
    "src/engine/scenario_runtime.py::ScenarioRuntimeService": (
        "Owns a Kernel for one scenario run (start/pause/step) for harnesses and the REST layer; a "
        "runtime driver. The campaign mechanism it serves is already bound as `campaigns`."
    ),
    "src/engine/spatial_query.py::SpatialQueryService": (
        "Its docstring: 'Optimized spatial queries using cached indices'. Cache and lookup "
        "infrastructure used by several mechanisms, none of its own."
    ),
    "src/entities/identity_resolver.py::EntityIdentityResolver": (
        "Its docstring: 'Single identity access layer' -- catalog-first read with legacy-enum "
        "fallback, loads nothing. A pure lookup with no rule of its own."
    ),
})



# "<repo-relative path>::<Class>" -> note. Wired, unbound, and NOT yet dispositioned: the identity
# question (bind to an existing mechanism, or register a new one) is an RPG-domain call that has not
# been made. Pinned so the residue stays visible and a new candidate cannot appear silently.
WIDER_PENDING: Dict[str, str] = {
    "src/progression/skills.py::SkillScalingService": (
        "Same-named twin of src/engine/rpg_depth.py::SkillScalingService (bound to `derived_stats`). "
        "Every caller imports the rpg_depth class; this one has no caller anywhere in src/ and 0 calls "
        "at runtime. Not registered as a mechanism (rpg-feature-planning 2026-09-30): a dead-code "
        "duplicate, filed as a defect (TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS)."
    ),
    "src/strategy/cognition_capacity.py::CapacityService": (
        "Same-named twin of src/strategy/capacity.py::CapacityService (bound to "
        "`cognition_capacity_fatigue`, the live one). `cognition_capacity_fatigue`'s own note records "
        "that this class's only caller is never called; 0 calls at runtime. Bind decision deferred "
        "with the defect (TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS)."
    ),
    "src/world/perception/gate.py::PerceptionGate": (
        "Wired (engine/behavior_consumers.py), 1872 runtime calls, sole production call is combat "
        "targeting at engine/tactical.py:199. Proposed `sense_gated_detection` (entity), scoped to "
        "combat-targeting gating. Held by rpg-feature-planning until their perception-contract "
        "relabelling lands, so the two records do not contradict on the day they are written."
    ),
}


@dataclass(frozen=True)
class WiderCandidate:
    id: str  # "<repo-relative path>::<Class>"
    top: str  # top-level src package
    callers: tuple  # sorted repo-relative paths of files in *other* top-level packages


def _wider_top(path: Path) -> str:
    return path.relative_to(_SRC_DIR).parts[0]


def _wider_bound_symbols(mechanisms: List[dict]) -> Dict[str, set]:
    """repo-relative path -> set of bound symbols; an empty-string member means file-level."""
    out: Dict[str, set] = {}
    for m in mechanisms:
        for entry in m.get("implemented_by") or []:
            rel, sym = parse_implemented_by_entry(entry)
            # "Class::method" binds the class for this file-level question.
            out.setdefault(rel, set()).add(sym.split("::", 1)[0] if sym else "")
    return out


def enumerate_wider_candidates(mechanisms: List[dict]) -> Dict[str, object]:
    files = sorted(p for p in _SRC_DIR.rglob("*.py") if "tests" not in p.parts)
    trees = {}
    for p in files:
        try:
            trees[p] = ast.parse(p.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
    used = {
        p: {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
        | {n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)}
        for p, t in trees.items()
    }
    skip_tops = _WIDER_INFRA_DIRS | {"domains", "systems"}
    scope = [
        p for p in trees
        if p.name != "__init__.py" and len(p.relative_to(_SRC_DIR).parts) > 1
        and _wider_top(p) not in skip_tops
    ]
    bound_syms = _wider_bound_symbols(mechanisms)

    def _rel(p: Path) -> str:
        return str(p.relative_to(_REPO_ROOT))

    def _is_bound(p: Path, cls: str) -> bool:
        syms = bound_syms.get(_rel(p), set())
        return "" in syms or cls in syms

    unbound_files = [p for p in scope if _rel(p) not in bound_syms]
    candidates = [
        (p, n.name) for p in scope for n in trees[p].body
        if isinstance(n, ast.ClassDef) and n.name.endswith(_WIDER_SUFFIXES)
        and not _is_bound(p, n.name)
    ]
    wired = []
    for p, cls in candidates:
        callers = sorted(
            _rel(q) for q in trees
            if q != p and q.name != "__init__.py" and cls in used[q] and _wider_top(q) != _wider_top(p)
        )
        if callers:
            wired.append(WiderCandidate(f"{_rel(p)}::{cls}", _wider_top(p), tuple(callers)))
    return {
        "scope_files": len(scope),
        "unbound_files": len(unbound_files),
        "candidates": len(candidates),
        "wired": sorted(wired, key=lambda c: c.id),
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
    """mechanism id -> list of resolved, absolute implemented_by paths. Node-set completeness is
    a file-level question ("is this file covered by some mechanism") -- an entry's optional
    "::Symbol" suffix (TCK-20260916-MECHANISM-IMPLEMENTED-BY-SYMBOL-LEVEL-BINDING) is dropped
    here; the symbol distinction matters for the caller-count checker, not for this one."""
    result = {}
    for m in mechanisms:
        entries = m.get("implemented_by") or []
        paths = [parse_implemented_by_entry(e)[0] for e in entries]
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
    # `state: gap` means no implementing code exists, so `implemented_by` does not apply to it
    # (TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION). Reported under its own heading
    # and left out of the "unbound" coverage figure, so a gap never reads as a coverage hole.
    gap_mechanisms: List[str] = field(default_factory=list)
    unbound_real_state: List[str] = field(default_factory=list)  # non-gap, no implemented_by
    wider: Dict[str, object] = field(default_factory=dict)  # enumerate_wider_candidates() result
    wider_unresolved: List[str] = field(default_factory=list)  # wired, neither excluded nor pending


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

    gap_mechanisms = sorted(m["id"] for m in mechanisms if m.get("state") == "gap")
    unbound_real_state = sorted(
        m["id"] for m in mechanisms if m.get("state") != "gap" and not bindings.get(m["id"])
    )

    wider = enumerate_wider_candidates(mechanisms)
    wider_unresolved = sorted(
        c.id for c in wider["wired"]
        if c.id not in WIDER_EXCLUSIONS and c.id not in WIDER_PENDING
    )

    return Report(
        wider=wider,
        wider_unresolved=wider_unresolved,
        gap_mechanisms=gap_mechanisms,
        unbound_real_state=unbound_real_state,
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
            "gap_mechanisms": report.gap_mechanisms,
            "unbound_real_state": report.unbound_real_state,
            "wider": {
                "scope_files": report.wider["scope_files"],
                "unbound_files": report.wider["unbound_files"],
                "candidates": report.wider["candidates"],
                "wired": {c.id: list(c.callers) for c in report.wider["wired"]},
                "excluded": WIDER_EXCLUSIONS,
                "pending": WIDER_PENDING,
                "unresolved": report.wider_unresolved,
            },
        }, indent=2))
        return 0

    applicable = report.total_mechanisms - len(report.gap_mechanisms)
    print(f"{report.mechanisms_with_binding} of {report.total_mechanisms} mechanisms have a real "
          f"implemented_by code binding.")
    print(f"{len(report.gap_mechanisms)} are state: gap -- no implementing code exists, so "
          f"implemented_by does not apply; not counted as unbound. Coverage where it applies: "
          f"{report.mechanisms_with_binding} of {applicable}.")
    if report.unbound_real_state:
        print(f"{len(report.unbound_real_state)} non-gap mechanism(s) still without implemented_by: "
              f"{', '.join(report.unbound_real_state)}")
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

    w = report.wider
    wired_ids = [c.id for c in w["wired"]]
    print()
    print(f"Wider scope (non-infra src/ outside domains/ and systems/): {w['scope_files']} files, "
          f"{w['unbound_files']} cited by no implemented_by, {w['candidates']} unbound "
          f"mechanism-shaped classes, {len(wired_ids)} of them referenced from another top-level "
          f"package. A floor, not a ceiling (see the wider-scope note in this file); unbound is "
          f"not asserted to be a gap.")
    print(f"  {sum(1 for i in wired_ids if i in WIDER_EXCLUSIONS)} recorded infrastructure "
          f"exclusion(s), {sum(1 for i in wired_ids if i in WIDER_PENDING)} pending an identity "
          f"decision, {len(report.wider_unresolved)} undispositioned.")
    for i in report.wider_unresolved:
        print(f"  - UNDISPOSITIONED {i}")

    # Report-only: never fails the build by itself. Drift enforcement lives in the paired
    # regression test, not here.
    return 0


if __name__ == "__main__":
    sys.exit(main())
