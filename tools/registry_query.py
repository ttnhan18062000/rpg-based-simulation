"""Seed-vocabulary tag matching and union filtering over docs/REGISTRY.yaml entries.

Built for TCK-20260705-TAG-REGISTRY-QUERY: extends the prior-work search consumers
(`.claude/workflows/create-tickets.js`'s Investigate phase, `.claude/agents/investigator.md`'s
"Finding Prior Work" step) with a second, cheap filter dimension over `tags`, alongside each
consumer's existing dimension (`layer` for create-tickets.js, `related_code_areas` for
investigator.md). The seed vocabulary below is the same list of Subsystem/Topic words named in
`docs/guidelines/tag_taxonomy.md` — that doc's prose list and this module's `SEED_TAGS` tuple are
two independent copies of the same 10 words and must be kept in sync by hand; there is no
runtime parsing of the doc into this module (that would be over-engineering for a 10-word list).
"""

SEED_TAGS = (
    "combat",
    "economy",
    "cognition",
    "faction",
    "resource",
    "social",
    "content",
    "world",
    "engine",
    "strategy",
)


def candidate_tags_from_text(*texts: str) -> set[str]:
    """Return the subset of SEED_TAGS present as a substring anywhere in texts.

    Lowercases and concatenates all non-empty texts with a space, then does a plain
    case-insensitive substring test per seed tag — no NLP, no stemming.
    """
    haystack = " ".join(t for t in texts if t).lower()
    return {tag for tag in SEED_TAGS if tag in haystack}


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
