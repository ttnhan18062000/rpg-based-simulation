---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT
phase: done
date: 2026-08-31
tags: [architecture, content]
---

# TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT

## Title
Reformat `rpg_feature_atlas.html`'s and `simulation_capabilities.html`'s embedded per-card data from
minified single-line JS object literals into pretty-printed JSON `<script type="application/json">`
blocks

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary

Both files render their per-idea/per-capability cards client-side from a data object embedded as a
single, unbroken minified line inside an inline `<script>` tag — `rpg_feature_atlas.html`'s
`CARD_SECTIONS` (301,545 chars, 137 cards across 14 sections) and `REVISIONS` (70,952 chars, 69
entries), and `simulation_capabilities.html`'s `SECTIONS` (61,454 chars). This made both files
expensive to research, edit, and republish: reading even a small slice of the live-rendered atlas
artifact cost 1M+ tokens in a prior session (the giant line dominates any offset/limit read window),
git diffs against either blob are opaque single-line rewrites regardless of how small the actual
content change was, and the Artifact publish tool's content-verification step became expensive enough
to require `force:true` overrides rather than a normal read-then-publish cycle.

Direct investigation confirmed all three blobs are already valid JSON as written (double-quoted keys/
strings, no JS-only syntax like trailing commas, single quotes, or template literals) — this is a pure
formatting/structure change, not a data or rendering-logic rewrite. `rpg_simulation_wiring_map.html`
(64KB, max line 1,149 chars), `rpg_expected_schemas.html`, and `design_merit_scorecard.html` were
checked and confirmed to have no equivalent blob — they are static hand-authored HTML tables and are
explicitly out of scope for this reformat (see Out of Scope).

## Scope

- `docs/brainstorm/rpg_feature_atlas.html`: extract `CARD_SECTIONS` (currently `const CARD_SECTIONS =
  {...};` on one line) into a pretty-printed JSON block: `<script type="application/json"
  id="card-sections-data">...</script>`, and change the JS to `const CARD_SECTIONS =
  JSON.parse(document.getElementById('card-sections-data').textContent);`. Same treatment for
  `REVISIONS` → `id="revisions-data"`.
- `docs/brainstorm/simulation_capabilities.html`: same treatment for `SECTIONS` → `id="sections-data"`.
- No change to any render function (`renderBadges`, `renderCard`, `renderRevision`, the
  `simulation_capabilities.html` equivalent) — they already consume the parsed object identically
  regardless of whether it came from a JS literal or `JSON.parse`.
- No change to any card/section/revision *content* — this is a structural/whitespace change only. A
  round-trip diff (old minified value vs. new pretty-printed value, both parsed back to Python objects)
  must be byte-for-byte equal.

## Out of Scope

- `rpg_simulation_wiring_map.html`, `rpg_expected_schemas.html`, `design_merit_scorecard.html` — confirmed
  no embedded data blob exists in any of the three (largest single line in the Wiring Map is 1,149
  chars); converting them from static HTML to a JSON-plus-template shape would be a much larger,
  higher-risk change with no read/write pain point to justify it. Explicitly deferred per direct user
  decision this session, not an oversight.
- The per-idea cross-document index (`docs/brainstorm/idea_index.json` or similar) — a separate,
  already-agreed follow-up ticket, sequenced after this one but not bundled into it.
- Any content/wording change to any card, section, or revision entry.
- Any change to the CSS/visual design of either page.
- Republishing either artifact to its live Claude Artifacts URL — that's a follow-up action after this
  ticket closes, using the already-established read-then-publish (or verified-safe `force:true`) flow,
  not part of this ticket's own scope.

## Acceptance Criteria

- Both files' `CARD_SECTIONS`/`REVISIONS`/`SECTIONS` blobs live in `<script type="application/json">`
  blocks, pretty-printed (indent, one field per line where reasonable), not single unbroken lines.
- `JSON.parse(...)` replaces the previous bare JS object-literal assignment for all three blobs, with
  no other JS logic changed.
- Round-trip content equality verified: the pretty-printed JSON, parsed, equals the original minified
  JS-literal blob, parsed — for all three blobs, checked programmatically, not by eye.
- Both files still parse as valid HTML (`html.parser`, no exceptions).
- No line in either file is structurally dominated by the whole dataset anymore — confirmed the actual
  maintainability problem (grep/read cost) is fixed by the drop from 301,545/70,952/61,454-char single
  lines to a max of 9,361 chars (Atlas) and 1,163 chars (Simulation Capabilities). The Atlas's one
  remaining ~9.3K-char line is a single legitimately long `desc` field's content (Idea 32's card),
  confirmed by direct inspection, not a residual structural problem — JSON pretty-printing keeps one
  string value on one line regardless of length, and a single field is trivially cheap to read/grep
  compared to the entire former dataset on one line. The original "~2000 chars" target in this
  criterion was an unverified guess before the actual content distribution was checked; revised here
  to the real, verified numbers.
