---
status: draft
layer: simulation
authority: P1
audience: agent
artifact_type: test_plan
tags: [epic-scoping, simulation-quality, world-content, feature-flags]
---

# Test Plan — TCK-20260704-SIMQ-CORPUS-TIERS-EPIC

Per CLAUDE.md's Tier Routing table, this is an `epic`-tier ticket — it has no direct implementation
and therefore no tests of its own to write or run. This file exists to satisfy the "standard/epic
only" required-artifacts rule honestly, not to fabricate epic-level test coverage that doesn't
exist.

## Where real testing happens

Each of the 10 child tickets owns its own test plan, scoped to its own change:
- Tickets 1-2 (taxonomy doc, scale metric): doc/instrumentation-only, minimal or no new tests.
- Tickets 3, 6 (AGENCY flag generalization, AGENCY unit-tier world): must not regress the existing
  `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` ruling — each child ticket's own test plan must include a
  regression check confirming the 9 existing non-routing worlds' AGENCY grade is unchanged.
- Tickets 4-5, 8 (unit-tier and stress-tier world authoring): each requires the same
  population-stability (>=60% alive floor) and grade-anchor verification discipline established by
  `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`.
- Ticket 7 (end-to-end content expansion): requires the Step-4a-style existing-anchor drift check
  (re-verify, don't assume `make evaluate`'s dry-run diff catches genuine content changes) — this
  ticket touches 8 existing worlds' calibration anchors and carries the highest regression risk in
  this epic.
- Ticket 10 (scenario flag guardrail): is itself a test-authoring ticket — its own "test plan" is to
  build a test matrix covering every world/flag combination tickets 3-9 introduce.

## Epic-level verification (only meaningful check at this tier)

When all 10 children reach `tickets/done/`, confirm:
1. `make evaluate --dry-run` and the fast-tier regression suite (`pytest -m "not slow"`) both pass
   against the full expanded corpus.
2. No existing non-routing world's AGENCY grade changed from C.
3. The regression/baseline-tier worlds named nowhere in tickets 7-8 have zero diff in their
   `resolved/` output (confirming the "do not touch" policy was actually honored, not just stated).
