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
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_FILES = [
    _REPO_ROOT / "docs" / "brainstorm" / "rpg_simulation_wiring_map.html",
    _REPO_ROOT / "docs" / "brainstorm" / "rpg_feature_atlas.html",
]

# NODE[...unquoted label...] where the label contains a literal or entity-escaped paren.
# `[^"][^\]]*` requires the character right after `[` to not be `"` -- a quoted label
# (`NODE["..."]`) is exactly what's safe, so it's deliberately excluded from this match.
_UNQUOTED_LABEL_WITH_PAREN_RE = re.compile(
    r'\b[A-Za-z][A-Za-z0-9_]*\[[^"][^\]]*(?:\(|\)|&#40;|&#41;)[^\]]*\]'
)


def test_no_unquoted_mermaid_node_label_contains_a_paren():
    for path in _FILES:
        text = path.read_text(encoding="utf-8")
        hits = _UNQUOTED_LABEL_WITH_PAREN_RE.findall(text)
        assert hits == [], (
            f"{path}: unquoted mermaid node label(s) containing a paren would break mermaid's "
            f"parser (quote the label instead) — see "
            f"TCK-20260929-WIRING-MAP-LIFECYCLE-ARC-MERMAID-PARSE-ERROR: {hits}"
        )


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
