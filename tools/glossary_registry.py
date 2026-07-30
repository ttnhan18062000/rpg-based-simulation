#!/usr/bin/env python3
"""
Manage the append-only dashboard glossary registry (registries/glossary_registry.jsonl).

Built for TCK-20260718-GLOSSARY-REGISTRY (child of TCK-20260718-GLOSSARY-TOOLTIPS-EPIC). Mirrors
`tools/tag_registry.py`'s design (append-only JSONL, one entry per line, `add_term()` refuses to
re-add an existing term, CLI `add`/`list` commands) — read that module first if this one is
unclear, it is the direct template, chosen over `tools/layer_registry.py`'s flatter shape because
glossary terms, like tags, span multiple distinct domains and benefit from a `category` field.

Purpose: this repo's dashboard renders many short, otherwise-unexplained labels — ticket `## Status`
values, run/gate `final_status` values, `reason_code` values, agent-monitoring event `status`
values, `## Tier`/`## Priority`/`## Type` values — each meaningful only if you already know this
repo's workflow conventions. This registry is the single backend-owned source of a one-sentence
description per term, so the dashboard frontend can render hover tooltips without any description
text hardcoded in `dashboard-frontend/src/*.tsx` (the user's explicit requirement).

One deliberate difference from `tag_registry.py`/`layer_registry.py`: **no canonical-form rule**.
Tag/Layer enforce lowercase-hyphenated form because those are freely-chosen labels this repo wants
consistent. Glossary terms are NOT freely chosen — each is an existing, fixed string this repo's
own code already emits verbatim (`DONE`, `P0`, `ok`, `hotfix`, `dod_condition_failed`), and those
strings' casing is meaningful and non-negotiable (`ok` the event-status value is a different,
unrelated term from `OPEN` the ticket-status value — case-sensitive lookup, deliberately). Forcing
a canonical-form rule onto them would be actively wrong, not just unnecessary.

Categories (`GLOSSARY_CATEGORIES`): `ticket-status`, `run-status`, `reason-code`, `event-status`,
`tier`, `priority`, `type`, `phase`. Unlike Tag's 4-category taxonomy, this set is not meant to grow
openly — it mirrors the fixed small number of enum-like domains this dashboard actually renders. A given
term is registered exactly once even if it is meaningful in more than one domain (e.g. `DONE` means
"complete" whether it is a ticket `## Status` value or a run `final_status` value — one entry, not
two) — pick whichever category is the term's most natural primary home and write a description
that reads correctly in every context the term actually appears.

Usage:
  python3 tools/glossary_registry.py add <term> --category <category> --description "what it means"
  python3 tools/glossary_registry.py list
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Category taxonomy — fixed, not an open/growable set like Tag's (see module docstring).
# ---------------------------------------------------------------------------

GLOSSARY_CATEGORIES = {
    "ticket-status",
    "run-status",
    "reason-code",
    "event-status",
    "tier",
    "priority",
    "type",
    "phase",
}

# ---------------------------------------------------------------------------
# Registry file I/O — structurally identical to tag_registry.py's, minus canonical-form checking
# and with `description` (user-facing tooltip text) instead of `note` (internal why-it-exists
# annotation) as the descriptive field name, since the former is the more accurate name for text
# this module's whole purpose is to serve back to end users.
# ---------------------------------------------------------------------------

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_REL_PATH = Path("registries/glossary_registry.jsonl")


def registry_path(root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else _DEFAULT_ROOT
    return base / _REGISTRY_REL_PATH


def load_registry(root: Path | str | None = None) -> dict:
    """Return {term: entry_dict} for every registered term. Empty dict if the file doesn't exist
    yet.

    Raises ValueError on a duplicate term registration — the file must never contain the same term
    twice; that would violate the append-only-unique-term invariant `add_term()` otherwise
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
        term = entry["term"]
        if term in registry:
            raise ValueError(
                f"{path}: duplicate registration for term {term!r} at line {lineno} — "
                f"the registry must contain each term exactly once"
            )
        registry[term] = entry
    return registry


def is_term_registered(term: str, registry: dict) -> bool:
    """True if `term` is in the registry. Case-sensitive — see module docstring."""
    return term in registry


def add_term(
    term: str, category: str, description: str, root: Path | str | None = None
) -> dict:
    """Append a new glossary term registration. Returns the entry written.

    Raises ValueError if: `category` is not one of GLOSSARY_CATEGORIES, `description` is blank
    (an empty tooltip is a real bug the registry itself should catch, not a valid entry), or
    `term` is already registered (terms can only be added, never updated or re-added).
    """
    if category not in GLOSSARY_CATEGORIES:
        raise ValueError(
            f"category must be one of {sorted(GLOSSARY_CATEGORIES)}, got {category!r}"
        )
    if not description.strip():
        raise ValueError(f"cannot register {term!r}: description must not be blank")

    registry = load_registry(root)
    if term in registry:
        existing = registry[term]
        raise ValueError(
            f"{term!r} is already registered (category={existing['category']!r}, "
            f"added {existing['added_date']}) — terms cannot be re-added or changed"
        )

    entry = {
        "term": term,
        "category": category,
        "added_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "description": description,
    }

    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    return entry


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage the append-only glossary registry (registries/glossary_registry.jsonl)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser(
        "add", help="Register a new glossary term (append-only — cannot update or delete an existing term)"
    )
    add_p.add_argument("term")
    add_p.add_argument("--category", required=True, choices=sorted(GLOSSARY_CATEGORIES))
    add_p.add_argument("--description", required=True, help="One-sentence tooltip text")
    add_p.add_argument("--root", default=None)

    list_p = sub.add_parser("list", help="Print all registered glossary terms")
    list_p.add_argument("--root", default=None)

    args = parser.parse_args()

    if args.command == "add":
        try:
            entry = add_term(args.term, args.category, args.description, root=args.root)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Registered term {entry['term']!r} as {entry['category']!r} ({entry['added_date']}).")
        return

    if args.command == "list":
        registry = load_registry(args.root)
        for term in sorted(registry):
            entry = registry[term]
            print(f"{term:<24} {entry['category']:<14} {entry['added_date']}  {entry.get('description', '')}")
        return


if __name__ == "__main__":
    main()
