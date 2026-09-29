---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK
phase: open
date: 2026-09-28
tags: [engine, lifecycle, combat]
---

# TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK

## Title
Do same-tick combat and hazard deaths on one entity resolve under a declared rule, and is the death
processed exactly once?

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
**A check, not a fix.** The invariant under test: same-tick deaths from combat and hazard damage
resolve under a **declared** rule. Precedence is currently asserted in code comments
(`src/systems/world_systems/groups.py:99`, `src/engine/pipeline_phases/clan_lifecycle.py:19`);
whether it actually holds is `UNKNOWN_WITH_REASON` — there is a plausible ordering, but no scenario
exercises the collision.

Implements Card C1 of `docs/plans/systemic_world/ticket_planner_handoff.md` (branch
`systemic-world-roadmap-proposal` @ `43db4a7fc`, PR #249, unmerged).

## Scope
- Determine whether a same-tick combat + hazard kill on one entity is **reachable in production**,
  or only in a harness.
- Determine the committed state and the recorded cause, and whether the death is processed
  **exactly once**.
- Determine whether the commented precedence actually holds.
- Close with exactly one exit state: `CONFIRMED_FINE_WITHIN_SCOPE`, `DEFECT_CONFIRMED` (routed
  separately, not fixed here), or `BLOCKED_WITH_REASON`.
- Record the outcome as a **dated addendum in roadmap §3.1**.

## Out of Scope
- **Fixing anything.** A confirmed defect is routed as separate work. This ticket produces a verdict.
- `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`. Out of scope, and **its verified
  comparison of the two ownership writers must not be re-derived** — it already carries one.
- Natural-aging death. That is a separate, in-flight ticket (see Related Tickets). This ticket is
  about the **combat/hazard** same-tick collision.

## Acceptance Criteria
1. Exactly one exit state is recorded: `CONFIRMED_FINE_WITHIN_SCOPE`, `DEFECT_CONFIRMED`, or
   `BLOCKED_WITH_REASON`.
2. **A harness limitation is never reported as "fine".** If the collision can only be produced in a
   harness, that is `BLOCKED_WITH_REASON` or a scoped `CONFIRMED_FINE_WITHIN_SCOPE` whose scope
   names the limitation explicitly — never an unqualified pass.
3. Production reachability of the same-tick collision is answered explicitly, separately from
   whether the precedence holds.
4. Whether the death is processed exactly once is answered with evidence, not inferred from the
   comments.
5. The outcome is recorded as a dated addendum in roadmap §3.1.
6. **If any fix this ticket routes would touch the ordering between world dynamics and lifecycle,
   that is escalated to the planner before it is written** — it must then be sequenced with
   `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`, which is determinism-sensitive (a
   naive consolidation delays death-driven ownership changes by one tick).
7. **If any change alters who decides alive/dead, `make semantic-control-plane-drift-check` is run
   afterwards** and its output reported. SCP rows `LIFE-01`/`LIFE-02` cite `combat_resolution`; the
   check is report-only (exit 0 always), so a clean run must be shown, not assumed.
8. Findings are routed back to the systemic-world roadmap track (`world-rule-catalog-design`).

## Related Tickets
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — **merged 2026-09-29 as `5d4e4a237`
  (PR #254); no longer in flight.** Same field (`entity.lifecycle.active`), different writers and
  different cause. Its landed fix makes `resolve_lifecycle` sole authority for **old-age**
  deactivation via `src/engine/apply.py:109`. This check must still name the engine commit it
  observed, but the coordination risk is now closed — observe at or after `5d4e4a237`.
- `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` — held; sequencing constraint, see AC6.

## Placement Note
**Deliberately filed at `tickets/todos/` top level, not in the
`tickets/todos/systemic-world-first-wave/` folder**, by owner decision 2026-09-29. It remains Card C1
of the systemic-world first wave and its scope is unchanged — only its dispatch grouping differs, so
that `/implement-epic` over the wave folder does not pull it in alongside J and B0.

Reason: this ticket touches the entity-death authority boundary, which is the same field PR #254 just
changed and the same subject as the held, determinism-sensitive
`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`. It carries a real sequencing dependency
that J and B0 do not. `tools/open_ticket_overlap.py` independently ranks the sovereignty ticket as
this ticket's #3 overlap (score 30.9). Dispatch it on its own, after the sovereignty ticket's hold is
resolved — see AC6, which already requires escalation before any fix touching world-dynamics /
lifecycle ordering is written.
- `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP` — split out of the natural-aging ticket;
  `resolve_lifecycle` has no HP/alive-based death branch at all, and only `OLD_AGE`/`COMBAT` exist as
  `death_reason` literals repo-wide. **Directly relevant**: a hazard death may have no death-reason
  path to be recorded under in the first place.
- `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING`,
  `TCK-20260928-COMBAT-DEATH-TRACE-SITUATED-ENCOUNTERABILITY` — parallel wave items, independent.

## Related Docs
- `docs/plans/systemic_world/ticket_planner_handoff.md` — Card C1 (@ `43db4a7fc`).
- `docs/plans/systemic_world/roadmap.md` §3.1 — the audit table this outcome is appended to.
- `docs/engine/authoritative_mutation_pipeline_contract.md` — mutation rules and apply-path law.
- `docs/engine/kernel.md` — the 7-phase deterministic loop.

## Related Stored Artifacts
- `docs/plans/systemic_world/evidence/2026-09-27-authority-boundary-audit-findings.md`, boundary 2
  (on the unmerged branch above).

## Related Code Areas
- `src/systems/world_systems/groups.py:99` — precedence comment.
- `src/engine/pipeline_phases/clan_lifecycle.py:19` — precedence comment.
- `src/engine/pipeline.py:255-283` — same-phase concatenation before one merge.
- `src/systems/lifecycle_systems/lifecycle.py` — `resolve_lifecycle`, including the
  already-inactive skip guard at `:147-148` and the `death_reason` literals.

## Assumptions / Open Questions
- **Q1.** Is a same-tick combat + hazard kill on one entity reachable in production, or only in a
  harness?
- **Q2.** What is the committed state and the recorded cause, and is the death processed exactly
  once?
- **Q3.** Does the commented precedence actually hold?
- **Q4, surfaced while planning and not in Card C1.** Given that `resolve_lifecycle` has no
  HP/alive-based death branch and only `OLD_AGE`/`COMBAT` exist as `death_reason` literals, is a
  "hazard death" even representable today? If hazard damage can only kill via the passive HP path,
  the same-tick collision this ticket tests for may be unreachable *for that reason* rather than for
  an ordering reason — a materially different finding, and one that should be reported as such
  rather than folded into `CONFIRMED_FINE_WITHIN_SCOPE`.
- **Background, non-binding.** An incomplete scenario draft from a stopped exploratory agent sits on
  the local branch `natural-aging-old-age-dispatch-fix-unreviewed`. **It is not evidence.**

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
