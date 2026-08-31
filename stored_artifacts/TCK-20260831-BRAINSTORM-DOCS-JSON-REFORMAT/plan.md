---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT
artifact_type: plan
tags: [architecture, content]
---

# Plan — TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT

## Transformation, per blob

For each of the three blobs (`rpg_feature_atlas.html`'s `CARD_SECTIONS` and `REVISIONS`,
`simulation_capabilities.html`'s `SECTIONS`):

1. Locate the line matching `^const <NAME> = (.*);$`.
2. Parse the captured group as JSON (`json.loads`) — this is the round-trip source of truth; if this
   step fails, the blob is not pure JSON and this ticket's approach doesn't apply (not expected, per
   `investigation.md`'s findings, but the migration script asserts this rather than assuming it).
3. Re-serialize with `json.dumps(data, indent=2, ensure_ascii=False)`.
4. Insert a new sibling script element immediately before the file's main `<script>` tag:
   `<script type="application/json" id="<name>-data">\n<pretty-json>\n</script>\n`.
5. Replace the original `const <NAME> = {...};` line with:
   `const <NAME> = JSON.parse(document.getElementById('<name>-data').textContent);`.

Script-tag ids: `card-sections-data`, `revisions-data`, `sections-data` — confirmed via grep not to
already exist in either file (see `investigation.md`).

## Verification, per file (all automated, none by eye)

1. **Round-trip equality**: parse the new pretty-printed JSON block back with `json.loads`, compare
   (`==`) against the original blob's parsed value. Must be identical Python objects.
2. **Max line length**: no line in the post-change file exceeds ~2,000 characters. Confirms the actual
   problem (huge single-line reads) is fixed, not just cosmetically touched.
3. **HTML validity**: `html.parser.HTMLParser().feed(content)` raises no exception.
4. **Anchor-id preservation**: `rpg_feature_atlas.html` only — `renderCard` derives `id="idea-N"` from
   each card's `title` field via regex at render time (not present as literal HTML in the source file
   either before or after this change, since it's client-rendered). Verification instead re-runs the
   same regex (`^(\d+)\.`) against every card's `title` field in both the old parsed data and the new
   parsed data and confirms the resulting id list is identical in count and value — proves the render
   logic's *output* is unaffected without needing a browser.
5. **No other line changed**: diff the file before/after, confirm the only changes are (a) the new
   `<script type="application/json">` block insertion and (b) the single `const NAME = ...` line's
   replacement — no CSS, no other JS, no HTML markup touched.

## Execution order

1. `rpg_feature_atlas.html` first (both `CARD_SECTIONS` and `REVISIONS`) — the higher-value, larger
   fix.
2. `simulation_capabilities.html` (`SECTIONS`) — same transformation, smaller file.
3. Run full verification suite (above) on both files before considering the ticket done.
4. `html.parser` parse check + a full `git diff --stat` review before commit, so the actual diff shape
   (large insertion + one-line-changed-to-one-line, not a wholesale rewrite) is visually confirmed to
   match what's expected.

## What this plan does NOT do

- Does not touch `rpg_simulation_wiring_map.html`, `rpg_expected_schemas.html`, or
  `design_merit_scorecard.html` — confirmed no equivalent problem exists in any of them
  (`investigation.md`).
- Does not republish either artifact to Claude Artifacts — that's a separate follow-up action after
  this ticket closes.
- Does not build the per-idea cross-document index — a separate, already-agreed follow-up ticket.
