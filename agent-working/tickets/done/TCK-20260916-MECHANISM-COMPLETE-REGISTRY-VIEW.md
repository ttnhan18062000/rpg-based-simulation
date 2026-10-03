---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW
phase: done
date: 2026-09-16
tags: [architecture, schema, simulation-quality]
---

# TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW

## Title
A third generated view (all 75 mechanisms, priority + verification together), then a generated
HTML page replacing the hand-authored one already published

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Second user request: list all mechanisms classified by verified/not verified, not just the ranked
unverified-only list. Real gap, not an omission — the existing two views already cover all 75
between them but neither answers "what matters most, and do we know it works" in one place:
- `mechanism_verification_view.md` — all 75, no priority, sorted verdicts-first then alphabetically.
- `mechanism_priority_view.md` — priority, unverified only, truncated at top-25.

A verified mechanism has no rank; a high-priority mechanism's verdict is in a different document.

Separately, peer's own earlier attempt to answer this request by hand-authoring a published
artifact (embedding the 75/67 numbers, the ranked table, the ledger directly) was caught and
reverted before landing — exactly the failure this epic exists to prevent: a hand-maintained
surface duplicating generated data, which would go stale the moment `mechanisms.yaml` changes
(which the dependency-edge ticket just did). The fix belongs in a generated view; nothing
hand-authored.

**Governing principle** (user, absolute): a piece of information must be defined in one document
only. Defined-once-rendered-many-times is fine (a generated file is a rendering); authored twice
is not, regardless of register or audience.

## Scope
1. A third generated view, `docs/brainstorm/mechanism_registry_view.md`: all 75 mechanisms, one row
   each. Columns: mechanism, layer, state, evidence (runtime/static/unverified), verdict, priority,
   transitive dependents. Sorted by priority descending. Counts by verification status at the head.
   Do not delete the other two views — this is a third, not a replacement; each answers a
   genuinely different question (verify next / rank everything / full ledger detail).
2. A generated HTML page, `docs/brainstorm/mechanism_registry.html`, built by a new `make` target
   from `mechanisms.yaml` directly — data generated, never typed. The measured epic findings (17%
   wiring drift, 2 stale atlas badges, the `camp` seeding error, the scoping doc's own wrong claim,
   the inverted priority formula) are **linked to** the epic ticket's own Completion Summary, never
   restated on the page — restating them would itself be the duplication this ticket exists to
   avoid. Framing prose, wherever genuinely needed, lives in the generator script, defined once.
3. Sequenced after the dependency-edge ticket (already landed) specifically so priority numbers
   published here are the corrected, fuller-graph numbers, not the ones already known to be wrong.
4. Reconsider the priority view's own top-25 truncation now that a complete view exists — prefer
   the complete view stay complete/scrollable rather than also truncated, so foundational
   mechanisms don't disappear again for a new reason.

## Out of Scope
- Deleting or restructuring the existing two views (`mechanism_verification_view.md`,
  `mechanism_priority_view.md`) — both stay, each still the right answer to its own narrower
  question.
- Claims-as-tests phase 1 (caller-count/stub detection) — sequenced explicitly after this ticket,
  since it needs to run against this now-complete, now-correctly-prioritized graph, not before.
- The atlas↔capabilities prose-mirroring duplication (flagged by peer as the largest remaining
  hand-duplication in the corpus) — explicitly noted as a follow-up candidate, not acted on here.
- A which-document-owns-what table — explicitly flagged by peer as the same duplication error in a
  different shape; not built.

## Acceptance Criteria
1. The new markdown view contains all 75 mechanisms, correctly sorted by priority, with the
   verification-status counts stated at the head.
2. The new HTML page is generated (a `make` target, not hand-authored), regenerates cleanly from
   `mechanisms.yaml` alone, and is verified to stay in sync via the same `--check` convention the
   other two generators already use.
3. The HTML page links to the epic ticket's own measured findings rather than restating them.
4. The other two existing views are unmodified in structure/purpose (content naturally changes
   since the underlying registry changed, but their own scope/columns/audience stay as designed).
