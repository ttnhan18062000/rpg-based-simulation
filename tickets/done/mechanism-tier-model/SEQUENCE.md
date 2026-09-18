# Implementation Sequence — mechanism-tier-model

tracking_doc: docs/plans/mechanism_tier_model_initiative.md

`TCK-20260917-EPIC-MECHANISM-TIER-MODEL` is the epic-tier parent and is not implemented directly —
it tracks the child(ren) below. This epic deliberately starts with exactly one drafted child;
children 2–4 (the `system` tier, the `axis` tier, and the proposal-decomposition check) are named
in the epic's own Scope but not drafted, since their shape depends on this investigation's own
findings — drafting them now would invent structure rather than discover it.

## Order

1. TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION (no deps in this batch — the only
   drafted child)

## Why This Order Matters

There is only one child to sequence. Children 2–4 are expected to be filed into this same folder
once this investigation's own findings land, at which point this file should be updated to place
them in whatever order the findings dictate — not assumed here.

## Precondition this epic depends on, filed elsewhere and not in this sequence

`TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` (`tickets/todos/`, P2) is a real
precondition for the `system` tier specifically — system membership derives from `depends_on`
edges, and ~64 of them predate the identity-rules ticket's own stated definition of what a real
edge is. It is not part of this sequence because it is independently useful (it corrects the
registry's own accuracy regardless of whether the tier model ships) and does not block the
feasibility investigation itself — the investigation's own Scope item 4 explicitly asks it to
*report* how much its findings depend on unaudited edges, not to run the audit. Whether the audit
becomes a hard precondition for the `system` tier's own implementation (child 2, not yet drafted)
is exactly one of the things this investigation is expected to answer.

## Known drift between this epic's own scoping and the initiative document

None recorded yet — this epic and its scoping document
(`docs/plans/mechanism_tier_model_initiative.md`) were authored together, unlike the
mechanism-verification epic's own relationship to `mechanism_claims_as_tests_initiative.md`. Record
any future drift here if it's found, per that epic's own precedent.