- Existing anchor IDs (`id="idea-N"`, generated by `renderCard`'s `ideaMatch` regex against `c.title`)
  are unchanged in count and value before/after, confirmed by direct comparison — the render logic
  path that produces them is untouched, but this is verified, not assumed.

## Related Tickets
- None — first ticket in this initiative. A follow-up ticket for the per-idea cross-document index is
  planned next, sequenced after this one closes.

## Related Docs
- `docs/brainstorm/rpg_feature_atlas.html`, `docs/brainstorm/simulation_capabilities.html` — the two
  files this ticket modifies.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT/{investigation,plan,test_plan}.md`

## Related Code Areas
- N/A — `docs/` only, no `src/` change.

## Assumptions / Open Questions
- `id="card-sections-data"` / `id="revisions-data"` / `id="sections-data"` are new DOM ids introduced
  by this ticket — confirmed via grep that none of these three strings already exist anywhere in
  either file, so no collision risk.
- Pretty-print indentation width (2 spaces) was chosen to match the existing hand-authored CSS/HTML
  indentation convention already used elsewhere in both files, not derived from any external
  requirement.

## Implementation Notes
Wrote a one-time migration script (scratch tooling, not committed) implementing exactly the
`plan.md` transformation: locate `const NAME = {...};`, `json.loads` the captured group, re-serialize
with `json.dumps(indent=2, ensure_ascii=False)`, insert as a `<script type="application/json"
id="name-data">` block immediately before the file's main `<script>` tag, replace the original
assignment line with `const NAME = JSON.parse(document.getElementById('name-data').textContent);`.
Round-trip equality and anchor-id preservation are asserted inside the script before any file is
written — a failure anywhere aborts before touching disk.

One real finding during implementation: the initial `<2000 chars` max-line-length assertion (this
ticket's original acceptance criterion) tripped on the Atlas at 9,361 chars. Investigated directly
rather than just loosening the number blindly — traced to idea 32 (Reproduction)'s `desc` field, a
single legitimately long paragraph (9,322 chars). This is inherent to JSON pretty-printing (a string
value stays on one line regardless of length) and not a residual structural problem — the acceptance
criterion was revised to reflect the real, verified numbers (see that section's own note) rather than
an unverified pre-implementation guess.

## Test Summary
All checks in `test_plan.md` ran and passed:
- Round-trip JSON equality: `CARD_SECTIONS`, `REVISIONS`, `SECTIONS` all identical before/after
  (parsed-object comparison, not text comparison).
- Anchor-id preservation: 66 `idea-N` ids re-derived from `title` fields via the same regex
  `renderCard` uses, identical set before and after.
- `html.parser` parses both files cleanly, checked twice (once inside the migration script before
  writing, once fresh afterward as an independent check).
- `</script>` occurrence count matches exactly what the new structure predicts (3 in the Atlas: 2 new
  JSON-data blocks + 1 original script close; 2 in Simulation Capabilities: 1 + 1) — confirms no card
  content contains a literal `</script>` substring that would have broken out of a JSON script block
  early.
- Max line length: Atlas 301,545 → 9,361 chars (32x reduction); Simulation Capabilities 61,454 → 1,163
  chars (53x reduction).
- `git diff --stat`: 2 files changed, 2674 insertions(+), 3 deletions(-) — exactly 3 deletions (the 3
  original `const NAME = {...};` lines: 2 in the Atlas, 1 in Simulation Capabilities), confirming no
  other line was touched.

## Files Changed
- `docs/brainstorm/rpg_feature_atlas.html` — `CARD_SECTIONS`/`REVISIONS` reformatted to JSON script
  blocks
- `docs/brainstorm/simulation_capabilities.html` — `SECTIONS` reformatted to a JSON script block

## Completion Summary
Reformatted both files' embedded per-card/per-section data from single-line minified JS object
literals into pretty-printed `<script type="application/json">` blocks, with the JS render logic
switched to `JSON.parse(...)` against them. No card/section/revision content, render logic, or CSS
changed — purely a structural/whitespace fix, verified by round-trip JSON equality and anchor-id
preservation, not just visual inspection. Max single-line length dropped from 301,545/70,952/61,454
chars to 9,361/1,163 chars across the two files — the actual read/write/diff cost driver this ticket
existed to fix. `rpg_simulation_wiring_map.html`, `rpg_expected_schemas.html`, and
`design_merit_scorecard.html` confirmed to have no equivalent problem and were correctly left
untouched.
