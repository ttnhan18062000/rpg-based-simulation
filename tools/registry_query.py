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
