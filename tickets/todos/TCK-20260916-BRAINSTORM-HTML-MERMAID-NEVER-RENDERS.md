---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS
phase: open
date: 2026-09-16
tags: [architecture, documentation]
---

# TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS

## Title
`docs/brainstorm/*.html`'s `<pre class="mermaid">` diagrams have no rendering path through this repo's own doc infrastructure — likely never rendered as diagrams for anyone viewing them through it

## Status
OPEN

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
  than assume).
- Decide the fix: (a) add a mermaid-rendering script directly to the affected HTML files
  (self-contained, no external infrastructure dependency), (b) configure Docusaurus to pick up
  `docs/brainstorm/*.html` and add the mermaid theme plugin, or (c) some other resolution —
  scope the actual fix once the confirmation above is complete.
- Check whether `docs/brainstorm/rpg_feature_atlas.html` or any other `docs/brainstorm/*.html`
  file has the same gap (this investigation checked only the wiring map file directly).

## Out of Scope

- Any change to the diagrams' own content/topology.
- `TCK-20260915-MECHANISM-PRIORITY-DERIVATION`'s own new generated charts (a separate, additive
  artifact type — this ticket is about the pre-existing hand-authored diagrams only).

## Acceptance Criteria

- [ ] A definitive, evidence-backed answer for how (if at all) these diagrams currently render for
      a real reader through this repo's own infrastructure.
- [ ] A working rendering path exists after the fix, verified directly (not assumed).

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

## Implementation Notes
Not yet started.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed as a real, separately-scoped gap per peer review during
`TCK-20260915-MECHANISM-PRIORITY-DERIVATION`'s own investigation, rather than folded into that
ticket's scope.
