---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION
phase: open
date: 2026-09-11
tags: [observability, architecture]
---

# TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION

## Title
10 of `ObservabilityConfig`'s 17 feature-flag convenience methods are unused, and their own
underlying flags are never read anywhere else either — determine whether the subsystems they
name run ungated, never run, or have a real missing-gate bug

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (`docs/audits/
unreachable_code_inventory.md`, Cluster C2). `src/observability/config.py`'s `ObservabilityConfig`
declares 17 `is_X_enabled()`-shaped classmethods, each a thin wrapper
(`return cls.get_flag("OBS_X")`) around a named observability feature flag. 10 have zero real call
sites anywhere: `is_event_recorder_enabled`, `is_entity_timeline_enabled`,
`is_behavior_timeline_enabled`, `is_behavior_episodes_enabled`, `is_behavior_metrics_enabled`,
`is_behavior_patterns_enabled`, `is_behavior_scorecards_enabled`, `is_cohort_analysis_enabled`,
`is_run_comparison_enabled`, `is_insight_generation_enabled`, `is_warehouse_ingest_enabled`. 3
genuinely-similar siblings (`is_live_stream_enabled`, `is_behavior_normalization_enabled`,
`is_dashboard_export_enabled`) ARE real, live-called methods — ruling out "this whole cluster is a
naming artifact of the audit tool."

**Checked further, not assumed**: the underlying flag strings themselves (`OBS_EVENT_RECORDER`,
`OBS_ENTITY_TIMELINE`, `OBS_COHORT_ANALYSIS`, `OBS_WAREHOUSE_INGEST`, spot-checked) are not read
directly anywhere else in the codebase either. This rules out "the convenience method is unused but
some other code checks the same flag directly instead" — the underlying gate itself is never
consulted by anything, not just this one method.

This leaves three real possibilities, genuinely undetermined:
1. The observability subsystems these flags name (entity timeline, cohort analysis, warehouse
   ingest, behavior episodes/metrics/patterns/scorecards, run comparison, insight generation, the
   event recorder itself) run **unconditionally** — the flag is dead scaffolding for a future
   kill-switch that was never wired to the actual conditional, but the subsystem itself works fine
   without it.
2. The subsystems **never run at all** for some other reason (a separate wiring gap), making the
   missing gate moot either way.
3. There is a **real, missing gate check** — the subsystem should be conditionally running based on
   this flag and currently always runs (or never runs) regardless of what the flag is set to,
   which is a real correctness/resource-control bug, not dead code.

## Scope
- For each of the 10 unused flag names, identify the real subsystem it's meant to gate (the naming
  is suggestive — `OBS_ENTITY_TIMELINE` almost certainly gates `src/observability/live/` or
  similar entity-timeline machinery, `OBS_WAREHOUSE_INGEST` the warehouse ingestion pipeline, etc.
  — confirm each mapping directly, don't assume from the name alone).
- For each subsystem: determine whether it currently runs unconditionally, never runs, or should
  be conditionally gated and isn't. This determines which of the 3 possibilities above applies —
  do this per-flag, not as a single blanket answer, since different flags may land in different
  buckets.
- Decide the disposition per flag once its bucket is known: wire the gate check in (if the
  subsystem should genuinely be conditional and currently isn't), delete the unused convenience
  method (if the subsystem doesn't need gating at all and the method is pure vestigial scaffolding),
  or document (if there's a real reason the gate is deliberately not wired yet, e.g. the feature
  itself is still incomplete).

## Out of Scope
- The 3 confirmed-live sibling methods (`is_live_stream_enabled`, `is_behavior_normalization_enabled`,
  `is_dashboard_export_enabled`) — already working, not re-litigated here.
- Any other cluster from the same audit — each has, or will have, its own ticket.
- Full implementation of whatever wiring decision is made per flag — this ticket is the
  determination and, for clear-cut cases, the fix; a flag whose fix isn't trivial should route the
  decision through peer review before implementing, matching this whole follow-up arc's own
  precedent for design-level findings.

## Acceptance Criteria
- [ ] Each of the 10 unused flags is mapped to its real intended subsystem, confirmed directly
      (not assumed from the flag's own name).
- [ ] Each flag's real bucket (unconditional-and-fine / never-runs-anyway / genuinely-missing-gate)
      is determined with evidence, not guessed.
- [ ] A disposition (wire / delete / document) is recorded per flag, with rationale.
- [ ] Any flag determined to be a real missing-gate bug has its fix-approach decision routed
      through peer review before implementation if the fix isn't trivial.

## Related Tickets
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (origin — Cluster C2)

## Related Docs
- `docs/audits/unreachable_code_inventory.md` (Cluster C2's own writeup)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/observability/config.py` (`ObservabilityConfig`, all 17 `is_X_enabled` methods and their
  underlying `OBS_*` flag strings)
- Whatever subsystem each flag maps to (identify during Investigate)

## Assumptions / Open Questions
- Which of the 3 possible buckets each flag falls into is the central, deliberately-unresolved
  question this ticket exists to answer — not assumed uniformly across all 10.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
