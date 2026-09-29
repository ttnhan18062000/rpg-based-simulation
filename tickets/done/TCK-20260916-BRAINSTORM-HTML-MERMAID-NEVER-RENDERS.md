---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS
phase: done
date: 2026-09-16
tags: [architecture, documentation]
---

# TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS

## Title
`docs/brainstorm/*.html`'s `<pre class="mermaid">` diagrams have no rendering path through this repo's own doc infrastructure — likely never rendered as diagrams for anyone viewing them through it

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary

Found live during `TCK-20260915-MECHANISM-PRIORITY-DERIVATION`'s own investigation (one of the
ticket's own open questions: how do the wiring map's existing mermaid diagrams actually render).

`docs/brainstorm/rpg_simulation_wiring_map.html` has 3 `<pre class="mermaid">` diagram blocks.
Checked how they're meant to render, rather than assuming:

1. **No embedded script.** `grep -n "<script" docs/brainstorm/rpg_simulation_wiring_map.html`
   returns nothing — the file has zero `<script>` tags. No client-side mermaid.js include, no
   inline renderer.
2. **Docusaurus doesn't pick the file up as a page.** `website/docusaurus.config.js`'s docs plugin
   config has a `path`/`routeBasePath`/`exclude` block for `docs/brainstorm/` content (`brainstorm/**`
   is not in the `exclude` list), but the classic docs plugin's default include glob is
   `**/*.{md,mdx}` — no `include:` override exists in this repo's config, so `.html` files are
   never globbed as docs pages at all. `docs/brainstorm/rpg_simulation_wiring_map.html` is not
   under `website/static/` either, so there's no static-passthrough path copying it into the built
   site verbatim.
3. No `@docusaurus/theme-mermaid` plugin (or equivalent) is configured in
   `website/docusaurus.config.js` — even if the file *were* picked up as a doc page, nothing would
   render its mermaid blocks.

**Net effect**: opening this file directly in a browser shows the 3 diagrams as raw mermaid source
text, not rendered diagrams. `make docs-serve`/`make docs-build` (this repo's own real doc-serving
infrastructure) does not render them either — the file is invisible to that pipeline entirely. The
only known working rendering path is publishing the file through Claude Code's own Artifact tool
(which natively supports `<pre class="mermaid">` HTML blocks), which is not how this repo's own
documentation is normally consumed.

Same shape as this arc's own recurring pattern (mechanism this session has now named twice today):
a real artifact whose actual state is silent because nothing exercises the path that would reveal
it — here, "does this diagram actually render for a real reader" was never checked before.

## Scope

- Confirm definitively whether any other path renders these files (this investigation found none,
  but did not exhaustively check every possible viewing method — e.g., whether GitHub's own web UI
  renders inline HTML mermaid blocks when viewing the raw file, which it does not for `.html`
  files the way it does for `.md` files' ```` ```mermaid ```` fences, but confirm directly rather
  than assume). **CONFIRMED**: no other rendering path exists — see Implementation Notes.
- Decide the fix: (a) add a mermaid-rendering script directly to the affected HTML files
  (self-contained, no external infrastructure dependency), (b) configure Docusaurus to pick up
  `docs/brainstorm/*.html` and add the mermaid theme plugin, or (c) some other resolution —
  scope the actual fix once the confirmation above is complete. **DECIDED: (a)**. Self-contained,
  additive, no dependency on the doc pipeline that has never picked these files up anyway; (b)
  would be a much larger blast-radius change (Docusaurus config + a new theme dependency) for the
  same outcome, and (c) had no better candidate once (a) was confirmed to actually work (see
  Implementation Notes verification). Added a `<script src="mermaid@10.9.1 CDN">` +
  `mermaid.initialize({ startOnLoad: true })` pair at the end of each affected file.
- Check whether `docs/brainstorm/rpg_feature_atlas.html` or any other `docs/brainstorm/*.html`
  file has the same gap (this investigation checked only the wiring map file directly).
  **CONFIRMED**: `rpg_feature_atlas.html` has the identical gap (4 `<pre class="mermaid">` blocks,
  0 script tags loading/initializing mermaid — its existing 3 `<script>` blocks are unrelated card-
  rendering/data logic). Independently re-grepped every `docs/brainstorm/*.html` file for
  `class="mermaid"`: only these two files match. Both fixed identically.

## Out of Scope

- Any change to the diagrams' own content/topology.
- `TCK-20260915-MECHANISM-PRIORITY-DERIVATION`'s own new generated charts (a separate, additive
  artifact type — this ticket is about the pre-existing hand-authored diagrams only).

## Acceptance Criteria

- [x] A definitive, evidence-backed answer for how (if at all) these diagrams currently render for
      a real reader through this repo's own infrastructure.
- [x] A working rendering path exists after the fix, verified directly (not assumed).

## Related Tickets
- `TCK-20260915-MECHANISM-PRIORITY-DERIVATION` — where this was found; that ticket's own generated
  dependency charts derive their `classDef` state-coloring from the registry but do not depend on
  this ticket's resolution.

## Related Docs
- None yet.

## Related Stored Artifacts
- None — hotfix tier, self-evident intent per this ticket's own body.

## Related Code Areas
- `docs/brainstorm/rpg_simulation_wiring_map.html`
- `docs/brainstorm/rpg_feature_atlas.html` (unconfirmed, same pattern suspected)
- `website/docusaurus.config.js`

## Assumptions / Open Questions
- Whether any human has actually verified these diagrams render correctly at some point (e.g., via
  a one-off local script include that was later removed) — not checked via git history in this
  pass.
