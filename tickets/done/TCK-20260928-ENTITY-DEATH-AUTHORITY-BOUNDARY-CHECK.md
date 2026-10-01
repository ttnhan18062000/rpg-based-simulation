---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK
phase: done
date: 2026-09-28
tags: [engine, lifecycle, combat]
---

# TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK

## Title
Do same-tick combat and hazard deaths on one entity resolve under a declared rule, and is the death
processed exactly once?

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
**RESOLVED 2026-10-01 — `DEFECT_CONFIRMED`. The premise stated below was disproved by this check:
there is no declared rule to resolve under, and the two cited comments are a same-tick
read-freshness rule, not a precedence rule. `resolve_lifecycle` has no HP/alive death branch, so a
hazard drain coinciding with a combat kill erases the death record rather than resolving it under
any precedence. See Implementation Notes for the verdict and the request text below for the
original framing, kept as the historical record of what was asked.**

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

**Exit state: `DEFECT_CONFIRMED`** (AC1). Observed at engine commit `e9db40f0a`, i.e. at/after
`5d4e4a237` (PR #254) as this ticket requires. No fix written — ticket's own Out of Scope.

**The defect is not the one this card hypothesised.** C1 asked whether same-tick combat and hazard
deaths resolve under a declared rule. There is no rule to resolve *under*: `resolve_lifecycle`
recognises only `KILL`/`PERMADEATH` → `COMBAT` and `age >= max_age` → `OLD_AGE`
(`src/systems/lifecycle_systems/lifecycle.py:189-218`). It has **no HP/alive-based death branch**,
and no third `death_reason` literal exists in `src/`. So the collision does not resolve wrongly —
it destroys the combat death record outright.

- **Q3's premise does not hold.** The comments at `src/systems/world_systems/groups.py:99` and
  `src/engine/pipeline_phases/clan_lifecycle.py:19` are **not** a combat-vs-hazard precedence
  rule; both assert a same-tick *read-freshness* rule for downstream consumers. This check
  supersedes the Request Summary's reading. Those consumers use `is_alive()`/`is_active()` and so
  **do** treat an `alive_set=False` entity as dead while `resolve_lifecycle` does not — which is
  how the inconsistency becomes observable.
- **Mechanism.** `world_dynamics.py:39` does `replace(c_upd, ..., outcome_kind="HAZARD", ...)` —
  an unconditional overwrite — and runs at `pipeline.py:348`, between the phase writing `KILL`
  (:297/:320) and the phase reading it (:414), inside one accumulating update. Its loop guard
  (`world_dynamics.py:31`) reads committed state, where a victim killed earlier this tick is still
  alive, so the victim is always eligible. The `KILL` sits on the **victim's** own `EntityUpdate`
  (`combat.py:495`/`:553`) — exactly the key `resolve_lifecycle` reads.
- **Q2.** The death is processed **exactly once, but as a non-death**: `death_reason`,
  `death_tick` and `is_permadeath` are never set, so the succession/heirloom/lineage dispatch
  inside `if is_dead:` never runs. Deactivation still lands, one tick late, via `apply.py:109`'s
  passive HP gate. Regional trauma is booked identically to the control arm.
- **Q1, answered in two parts (AC3).** Zero `KILL`/`PERMADEATH` in 120 unscripted ticks of
  `frontier_marches` (kinds seen: `SURVIVE` 84, `REJECTED` 34, `DEFEAT` 4, `REBIRTH` 1); hazard
  drain > 0 on 0.3% of eligible entity-ticks. The joint event was **not observed** — which is
  **not** evidence of unreachability, just the expected result of sampling a conjunction of two
  rare events. Nothing in the code prevents it.
- **But the end-state is routine in production.** The committed signature `combat.alive=False` +
  `lifecycle.active=True` + `death_reason=None` occurs on 8 separate ticks in that unmodified run,
  via **three** routes that need no combat kill: hazard-only drain deaths, `DEFEAT` (because
  `combat.py:136` forces `is_lethal=False` for `EntityRole.HERO` defenders), and `REBIRTH`.

**AC2 honoured:** nothing is reported as "fine". The scripted-arm caveat is stated in both
`investigation.md` and the test module docstring, and the unscripted corpus evidence is kept
separate from it.

**AC6/AC7 not triggered by this ticket** — no fix is written and nothing here alters who decides
alive/dead. Both bind the follow-up ticket instead; `make semantic-control-plane-drift-check` is
not run here because recording a clean run would be recording a check of nothing.

**Four instrument errors were found and corrected before any conclusion was drawn** (faction
immunity masking the hazard, `trauma_level` vs `trauma_score`, a two-variable differential, and a
`round(..., 3)` artifact). A positive control confirmed the reachability probe can see kills at
all. Details in `investigation.md` § Instrument honesty.

## Test Summary

- `tests/mechanic_scenarios/test_entity_death_authority_boundary.py` (new, 3 tests) plus B0's
  `test_combat_death_trace_encounterability.py` as an independent control: **5 passed**.
- Scoped domain re-run, `tests/unit/progression/test_lifecycle.py` +
  `tests/unit/engine/test_apply.py` (`-m "not slow"`): **46 passed**.
- The new tests assert the **current, defective** behaviour on purpose; when the routed fix lands
  they are expected to fail and must be rewritten to the fixed contract, not deleted. Stated in
  the module docstring.
- Known limitation, recorded not hidden: the corpus test is `@pytest.mark.slow`, which
  `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` establishes is excluded from the gating
  CI lane. It is `@slow` because it genuinely is; promoting it out of the marker to dodge that is
  the wrong fix.

## Files Changed

- `tests/mechanic_scenarios/test_entity_death_authority_boundary.py` (new)
- `tickets/inprogress/` → `tickets/done/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK.md`
- `stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/{plan,investigation,test_plan}.md`

No `src/` file was modified.

## Completion Summary

Card C1 answered with one exit state, `DEFECT_CONFIRMED`, and all four questions answered
separately with evidence rather than inference. The headline is that the card's own framing was
wrong in a way that matters: this is not an ordering/precedence defect but a **missing
HP/alive-based death branch**, so every non-`KILL` route to `combat.alive=False` yields an entity
dead to combat, groups, clans and regional trauma, and alive to lifecycle, with no cause recorded.

Routed as two separate pieces of follow-up work, deliberately not merged:

1. The missing HP/alive death branch → **`TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`**
   (already open; this check supplies the production evidence it lacked).
2. The unconditional `outcome_kind` overwrite at `src/engine/world_dynamics.py:39` → **no open
   ticket covers this; a new one is needed.** A fix there touches world-dynamics/lifecycle
   ordering, so it inherits this ticket's AC6 escalation and must be sequenced against
   `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`, which is determinism-sensitive.

Findings routed back to the systemic-world roadmap track (AC8) for the dated §3.1 addendum (AC5),
which `world-rule-catalog-design` owns.
