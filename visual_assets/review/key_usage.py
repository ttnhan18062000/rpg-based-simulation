"""The key-usage report (`TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT`): which visual keys the code references, against the registry, the adopted sources and the latest release candidate.

REPORT ONLY: it reads sources, the registry, the adoption records and the committed candidates, writes nothing and fails nothing (a CI gate belongs to activation). Four findings, each a sorted list:

- `unknown`: a string literal in the scanned code that is exactly a key of a registered family (`terrain.`, `border.`, `icon.`, ...) but is not in the registry (nor an alias): a typo or a key that was never registered.
- `unreferenced`: a registered key no scanned file mentions as a literal. Expected for keys that are only adopted so far; a key built at run time (`terrain.${name}`) is invisible to a literal scan, so the dynamic references are listed too (`dynamic_references`) and an `unreferenced` key under one of their prefixes may be a false positive.
- `adopted_unreleased`: a registered key whose live source revision is adopted but which the latest release candidate does not hold (an adopted icon no candidate covers).
- `fallback_only`: a key (an alias counts for its target) the APPLICATION code (anything outside the isolated `frontend/src/visualAssets` harness) references but the latest candidate does not hold, so it can only ever resolve through its fallback.

`references` also says where each key is mentioned: `app` (application code) or `harness` (the isolated rehearsal and preview pages under `frontend/src/visualAssets`). Tests and fixtures are never scanned. The output is deterministic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from visual_assets.review.pilot_colour_vision import REPO
from visual_assets.store import config, records
from visual_assets.store.catalog.registry import Registry, load_registry

SCAN_ROOTS = ("frontend/src", "src")
SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".py"}
SKIP_PARTS = {"__tests__", "__fixtures__", "node_modules", "__pycache__", "tests", "test"}
HARNESS = "frontend/src/visualAssets/"
_KEY = r"[a-z][a-z0-9_]{0,31}(?:\.[a-z][a-z0-9_]{0,31}){1,3}"


def _literals(text: str):
    """(line number, literal body) for every quoted string on a line; a template literal with `${` never fullmatches a key, so it is never a plain reference."""
    for number, line in enumerate(text.splitlines(), 1):
        for match in re.finditer(r"""(["'`])((?:\\.|(?!\1).)*?)\1""", line):
            yield number, match.group(2)


def scan_references(roots: tuple[str, ...] = SCAN_ROOTS, repo: Path = REPO, families: frozenset[str] = frozenset()) -> tuple[dict[str, list[dict]], list[dict]]:
    """({key: [{file, line, where}]}, [{file, line, prefix}]) over the plain literals that are a key of a given family, and over template literals whose prefix is a family (`terrain.${x}`)."""
    refs: dict[str, list[dict]] = {}
    dynamic: list[dict] = []
    dynamic_re = re.compile(r"`(" + "|".join(sorted(map(re.escape, families))) + r")\.[^`]*\$\{") if families else None
    for root in roots:
        base = repo / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix not in SUFFIXES or any(part in SKIP_PARTS for part in path.relative_to(repo).parts):
                continue
            rel = path.relative_to(repo).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            where = "harness" if rel.startswith(HARNESS) else "app"
            for number, literal in _literals(text):
                if re.fullmatch(_KEY, literal) and literal.split(".")[0] in families:
                    refs.setdefault(literal, []).append({"file": rel, "line": number, "where": where})
            if dynamic_re:
                for number, line in enumerate(text.splitlines(), 1):
                    for match in dynamic_re.finditer(line):
                        dynamic.append({"file": rel, "line": number, "prefix": match.group(1) + "."})
    return {k: sorted(v, key=lambda r: (r["file"], r["line"])) for k, v in sorted(refs.items())}, sorted(dynamic, key=lambda r: (r["file"], r["line"], r["prefix"]))


def adopted_keys() -> set[str]:
    """The visual key of the live (latest unrevoked) revision of every adopted source asset."""
    out: set[str] = set()
    for sid in records.list_source_ids():
        live = [r for r in records.list_revisions(sid) if records.is_eligible(sid, r)]
        if live:
            out.add(records.revision_slot(sid, live[-1])[0])
    return out


def latest_candidate(catalog_id: str = "pilot") -> tuple[str | None, set[str]]:
    """(release id, the visual keys its entries hold) of the highest release candidate of `catalog_id`, or (None, set())."""
    folder = records.manifests_dir() / catalog_id
    files = sorted(folder.glob("rc-*.json")) if folder.is_dir() else []
    if not files:
        return None, set()
    data = json.loads(files[-1].read_text())
    return data["release_id"], {e["visual_key"] for e in data["entries"]}


def build_report(registry: Registry, references: dict[str, list[dict]], dynamic: list[dict], adopted: set[str], release: tuple[str | None, set[str]]) -> dict:
    """The pure comparison (a planted-case test feeds it by hand)."""
    release_id, released = release
    known = set(registry.keys) | set(registry.aliases)
    resolve = lambda key: registry.aliases.get(key, key)  # noqa: E731  (a reference through an alias counts for its target)
    referenced = {resolve(k) for k in references}
    app_referenced = {resolve(k) for k, locs in references.items() if any(loc["where"] == "app" for loc in locs)}
    return {
        "registry_keys": len(registry.keys),
        "latest_release_candidate": release_id,
        "released_keys": sorted(released),
        "unknown": sorted(k for k in references if k not in known),
        "unreferenced": sorted(k for k in registry.keys if k not in referenced),
        "adopted_unreleased": sorted(k for k in registry.keys if k in adopted and k not in released),
        "fallback_only": sorted(k for k in app_referenced if k in registry.keys and k not in released),
        "dynamic_references": dynamic,
        "references": {k: {"app": sum(1 for loc in v if loc["where"] == "app"), "harness": sum(1 for loc in v if loc["where"] == "harness"), "first": v[0]["file"] + ":" + str(v[0]["line"])} for k, v in references.items()},
    }


def report(repo: Path = REPO, roots: tuple[str, ...] = SCAN_ROOTS) -> dict:
    registry = load_registry(config.CATALOG_ROOT / "definitions" / "visual_keys.yaml")
    families = frozenset(d.family for d in registry.keys.values()) | frozenset(k.split(".")[0] for k in registry.keys)
    references, dynamic = scan_references(roots, repo, families)
    return build_report(registry, references, dynamic, adopted_keys(), latest_candidate())


def report_json(**kwargs) -> str:
    return json.dumps(report(**kwargs), indent=1, sort_keys=True) + "\n"
