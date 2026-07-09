#!/usr/bin/env python3
"""
Detect drift across the 4 hand-maintained tag -> skill mapping table copies.

Built for TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK. The `Process/Skill-signal` tag -> suggested
skill mapping (`api-design`, `debugging`, `performance`, `security`) was introduced by
TCK-20260705-TAG-SKILL-SUGGEST as 4 independently hand-maintained textual copies, with no
consistency check between them:

  1. `.claude/agents/ticket-scoper.md`      — raw markdown pipe table
  2. `docs/guides/ticket_tagging.md`        — raw markdown pipe table
  3. `.claude/workflows/implement-ticket.js` — markdown pipe table inside a JS template string
     (backticks escaped as `\\``)
  4. `.claude/workflows/create-tickets.js`   — arrow-list (`tag -> target`), `debugging`'s target
     wraps across multiple lines

This module reads and compares those 4 copies; it does not write to any of them, and it is not a
single source of truth for the mapping (the prose still lives independently in 4 places). It
follows `tools/tag_registry.py::check_tags_registered()`'s precedent: parsing/comparison logic
lives here, `tests/tools/test_tag_skill_mapping_check.py` imports it via the same
`sys.path.insert(0, "tools")` shim.

Comparison is on *normalized* `(primary_skill, carveout_agent, carveout_paths)` tuples, not raw
text — `ticket-scoper.md` and `ticket_tagging.md` carry legitimately longer prose (a
`world-debugger` carve-out parenthetical, a "first codification" note on `security`) that
`implement-ticket.js` and `create-tickets.js`'s terser prompt-template copies omit. Byte-identical
comparison would false-positive on that prose.

Disclosed limitation — KNOWN_TAGS is itself a de-facto 5th copy of the tag set: if a 5th
`Process/Skill-signal` tag is ever added to the real 4 copies, this allowlist must be updated too,
or this check will silently ignore the new tag rather than compare it. This is a deliberate,
accepted decision, not an oversight: deriving KNOWN_TAGS from one of the 4 files would make that
file an implicit source of truth for the other 3, which contradicts this ticket's own Out of Scope
(no de-duplication of the 4 copies into one source of truth). No code-level mitigation is planned;
this disclosure is the complete mitigation.
"""

import re
from pathlib import Path

KNOWN_TAGS = frozenset({"api-design", "debugging", "performance", "security"})

# tools/tag_skill_mapping_check.py's parent is tools/, so parent.parent is the repo root —
# robust regardless of the caller's current working directory (mirrors tag_registry.py).
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent

_FILE_PARSERS = (
    (Path(".claude/agents/ticket-scoper.md"), "extract_pairs_markdown"),
    (Path("docs/guides/ticket_tagging.md"), "extract_pairs_markdown"),
    (Path(".claude/workflows/implement-ticket.js"), "extract_pairs_js_escaped"),
    (Path(".claude/workflows/create-tickets.js"), "extract_pairs_arrow_list"),
)

_MARKDOWN_TAG_RE = re.compile(r"^`([a-z][a-z-]*)`$")
_JS_ESCAPED_TAG_RE = re.compile(r"^\\?`([a-z][a-z-]*)\\?`$")
_ARROW_ENTRY_RE = re.compile(r"^\s*([a-z][a-z-]*)\s*->\s*(.+)$")
_PRIMARY_SKILL_RE = re.compile(r"(/[a-z][a-z-]*)")
_SRC_PATH_RE = re.compile(r"src/[\w./]+")
# Bounds carve-out path extraction to the actual "path under X, Y, or Z" condition clause, not any
# src/-shaped substring anywhere in the row's prose. ticket-scoper.md's debugging row has a trailing
# parenthetical mentioning `src/worldgeneration/` as explicitly EXCLUDED from the carve-out (a known,
# separately-flagged, deliberately-deferred oddity — see the ticket's Out of Scope) — without this
# anchor, that excluded mention would be misread as a 6th carve-out path and produce a false mismatch
# against the other 3 copies, violating the "tolerate prose differences" requirement this check exists
# to satisfy.
_CARVEOUT_LIST_RE = re.compile(
    r"path under\s+((?:\\?`?src/[\w./]+\\?`?[,\s]*(?:or\s+)?)+)", re.IGNORECASE
)

_ARROW_START_ANCHOR = "Map each assigned tag against this table"
_ARROW_END_ANCHOR = "Do not invent mappings for tags outside this 4-entry table"


