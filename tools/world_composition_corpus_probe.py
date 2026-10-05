"""Corpus probe for composition-time silent drops and overwrites.

Measures four suspicions over every ``data/worlds/*`` composition, per world, and reports the count
whatever it is (zero is a valid result):

``duplicate_place_ids``
    Place ids that appear more than once in the resolved ``WorldSpec`` (two modules contributing the
    same id), and how many places the compiler's bare ``places[p_spec.id] = ...`` assignment lost.
``dropped_placements``
    Populations, resource nodes and buildings naming a region the spec does not define. The
    compile-time guard now raises for these, so this is expected to be zero; it is reported so the
    count exists per world.
``faction_merge``
    Faction ids a module contributes that the resolver had not already seeded from the catalog, and
    ids contributed with differing definitions. The first-wins merge in the resolver can only change
    a result in one of those two cases.
``biome_provenance``
    Regions whose recorded provenance biome differs from the biome of the region the module authored,
    because the resolver recovers a namespaced region's catalog definition with ``split("_", 1)[1]``.

``validator_residue`` additionally runs each ``WorldValidator`` rule on the resolved spec and counts
the issues per rule, which shows what the validator would flag beyond region-reference resolution.

The detectors are pure functions over plain data so a deliberate instance can prove each one fires
(tests/tools/test_world_composition_corpus_probe.py). Output is ``.jsonl``, one row per world and
check. Read-only: nothing under ``data/`` is written.

Usage: ``python3 tools/world_composition_corpus_probe.py --out <path>.jsonl``
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.content.repository import CatalogRepository  # noqa: E402
from src.worldassembly.resolve_io import load_composition_spec, load_content_repositories  # noqa: E402
from src.worldassembly.resolver import WorldAssemblyResolver  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.validator import WorldValidator  # noqa: E402

CHECKS = (
    "duplicate_place_ids",
    "dropped_placements",
    "faction_merge",
    "biome_provenance",
    "validator_residue",
)


# --------------------------------------------------------------------------------------
# Pure detectors
# --------------------------------------------------------------------------------------

def duplicate_place_ids(spec: Any) -> Dict[str, Any]:
    """Ids that occur more than once across every region's ``places`` in ``spec``."""
    ids = [p.id for region in spec.regions for p in getattr(region, "places", [])]
    counts = Counter(ids)
    duplicates = sorted(pid for pid, n in counts.items() if n > 1)
    return {"places_declared": len(ids), "duplicate_ids": duplicates, "count": len(duplicates)}


def dropped_placements(spec: Any) -> Dict[str, Any]:
    """Placements naming a region the spec does not define (what the compile loops used to skip)."""
    region_ids = {r.id for r in spec.regions}
    dangling: List[str] = []
    dangling += [f"population:{p.id}->{p.spawn_region}" for p in spec.entities if p.spawn_region not in region_ids]
    dangling += [f"resource:{r.id}->{r.region}" for r in spec.resources if r.region not in region_ids]
    dangling += [f"building:{b.id}->{b.region}" for b in spec.buildings if b.region not in region_ids]
    return {"dangling": dangling, "count": len(dangling)}


def faction_merge(
    seeded_ids: Iterable[str],
    contributions: Sequence[Tuple[str, Sequence[Any]]],
) -> Dict[str, Any]:
    """Cases where the resolver's first-wins faction merge could change a result.

    ``contributions`` is ``[(module_id, [FactionSpec, ...]), ...]``. A contribution matters only if the
    id was not pre-seeded (its branch is then the one that runs) or if two contributions of the same id
    disagree (first-wins then hides one of them).
    """
    seeded = set(seeded_ids)
    not_seeded: List[str] = []
    by_id: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    total = 0
    for module_id, facs in contributions:
        for fac in facs:
            total += 1
            if fac.id not in seeded:
                not_seeded.append(f"{module_id}:{fac.id}")
            by_id[fac.id].append((module_id, json.dumps(fac.model_dump(), sort_keys=True, default=str)))
    differing = sorted(
        fid for fid, entries in by_id.items() if len({definition for _, definition in entries}) > 1
    )
    return {
        "contributions": total,
        "not_pre_seeded": sorted(not_seeded),
        "differing_definitions": differing,
        "count": len(not_seeded) + len(differing),
    }


