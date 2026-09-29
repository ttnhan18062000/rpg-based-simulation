"""Regression guard for TCK-20260929-WIRING-MAP-LIFECYCLE-ARC-MERMAID-PARSE-ERROR: an unquoted
mermaid `NODE[...]` label containing a literal `(`/`)` (or an HTML-entity-escaped one, which a
browser decodes to a literal paren before mermaid ever sees the text) breaks mermaid's parser --
a bare paren inside an unquoted square-bracket label is read as round-node syntax.

Real, once-broken example: `docs/brainstorm/rpg_simulation_wiring_map.html`'s `SC[Scarred — NOT
BUILT, heal_wound&#40;&#41; deleted...]` (real file line 614), confirmed with `mermaid.parse()`
(v10.9.1, Node/jsdom) to produce "Parse error on line 9: ... Expecting ... got 'PS'" before the
fix. Fixed by quoting the label (`SC["Scarred — NOT BUILT, heal_wound() deleted..."]`) -- mermaid
treats a quoted label as literal text, parens included.

This test is a cheap, Python-only static guard (no Node/mermaid npm dependency) against the same
class recurring on a future diagram edit -- it does not replace a real `mermaid.parse()` run
(TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS/TCK-20260929-WIRING-MAP-LIFECYCLE-ARC-MERMAID-
PARSE-ERROR both recorded that command's output directly in their own tickets' Implementation
Notes rather than committing a Node-dependent test).

**Scoped to `<pre class="mermaid">...</pre>` block contents only (peer review round 2 on this
ticket)**: the first version of this guard ran the label regex over each *entire* file --
including prose cards, embedded JSON data, and `<script>` blocks. `rpg_feature_atlas.html` is a
pinned living page other sessions edit often; ordinary prose like `[see TCK-1 (P1)]` or JS like
`a[f(x)]` would match the same `\bWORD[...(...]` shape and fail an unrelated atlas-edit PR, even
though mermaid parsing is completely unaffected outside a mermaid block. Extracting mermaid block
contents first, the same way TCK-20260916/TCK-20260929's own verification scripts did, keeps the
guard's blast radius matching its actual claim.
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_FILES = [
    _REPO_ROOT / "docs" / "brainstorm" / "rpg_simulation_wiring_map.html",
    _REPO_ROOT / "docs" / "brainstorm" / "rpg_feature_atlas.html",
]

_MERMAID_BLOCK_RE = re.compile(r'<pre class="mermaid">(.*?)</pre>', re.S)

# NODE[...unquoted label...] where the label contains a literal or entity-escaped paren.
# `[^"][^\]]*` requires the character right after `[` to not be `"` -- a quoted label
# (`NODE["..."]`) is exactly what's safe, so it's deliberately excluded from this match.
_UNQUOTED_LABEL_WITH_PAREN_RE = re.compile(
    r'\b[A-Za-z][A-Za-z0-9_]*\[[^"][^\]]*(?:\(|\)|&#40;|&#41;)[^\]]*\]'
)


def _mermaid_block_contents(text: str) -> list:
    """Extracts only the text between `<pre class="mermaid">` and `</pre>`, matching the
    extraction shape TCK-20260916/TCK-20260929's own mermaid.parse() verification scripts used --
    the guard below only ever needs to see mermaid source, never surrounding HTML/prose/JSON/JS."""
    return _MERMAID_BLOCK_RE.findall(text)


def test_no_unquoted_mermaid_node_label_contains_a_paren():
    for path in _FILES:
        text = path.read_text(encoding="utf-8")
        for block in _mermaid_block_contents(text):
            hits = _UNQUOTED_LABEL_WITH_PAREN_RE.findall(block)
            assert hits == [], (
                f"{path}: unquoted mermaid node label(s) containing a paren would break mermaid's "
                f"parser (quote the label instead) — see "
                f"TCK-20260929-WIRING-MAP-LIFECYCLE-ARC-MERMAID-PARSE-ERROR: {hits}"
            )


def test_resolver_ignores_a_paren_in_brackets_outside_a_mermaid_block():
    """Peer review round 2's own failure shape: ordinary prose/JS text with the same
    `WORD[...(...]` pattern, but outside any <pre class="mermaid"> block, must never be flagged --
    proves the guard is scoped to mermaid source, not the whole file."""
    sample = (
        '<p>See TCK-1 (P1) for details: a[f(x)]</p>\n'
        '<pre class="mermaid">\nflowchart LR\n    AL[Spawned / Alive]\n</pre>\n'
    )
    blocks = _mermaid_block_contents(sample)
    assert len(blocks) == 1
    assert _UNQUOTED_LABEL_WITH_PAREN_RE.findall(sample) != [], (
        "sanity check: the prose text alone must still match the raw label regex, or this test "
        "isn't proving block-scoping actually matters"
    )
    for block in blocks:
        assert _UNQUOTED_LABEL_WITH_PAREN_RE.findall(block) == []


def test_resolver_detects_the_real_pre_fix_shape():
    """Proves the regex actually catches the real defect shape, not just that today's files
    happen to pass -- independent of the real repo tree."""
    sample = 'SC[Scarred — NOT BUILT, heal_wound&#40;&#41; deleted; wounds decided permanent]\n'
    assert _UNQUOTED_LABEL_WITH_PAREN_RE.findall(sample) != []


def test_resolver_does_not_flag_a_quoted_label_with_a_paren():
    sample = 'SC["Scarred — NOT BUILT, heal_wound() deleted; wounds decided permanent"]\n'
    assert _UNQUOTED_LABEL_WITH_PAREN_RE.findall(sample) == []


def test_resolver_does_not_flag_an_unquoted_label_without_a_paren():
    sample = 'AL[Spawned / Alive]\n'
    assert _UNQUOTED_LABEL_WITH_PAREN_RE.findall(sample) == []
