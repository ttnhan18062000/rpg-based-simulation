---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260929-WIRING-MAP-LIFECYCLE-ARC-MERMAID-PARSE-ERROR
phase: done
date: 2026-09-29
tags: [process-improvement]
---

# TCK-20260929-WIRING-MAP-LIFECYCLE-ARC-MERMAID-PARSE-ERROR

## Title

The wiring map's Entity Lifecycle Arc diagram fails to parse because of a bare `()` inside a
square-bracket node label, so it renders as a mermaid error banner.

## Status

DONE

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

Quoted the SC label exactly as the ticket's own example proposed:
`SC["Scarred — NOT BUILT, heal_wound() deleted; wounds decided permanent, DEV-005"]` (converted
the `&#40;&#41;` entities to literal `()` directly, since a browser already decodes them to `()`
for display either way — visually identical, AC2). Checked for any other unquoted `NODE[...]`
label containing a literal or entity-escaped paren across both `docs/brainstorm/*.html` files
(regex sweep, then eyeballed every paren-containing label line): none — `SC` was the only
instance. Added a small Python-only regex regression guard
(`tests/tools/test_wiring_map_mermaid_label_quoting.py`) against the same defect class recurring,
proportionate to the fix's own size (no new Node/mermaid npm dependency committed).

**Peer review round 2 (post-`4ddd6fd06`) — one required change, done:** the guard's first version
ran the label regex over each *entire* HTML file, not just mermaid source — prose cards, embedded
JSON, and `<script>` blocks were all in scope. `rpg_feature_atlas.html` is a pinned living page
other sessions edit often; ordinary prose like `[see TCK-1 (P1)]` or JS like `a[f(x)]` share the
same `\bWORD[...(...]` shape and would fail an unrelated atlas-edit PR, even though mermaid
parsing is unaffected outside a real mermaid block (confirmed no such pattern exists in the real
files *today* — this was a preventive fix for a future edit, not an active false positive). Fixed
by extracting `<pre class="mermaid">...</pre>` block contents first (the same extraction shape
this ticket's own `mermaid.parse()` verification script used) and applying the label regex only to
those. Added a negative test proving a paren-in-brackets string *outside* a mermaid block doesn't
trigger the guard.

## Test Summary

AC1: re-ran `mermaid.parse()` (v10.9.1, Node/jsdom, identical harness to
TCK-20260916-BRAINSTORM-HTML-MERMAID-NEVER-RENDERS) against all 7 real diagrams extracted from
both files. All 7 now return `VALID ... parse() returned true` (previously 6/7, with the wiring
map's 3rd diagram failing "Parse error on line 9"). AC2: label's decoded/visible text unchanged,
confirmed by inspection (entity-decoded original === new literal text, byte-for-byte). AC3:
`python3 tools/mechanism_registry/mechanism_wiring_map_classdef.py --check` still `OK`
(unaffected — `SC` isn't in that tool's `OPERATING_LOOP_NODE_TO_MECHANISM_ID` mapping). New guard
test (now 5 tests, round 2) confirmed to fail on the pre-fix content (revert/rerun/restore method)
and pass after; the block-scoping negative test confirms a false-positive-shaped prose/JS string
outside a mermaid block is correctly ignored. `tests/unit/tools/test_mechanism_wiring_map_classdef.py`
(15 tests) unaffected, still pass.

## Files Changed

- `docs/brainstorm/rpg_simulation_wiring_map.html`
- `tests/tools/test_wiring_map_mermaid_label_quoting.py` (new; block-scoped in round 2)

## Completion Summary

Quoted the one unquoted mermaid node label containing parens (real file line 614), the exact
shape that broke `mermaid.parse()` for the wiring map's Entity Lifecycle Arc diagram. Verified all
7 real diagrams across both `docs/brainstorm/*.html` files now parse (previously 6/7), confirmed
no visible content changed, confirmed the mechanism-registry drift check is unaffected, and added
a lightweight regression guard against the same defect class. Left the label's stale-sounding
content ("wounds decided permanent") untouched per Out of Scope — a content question for whoever
owns the wiring map, not this syntax fix.
