---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT
artifact_type: investigation
tags: [architecture, content]
---

# Investigation — TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT

## Trigger

A prior session hit real, measured costs editing/publishing `docs/brainstorm/rpg_feature_atlas.html`:
reading a live-rendered copy of the artifact cost 1M+ tokens for the first 2,000 lines alone (the
file's own embedded data dominates any read window), and the Artifact publish tool's identical-content
verification step became too expensive to complete normally, requiring a user-approved `force:true`
override instead of the normal read-then-publish flow. This investigation confirms the exact cause and
scopes a fix.

## Method

Direct file inspection: line-length distribution (`awk '{print length, NR}' | sort -rn`), locating
`<script>` tags, and extracting/parsing the suspect lines as JSON via Python to confirm both the
problem's shape and that a pure-reformat fix (no data or logic rewrite) is sufficient.

## Findings

### `rpg_feature_atlas.html` (569,110 bytes, 1,157 lines)

- Single `<script>` block starts at line 1127.
- Line 1128: `const CARD_SECTIONS = {...};` — **301,545 characters**, one line. Parses as valid JSON
  (`json.loads` succeeds on the object-literal portion after `const CARD_SECTIONS = ` and before the
  trailing `;`). 14 top-level section keys, 137 cards total across them.
- Line 1147: `const REVISIONS = [...];` — **70,952 characters**, one line. Parses as valid JSON. 69
  entries (each `{"n": <int>, "text": <str>}`).
- Lines 1129-1146 and 1148-1157 (the actual render logic — `renderBadges`, `renderCard`,
  `renderRevision`, and the `document.querySelectorAll`/`innerHTML` wiring) are normal, short,
  human-readable lines — the problem is entirely the two data lines, not the logic.
- `renderCard` derives each card's DOM anchor id from its own title text via regex
  (`c.title.match(/^(\d+)\./)` → `id="idea-${ideaMatch[1]}"`), not from any separate id field in the
  data — this means the reformat must preserve `title` strings exactly (whitespace-safe, since the
  regex only looks at the leading digits) but does not need to introduby a new id field.

### `simulation_capabilities.html` (79,665 bytes, ~359 lines)

- Single `<script>` block starts at line 339.
- Line 340: `const SECTIONS = [...];` — **61,454 characters**, one line. Parses as valid JSON. Confirmed
  same shape as the Atlas's problem, smaller in absolute size (roughly 1/5th the Atlas's largest blob)
  but still the dominant cost driver for this file specifically.

### Files checked and confirmed NOT to have this problem (no line above ~2,600 chars in any of them)

- `rpg_simulation_wiring_map.html` (64,781 bytes, 697 lines): no `<script>` tag at all — max line
  length 1,149 chars. Static hand-authored HTML/CSS only.
- `rpg_expected_schemas.html` (132,250 bytes): worked with directly in a prior session without any
  read-cost or publish-cost issue; static hand-authored `<section>`/`<table>` markup, same shape as the
  Wiring Map.
- `design_merit_scorecard.html` (52,864 bytes): same — static hand-authored HTML table, no blob.

This means the maintainability problem this ticket fixes is real and specific to exactly two files,
not all five brainstorm sibling docs — an earlier framing of "standardize all 5 docs onto the same
JSON-plus-template shape" was based on an unverified assumption and has been dropped from this
initiative's scope by direct user decision, in favor of this narrower, evidence-backed fix.

## Conclusion

Both blobs in both files are already valid JSON — this is a pure structural/whitespace reformat, not a
data model change or a rendering-logic rewrite. The fix: move each blob into a
`<script type="application/json" id="...">` block (pretty-printed), and replace the bare
`const NAME = {...};` assignment with `const NAME = JSON.parse(document.getElementById('...').textContent);`.
See `plan.md` for the exact steps and verification approach.