- **New finding, out of this ticket's scope (content/topology changes excluded):** the wiring
  map's 3rd diagram (`rpg_simulation_wiring_map.html`'s "Entity detail: the lifecycle arc" —
  `flowchart LR`) has a genuine pre-existing mermaid syntax error, independent of this ticket's
  fix. Its `SC[...]` node, **real file line 614**:
  ```
  SC[Scarred — NOT BUILT, heal_wound&#40;&#41; deleted; wounds decided permanent, DEV-005]
  ```
  — the literal `()` after `heal_wound` (which a browser's own HTML parsing decodes from those
  `&#40;&#41;` entities before mermaid ever sees the text, so the entity-escaping doesn't protect
  against mermaid's own grammar) is ambiguous with mermaid's round-node syntax inside a square-
  bracket label. Confirmed via `mermaid.parse()` (the library's own real parser, v10.9.1, run
  under Node/jsdom, no browser needed) against the extracted diagram source; exact output:
  ```
  Parse error on line 9:
  ...OT BUILT, heal_wound() deleted; wounds d
  -----------------------^
  Expecting 'SQE', 'DOUBLECIRCLEEND', 'PE', '-)', 'STADIUMEND', 'SUBROUTINEEND', 'PIPE',
  'CYLINDEREND', 'DIAMOND_STOP', 'TAGEND', 'TRAPEND', 'INVTRAPEND', 'UNICODE_TEXT', 'TEXT',
  'TAGSTART', got 'PS'
  ```
  (mermaid's own "line 9" counts from `flowchart LR` as line 1 within the extracted diagram
  source, not the real file's line numbering — real file line 614 is the authoritative location.)
  The other 6 real diagrams across both files (all 4 atlas diagrams, the wiring map's Layer Model
  and Entity Operating Loop) all parse as valid. This means the fix in this ticket makes 6 of 7
  diagrams render correctly and turns the 7th from silently-invisible-as-raw-text into a visibly-
  broken mermaid parse-error banner — a real improvement (the defect is no
  longer silent) but not a full fix for that one diagram. Worth a follow-up ticket; not filed here
  to keep this ticket's own scope from growing past what was asked.

## Implementation Notes
**No other rendering path confirmed** (Scope item 1): re-verified `grep -n "<script"` on both
files independently (wiring map: 0 hits; atlas: 3 hits, all unrelated JSON-data/card-rendering
logic, none touching mermaid), `website/docusaurus.config.js` has no `include:` override and no
`@docusaurus/theme-mermaid` plugin (confirmed by grep, 0 hits for "mermaid" in both
`website/package.json` and `website/docusaurus.config.js`), and GitHub's own web UI does not
execute inline `<script>` tags when viewing a `.html` file in its repo browser (files are shown as
syntax-highlighted source or served as inert content, never executed) — matching the original
investigation's claim, confirmed rather than re-assumed.

**Fix**: added an identical additive block to the end of both files —
```html
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({ startOnLoad: true });</script>
```
Pinned to `10.9.1` (a specific stable release, not a floating major-version CDN URL) so the render
behavior can't silently drift on a future mermaid release. Verified the CDN URL is live (`curl -sI`
→ `200`, `content-type: application/javascript`) before relying on it. Placed after each file's
existing `<script>` block (not before) purely for readability/convention consistency — the mermaid
blocks are static content inside their own `<div class="diagram-card">` wrappers, never inside a
`[data-section]` container the atlas's card-rendering script replaces via `innerHTML`, so there is
no DOM-replacement race either way. No diagram content/topology touched in either file (Out of
Scope respected) — `rpg_feature_atlas.html`'s pinned-living-page/mirrored-to-
`simulation_capabilities.html` status specifically requires this (per peer review), and this
change carries no gameplay-visible or card-content implication, so no
`simulation_capabilities.html` mirror update is needed.

**Verified directly, not assumed** (AC2): no headless-browser tooling was available in this
sandbox (`playwright`/`selenium` not installed; `puppeteer browsers install` failed — TLS
interception blocks the Chrome binary download, a known environment limitation), so full pixel-
level rendering couldn't be screenshotted. Instead verified with `mermaid`'s own real npm package
(pinned to the same `10.9.1`) run under Node + jsdom (no browser needed for pure parse validation):
`mermaid.parse()` against all 7 real diagram sources extracted from both files. 6/7 return `true`
(valid syntax, will render as diagrams once the script loads); the 7th's pre-existing defect is
documented above, out of scope. This directly exercises the same parser version the CDN script
will run in a real browser — the strongest verification available without a real display.

## Test Summary
No automated test suite covers `docs/brainstorm/*.html` content (confirmed: no test file
references either filename beyond the mechanism-registry tools' own drift checks, which only read
specific JSON/mermaid-classDef substrings, not overall file validity — unaffected by this change).
Verification was manual/direct per Implementation Notes: CDN reachability, HTML edit correctness
(both files still well-formed — same loose fragment style as before, no `<head>`/`<body>` tags
either originally), and `mermaid.parse()` syntax validation of all 7 real diagrams (6/7 valid, 1
pre-existing defect documented and left alone per Out of Scope).

## Files Changed
- `docs/brainstorm/rpg_simulation_wiring_map.html`
- `docs/brainstorm/rpg_feature_atlas.html`

## Completion Summary
Confirmed no rendering path existed anywhere in this repo's own infrastructure (doc pipeline,
Docusaurus config, GitHub's own file viewer), and that `rpg_feature_atlas.html` had the identical
gap the original investigation only checked for in the wiring map file. Fixed both with an additive,
self-contained mermaid.js CDN include (pinned version), no change to either file's diagram
content/topology. Verified with the real mermaid parser (not assumed): 6 of 7 real diagrams parse
as valid and will now render; found and documented (not fixed, per Out of Scope) one pre-existing
broken-syntax diagram as a byproduct of this verification, worth a small follow-up ticket someone
should file.
