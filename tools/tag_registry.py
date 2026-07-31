#!/usr/bin/env python3
"""
Manage the append-only ticket/artifact tag registry (registries/tag_registry.jsonl).

Built for TCK-20260706-TAG-REGISTRY-DATA. The registry is the machine-readable source of truth for
which tags exist, replacing the informal "tags are free text, just follow the canonical-form
rules" model docs/guidelines/tag_taxonomy.md originally described. Each line is one JSON object —
one tag, registered exactly once, never rewritten:

  {"tag": "faction", "category": "subsystem-topic", "added_date": "2026-07-06", "note": "..."}

Design constraints (all deliberate, not incidental):
  - Append-only: `add_tag()` is the only writer, and it refuses to add a tag that already exists
    (no update, no delete — the CLI has no command for either). The file itself, plus git history
    on it, is the changelog; there is no separate changelog file to keep in sync by hand.
  - `category` must be one of ADDABLE_CATEGORIES. `phase-milestone` is deliberately excluded from
    that set: phase tags follow the open-ended `phase-N` pattern (`is_tag_registered()` recognizes
    any canonical `phase-N` tag automatically) rather than requiring each phase number to be
    registered individually.
  - This module owns the canonical-form rules (`canonical_form_violation`, `FORBIDDEN_PRIORITY_TAGS`,
    `TAG_SYNONYM_MAP`, `TAG_TAXONOMY_EFFECTIVE_DATE`) that `validate_frontmatter.py` and
    `tag_report.py` both import, rather than each defining their own copy — this module has no
    dependency on either of them, so there is no import cycle.

Usage:
  python3 tools/tag_registry.py add <tag> --category <category> --note "why this tag exists"
  python3 tools/tag_registry.py list
  python3 tools/tag_registry.py skill-mapping
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Taxonomy constants — see docs/guidelines/tag_taxonomy.md.
# ---------------------------------------------------------------------------

# Enforcement is forward-only: only tickets/artifacts whose ticket_id embeds a date on or after
# this cutoff are checked, per the "no backfill of history" decision (TCK-20260704-TAG-TAXONOMY).
TAG_TAXONOMY_EFFECTIVE_DATE = "20260704"

# Duplicates the dedicated `## Priority` ticket-body field — never valid as a tag, at any date.
FORBIDDEN_PRIORITY_TAGS = {"p0", "p1", "p2"}

# Confirmed synonyms the general format rule cannot derive mechanically, because the non-canonical
# spelling has no separator character to normalize (run-together compounds and abbreviations).
# Keep this small and evidence-based — do not use it to pre-enumerate subsystem tags.
TAG_SYNONYM_MAP = {
    "obs": "observability",
    "cog": "cognition",
    "sim": "simulation",
    "worldmodules": "world-modules",
    "selfmodel": "self-model",
    "datamodel": "data-model",
    "worldspec": "world-spec",
}

# The 5 tag_taxonomy.md categories. `meta-process` is the 5th, added alongside this registry to
# cover tags about the ticket/agent-workflow process itself (e.g. `workflows`, `agent-monitoring`,
# `documentation`) — evidence: seeding this registry from the live corpus found the large majority
# of in-use tags were exactly this kind of tag, not a bad fit for the original 4 categories.
ALL_CATEGORIES = {
    "subsystem-topic",
    "phase-milestone",
    "process-skill-signal",
    "quality-attribute",
    "meta-process",
}

# Categories a tag can actually be registered under via `add`. `phase-milestone` is excluded on
# purpose — see module docstring.
ADDABLE_CATEGORIES = ALL_CATEGORIES - {"phase-milestone"}

_PHASE_NONCANONICAL_RE = re.compile(r"^phase(\d+)$")
_PHASE_CANONICAL_RE = re.compile(r"^phase-\d+$")

# ---------------------------------------------------------------------------
# Canonical-form rule (single source of truth — validate_frontmatter.py imports this)
# ---------------------------------------------------------------------------


def canonical_form_violation(tag: str) -> str | None:
    """Return a human-readable violation message if `tag` is not in canonical form, else None.

    Canonical form: lowercase, hyphen-separated, `phase-N` (not `phaseN`), not a forbidden
    priority tag, not a known non-canonical synonym.
    """
    lower = tag.lower()
    if lower in FORBIDDEN_PRIORITY_TAGS:
        return f"{tag!r} duplicates the dedicated Priority field — remove it"
    if tag != lower or "_" in tag:
        return f"{tag!r} is not canonical form (use {lower.replace('_', '-')!r})"
    phase_match = _PHASE_NONCANONICAL_RE.match(tag)
    if phase_match:
        return f"{tag!r} is not canonical form (use {'phase-' + phase_match.group(1)!r})"
    if tag in TAG_SYNONYM_MAP:
        return f"{tag!r} is a non-canonical synonym (use {TAG_SYNONYM_MAP[tag]!r})"
    return None


def is_phase_milestone_tag(tag: str) -> bool:
    """True if `tag` is a canonical `phase-N` tag — exempt from registry membership."""
    return bool(_PHASE_CANONICAL_RE.match(tag))


# ---------------------------------------------------------------------------
# Legacy skill-mapping fallback (TCK-20260720-SKILL-MAPPING-DEDUP)
# ---------------------------------------------------------------------------

# Disclosed bounded residual, not an undisclosed shadow copy — modeled on
# tag_skill_mapping_check.py's own KNOWN_TAGS disclosure (see that module's docstring). The 4
# `process-skill-signal` rows below were registered on 2026-07-06, before `triggers_skill` existed
# as a schema field, and tag_registry.jsonl's append-only invariant (see module docstring) forbids
# rewriting an already-written line to backfill the field. get_skill_mapping() merges this fallback
# with any `triggers_skill` field present on a registry row, so any *future* process-skill-signal
# tag added via `add_tag(..., triggers_skill=...)` needs no entry here at all. Do not add a 5th
# entry to this dict, and do not change any of the 4 existing entries' `skill` values — this is
# dedup of representation, not a content change to the mapping itself.
_LEGACY_SKILL_TRIGGERS: dict[str, dict] = {
    "api-design": {
        "skill": "/api-design-principles",
        "carveout_agent": None,
        "carveout_paths": (),
        "carveout_excluded_paths": (),
    },
    "debugging": {
        "skill": "/debugging-strategies",
        "carveout_agent": "world-debugger",
        "carveout_paths": (
            "src/worldassembly/",
            "src/worldbuilding/",
            "src/worldmodules/",
            "src/content/",
            "src/core/registries.py",
        ),
        "carveout_excluded_paths": ("src/worldgeneration/",),
    },
    "performance": {
        "skill": "/python-performance-optimization",
        "carveout_agent": None,
        "carveout_paths": (),
        "carveout_excluded_paths": (),
    },
    "security": {
        "skill": "/security-review",
        "carveout_agent": None,
        "carveout_paths": (),
        "carveout_excluded_paths": (),
    },
}

# ---------------------------------------------------------------------------
# Registry file I/O
# ---------------------------------------------------------------------------

# tools/tag_registry.py's parent is tools/, so parent.parent is the repo root — robust regardless
# of the caller's current working directory.
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_REL_PATH = Path("registries/tag_registry.jsonl")


def registry_path(root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else _DEFAULT_ROOT
    return base / _REGISTRY_REL_PATH


def load_registry(root: Path | str | None = None) -> dict:
    """Return {tag: entry_dict} for every registered tag. Empty dict if the file doesn't exist yet.

    Raises ValueError on a duplicate tag registration — the file must never contain the same tag
    twice; that would violate the append-only-unique-tag invariant `add_tag()` otherwise guarantees.
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
        tag = entry["tag"]
        if tag in registry:
            raise ValueError(
                f"{path}: duplicate registration for tag {tag!r} at line {lineno} — "
                f"the registry must contain each tag exactly once"
            )
        registry[tag] = entry
    return registry


