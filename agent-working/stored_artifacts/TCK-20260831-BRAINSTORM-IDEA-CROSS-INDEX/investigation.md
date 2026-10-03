---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX
artifact_type: investigation
tags: [architecture, content]
---

# Investigation — TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX

## Trigger

Researching one design idea across the brainstorm corpus requires manually checking up to 5 documents
by idea number — a real, measured cost from this session's own codex-reconciliation work, where doing
exactly this by hand for ~10 ideas took a significant fraction of that session. `search_docs` (now
functional per `TCK-20260831-KNOWLEDGE-INDEX-HF-HUB-TIMEOUT`) helps with free-text queries but doesn't
answer "show me every document that discusses idea 39" directly.

## Method

Direct grep of each document's real anchor/id conventions, and of each M1-M9 epic doc's `**Source:**`
line for idea-number ownership.

## Findings

- **Feature Atlas** (`rpg_feature_atlas.html`): `id="idea-N"` anchors, generated at render time by
  `renderCard`'s regex against each card's `title` field. 66 anchors confirmed present (verified
  directly in `TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT`'s own anchor-preservation check) — ideas 1-65
  plus idea 66.
- **Schema Registry** (`rpg_expected_schemas.html`): `id="schema-N"` anchors, but only for the ~30
  ideas that introduce new durable state (confirmed by its own "Coverage Note" section, which explicitly
  lists which ideas are pure logic/wiring fixes with no schema). 30 anchors present.
- **Merit Scorecard** (`design_merit_scorecard.html`): idea number appears as text inside a
  `<span class="num">N.</span>` in each of 65 `<tr>` rows (idea 66 explicitly excluded, added after the
  original scoring pass — confirmed in `TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT`'s own fork report).
  **No `<tr id="...">` exists anywhere in this file** — confirmed by direct grep (`<tr id=` returns 0
  matches). This document currently has no anchor to link to at all, for any idea.
- **Wiring Map** (`rpg_simulation_wiring_map.html`): "Idea N" / "idea N" appears as prose text 79 times
  across the file, but not 1:1 per idea — some ideas are mentioned in multiple different rows (e.g. idea
  17's wound/scar mechanic touches both the Trauma summary row and Lifecycle Arc rows T6/T7), and some
  mentions are incidental cross-references inside another idea's own row (e.g. "Idea 22 flags this split
  as an open question" appearing inside idea 21's row). There is no reliable way to derive a single
  correct per-idea anchor from this document's current structure without restructuring it — confirmed by
  spot-checking several ideas' mention patterns directly, not assumed from the raw count alone.
- **Milestone ownership**: each M1-M9 epic doc's `**Source:**` line lists its exact idea numbers
  directly. Extracted directly via grep (not retyped from memory): M1 = {1,3,7,9,10,12,13,15-19,20-22,
  24-26,29,42} (20 ideas), M2 = {2,4,5,6,8,11,14,23,27,28,30,35,36,37,43,48} (16 ideas), M3 =
  {31,32,33,34,38} (5), M4 = {40,41,44,45,46,47,49,50,51,52,61,64} (12), M5 =
  {53,54,55,57,58,60,62,63} (8), M6 = {39,56,59,65} (4). Total: 65, matching the corpus size before idea
  66 was added. M7/M8/M9's own `**Source:**` lines cite process documents (`quality_scoring_contract.md`,
  direct code investigation), not idea numbers — confirmed these three own no idea-specific subset;
  recorded as `milestone: null` for any idea not in the M1-M6 lists above. Idea 66 is explicitly
  documented in the roadmap's own Sequencing rules as "scoped under M8" while gating M2's ideas 35/48 —
  recorded as `milestone: "M8"` for idea 66 specifically, distinct from the M1-M6 lists.

## Conclusion

A clean, verifiable 1:1 per-idea anchor exists today for the Atlas (all 66 ideas) and the Schema
Registry (the ~30 ideas with new state). The Merit Scorecard needs one small, safe addition
(`id="score-N"` on each row) to have an anchor at all. The Wiring Map genuinely does not support a
1:1 anchor without restructuring — the index records a mention-count hint for it instead of fabricating
an anchor that wouldn't reliably point at the right content. See `plan.md` for the generator's exact
approach.
