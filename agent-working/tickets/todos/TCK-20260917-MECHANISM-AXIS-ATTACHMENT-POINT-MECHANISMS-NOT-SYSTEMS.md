---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS
phase: open
date: 2026-09-18
tags: [architecture, documentation, schema]
---

# TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS

## Title
Record: axes attach to mechanisms, not systems — resolved independent of the `system` tier's own
fate

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` (Assumption #4) and
`TCK-20260917-EPIC-MECHANISM-TIER-MODEL` (Scope, `axis` tier) both left one open question
unresolved: does an axis — a declared, overlapping, cross-cutting dimension of play (spatial,
temporal, knowledge-belief) — attach to individual **mechanisms**, or to the coarser **system**
grouping above them? Attaching to systems means fewer declarations; attaching to mechanisms is more
precise.

`TCK-20260917-EPIC-MECHANISM-TIER-MODEL` closed with the disposition **do not build the `system`
tier** (see that epic's own Completion Summary; root cause: `depends_on` encodes prerequisite, a
system encodes collaboration, and no traversal over the first reliably produces the second). That
closes off "attach to systems" as an option **by construction** — there is no system tier for an
axis to attach to. But the question was never answered on evidence of its own; it was foreclosed by
the tier it would have attached to disappearing. This ticket exists to state the real, independent
reason axes attach to mechanisms: the temporal axis proposal's own concerns span three different
candidate systems (see below), which is a data point in the mechanism-attachment column regardless
of whether the `system` tier ever existed.

## Scope
1. Record the evidence: the temporal axis proposal (`docs/brainstorm/*temporal-axis-proposal.md` /
   the calendar-authority investigation thread referenced in `docs/plans/mechanism_tier_model_initiative.md`)
   raises concerns that land on mechanisms spanning at least three different candidate system groupings
   investigated in `TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION` (combat-adjacent,
   progression-adjacent, world/economy-adjacent) — a single axis crossing that many system-level
   boundaries is itself evidence that system-level attachment would either force one axis into
   multiple system entries (defeating "fewer declarations") or push the axis to attach at whatever
   level actually varies per-concern, which is the mechanism.
2. State plainly, in whatever doc ends up carrying axis design (`docs/plans/mechanism_tier_model_initiative.md`'s
   own axis section, updated per that doc's own status-block ticket) that axis declarations are a
   per-mechanism tag list, overlapping, with no mechanical derivation — same "no mechanical backing"
   caveat `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` §2 already named, now anchored to
   mechanisms specifically rather than left ambiguous between the two tiers.
3. This ticket does **not** implement axis declarations in `registries/mechanisms.yaml` — no `axis`
   field, no schema change. It records the attachment-point finding so a future axis proposal (e.g.
   the temporal axis itself, or the knowledge-belief / social-relationship / legacy-memory axis docs
   already referenced in `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM`'s own Related Docs)
   has a settled attachment point to design against, rather than reopening this question per proposal.

## Out of Scope
- **Building the `axis` tier itself** (schema, validation, declaration mechanics) — that was
  `TCK-20260917-EPIC-MECHANISM-TIER-MODEL`'s child 3, now permanently undrafted alongside child 2. An
  axis attachment *point* can be recorded without building the tier that would consume it; if an axis
  tier is ever reconsidered under a different design (not derived from `depends_on`), this ticket's
  finding is what it should start from.
- **Re-deriving the `system` tier** to test the alternative. The epic's own disposition already
  forecloses this on independent grounds; this ticket does not relitigate that.
- **The temporal axis proposal's own substantive design** (what the axis actually declares) — only
  the attachment-point question is in scope here.

## Acceptance Criteria
1. The three-candidate-system evidence for the temporal axis is stated with real ticket/doc
   citations, not asserted from memory.
2. The finding is written somewhere durable and referenceable (this ticket, cross-linked from
   `docs/plans/mechanism_tier_model_initiative.md`'s status block) — not left only in a closed
   ticket's Completion Summary prose where a future axis proposal would not think to look.
3. No schema or registry change is made under this ticket — recording only.

## Related Tickets
- `TCK-20260917-EPIC-MECHANISM-TIER-MODEL` — **done**; this ticket carries forward one of its two
  surviving results (the other being the depends_on-audit's independent value).
- `TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION` — **done**; source of the
  three-candidate-system evidence this ticket cites.
- `TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` — **done, superseded**; original source
  of the axis-attachment open question (its own Assumption #4).

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md` — the model and its own status block, to be
  cross-linked once updated.

## Related Stored Artifacts
None yet.

## Related Code Areas
None — documentation/recording ticket, no registry or code changes.

## Assumptions / Open Questions
None currently — the attachment-point question this ticket answers was the open question; no new
one is introduced. If a future axis proposal finds a mechanism-level attachment awkward in practice,
that would be new evidence to record here or in a follow-on ticket, not an open question yet.

## Implementation Notes
Not yet started.

## Test Summary
Not applicable — documentation/recording ticket, no code under test.

## Files Changed
None yet (this ticket file only, plus a cross-link edit to
`docs/plans/mechanism_tier_model_initiative.md` when actioned).

## Completion Summary
Open. Filed 2026-09-18 alongside the closure of `TCK-20260917-EPIC-MECHANISM-TIER-MODEL`, per the
same principle applied earlier this epic to `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS`:
a finding that survives independently of the ticket that produced it gets its own home rather than
being buried in a closing ticket's prose.
