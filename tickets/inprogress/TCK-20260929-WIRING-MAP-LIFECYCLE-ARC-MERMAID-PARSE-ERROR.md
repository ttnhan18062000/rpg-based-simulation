---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260929-WIRING-MAP-LIFECYCLE-ARC-MERMAID-PARSE-ERROR
phase: open
date: 2026-09-29
tags: [process-improvement]
---

# TCK-20260929-WIRING-MAP-LIFECYCLE-ARC-MERMAID-PARSE-ERROR

## Title

The wiring map's Entity Lifecycle Arc diagram fails to parse because of a bare `()` inside a
square-bracket node label, so it renders as a mermaid error banner.

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P3

## Request Summary

Found by `TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS` (branch
`working-log-consolidation-cross-checkout-fix`, `045136573` / `a2e69ddd1`), which added mermaid.js
to `docs/brainstorm/rpg_simulation_wiring_map.html` and `rpg_feature_atlas.html`. That ticket
verified all 7 diagrams with `mermaid.parse()` (v10.9.1, Node/jsdom). 6 parse, and 1 fails: the
wiring map's "Entity detail: the lifecycle arc" (`flowchart LR`), real file line 614:

```
SC[Scarred — NOT BUILT, heal_wound&#40;&#41; deleted; wounds decided permanent, DEV-005]
```

The browser decodes `&#40;&#41;` to `()` before mermaid sees the text, and a bare `(` inside an
unquoted `[...]` label is read as round-node syntax. Exact parser output (recorded in that ticket):

```
Parse error on line 9:
...OT BUILT, heal_wound() deleted; wounds d
-----------------------^
Expecting 'SQE', ..., got 'PS'
```

Before the mermaid.js include, the diagram was silently raw text. Now it's a visible error banner:
better, but still broken.

## Scope

- Quote the label so mermaid treats it as text, for example
  `SC["Scarred — NOT BUILT, heal_wound() deleted; wounds decided permanent, DEV-005"]`, keeping the
  wording identical.
- Check that no other node label in either file has the same unquoted bracket/paren pattern.
- Re-run the same `mermaid.parse()` check on all 7 diagrams. All must parse.

## Out of Scope

- Any wording or content change to the label. Note for the user: "Scarred — NOT BUILT … wounds
  decided permanent" may be stale now that the registry's `trauma` mechanism reads `done` (the
  Operating Loop's TRM node is `live`). Whether the Lifecycle Arc's text should change is a content
  decision for whoever owns the wiring map, not part of this syntax fix.
- The mermaid.js include itself (done in TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS).

## Acceptance Criteria

- AC1: `mermaid.parse()` succeeds for all 7 diagrams across both files. Record the command and
  its output.
- AC2: The SC label's visible text is unchanged apart from the added quoting.
- AC3: `mechanism_wiring_map_classdef.py --check` still passes (that diagram isn't in its mapping,
  but the file is shared).

## Related Tickets

- `TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS` (found it)
- `TCK-20260919-MECHANISM-WIRING-MAP-CLASSDEF-REGENERATE-MODE-GAP` (same file)

## Related Docs

- `docs/brainstorm/rpg_simulation_wiring_map.html`

## Related Stored Artifacts

None.

## Related Code Areas

- `docs/brainstorm/rpg_simulation_wiring_map.html`

## Assumptions / Open Questions

- Assumes mermaid 10.9.1's quoted-label syntax accepts the em-dash and parens. AC1 verifies this
  directly rather than assuming it.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
