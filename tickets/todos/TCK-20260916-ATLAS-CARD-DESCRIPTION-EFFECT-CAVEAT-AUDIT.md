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

**A second, differently-shaped confirmed instance (found 2026-09-16, while tracing dependency
edges for `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION` — not this ticket's own scan, and
not `camp`'s own precondition-gap shape)**: `motivation_doctrine`'s atlas card (`entity-cognition#5`)
described a class-based doctrine-resolution system as "confirmed live via the always-on Adventure
route scoring path." The described code (`DoctrineResolver`, `MotivationBiasService`) was real once
but has since been **deleted outright** (`TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT`,
confirmed dead in production before removal, see `docs/guidelines/intentional_divergences.md`
§2.53), superseded by `adventure_routing`'s own live `personality_bias` mechanism. Foundation's own
seeding cited a card describing pre-retirement architecture without cross-checking it against the
already-existing divergence record. Corrected: `state: gap` (not `orphan` — the implementing code
is gone, not merely present-with-zero-callers, and `orphan` would be a literally false claim once
claims-as-tests makes it executable) + `verified: {instrument: code_trace, verdict: observed}`.
Atlas card and capabilities card (`mind#7`) both corrected to match, including their own stale
description text, not just their badges/tiers.

**Two confirmed instances now, from different directions** — `camp` found by reading a
description for a precondition gap, `motivation_doctrine` found by tracing a dependency edge into
a card whose framing turned out to be a stale, pre-retirement account. Per peer review, this
broadens what this audit's own re-read should check: not just "does the description contain a
never-fires caveat the badge misses" (`camp`'s shape), but also "does the description's own
framing still match `docs/guidelines/intentional_divergences.md`'s record for that subsystem" —
a card can be wrong not because of a caveat buried in its own prose, but because the prose itself
describes an architecture the codebase has since moved past.

## Scope

- Re-read all 73 mechanism-mapped atlas cards' own full `desc` text (not just badge/title) for a
  real, effect-level "never observed working in practice" caveat the current `state` doesn't
  already carry (`camp`'s own shape).
- **Also check each card's own description against `docs/guidelines/intentional_divergences.md`**
  for the subsystem it describes — not just for a hidden caveat, but for whether the description
  itself still matches the current architecture, or describes something since retired/superseded
  (`motivation_doctrine`'s own shape, found 2026-09-16).
- For each real precondition-gap instance found (matching `camp`), record a
  `verified: {instrument: code_trace, verdict: contradicted}` block (`state` unchanged, not
  `orphan`).
- For each real stale-architecture instance found (matching `motivation_doctrine`), correct
  `state` to whatever the current code actually supports (`gap` if the implementing code no longer
  exists, per the claims-as-tests-survives-execution reasoning recorded on that mechanism's own
  `verified` note — never `orphan` for code that isn't merely uncalled but is gone outright) and
  record `verified: {instrument: code_trace, verdict: observed}`, plus correct the card's own
  description text (not just its badge), citing the specific divergence-record entry.
- Cross-reference every precondition-gap instance found against
  `docs/plans/world_composition_precondition_gap_finding.md`'s existing pattern.

## Out of Scope

- Design-idea cards (68 of them) — this ticket only re-reads the 73 mechanism-mapped cards.
- Re-deriving the card-to-mechanism mapping itself (already built and verified in
  `tools/mechanism_registry/mechanism_atlas_card_mapping.py` by `TCK-20260915-ARTIFACT-STATE-CONVERGENCE`).
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
- `TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT` — the retirement `motivation_doctrine`'s own
  card missed.
- `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION` — where `motivation_doctrine`'s own instance
  was found, incidentally, while tracing an unrelated edge.

## Related Docs
- `docs/plans/world_composition_precondition_gap_finding.md` — the pattern `camp` belongs to.
- `docs/guidelines/intentional_divergences.md` §2.53 — the retirement record `motivation_doctrine`'s
  own stale card should have been checked against.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md` — the original
  citation table this ticket re-checks.

## Related Code Areas
- `docs/brainstorm/rpg_feature_atlas.html`
- `docs/brainstorm/mechanisms.yaml`
- `tools/mechanism_registry/mechanism_atlas_card_mapping.py`

## Assumptions / Open Questions
- Whether the real instance count beyond `camp` is 0, a handful, or many — genuinely unknown until
  the re-read happens; this ticket exists specifically because nobody has checked yet.

## Implementation Notes
This is also the natural first real producer for the verification axis at scale — a better outcome
than `TCK-20260915-ARTIFACT-STATE-CONVERGENCE` quietly absorbing this work as scope creep on the
epic's last child ticket.

**The motivating measurement for the prose-duplication question, parked but recorded here per peer
review (2026-09-16), not acted on in this batch**: fixing `motivation_doctrine` required a manual
prose correction in *three* separate documents (the atlas card, the capabilities card, and the
wiring map's own node label) — none of which is a field T4's own convergence made derivable.
`state` correctly derives from the registry now; the *description text* explaining what a state
means does not, and is still hand-authored once per artifact. One retirement
(`TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT`) went uncaught for eight days specifically
because all three descriptions kept saying "confirmed live"/"currently real" independently, and a
correct `state` token sitting next to a wrong paragraph doesn't help a reader who reads the
paragraph, not the token. **This is sharper, concrete evidence for the same duplication principle
the user has already stated as absolute** (one document owns a piece of information; a generated
rendering is fine, a second hand-authored copy is not) — the standing atlas↔capabilities
mirroring rule is the corpus's largest surviving instance of exactly this. Not this ticket's own
scope to resolve; recorded so it is a decision to make deliberately later, not something
rediscovered from scratch.

## Test Summary
Not yet started.

## Files Changed
None yet (this ticket file only).

## Completion Summary
Open. Filed as a real, separately-scoped follow-up per peer review, rather than swept into
`TCK-20260915-ARTIFACT-STATE-CONVERGENCE`'s own scope.