def biome_provenance(
    regions: Sequence[Tuple[str, str, str]],
    catalog: Any,
    records: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare recorded provenance biome with the biome of the region the module authored.

    ``regions`` is ``[(module_id, prefix, merged_region_id), ...]``. The authored id is the merged id
    with ``prefix`` removed; its catalog definition is the truth the provenance should match.
    """
    mismatches: List[Dict[str, Any]] = []
    namespaced = 0
    for module_id, prefix, merged_id in regions:
        authored_id = merged_id[len(prefix):] if prefix and merged_id.startswith(prefix) else merged_id
        authored_def = catalog.get_region(authored_id)
        expected = authored_def.biome if authored_def else None
        record = records.get(merged_id)
        actual = (record.profiles or {}).get("biome") if record is not None else None
        if prefix:
            namespaced += 1
        if expected != actual:
            mismatches.append(
                {
                    "module": module_id,
                    "region": merged_id,
                    "authored_id": authored_id,
                    "expected_biome": expected,
                    "recorded_biome": actual,
                    "namespaced": bool(prefix),
                }
            )
    return {
        "regions_checked": len(regions),
        "namespaced_regions": namespaced,
        "mismatches": mismatches,
        "count": len(mismatches),
    }


def validator_residue(spec: Any, catalog: Optional[CatalogRepository]) -> Dict[str, Any]:
    """Issue counts per ``WorldValidator`` rule id, running each rule without raising."""
    validator = WorldValidator(catalog_repo=catalog)
    per_rule: Counter = Counter()
    errors = 0
    for rule in validator.rules:
        for issue in rule.validate(spec):
            per_rule[issue.rule_id] += 1
            if issue.severity == "ERROR":
                errors += 1
    return {"per_rule": dict(sorted(per_rule.items())), "errors": errors, "count": sum(per_rule.values())}


# --------------------------------------------------------------------------------------
# Collection
# --------------------------------------------------------------------------------------

def probe_composition(
    composition: Any,
    catalog: CatalogRepository,
    module_repo: Any,
    *,
    compile_seed: int = 42,
) -> List[Dict[str, Any]]:
    """Resolve and compile one composition, returning one row per check."""
    world_id = composition.world_id
    resolver = WorldAssemblyResolver(catalog, module_repo)
    captured: List[Tuple[str, str, Any]] = []
    original = resolver.resolve_module_contribution

    def recording(spec: Any, prefix: str, param_vals: Any) -> Any:
        contribution = original(spec, prefix, param_vals)
        captured.append((spec.module_id, prefix, contribution))
        return contribution

    resolver.resolve_module_contribution = recording  # type: ignore[method-assign]
    bundle = resolver.assemble(composition)
    spec = bundle.world_spec

    rows: List[Dict[str, Any]] = []

    place_row = duplicate_place_ids(spec)
    try:
        state, _report = WorldCompiler.compile(spec, seed=compile_seed, context=bundle.compile_context)
        place_row["places_in_compiled_state"] = len(state.places)
        place_row["places_lost_at_compile"] = place_row["places_declared"] - len(state.places)
        place_row["compile_error"] = None
    except Exception as exc:  # noqa: BLE001 - a probe reports, it does not decide
        place_row["places_in_compiled_state"] = None
        place_row["places_lost_at_compile"] = None
        place_row["compile_error"] = f"{type(exc).__name__}: {exc}"
    rows.append({"world": world_id, "check": "duplicate_place_ids", **place_row})

    rows.append({"world": world_id, "check": "dropped_placements", **dropped_placements(spec)})

    faction_row = faction_merge(
        catalog.factions.keys() if hasattr(catalog, "factions") else [],
        [(module_id, list(c.factions)) for module_id, _prefix, c in captured],
    )
    seeded_from_module = sorted(
        rid
        for rid, rec in bundle.provenance_manifest.records.items()
        if rec.element_type == "faction" and rec.source_module is not None and rid in catalog.factions
    )
    faction_row["faction_records_with_a_source_module"] = seeded_from_module
    rows.append({"world": world_id, "check": "faction_merge", **faction_row})

    region_triples = [
        (module_id, prefix, region.id) for module_id, prefix, c in captured for region in c.regions
    ]
    rows.append(
        {
            "world": world_id,
            "check": "biome_provenance",
            **biome_provenance(region_triples, catalog, bundle.provenance_manifest.records),
        }
    )

    rows.append({"world": world_id, "check": "validator_residue", **validator_residue(spec, catalog)})
    return rows


def run_probe(
    worlds_dir: str = "data/worlds",
    world_ids: Optional[Sequence[str]] = None,
    catalog_root: str = "data/content",
    modules_dir: Optional[str] = None,
    compile_seed: int = 42,
) -> List[Dict[str, Any]]:
    """Probe every ``<worlds_dir>/*/world.yaml`` composition (or just ``world_ids``)."""
    catalog, module_repo = load_content_repositories(catalog_root, modules_dir)
    rows: List[Dict[str, Any]] = []
    for path in sorted(Path(worlds_dir).glob("*/world.yaml")):
        if world_ids is not None and path.parent.name not in world_ids:
            continue
        composition = load_composition_spec(path)
        try:
            rows.extend(probe_composition(composition, catalog, module_repo, compile_seed=compile_seed))
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {"world": composition.world_id, "check": "probe_error", "count": None, "error": f"{type(exc).__name__}: {exc}"}
            )
    return rows


def write_jsonl(rows: Iterable[Dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            n += 1
    return n


def summarize(rows: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Per check: worlds probed, worlds with a non-zero count, total count."""
    out: Dict[str, Dict[str, int]] = {}
    for check in CHECKS + ("probe_error",):
        subset = [r for r in rows if r.get("check") == check]
        if not subset:
            continue
        out[check] = {
            "worlds": len(subset),
            "worlds_nonzero": sum(1 for r in subset if (r.get("count") or 0) > 0),
            "total": sum((r.get("count") or 0) for r in subset),
        }
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True, help="Output .jsonl path (one row per world and check)")
    parser.add_argument("--worlds-dir", default="data/worlds")
    parser.add_argument("--world", action="append", help="Restrict to a world id (repeatable)")
    args = parser.parse_args(argv)
    if not str(args.out).endswith(".jsonl"):
        parser.error("--out must end in .jsonl (.json is dropped by .gitignore under stored_artifacts/)")
    rows = run_probe(worlds_dir=args.worlds_dir, world_ids=args.world)
    n = write_jsonl(rows, Path(args.out))
    print(f"wrote {n} rows to {args.out}")
    for check, stats in summarize(rows).items():
        print(f"{check:20s} worlds={stats['worlds']:2d} nonzero={stats['worlds_nonzero']:2d} total={stats['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
