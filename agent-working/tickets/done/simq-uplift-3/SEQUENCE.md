# SimQ Uplift Batch 3 — Implementation Sequence

Follow-on work identified while closing out SimQ Uplift Batch 2
(`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`, `-FACTION`, `-INFORMATION`,
`TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`). Scoped 2026-07-03 per user direction
after reviewing the updated `docs/audits/D20_simq_integration.md`.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260703-SIMQ-UPLIFT3-FAST-CALIBRATE | Tiny, well-understood fix (reuse the `no_frame_pacing` pattern already proven in `TCK-20260628-E-LONGRUN-REGRESSION`) that unblocks fast iteration on everything below it — do first |
| 2 | TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC | Doc-only, no dependencies, captures a lesson from Batch 2 before it's forgotten; informs how tickets 3-4 below should be scoped |
| 3 | TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT | Investigation-only; findings may inform whether ticket 4 (world corpus) needs to also seed ECONOMY/SOCIAL content in new worlds |
| 4 | TCK-20260703-SIMQ-UPLIFT3-BRANCH-B | Independent of the others; real cognition-contract bug fix, touches shared `SelfModelUpdatePhase` |
| 5 | TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS | Benefits from ticket 1 (fast calibration) being done first so the larger corpus this ticket adds doesn't take hours to validate |
| 6 | TCK-20260703-SIMQ-UPLIFT3-AUDIT-WORKFLOW | Formalizes the process used across Batches 1-3; benefits from the expanded corpus in ticket 5 existing so the workflow has something real to audit |
| 7 | TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE | Independent, larger scope (`audit_fix_plan.md` P1-D) |
| 8 | TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE | Independent, smaller scope (`audit_fix_plan.md` P1-H) |

## Dependency Notes
- Tickets 1-2 have no dependencies and can run in any order relative to each other.
- Ticket 3 (dual-gate audit) is investigation-only — no code changes — so it can run in parallel
  with ticket 4, but its findings should be read before finalizing ticket 5's world-corpus scope,
  in case ECONOMY/SOCIAL also need compile-time seeding fixes in the new worlds ticket 5 adds.
- Ticket 6 (audit workflow) is easiest to design well once ticket 5's expanded corpus exists —
  building a repeatable-audit process against a thin corpus risks under-specifying it.
- Tickets 7-8 are unrelated to the SimQ pillar-activation work above (they're
  `docs/plans/audit_fix_plan.md` P1-D/P1-H items in the same cognition/strategy neighborhood) and
  can be picked up independently, any time.
- AGENCY's `ENABLE_ADVENTURE_ROUTING` global-rollout question was raised during scoping and
  explicitly deferred — no ticket created; current DA decision (opt-in per archetype) stands.