def extract_pairs_markdown(text: str) -> dict[str, str]:
    r"""Parse Format A: a raw markdown pipe table (`| \`tag\` | target |`).

    Header (`| Tag | Suggested skill |`) and separator (`|---|---|`) rows are skipped naturally —
    neither cell matches the `` `tag` `` pattern, so no special-casing is needed.
    """
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")]
        while cells and cells[0] == "":
            cells.pop(0)
        while cells and cells[-1] == "":
            cells.pop()
        if len(cells) < 2:
            continue
        match = _MARKDOWN_TAG_RE.match(cells[0])
        if not match or match.group(1) not in KNOWN_TAGS:
            continue
        pairs[match.group(1)] = cells[1]
    return pairs


def extract_pairs_js_escaped(text: str) -> dict[str, str]:
    """Parse Format B: a markdown pipe table embedded in a JS template string.

    Same pipe-split approach as `extract_pairs_markdown`, but the tag cell's raw bytes contain a
    literal backslash before/after the backtick (the source is a JS template-string literal with
    escaped backticks, read here as plain text rather than evaluated as JS).
    """
    pairs: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")]
        while cells and cells[0] == "":
            cells.pop(0)
        while cells and cells[-1] == "":
            cells.pop()
        if len(cells) < 2:
            continue
        match = _JS_ESCAPED_TAG_RE.match(cells[0])
        if not match or match.group(1) not in KNOWN_TAGS:
            continue
        pairs[match.group(1)] = cells[1]
    return pairs


def extract_pairs_arrow_list(text: str) -> dict[str, str]:
    """Parse Format C: an arrow-list (`tag -> target`) with multi-line continuation.

    The scan window is bounded by stable anchor substrings, not line numbers, so the parser is
    robust to the block shifting up/down. Raises `ValueError` if either anchor is missing — a
    silent empty/partial result here would let the consistency check false-pass by skipping this
    file entirely (see module Anti-Drift note in the ticket's plan.md).
    """
    lines = text.splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if start_idx is None and _ARROW_START_ANCHOR in line:
            start_idx = i
        elif start_idx is not None and _ARROW_END_ANCHOR in line:
            end_idx = i
            break

    if start_idx is None or end_idx is None:
        raise ValueError(
            "could not locate arrow-list mapping block: missing anchor "
            f"({_ARROW_START_ANCHOR!r} or {_ARROW_END_ANCHOR!r})"
        )

    pairs: dict[str, str] = {}
    current_tag = None
    for line in lines[start_idx + 1 : end_idx]:
        match = _ARROW_ENTRY_RE.match(line)
        if match and match.group(1) in KNOWN_TAGS:
            current_tag = match.group(1)
            pairs[current_tag] = match.group(2).strip()
        elif current_tag is not None and line.strip():
            pairs[current_tag] += " " + line.strip()
    return pairs


def normalize_target(raw_target: str) -> tuple[str, str | None, tuple[str, ...]]:
    """Reduce a raw target string to a comparable tuple, ignoring prose/wording differences.

    Captures both halves of the `debugging` carve-out — the default skill AND the carve-out's
    agent + path set — so a drift in either half fails the comparison.
    """
    primary_skill = _PRIMARY_SKILL_RE.search(raw_target).group(1)
    carveout_agent = "world-debugger" if "world-debugger" in raw_target else None
    list_match = _CARVEOUT_LIST_RE.search(raw_target)
    carveout_list_text = list_match.group(1) if list_match else ""
    carveout_paths = tuple(sorted(set(_SRC_PATH_RE.findall(carveout_list_text))))
    return (primary_skill, carveout_agent, carveout_paths)


_PARSERS = {
    "extract_pairs_markdown": extract_pairs_markdown,
    "extract_pairs_js_escaped": extract_pairs_js_escaped,
    "extract_pairs_arrow_list": extract_pairs_arrow_list,
}


def check_tag_skill_mapping_consistency(root: Path | str | None = None) -> list[dict]:
    """Read all 4 live mapping-table copies and return a list of per-tag mismatch records.

    Empty list means fully consistent. Each mismatch record names the tag and the normalized
    tuple extracted from every source file, so a disagreeing file/tag pair is identifiable.
    """
    base = Path(root) if root is not None else _DEFAULT_ROOT

    normalized_by_file: dict[str, dict[str, tuple]] = {}
    for rel_path, parser_name in _FILE_PARSERS:
        path = base / rel_path
        text = path.read_text(encoding="utf-8")
        raw_pairs = _PARSERS[parser_name](text)
        normalized_by_file[str(rel_path)] = {
            tag: normalize_target(raw_target) for tag, raw_target in raw_pairs.items()
        }

    file_paths = list(normalized_by_file)
    mismatches = []
    for tag in sorted(KNOWN_TAGS):
        values = {fp: normalized_by_file[fp].get(tag) for fp in file_paths}
        if len(set(values.values())) > 1:
            mismatches.append({"tag": tag, "values": values})
    return mismatches