def is_tag_registered(tag: str, registry: dict) -> bool:
    """True if `tag` is in the registry, or is a canonical phase-N tag (always allowed)."""
    return tag in registry or is_phase_milestone_tag(tag)


def check_tags_registered(tags: list[str], root: Path | str | None = None) -> list[str]:
    """Return the subset of `tags` that are NOT registered (phase-N tags always excluded).

    Built for TCK-20260706-SCOPE-TAG-REGISTRY-CHECK: lets the Scope phase
    (`.claude/workflows/implement-ticket.js`) catch an unregistered tag immediately, instead of
    only discovering it 6+ phases later at Verify (`done-checker`'s `frontmatter_valid` condition,
    `TCK-20260706-TAG-REGISTRY-DATA`). One `load_registry()` call, not one per tag.
    """
    registry = load_registry(root)
    return [tag for tag in tags if not is_tag_registered(tag, registry)]


def add_tag(
    tag: str,
    category: str,
    note: str = "",
    root: Path | str | None = None,
    triggers_skill: dict | None = None,
) -> dict:
    """Append a new tag registration. Returns the entry written.

    Raises ValueError if: `tag` is not canonical form, `category` is not addable, or `tag` is
    already registered (tags can only be added, never updated or re-added).

    `triggers_skill`, if given, is written verbatim as the entry's `triggers_skill` field — used by
    `get_skill_mapping()` to resolve a `process-skill-signal` tag to a suggested skill. Omitted
    (the default) produces byte-identical output to every pre-existing caller.
    """
    violation = canonical_form_violation(tag)
    if violation:
        raise ValueError(f"cannot register {tag!r}: {violation}")
    if category not in ADDABLE_CATEGORIES:
        raise ValueError(
            f"category must be one of {sorted(ADDABLE_CATEGORIES)}, got {category!r}"
        )

    registry = load_registry(root)
    if tag in registry:
        existing = registry[tag]
        raise ValueError(
            f"{tag!r} is already registered (category={existing['category']!r}, "
            f"added {existing['added_date']}) — tags cannot be re-added or changed"
        )

    entry = {
        "tag": tag,
        "category": category,
        "added_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note": note,
    }
    if triggers_skill is not None:
        entry["triggers_skill"] = triggers_skill

    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

    return entry