5. The top-25 truncation decision is explicitly revisited and recorded for this new complete view
   specifically (expected: no truncation here, since completeness is this view's whole purpose).

## Related Tickets
- `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION` — must land first; this view is generated
  from its corrected graph.
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — closed epic; this page links to, never restates, its
  Completion Summary's own measured findings.
- `TCK-20260915-MECHANISM-VERIFICATION-AXIS`, `TCK-20260915-MECHANISM-PRIORITY-DERIVATION` — own
  the two existing views this one sits alongside, not replaces.

## Related Docs
None new — this ticket's own governing principle is the user's standing instruction, not a
separate doc.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/mechanism_registry.py` (`all_mechanisms_combined_view`, already drafted)
- `tools/generate_mechanism_registry_view.py` (new, markdown)
- `tools/generate_mechanism_registry_html.py` (new, HTML page)
- `docs/brainstorm/mechanism_registry_view.md` (new, generated)
- `docs/brainstorm/mechanism_registry.html` (new, generated)
- `Makefile`

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Sequenced after `TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS` (node-set completeness) and
`TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING` (real code binding, needed so a completeness
checker could exist at all) landed. `all_mechanisms_combined_view()`
(`tools/mechanism_registry.py`) reuses `build_verification_view()` and `priority()` rather than
reimplementing either axis — a verified mechanism keeps its real priority number instead of being
dropped, the load-bearing difference from `unverified_priority_ranking()`.

The markdown view (`mechanism_registry_view.md`) carries an explicit "node-set note" stating that
every earlier published figure (the 67-unverified count, the priority ranking, the 26-hub
dependency count) was computed against the 75-mechanism set later found incomplete, and should be
treated as superseded — per peer review, this keeps the epic's own history honest rather than
letting a stale number stand uncorrected next to a new, correct one.

The HTML page (`mechanism_registry.html`) is fully generated from `mechanisms.yaml` via
`tools/generate_mechanism_registry_html.py` — no hand-typed data, reuses the same
`all_mechanisms_combined_view()` the markdown view uses so the two can never independently
disagree. It links to `TCK-20260915-EPIC-MECHANISM-REGISTRY`'s own Completion Summary for the
epic's measured findings (17% wiring drift, 2 stale atlas badges, the `camp` seeding error) rather
than restating them, per the ticket's own Scope item 2 and the user's standing "defined once"
principle.

AC #5 (top-25 truncation, revisited): kept for `mechanism_priority_view.md` — recorded directly in
that generator's own docstring. Its purpose is a short, actionable "verify next" list, not
completeness; truncating it no longer hides anything now that a genuinely complete view exists
alongside it.

## Test Summary
`tests/unit/tools/test_mechanism_registry_view.py` (8 tests) and
`tests/unit/tools/test_mechanism_registry_html.py` (7 tests), both passing against the final
89-mechanism registry. Full scoped suite: 165 tests passing, including with `graphify-out/`
genuinely moved aside and restored.

## Files Changed
- `docs/brainstorm/mechanisms.yaml`, `docs/brainstorm/mechanism_verification_view.md`,
  `docs/brainstorm/mechanism_priority_view.md`, `docs/brainstorm/rpg_feature_atlas.html`,
  `docs/brainstorm/rpg_simulation_wiring_map.html`, `docs/REGISTRY.yaml` — owned by
  `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING`, closed alongside this ticket in the same pass
- `tools/mechanism_registry.py` — `all_mechanisms_combined_view()`
- `tools/generate_mechanism_registry_view.py` — new, markdown generator with `--check` mode and the
  node-set superseded-figures note
- `tools/generate_mechanism_registry_html.py` — new, HTML generator, links to the epic's own
  Completion Summary rather than restating its findings
- `docs/brainstorm/mechanism_registry_view.md`, `docs/brainstorm/mechanism_registry.html` — new,
  generated
- `tools/generate_mechanism_priority_view.py` — docstring records the AC #5 truncation decision
- `Makefile` — `mechanism-registry-view`, `mechanism-registry-html` targets
- `tests/unit/tools/test_mechanism_registry_view.py`, `test_mechanism_registry_html.py` — new

## Completion Summary
Closed. Both scope items delivered: a third generated view (`mechanism_registry_view.md`, every
mechanism, priority + verification together, deliberately not truncated) and a generated HTML page
(`mechanism_registry.html`, replacing the hand-authored artifact peer caught and reverted before it
landed) — both regenerated against the genuinely complete, 89-mechanism, `implemented_by`-bound
node set the two prerequisite tickets produced, not the original 75. Every prior published figure
computed against that old set is explicitly marked superseded in the new view rather than left to
silently disagree with it. The two existing views (`mechanism_verification_view.md`,
`mechanism_priority_view.md`) are unmodified in structure/purpose. The top-25 truncation decision
for the priority view was explicitly revisited and kept, recorded in its own generator.
