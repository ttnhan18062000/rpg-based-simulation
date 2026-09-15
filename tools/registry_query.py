"""Seed-vocabulary tag matching and union filtering over docs/REGISTRY.yaml entries.

Built for TCK-20260705-TAG-REGISTRY-QUERY: extends the prior-work search consumers
(`.claude/workflows/create-tickets.js`'s Investigate phase, `.claude/agents/investigator.md`'s
"Finding Prior Work" step) with a second, cheap filter dimension over `tags`, alongside each
consumer's existing dimension (`layer` for create-tickets.js, `related_code_areas` for
investigator.md).

As of TCK-20260720-TAG-TOUCHPOINT-CLEANUP, the seed vocabulary is read live from
`registries/tag_registry.jsonl`'s `subsystem-topic` tags instead of a hand-copied tuple —
registering a new `subsystem-topic` tag via the CLI makes it queryable here with zero code change.
"""

import argparse
import sys
from pathlib import Path

from tag_registry import load_registry


def candidate_tags_from_text(*texts: str, root=None) -> set[str]:
    """Return the subset of live `subsystem-topic` tags present as a substring anywhere in texts.

    Lowercases and concatenates all non-empty texts with a space, then does a plain
    case-insensitive substring test per registered `subsystem-topic` tag — no NLP, no stemming.
    `root` mirrors `tag_registry.py`'s own `root` parameter convention (test fixtures via
    `monkeypatch.chdir(tmp_path)` or an explicit path).
    """
    registry = load_registry(root)
    subsystem_topic_tags = {
        tag for tag, entry in registry.items() if entry.get("category") == "subsystem-topic"
    }
    haystack = " ".join(t for t in texts if t).lower()
    return {tag for tag in subsystem_topic_tags if tag in haystack}


def filter_registry(entries, layers=None, candidate_tags=None):
    """Union filter: an entry matches if its `layer` is in `layers`, OR its `tags` intersect
    `candidate_tags`. Either side contributes zero matches when empty/None — this does not
    degrade to "match everything". Preserves input order.
    """
    layers = layers or ()
    candidate_tags = candidate_tags or ()
    layers_set = set(layers)
    tags_set = set(candidate_tags)

    def _matches(e):
        layer_match = bool(layers_set) and e.get("layer") in layers_set
        tag_match = bool(tags_set) and bool(set(e.get("tags") or ()) & tags_set)
        return layer_match or tag_match

    return [e for e in entries if _matches(e)]


def main(argv=None) -> int:
    """CLI entry point (TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT). Before this existed,
    running this module directly imported it, did nothing, and exited 0. This module has two
    real functions with no single obvious entry point (unlike parity_ledger_scan.py/
    ticket_field_values.py's own single primary function) — exposed as two mutually exclusive
    modes, since neither is a PASS/FAIL "check" the way the other two fixed modules are:

    --text: runs candidate_tags_from_text, printing the live subsystem-topic tags found in the
    given free text.
    --layers/--tags: runs filter_registry against the real docs/REGISTRY.yaml, printing each
    matching entry's own path.

    Exit 0 = query ran (regardless of how many results); exit 1 = no mode selected, or a real
    runtime error (e.g. docs/REGISTRY.yaml missing) -- there is no PASS/FAIL "check" outcome
    here, so those are the only two meaningful exit states for a pure query tool.
    """
    parser = argparse.ArgumentParser(
        description="Query docs/REGISTRY.yaml's live tag/layer vocabulary. Exactly one of "
        "--text or --layers/--tags must be given."
    )
    parser.add_argument(
        "--text", nargs="+", default=None,
        help="Free text to match against the live subsystem-topic tag vocabulary "
        "(candidate_tags_from_text).",
    )
    parser.add_argument("--layers", nargs="+", default=None, help="Layer values to filter on.")
    parser.add_argument("--tags", nargs="+", default=None, help="Tag values to filter on.")
    parser.add_argument(
        "--registry", default="docs/REGISTRY.yaml",
        help="Path to the registry YAML (default: docs/REGISTRY.yaml) — used by --layers/--tags.",
    )
    args = parser.parse_args(argv)

    if args.text is not None:
        tags = candidate_tags_from_text(*args.text)
        print(f"Matched tags: {sorted(tags)}")
        return 0

    if args.layers is not None or args.tags is not None:
        import yaml

        registry_path = Path(args.registry)
        if not registry_path.exists():
            print(f"ERROR: {registry_path} does not exist", file=sys.stderr)
            return 1
        entries = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or []
        matches = filter_registry(entries, layers=args.layers, candidate_tags=args.tags)
        print(f"Matched {len(matches)} entr{'y' if len(matches) == 1 else 'ies'}:")
        for e in matches:
            print(f"  {e.get('path')}")
        return 0

    parser.error("one of --text or --layers/--tags is required")
    return 1  # unreachable — parser.error() calls sys.exit(2) itself


if __name__ == "__main__":
    sys.exit(main())
