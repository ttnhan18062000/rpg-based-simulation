#!/usr/bin/env python3
"""
Manage the append-only mechanism `systems:` registry (registries/system_registry.jsonl).

Built for TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION. Mirrors `tools/layer_registry.py`'s
design (append-only JSONL, one entry per line, `add_system()` refuses to re-add an existing
system, CLI `add`/`list` commands) — read that module first if this one is unclear, it is the
direct template. A `system` is a declared, hand-authored membership grouping on a mechanism
(`registries/mechanisms.yaml`'s own `systems: []` field) — the review lens the
system-membership-value investigation found worth building, not a mechanical/derived property.

Two things this registry deliberately does NOT do, unlike `layer`/`tag`:
  - **It does not itself hold membership.** A system's members live on each mechanism's own
    `systems: []` list (declared-on-mechanism, per the foundation ticket's own §2 rationale — a
    separate membership list here would be a second place holding mechanism ids, and a renamed
    mechanism would leave a dangling reference). This registry only records that a system NAME
    exists and is legitimate to reference.
  - **It is checked for orphans, unlike `layer`/`tag`.** `registry.py::validate()`'s own
    invariant #9/#10 (see that module) fails if a registered system has zero mechanisms declaring
    it — a system that fits `layer`/`tag`'s own "registered but temporarily unused" tolerance is
    dead vocabulary here, since the entire value of this registry is a curated review lens, not an
    open-ended tagging vocabulary.

Usage:
  python3 tools/mechanism_registry/system_registry.py add <system> --note "why this system exists"
  python3 tools/mechanism_registry/system_registry.py list
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical-form rule — mirrors layer_registry.py::canonical_form_violation's shape.
# ---------------------------------------------------------------------------

_CANONICAL_SYSTEM_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def canonical_form_violation(system: str) -> str | None:
    """Return a human-readable violation message if `system` is not in canonical form, else None.

    Canonical form: lowercase, underscore-separated (matches the 7 seed values' own convention:
    combat, progression, cognition, social, faction, economy, world).
    """
    if not _CANONICAL_SYSTEM_RE.match(system):
        return (
            f"{system!r} is not canonical form (use lowercase, underscore-separated, e.g. "
            f"{system.lower().replace('-', '_')!r})"
        )
    return None


# ---------------------------------------------------------------------------
# Registry file I/O — structurally identical to layer_registry.py's.
# ---------------------------------------------------------------------------

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent
_REGISTRY_REL_PATH = Path("registries/system_registry.jsonl")


def registry_path(root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else _DEFAULT_ROOT
    return base / _REGISTRY_REL_PATH


def load_registry(root: Path | str | None = None) -> dict:
    """Return {system: entry_dict} for every registered system. Empty dict if the file doesn't
    exist yet.

    Raises ValueError on a duplicate system registration — the file must never contain the same
    system twice; that would violate the append-only-unique-system invariant `add_system()`
    otherwise guarantees.
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
        system = entry["system"]
        if system in registry:
            raise ValueError(
                f"{path}: duplicate registration for system {system!r} at line {lineno} — "
                f"the registry must contain each system exactly once"
            )
        registry[system] = entry
    return registry


def is_system_registered(system: str, registry: dict) -> bool:
    """True if `system` is in the registry."""
    return system in registry


def check_systems_registered(systems: list[str], root: Path | str | None = None) -> list[str]:
    """Return the subset of `systems` that are NOT registered.

    Plural-input helper mirroring `layer_registry.py::check_layers_registered`'s shape, but
    genuinely plural here (unlike `layer`, a mechanism's own `systems: []` can hold several
    values) — useful for validating one mechanism's full membership list in one call.
    """
    registry = load_registry(root)
    return [system for system in systems if not is_system_registered(system, registry)]


def add_system(system: str, note: str = "", root: Path | str | None = None) -> dict:
    """Append a new system registration. Returns the entry written.

    Raises ValueError if: `system` is not canonical form, or `system` is already registered
    (systems can only be added, never updated or re-added).
    """
    violation = canonical_form_violation(system)
    if violation:
        raise ValueError(f"cannot register {system!r}: {violation}")

    registry = load_registry(root)
    if system in registry:
        existing = registry[system]
        raise ValueError(
            f"{system!r} is already registered (added {existing['added_date']}) — "
            f"systems cannot be re-added or changed"
        )

    entry = {
        "system": system,
        "added_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note": note,
    }

    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    return entry


def system_values(root: Path | str | None = None) -> frozenset[str]:
    """Return the full set of currently-registered system names."""
    return frozenset(load_registry(root).keys())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage the append-only mechanism-systems registry (registries/system_registry.jsonl)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser(
        "add", help="Register a new system (append-only — cannot update or delete an existing system)"
    )
    add_p.add_argument("system")
    add_p.add_argument("--note", default="", help="Why this system is being added")
    add_p.add_argument("--root", default=None)

    list_p = sub.add_parser("list", help="Print all registered systems")
    list_p.add_argument("--root", default=None)

    args = parser.parse_args()

    if args.command == "add":
        try:
            entry = add_system(args.system, args.note, root=args.root)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Registered system {entry['system']!r} ({entry['added_date']}).")
        return

    if args.command == "list":
        registry = load_registry(args.root)
        for system in sorted(registry):
            entry = registry[system]
            print(f"{system:<16} {entry['added_date']}  {entry.get('note', '')}")
        return


if __name__ == "__main__":
    main()