def get_skill_mapping(root: Path | str | None = None) -> dict[str, dict]:
    """Return {tag: {"skill", "carveout_agent", "carveout_paths", "carveout_excluded_paths"}}.

    The single source every `Process/Skill-signal` -> suggested-skill consumer reads (directly, or
    via the `skill-mapping` CLI subcommand): a registry row's own `triggers_skill` field takes
    precedence when present (the forward-only path new tags use), falling back to
    `_LEGACY_SKILL_TRIGGERS` for the 4 tags registered before that field existed. Tags with neither
    are omitted — this function names actual suggestions, not the full tag registry.
    """
    registry = load_registry(root)
    mapping: dict[str, dict] = {}
    for tag, entry in registry.items():
        if "triggers_skill" in entry:
            mapping[tag] = entry["triggers_skill"]
        elif tag in _LEGACY_SKILL_TRIGGERS:
            mapping[tag] = _LEGACY_SKILL_TRIGGERS[tag]
    return mapping


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manage the append-only tag registry (registries/tag_registry.jsonl)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser(
        "add", help="Register a new tag (append-only — cannot update or delete an existing tag)"
    )
    add_p.add_argument("tag")
    add_p.add_argument("--category", required=True, choices=sorted(ADDABLE_CATEGORIES))
    add_p.add_argument("--note", default="", help="Why this tag is being added")
    add_p.add_argument(
        "--triggers-skill",
        default=None,
        help='JSON object, e.g. \'{"skill": "/foo", "carveout_agent": null, '
        '"carveout_paths": [], "carveout_excluded_paths": []}\'',
    )
    add_p.add_argument("--root", default=None)

    list_p = sub.add_parser("list", help="Print all registered tags")
    list_p.add_argument("--root", default=None)

    skill_mapping_p = sub.add_parser(
        "skill-mapping", help="Print the live Process/Skill-signal tag -> skill mapping as JSON"
    )
    skill_mapping_p.add_argument("--root", default=None)

    args = parser.parse_args()

    if args.command == "add":
        triggers_skill = json.loads(args.triggers_skill) if args.triggers_skill else None
        try:
            entry = add_tag(
                args.tag, args.category, args.note, root=args.root, triggers_skill=triggers_skill
            )
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Registered tag {entry['tag']!r} as {entry['category']!r} ({entry['added_date']}).")
        return

    if args.command == "list":
        registry = load_registry(args.root)
        for tag in sorted(registry):
            entry = registry[tag]
            print(f"{tag:<28} {entry['category']:<22} {entry['added_date']}  {entry.get('note', '')}")
        return

    if args.command == "skill-mapping":
        print(json.dumps(get_skill_mapping(args.root), sort_keys=True))
        return


if __name__ == "__main__":
    main()
