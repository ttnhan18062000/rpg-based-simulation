---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT
artifact_type: test_plan
tags: [architecture, content]
---

# Test Plan — TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT

No `src/` code changes and no automated test suite covers `docs/brainstorm/*.html` — verification is
direct, scripted checks against the two changed files, run as part of the migration itself (see
`plan.md`'s Verification section) plus these additional checks before commit.

## Normal flow

- Both files still render conceptually the same content: round-trip JSON equality (old parsed blob ==
  new parsed blob) for all three data blobs, checked programmatically.
- `renderCard`'s anchor-id output (`id="idea-N"`) is unchanged in count and value, re-derived from the
  `title` field the same way the real render function does.

## Edge cases

- Any card/section/revision `title` or `text` field containing characters that need JSON escaping
  (quotes, backslashes, non-ASCII like curly quotes or em-dashes, already confirmed present in
  `REVISIONS`) — round-trip equality check covers this directly; `json.dumps(..., ensure_ascii=False)`
  preserves non-ASCII characters as literal UTF-8 rather than `\uXXXX` escapes, keeping the file
  readable.
- The new `<script type="application/json">` block must not itself be treated as executable JS by the
  browser (it isn't — `type="application/json"` is a standard way to embed non-executing data) and must
  not break `html.parser`'s parse of the file.

## Failure modes

- If round-trip equality fails for any blob, the migration script aborts before writing the file —
  never leave a file half-migrated or with silently-altered content.
- If `html.parser` raises on the post-change file, the change is reverted before commit — a page that
  fails to parse is a regression regardless of how clean the underlying JSON is.

## Regression-prone paths

- Anchor ids (`id="idea-N"` in the Atlas) are the one place external state could depend on this file's
  exact output — cross-linked from other brainstorm docs and from `docs/plans/rpg_design_roadmap/`.
  Verified directly (see above), not just assumed safe because the render function wasn't touched.

## Architecture tests

- Not applicable — no durable state, no authoritative mutation path. This is a static-asset formatting
  change.
