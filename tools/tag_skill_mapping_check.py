#!/usr/bin/env python3
"""
Guard that every tag -> skill mapping consumer references the live single source, not a copy.

Built for TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK; repurposed by
TCK-20260720-SKILL-MAPPING-DEDUP. The `Process/Skill-signal` tag -> suggested skill mapping
(`api-design`, `debugging`, `performance`, `security`) was originally introduced by
TCK-20260705-TAG-SKILL-SUGGEST as 4 independently hand-maintained textual copies, with this module
comparing them pairwise for drift. TCK-20260720-SKILL-MAPPING-DEDUP replaced all 4 copies with a
single live source — `tools/tag_registry.py`'s `get_skill_mapping()`, exposed to non-Python
consumers via `python3 tools/tag_registry.py skill-mapping` — so there is no longer anything to
compare pairwise; the old `extract_pairs_*`/`normalize_target`/`check_tag_skill_mapping_consistency`
functions and the hardcoded `KNOWN_TAGS` allowlist are gone.

This module's job now: a static regression guard against backsliding into a 6th hand-maintained
copy. For each of the same 4 consumer files, `check_consumers_reference_live_source()` asserts (a)
the file references the live mechanism (`skill-mapping` or `get_skill_mapping`), and (b) it does not
contain a re-duplicated literal table. `KNOWN_TAGS` is still exported, but now derived live from
`tag_registry.get_skill_mapping().keys()` instead of a separately hardcoded frozenset — resolving
this module's own previously-disclosed staleness limitation: now that a genuine single source of
truth exists, deriving the known-tag set from it no longer makes any one of the 4 consumer files an
implicit source of truth for the others (the objection that blocked doing this originally).
"""

import re
import sys
from pathlib import Path

# tools/tag_skill_mapping_check.py's parent is tools/, so parent.parent is the repo root —
# robust regardless of the caller's current working directory (mirrors tag_registry.py).
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent

_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import tag_registry  # noqa: E402

KNOWN_TAGS = frozenset(tag_registry.get_skill_mapping().keys())

_CONSUMER_FILES = (
    Path(".claude/agents/ticket-scoper.md"),
    Path("docs/guides/ticket_tagging.md"),
    Path(".claude/workflows/implement-ticket.js"),
    Path(".claude/workflows/create-tickets.js"),
)

_LIVE_SOURCE_RE = re.compile(r"skill-mapping|get_skill_mapping")

# A re-duplicated table looks like 3+ of the known tag names each formatted as a markdown table
# cell (`` `tag` `` or `\`tag\``) or an arrow-list row (`tag ->` / `tag  ->`) within the file — the
# same two shapes the old extract_pairs_markdown/extract_pairs_js_escaped/extract_pairs_arrow_list
# parsers used to read, now used in reverse to detect a backslide.
def _table_row_pattern(tag: str) -> re.Pattern:
    escaped_tag = re.escape(tag)
    return re.compile(
        rf"\\?`{escaped_tag}\\?`\s*\|" rf"|{escaped_tag}\s*->"
    )


def check_consumers_reference_live_source(root: Path | str | None = None) -> list[str]:
    """Return a list of violation strings, one per consumer file with a problem.

    Empty list means all consumer files correctly reference the live single source and none
    re-duplicate the mapping as a literal table.
    """
    base = Path(root) if root is not None else _DEFAULT_ROOT

    violations: list[str] = []
    for rel_path in _CONSUMER_FILES:
        path = base / rel_path
        text = path.read_text(encoding="utf-8")

        if not _LIVE_SOURCE_RE.search(text):
            violations.append(
                f"{rel_path}: does not reference the live single source "
                f"(expected a mention of 'skill-mapping' or 'get_skill_mapping')"
            )
            continue

        matched_tags = {tag for tag in KNOWN_TAGS if _table_row_pattern(tag).search(text)}
        if len(matched_tags) >= 3:
            violations.append(
                f"{rel_path}: appears to re-embed a literal tag -> skill table "
                f"(matched {sorted(matched_tags)} as table/arrow-list rows)"
            )

    return violations
