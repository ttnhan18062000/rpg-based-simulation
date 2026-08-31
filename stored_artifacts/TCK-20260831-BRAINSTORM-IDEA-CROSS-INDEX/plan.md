---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX
artifact_type: plan
tags: [architecture, content]
---

# Plan — TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX

## Step 1 — add Scorecard row anchors

One-time content edit to `design_merit_scorecard.html`: for each `<tr>` in the Full Scorecard table
whose first `<td>` contains `<span class="num">N.</span>`, add `id="score-N"` to that `<tr>`. Pure
attribute insertion — no visible rendering change, verified by `html.parser` parse plus a diff showing
only `id="score-N"` insertions.

## Step 2 — write `tools/generate_brainstorm_idea_index.py`

Mirrors `tools/generate_registry.py`'s shape (a real generator script with a `--output` flag, run via a
Makefile target, output committed to the repo). For ideas 1-66:

1. **`atlas_anchor`**: grep `rpg_feature_atlas.html` for `id="idea-N"`; always present for 1-66.
2. **`schema_anchor`**: grep `rpg_expected_schemas.html` for `id="schema-N"`; `null` if absent.
3. **`scorecard_anchor`**: grep `design_merit_scorecard.html` for `id="score-N"` (added in Step 1);
   `null` for idea 66 (never scored) and any other genuinely absent case.
4. **`wiring_map_mentions`**: count of `\bidea N\b` (case-insensitive) occurrences in
   `rpg_simulation_wiring_map.html` — an informational hint, not a link.
5. **`milestone`**: looked up from a small, explicit table built directly from each M1-M9 epic doc's
   `**Source:**` line (parsed at generation time via regex against each epic file, not hardcoded from
   memory) — `null` for M7/M8/M9 and for any idea number not found in any epic's list, except idea 66
   which is hardcoded as `"M8"` per the roadmap's own explicit Sequencing-rules statement (idea 66 isn't
   listed in any epic's `**Source:**` line the same way the other 65 are, since it was added after the
   original corpus).

Every anchor value is verified against the real file content at generation time (grep-and-check, not
asserted) — if a claimed anchor doesn't actually exist in its source file, the generator raises rather
than writing a dangling reference.

Output: `docs/brainstorm/idea_index.json`, a JSON object with a `_meta` key (schema description,
regeneration command, generation date) and an `"ideas"` array of 66 entries, sorted by idea number.

## Step 3 — Makefile target

`brainstorm-idea-index: ## Regenerate the per-idea cross-document index (docs/brainstorm/idea_index.json)`
running the new script — same shape as the existing `docs-registry` target.

## Verification

1. Exactly 66 entries, idea numbers 1-66 with no gaps or duplicates.
2. Every non-null anchor value resolves to a real id in its source file (re-checked independently after
   generation, not just trusted from the generator's own internal check).
3. Milestone totals match `investigation.md`'s counts exactly (M1=20, M2=16, M3=5, M4=12, M5=8, M6=4,
   idea 66="M8", all else null).
4. `design_merit_scorecard.html`: `html.parser` parses cleanly; diff shows only `id="score-N"`
   attribute insertions (65 of them), nothing else.
5. Running the generator twice produces byte-identical output (idempotency) — confirms no
   non-deterministic ordering (e.g. dict/set iteration) leaked into the JSON.

## What this plan does NOT do

- Does not add anchors to the Wiring Map — confirmed structurally unsupported without a rewrite
  (`investigation.md`).
- Does not score idea 66 in the Merit Scorecard — out of this ticket's scope, a separate design-review
  decision.
- Does not change any prose content in any of the four source documents.
