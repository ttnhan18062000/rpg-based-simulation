---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX
artifact_type: test_plan
tags: [architecture, content]
---

# Test Plan — TCK-20260831-BRAINSTORM-IDEA-CROSS-INDEX

No `src/` change and no existing pytest suite covers `docs/brainstorm/*` or this new generator —
verification is direct, scripted checks run as part of implementation, matching the shape
`TCK-20260831-BRAINSTORM-DOCS-JSON-REFORMAT` used for the same document family.

## Normal flow

- Generator produces exactly 66 entries, idea numbers 1-66, no gaps/duplicates.
- Every non-null anchor in the output actually exists in its source file — checked by re-parsing each
  source file independently after generation and confirming the claimed id is present, not just trusting
  the generator's own internal assertion.
- Milestone counts match `investigation.md`'s directly-grepped totals exactly.

## Edge cases

- Idea 66: `atlas_anchor` present, `schema_anchor`/`scorecard_anchor` both `null`, `milestone: "M8"` —
  the one idea with a genuinely different shape from the other 65, verified explicitly rather than
  assumed to follow the general pattern.
- Ideas with no schema section (the ~36 pure-logic/wiring ideas): `schema_anchor: null`, confirmed
  against the Schema Registry's own "Coverage Note" list of which ideas it doesn't cover.

## Failure modes

- Generator raises (does not silently write a partial/wrong file) if any claimed anchor doesn't
  actually resolve in its source document.
- If `design_merit_scorecard.html`'s `id="score-N"` insertion breaks `html.parser` parsing, the change
  is reverted before commit.

## Regression-prone paths

- Re-running the generator after a future brainstorm-doc edit must still produce a correct index —
  verified here by running it twice against the same unchanged inputs and confirming byte-identical
  output (idempotency), the closest available proxy for "will still work correctly after a real edit"
  without actually editing the docs again in this ticket.

## Architecture tests

- Not applicable — no durable state, no authoritative mutation path.
