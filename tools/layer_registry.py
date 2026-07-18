#!/usr/bin/env python3
"""
Manage the append-only ticket/doc `layer:` registry (docs/guidelines/layer_registry.jsonl).

Built for TCK-20260718-LAYER-REGISTRY-CONVERSION. Mirrors `tools/tag_registry.py`'s design
(append-only JSONL, one entry per line, `add_layer()` refuses to re-add an existing layer, CLI
`add`/`list` commands) — read that module first if this one is unclear, it is the direct template.
Converts `LAYER_VALUES` (`tools/validate_frontmatter.py`) from a hardcoded Python `set` literal,
which required a code change/PR/review to add a new legitimate value, into the same kind of
registry-file-backed, append-only process `Tag` already has.

Two structural differences from `Tag`, both deliberate, not oversights:
  - `Layer` stays **single-value per ticket** (the `layer:` frontmatter field takes exactly one
    value). This module does not change that cardinality — it only changes where the *set of
    legal values* comes from, not how many a ticket may hold. Single-value enforcement remains
    `validate_frontmatter.py::_check_enum`'s job, unchanged by this module.
  - A `Layer` registry entry has **no `category` field** — unlike `Tag`'s 4-way Subsystem/Process/
    Phase/Quality taxonomy, `Layer` *is* the subsystem-topic dimension itself, so a further
    category split inside it makes no sense. Each entry is just
    `{"layer": ..., "added_date": ..., "note": "why this layer exists"}`.

Usage:
  python3 tools/layer_registry.py add <layer> --note "why this layer exists"
  python3 tools/layer_registry.py list
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical-form rule — mirrors tag_registry.py::canonical_form_violation's shape, simplified:
# Layer has no forbidden-priority-tag concept and no known synonym map (seeded fresh from the
# exact 19 pre-existing LAYER_VALUES, all already lowercase/hyphen-free single words).
# ---------------------------------------------------------------------------

_CANONICAL_LAYER_RE = re.compile(r"^[a-z][a-z0-9-]*$")


def canonical_form_violation(layer: str) -> str | None:
    """Return a human-readable violation message if `layer` is not in canonical form, else None.

    Canonical form: lowercase, hyphen-separated (matches the 19 seed values' own convention —
    none of them currently use a hyphen, but the pattern allows one for a future multi-word layer
    rather than forcing awkward concatenation).
    """
    if not _CANONICAL_LAYER_RE.match(layer):
        return f"{layer!r} is not canonical form (use lowercase, hyphen-separated, e.g. {layer.lower().replace('_', '-')!r})"
    return None


# ---------------------------------------------------------------------------
# Registry file I/O — structurally identical to tag_registry.py's, minus the category field.
# ---------------------------------------------------------------------------

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_REL_PATH = Path("docs/guidelines/layer_registry.jsonl")


def registry_path(root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else _DEFAULT_ROOT
    return base / _REGISTRY_REL_PATH


def load_registry(root: Path | str | None = None) -> dict:
    """Return {layer: entry_dict} for every registered layer. Empty dict if the file doesn't
    exist yet.

    Raises ValueError on a duplicate layer registration — the file must never contain the same
    layer twice; that would violate the append-only-unique-layer invariant `add_layer()` otherwise
    guarantees.
    """
    path = registry_path(root)
    if not path.exists():
        return {}

    registry: dict = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        layer = entry["layer"]
        if layer in registry:
            raise ValueError(
                f"{path}: duplicate registration for layer {layer!r} at line {lineno} — "
                f"the registry must contain each layer exactly once"
            )
        registry[layer] = entry
    return registry


def is_layer_registered(layer: str, registry: dict) -> bool:
    """True if `layer` is in the registry."""
    return layer in registry


def check_layers_registered(layers: list[str], root: Path | str | None = None) -> list[str]:
    """Return the subset of `layers` that are NOT registered.

    Plural-input helper mirroring `tag_registry.py::check_tags_registered`'s shape — a single
    ticket only ever has one `layer:` value, but this is useful for batch/registry-audit callers
    checking many tickets at once without a `load_registry()` call per layer.
    """
    registry = load_registry(root)
    return [layer for layer in layers if not is_layer_registered(layer, registry)]


def add_layer(layer: str, note: str = "", root: Path | str | None = None) -> dict:
    """Append a new layer registration. Returns the entry written.

    Raises ValueError if: `layer` is not canonical form, or `layer` is already registered (layers
    can only be added, never updated or re-added).
    """
    violation = canonical_form_violation(layer)
    if violation:
        raise ValueError(f"cannot register {layer!r}: {violation}")

    registry = load_registry(root)
    if layer in registry:
        existing = registry[layer]
        raise ValueError(
            f"{layer!r} is already registered (added {existing['added_date']}) — "
            f"layers cannot be re-added or changed"
        )

    entry = {
        "layer": layer,
        "added_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note": note,
    }

    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    return entry


def layer_values(root: Path | str | None = None) -> frozenset[str]:
    """Return the full set of currently-registered layer names — the canonical value set
    `tools/validate_frontmatter.py::LAYER_VALUES` is computed from. A frozenset, matching
    `tools/ticket_field_values.py`'s other canonical enums' type.
    """
    return frozenset(load_registry(root).keys())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage the append-only layer registry (docs/guidelines/layer_registry.jsonl)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser(
        "add", help="Register a new layer (append-only — cannot update or delete an existing layer)"
    )
    add_p.add_argument("layer")
    add_p.add_argument("--note", default="", help="Why this layer is being added")
    add_p.add_argument("--root", default=None)

    list_p = sub.add_parser("list", help="Print all registered layers")
    list_p.add_argument("--root", default=None)

    args = parser.parse_args()

    if args.command == "add":
        try:
            entry = add_layer(args.layer, args.note, root=args.root)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Registered layer {entry['layer']!r} ({entry['added_date']}).")
        return

    if args.command == "list":
        registry = load_registry(args.root)
        for layer in sorted(registry):
            entry = registry[layer]
            print(f"{layer:<16} {entry['added_date']}  {entry.get('note', '')}")
        return


if __name__ == "__main__":
    main()
