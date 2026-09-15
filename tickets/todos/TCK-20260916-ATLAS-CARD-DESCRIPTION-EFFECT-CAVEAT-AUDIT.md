---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT
phase: open
date: 2026-09-16
tags: [architecture, investigation, schema]
---

# TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT

## Title
Re-read every mechanism card's full description for effect-level caveats the badge doesn't carry — `camp` is the confirmed instance, there may be more among the other 74

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary

Found live during `TCK-20260915-ARTIFACT-STATE-CONVERGENCE`'s own systematic atlas-drift check.
The registry's `camp` mechanism was seeded `state: done` from `Foundation`'s own citation
(`atlas beyond-city#0`), which is accurate for the card's own badge and title ("Camp: real,
dormant scaffolding for a lesser settlement"). But the card's full **description** text (not the
badge, not the title) contains a real, load-bearing caveat the citation missed: "no compiled or
procedurally-generated world anywhere ever seeds `state.camps`... this real, substantial system is
a permanent no-op in every world today."

That's the same shape as `docs/plans/world_composition_precondition_gap_finding.md`'s own pattern
— real, correct, wired code that never fires because a world-composition precondition is never
met. Resolved for `camp` in `TCK-20260915-ARTIFACT-STATE-CONVERGENCE` as `state: done` +
`verified: {instrument: code_trace, verdict: contradicted}` — the code is fine, the mechanism has
simply never been observed doing anything, and `contradicted` (not `orphan`) is the correct verdict
since the code itself is not defective.

**The methodology gap, not just the one instance**: `camp`'s own seeding read the card's badge and
title, and missed a caveat sitting in the card's own description. That is a real methodology gap in
how the registry's initial 75-mechanism seed was built (`TCK-20260915-MECHANISM-REGISTRY-
FOUNDATION`), not a one-off slip specific to `camp` — any other card whose badge says one thing
while its own prose records a "never fires / never seeded / no world contains this" caveat would
have been seeded the same, incomplete way.

## Scope

- Re-read all 73 mechanism-mapped atlas cards' own full `desc` text (not just badge/title) for a
  real, effect-level "never observed working in practice" caveat the current `state` doesn't
  already carry.
- For each real instance found (matching `camp`'s own shape — correct, wired code with a real,
  confirmed precondition gap), record a `verified: {instrument: code_trace, verdict: contradicted}`
  block, mirroring `camp`'s own disposition exactly (`state` unchanged, `verdict: contradicted`,
  not `orphan`).
- Cross-reference every instance found against
  `docs/plans/world_composition_precondition_gap_finding.md`'s existing pattern.

## Out of Scope

- Design-idea cards (68 of them) — this ticket only re-reads the 73 mechanism-mapped cards.
- Re-deriving the card-to-mechanism mapping itself (already built and verified in
  `tools/mechanism_atlas_card_mapping.py` by `TCK-20260915-ARTIFACT-STATE-CONVERGENCE`).
- Auto-ingesting any of this from an automated instrument. Every verdict here is a `code_trace`
  finding, written deliberately after a real re-read, matching `TCK-20260915-MECHANISM-
  VERIFICATION-AXIS`'s own explicit scope limit (no automated ingestion).

## Acceptance Criteria

1. Every one of the 73 mechanism-mapped cards' `desc` field has been actually read for this class
   of caveat, not sampled.
2. Every real instance found gets a `verified` block matching `camp`'s own disposition
   (`state` unchanged, `code_trace`/`contradicted`), with a citation to the specific description
   text that surfaced it.
3. A clear negative result ("re-read all 73, found N more real instances beyond camp, here they
   are") is an acceptable, complete outcome — this ticket does not need to find a large number to
   be done; it needs to have actually checked.

## Related Tickets
- `TCK-20260915-ARTIFACT-STATE-CONVERGENCE` — where `camp` was found and the methodology gap
  surfaced.
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — the original seeding pass this ticket audits.
- `TCK-20260915-MECHANISM-VERIFICATION-AXIS` — owns the `verified` schema this ticket populates
  more of.

## Related Docs
- `docs/plans/world_composition_precondition_gap_finding.md` — the pattern `camp` belongs to.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md` — the original
  citation table this ticket re-checks.

## Related Code Areas
- `docs/brainstorm/rpg_feature_atlas.html`
- `docs/brainstorm/mechanisms.yaml`
- `tools/mechanism_atlas_card_mapping.py`

## Assumptions / Open Questions
- Whether the real instance count beyond `camp` is 0, a handful, or many — genuinely unknown until
  the re-read happens; this ticket exists specifically because nobody has checked yet.

## Implementation Notes
This is also the natural first real producer for the verification axis at scale — a better outcome
than `TCK-20260915-ARTIFACT-STATE-CONVERGENCE` quietly absorbing this work as scope creep on the
epic's last child ticket.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed as a real, separately-scoped follow-up per peer review, rather than swept into
`TCK-20260915-ARTIFACT-STATE-CONVERGENCE`'s own scope.
