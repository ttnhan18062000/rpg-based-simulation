#!/usr/bin/env python3
"""
Generates mermaid dependency-priority charts from docs/brainstorm/mechanisms.yaml.

TCK-20260915-MECHANISM-PRIORITY-DERIVATION Scope items 2/4/5. A new, additive artifact type
(dependency axis) alongside the wiring map's existing containment/execution-order/lifecycle
diagrams -- not a replacement for them (see investigation.md's "four axes" finding). Two outputs
from one registry: a text/markdown table for agents, a mermaid chart for humans (Request
Summary's own framing).

Three bounded view types (never the whole 75-node graph -- Out of Scope explicitly excludes that;
mermaid stops being readable near 40 nodes):
  1. Single layer, paginated when the layer exceeds the readability threshold (the `entity` layer,
     43 mechanisms, is a real, immediately-hit case -- not hypothetical).
  2. Ancestors-of(mechanism_id) -- "what does X actually need" (the ticket's own worked example).
  3. Top-N unverified-priority (the flagship view, per peer review's reframing following T2's own
     seed finding: which of the unverified mechanisms to verify next, ordered by
     layer weight * transitive-dependent-count).

Readability is enforced, not documented: any view whose node count would exceed
_MAX_CHART_NODES either paginates or truncates with an explicit note -- never silently emits an
oversized diagram.

Direction is a parameter (`direction="BT"` by default), not a literal baked into a template --
reversing it later is a config change, not a code edit (this session cannot visually verify BT vs
TB subgraph-lane rendering itself; see investigation.md).

Usage:
  python3 tools/generate_mechanism_charts.py layer entity
  python3 tools/generate_mechanism_charts.py ancestors combat_resolution
  python3 tools/generate_mechanism_charts.py top-n --n 25
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _REPO_ROOT / "docs" / "brainstorm" / "mechanisms.yaml"

sys.path.insert(0, str(_REPO_ROOT / "tools"))
from mechanism_registry import (  # noqa: E402
    DependencyCycleError,
    transitive_dependencies_of,
    transitive_dependents,
    unverified_priority_ranking,
)

# Mermaid stops being readable near 40 nodes (design doc's own stated rule of thumb, confirmed
# real and immediately-hit: the `entity` layer alone has 43 mechanisms before any edges are drawn
# -- see investigation.md).
_MAX_CHART_NODES = 40

# Registry state -> a classDef name for these NEW charts. Uses the registry's own six-class
# vocabulary directly as classDef names (unlike the wiring map's four-class classDef, which this
# tool does not touch -- see tools/mechanism_wiring_map_classdef.py for that, separate, derivation).
_CLASSDEF_STYLES = {
    "done": "fill:#e4efe6,stroke:#3f7d5c,stroke-width:2px,color:#232019",
    "partial": "fill:#fdf3d8,stroke:#b8860b,stroke-width:2px,color:#232019",
    "gap": "fill:#f7e4e1,stroke:#b0392f,stroke-width:2px,color:#232019",
    "orphan": "fill:#f7e4e1,stroke:#b0392f,stroke-width:2px,stroke-dasharray: 2 2,color:#232019",
    "gated": "fill:#f7ecd2,stroke:#9a6b0c,stroke-width:2px,stroke-dasharray: 3 3,color:#232019",
    "skeleton": "fill:#eee,stroke:#888,stroke-width:1px,stroke-dasharray: 1 3,color:#232019",
}


def _load_registry(path: Path = _REGISTRY_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _classdef_block() -> str:
    return "\n".join(f"    classDef {state} {style}" for state, style in _CLASSDEF_STYLES.items())


def _node_decl(mech_id: str, state: str) -> str:
    label = mech_id.replace("_", " ")
    return f'    {mech_id}["{label}"]:::{state}'


def _render_diagram(mech_ids: List[str], mechanisms_by_id: Dict[str, dict], dep_map: Dict[str, List[str]], direction: str, title: Optional[str] = None) -> str:
    """Renders one mermaid flowchart for exactly the given mechanism ids, with edges drawn only
    between mechanisms both present in mech_ids (an edge to a mechanism outside this slice would
    reference an undeclared node)."""
    id_set = set(mech_ids)
    lines = [f"flowchart {direction}", _classdef_block(), ""]
    for mid in sorted(mech_ids):
        lines.append(_node_decl(mid, mechanisms_by_id[mid]["state"]))
    lines.append("")
    for mid in sorted(mech_ids):
        for dep in dep_map.get(mid, []):
            if dep in id_set:
                lines.append(f"    {dep} --> {mid}")
    return "\n".join(lines)


def render_layer_chart(data: dict, layer: str, direction: str = "BT", page_size: int = _MAX_CHART_NODES) -> List[str]:
    """One mermaid diagram per page. Paginates when the layer's own mechanism count exceeds the
    readability threshold (AC #5) -- the `entity` layer (43 mechanisms) is a real case, not
    hypothetical. Pages are sorted-by-id slices, not priority-ordered -- pagination here is a
    completeness fallback, not the recommended way to read a large layer (see investigation.md:
    top-N/ancestors-of are the naturally-bounded, actually useful views for `entity` specifically)."""
    mechanisms = data.get("mechanisms", []) or []
    mechanisms_by_id = {m["id"]: m for m in mechanisms}
    dep_map = {m["id"]: m.get("depends_on") or [] for m in mechanisms}
    ids = sorted(m["id"] for m in mechanisms if m.get("layer") == layer)

    pages = [ids[i:i + page_size] for i in range(0, len(ids), page_size)] or [[]]
    return [_render_diagram(page, mechanisms_by_id, dep_map, direction) for page in pages]


def render_ancestors_chart(data: dict, mechanism_id: str, direction: str = "BT") -> str:
    """'What does X actually need' -- the transitive closure of mechanism_id's own depends_on,
    plus mechanism_id itself. Fails loudly (raises) rather than silently truncating if this
    genuinely exceeds the readability threshold -- unlike the layer view, there is no natural
    pagination boundary for one mechanism's own ancestor chain."""
    mechanisms = data.get("mechanisms", []) or []
    mechanisms_by_id = {m["id"]: m for m in mechanisms}
    if mechanism_id not in mechanisms_by_id:
        raise KeyError(f"unknown mechanism id: {mechanism_id}")
    dep_map = {m["id"]: m.get("depends_on") or [] for m in mechanisms}

    ancestors = transitive_dependencies_of(mechanism_id, dep_map)
    ids = sorted(ancestors | {mechanism_id})
    if len(ids) > _MAX_CHART_NODES:
        raise ValueError(
            f"ancestors-of('{mechanism_id}') has {len(ids)} nodes, over the {_MAX_CHART_NODES}-node "
            f"readability threshold, and has no natural pagination boundary -- refusing to emit an "
            f"unreadable diagram (AC #5)"
        )
    return _render_diagram(ids, mechanisms_by_id, dep_map, direction)


def render_top_n_chart(data: dict, n: int = 25, direction: str = "BT") -> str:
    """The flagship view (reframed per peer review): the top-N currently-unverified mechanisms by
    priority (layer weight * transitive-dependent-count) -- 'which one to verify next.' Truncates to
    _MAX_CHART_NODES with an explicit note if n itself is set above the threshold, rather than
    silently emitting an oversized diagram."""
    mechanisms = data.get("mechanisms", []) or []
    mechanisms_by_id = {m["id"]: m for m in mechanisms}
    dep_map = {m["id"]: m.get("depends_on") or [] for m in mechanisms}

    ranking = unverified_priority_ranking(data)
    effective_n = min(n, _MAX_CHART_NODES)
    ids = [row["id"] for row in ranking[:effective_n]]
    diagram = _render_diagram(ids, mechanisms_by_id, dep_map, direction)
    if n > _MAX_CHART_NODES:
        diagram += (
            f"\n%% Truncated to top {_MAX_CHART_NODES} of the requested top {n} "
            f"(readability threshold) -- see the text ranking for the full list."
        )
    return diagram


def render_top_n_table(data: dict, n: int = 25) -> str:
    """The text form of the same view, for agents -- 'two outputs from one registry.'"""
    ranking = unverified_priority_ranking(data)[:n]
    lines = ["| Mechanism | Layer | State | Priority | Transitive Dependents |",
             "|---|---|---|---|---|"]
    for row in ranking:
        lines.append(
            f"| `{row['id']}` | {row['layer']} | {row['state']} | {row['priority']} | "
            f"{row['transitive_dependent_count']} |"
        )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="view", required=True)

    layer_p = sub.add_parser("layer")
    layer_p.add_argument("layer_name")
    layer_p.add_argument("--direction", default="BT")

    anc_p = sub.add_parser("ancestors")
    anc_p.add_argument("mechanism_id")
    anc_p.add_argument("--direction", default="BT")

    topn_p = sub.add_parser("top-n")
    topn_p.add_argument("--n", type=int, default=25)
    topn_p.add_argument("--direction", default="BT")
    topn_p.add_argument("--table", action="store_true", help="Print the text table instead of mermaid.")

    args = parser.parse_args(argv)
    data = _load_registry()

    if args.view == "layer":
        pages = render_layer_chart(data, args.layer_name, direction=args.direction)
        for i, page in enumerate(pages, 1):
            if len(pages) > 1:
                print(f"%% Page {i} of {len(pages)}")
            print(page)
            print()
    elif args.view == "ancestors":
        print(render_ancestors_chart(data, args.mechanism_id, direction=args.direction))
    elif args.view == "top-n":
        if args.table:
            print(render_top_n_table(data, n=args.n))
        else:
            print(render_top_n_chart(data, n=args.n, direction=args.direction))
    return 0


if __name__ == "__main__":
    sys.exit(main())
