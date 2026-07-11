---
status: draft
layer: simulation
authority: P1
audience: agent
artifact_type: plan
tags: [epic-scoping, simulation_quality, world-content, feature-flags]
---

# Plan — TCK-20260704-SIMQ-CORPUS-TIERS-EPIC

Per CLAUDE.md's Tier Routing table, an `epic`-tier ticket is **scope-only** — it tracks child
tickets and has no direct implementation of its own. This file exists to satisfy the "standard/epic
only" required-artifacts rule honestly, not to duplicate planning that belongs to the child
tickets.

## What this epic's "plan" actually is

The plan is the sequencing and dependency structure already recorded in
`tickets/todos/simq-corpus-tiers/SEQUENCE.md`, derived directly from `investigation.md`'s findings
and the three user decisions (AGENCY: new dedicated worlds, not a DA reversal; Branch B: one
isolated pilot world; content authoring: hybrid by tier). That file is the authoritative ordering
document — this plan.md does not restate it, to avoid the two documents drifting apart.

## What happens next

Each of the 10 child tickets (`TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` through
`TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL`) goes through its own full Scope → Investigate →
Plan → Review → Implement → Test → Parity → Verify → Finalize pipeline when picked up, with its own
`staging_artifacts/{child_ticket_id}/plan.md`. This epic ticket's own "Verify"/"Finalize" step (when
all 10 children reach `tickets/done/`) is limited to confirming all children closed consistent with
the 3 binding decisions above — it does not re-review each child's individual implementation, which
already went through its own review.

## Architecture constraints this epic imposes on every child ticket

- No child ticket may reverse `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for any of the 9 existing
  non-routing worlds.
- No child ticket may combine Branch B (`ENABLE_SELF_MODEL_COGNITION`) with
  `ENABLE_BELIEF_ASSIMILATION` or `ENABLE_ADVENTURE_ROUTING` in the same world without a fresh,
  explicit scope decision — the unit-tier pilot (ticket 5) is deliberately single-mechanic.
- The regression/baseline tier (today's already-calibration-anchored worlds not named in tickets 7
  or 8) is a "do not touch" policy, not a default any child ticket may quietly relax.
