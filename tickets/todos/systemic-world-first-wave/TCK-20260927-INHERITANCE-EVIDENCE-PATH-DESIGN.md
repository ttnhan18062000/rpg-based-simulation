---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260927-INHERITANCE-EVIDENCE-PATH-DESIGN
phase: open
date: 2026-09-27
tags: [lifecycle, investigation]
---

# TCK-20260927-INHERITANCE-EVIDENCE-PATH-DESIGN

## Title
Choose a legitimate, viewpoint-scoped evidence path through which a situated observer could
encounter a single inheritance

## Status
OPEN — brief only, not started. First-wave milestone M2. Independent of M1/M4a/M3. It never gates
world-side work. Starts only after the owner reviews the first-wave scope.

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
**Semantic contract** (roadmap §2 epistemic principle):
- A player learns the world from situated evidence. Every surface is a projection with a viewpoint
  and scope.
- Hidden world truth is never exposed to make a demonstration easier.
- Private events may stay private.
- Direct participation, uninvolved witnessing, and hearsay are distinct cases (roadmap §3.4).

**Observed problem** (read-only code inspection, 2026-09-27; roadmap §7.2):

| Check | Result | Evidence level |
|---|---|---|
| World state: the heir's inventory gains the item | `PASS` | Scenario runtime (`test_heir_inventory_transfer_corpus.py`, 1 passed) |
| Encounter: a co-located observer can receive a signal about it | `BLOCKED_WITH_REASON`, because no in-world carrier exists | Production-path inspection |
| Provenance: any clue identifies inheritance specifically | `ABSENT` | Production-path inspection |
| Inference by a blinded human | `BLOCKED` (nothing is encounterable to reason from; not `PENDING`) | — |

Supporting observations, cited as evidence and not as a design:
- the perceived-entity record carries no item or equipment information (`src/core/cognition.py:28-33`);
- the perception update phase has no production caller;
- the knowledge model assimilates only paid information facts;
- the inheritance transfer carries no origin marker (`src/systems/lifecycle_systems/lifecycle.py:252-257`).

## Scope
A short design note, reviewed by the owning domain(s), which:
1. names the minimum evidence-production and carrier path that would let a specified,
   provisional observer legitimately encounter a single inheritance, or its visible consequence;
2. states its viewpoint scope, its authority, and what stays hidden;
3. names the owning domain;
4. drafts the implementation ticket.

## Out of Scope
- Building the path.
- The scripted encounter and non-leakage test that becomes possible once the path exists.
- The blinded-human exercise.
- Any global history, event, or reputation feed.
- A permanent gameplay-lens decision.

## Acceptance Criteria
1. The design note exists and has been reviewed. It justifies its choice by domain meaning,
   authority, and viewpoint scope, and it names the owning domain.
2. The note says whether the chosen path yields only an ambiguous clue ("this person now carries
   X") or an inheritance-specific one, and why that is sufficient for the claim it would support.
3. The note names what must never leak through the path, including private cognition/strategic
   fields such as `cognition.motivation.named_intention` and `strategic.blockers`.
4. The implementation ticket is drafted.
5. Player-facing status is recorded explicitly. It stays `BLOCKED` until the path exists, then
   `PENDING` until a blinded-human exercise runs, and is never inferred from script output.
6. If no candidate is acceptable to its domain owner, the ticket closes `BLOCKED_WITH_REASON`,
   recording the objection.

## Related Tickets
None yet. The ticket drafted under acceptance criterion 4 becomes the follow-on.

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §2, §3.4, §3.5, §7.2
- `docs/plans/systemic_world/first_wave_plan.md` M2 and "Future follow-ons"

## Related Stored Artifacts
None.

## Related Code Areas
`src/domains/perception/`, `src/core/cognition.py`, `src/cognition/knowledge_model.py`,
`src/systems/lifecycle_systems/lifecycle.py`. Evidence locations only.

## Assumptions / Open Questions
- **Candidate directions (non-binding; the design owner decides).** Inspection surfaced two:
  - viewpoint-scoped visible equipment in perception, which yields only an ambiguous clue;
  - a witness-scoped local inheritance event, which makes an inheritance-specific clue possible.

  A dedicated provenance record is one possible means, not a requirement.
- **Grief trigger (related risk).** The existing grief trigger reaches trusted allies regardless of
  location (`src/observability/event_extractor.py:1722-1762`). That may conflict with the epistemic
  principle. It is noted for the roadmap's §3.4 track, not this ticket.

## Implementation Notes
_Not started — owned by the design/implementation agent._

## Test Summary
_Not started._

## Files Changed
_Not started._

## Completion Summary
_Not started._
