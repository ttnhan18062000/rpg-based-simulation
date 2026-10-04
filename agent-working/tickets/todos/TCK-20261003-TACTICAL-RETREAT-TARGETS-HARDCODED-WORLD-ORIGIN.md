---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN
phase: open
date: 2026-10-03
tags: [combat, world, root-cause]
---

# TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN

## Title

Three tactical retreat/wander branches send an entity to hardcoded world coordinate `(0.0, 0.0)`,
parking it outside every region permanently

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P1

## Request Summary

`src/engine/tactical.py` has **three** branches that set an entity's navigation target to the literal
`(0.0, 0.0)` as a "safe origin":

| line | reason tag | mode |
|---|---|---|
| 141 / 144 | `PANIC_RETREAT` | `MovementMode.RETREAT` |
| 247 / 250 | `SAFETY_PRESSURE_RETREAT` | `MovementMode.RETREAT` |
| 483 | *(untagged)* | `MovementMode.WANDER` |

The comment at `:138` reads *"PANIC: Move to safe origin"*. World coordinate `(0,0)` is not a safe
origin — in the corpus worlds it is **outside every region**. `frontier_marches`' nine region bounds
all start at ≥ 10.

**Measured, not inferred.** Found while measuring
`TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION`. Instrumented runs at
`509009d41` (`audit_mode=True`, `max_tick_budget_ms=1e9`, `LocalSequentialExecutor`,
`dropped_work_total == 0`, repeat-stable byte-identical): with raiders spawned at a real city and
correctly targeting it, **10 of 12 entered `PANIC_RETREAT` within 15–38 ticks of spawn**, had their
target overwritten with `(0.0, 0.0)`, walked **past** the city to the world origin, and **idled there
for the rest of the run** with `region_id=None`. `PANIC_RETREAT` fired 62–591 times per raider.

This is the same literal as the retired raid's spawn anchor, on the **flight** path instead of the
spawn path — which is why re-anchoring that raid would not have made it work, and part of why it was
retired instead (see §2.64).

**Scope caution, stated up front:** the measurement observed this for `goblin_raider` entities only.
Whether other entity kinds reach these branches, and how often, is **not measured**. The branches
themselves are kind-agnostic, so the suspicion is general — but that is inference, and this ticket
must not be written up as if the general case were measured.

## Scope

- ~~Decide what "retreat to safety" should mean positionally, and record the decision.~~ **Settled
  2026-10-03 by `world-rule-catalog-design`, the rule owner — see "Rule-layer ruling" below. The
  derivation is no longer an open choice; implement the ruling.**
- Replace the two **retreat** `(0.0, 0.0)` literals (`:141`, `:247`) with the ruled derivation, and
  the **`:483` WANDER** literal with a separate seeded nearby region-contained location. Per the
  ruling these are two different semantics and must **not** share one derivation.
- A test asserting a retreating entity's target is inside some region, so an out-of-world retreat
  cannot be reintroduced.
- Measure how often each of the three branches fires, and for which entity kinds, before changing
  behaviour — the fix's blast radius depends on it.

## Out of Scope

- The retired world-clock raid. `TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION`
  owns that and is done; do not revive it here.
- Re-introducing world-clock raids. If wanted they return as a declared feature, and this ticket is a
  prerequisite rather than part of it.
- Whether `is_fleeing` / safety-pressure thresholds are tuned correctly. Balance, parked by
  `owner_decision_memo.md` row 7.
- The `(0,0)` literal in any other module.

## Acceptance Criteria

1. The firing rate of all three branches is measured per entity kind, with `audit_mode=True` and a
   raised `max_tick_budget_ms`, **before** any behaviour change. Without that the blast radius is
   unknown.
   **BLOCKED CAVEAT, added 2026-10-03:** that protocol may not be sufficient on this very path.
   `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` records a measured
   combat/tactical-path divergence (780 vs 1609 opportunity attacks) that **survives `audit_mode=True`
   and a raised budget**, unlike the `INFRA-273` throttle. If that is confirmed, a firing-rate count
   taken here is unreliable no matter how carefully it is configured. **Settle that ticket first, or
   establish a different instrument for this one.** Do not take a count on this path and treat it as
   solid until then.
   **CAVEAT DOWNGRADED, 2026-10-03 (rule owner's recommendation):** AC-1 no longer blocks the fix.
   AC-3's containment invariant needs **no corpus count** — a constructed scenario is deterministic
   and fails on today's code. Proceed on AC-3 plus a constructed-scenario instrument; keep corpus
   firing-rate counts as **"after" evidence, explicitly labelled order-of-magnitude** until
   `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` settles. Do not present
   any corpus count from this path as exact before then.
2. A decision is recorded for what a retreat target should be, with reasoning, not silently adopting
   the first plausible option. **SATISFIED 2026-10-03 — see "Rule-layer ruling" below.** The
   implementer cites MOV-01 / LOC-01 / LOC-03 / MOV-03 and owner decision 8; it does not re-derive
   the choice.
3. A retreating entity's target is inside some region. Asserted by a test that fails on today's code.
   **This is the AC the fix now proceeds on.** Assert non-empty before any loop over entities — a
   position test on this repo has already passed vacuously on a fixture that produced no entities.
4. No entity ends a run parked at `(0.0, 0.0)` with `region_id=None` in a corpus run.
5. Any behaviour change is recorded in `docs/guidelines/intentional_divergences.md` with a rationale
   class, and the relevant `docs/parity_ledger/` entry updated. **Rationale class is `Bug Fix`** per
   the ruling — current behaviour violates LOC-01/MOV-01, it does not merely lack a feature. (Note
   this differs from the retired raid, which was *not* a bug fix and was withdrawn.)
6. ~~The rule-layer question is put to `world-rule-catalog-design` before implementation: PLACE-01
   says a bare coordinate is not a Place, which likely constrains what a legitimate retreat
   destination is.~~ **DONE 2026-10-03, and this AC's own premise was wrong.** The ruling is below.
   **PLACE-01 is not the governing Rule** — it constrains *named destinations* ("go to X"), and a
   retreat is movement *away from* a threat. A retreat target therefore **need not be a Place**; it
   must be a valid, region-contained location.

## Rule-layer ruling (2026-10-03)

**Source:** `world-rule-catalog-design`, the owner of `docs/world_rules/`, checked at `origin/main`
`1a40d22d1`. Recorded here because AC-2 requires the decision to live in the ticket, not in a
session. Rule IDs and their meanings were independently verified against
`docs/world_rules/space-environment/` before being written here.

**Governing Rules — Batch 04 (space-environment), not PLACE-01:**

| Rule | What it says | Why it governs |
|---|---|---|
| `MOV-01` | Movement's constituent facts are distinct; **destination validity** is one of six separate checks | `(0,0)` fails destination validity in every corpus world |
| `LOC-01` | A subject's spatial state must be unambiguous under its declared spatial model; point states are legitimate | An entity at `(0,0)` with `region_id=None` is **outside** the declared model — wrong world truth, so under memo row 7 this is a **hard bug** |
| `LOC-03` | Containment is a real, authoritative relationship | A target's region containment must be real, not incidental |
| `MOV-03` | An attempt does not guarantee arrival | **Holding position is a legitimate outcome**, so "no valid target" has a correct answer |

**The ruling — what a retreat target should be, in order:**

1. **Default: away from the perceived threat, projected to stay inside the entity's current region.**
   Uses only the perceived hostiles the branch already holds plus the entity's own position, so it
   introduces **no new world-truth read** — owner decision 8 makes the running perception
   authoritative, and `TCK-20261003-APPRAISAL-READS-REPUTATION-WITHOUT-A-KNOWLEDGE-GATE` shows what
   ungated reads cost.
2. **Acceptable alternative: `strategic.home_region_id` when set** — the entity's own durable state,
   so legitimately known. (Mutate only via `StrategicUpdate(home_region_id_set=…)`; `displacement.py`
   is the existing precedent.)
3. **When no valid location exists** (cornered, or no away-vector stays in-region): **hold position or
   keep the current target**, per MOV-03. **Never a sentinel coordinate.**

**Explicitly rejected, with reasons — do not "improve" on the ruling by picking one of these:**

- **Nearest settlement Place** — fleeing raiders would converge *into* the city, the opposite of
  retreat, and a large behaviour change.
- **Nearest friendly-held region** — needs an ungated read of ownership, the same knowledge-gate
  class as the appraisal ticket; ownership is near-inert anyway.
- **`(0,0)` or any literal coordinate** — fails MOV-01.

**`:483` is a different semantic and answers this ticket's own open question.** It is `WANDER`, not
retreat. Its target should be a **seeded, nearby, region-contained location**; do **not** route it
through the retreat derivation. The same MOV-01 / LOC-01 constraint applies to it.

**If the default proves infeasible in implementation** — for example if region projection is
ill-defined at region borders — **bring it back to `world-rule-catalog-design` before choosing
anything else.** Do not substitute a rejected option. This instruction exists because a
world-semantics fix was implemented ahead of the rule owner once already on this exact family of
defect, and was withdrawn in full.

## Related Tickets

- `TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION` (done) — same literal on
  the spawn path; its measurement is what found this. Read its §2.64 divergence entry first.
- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` (done) — the first of this family, on the camp path.
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` (open, moved into decision-7
  foundation scope) — "proves a mechanism executes, not that it matters" is exactly the shape of this
  defect class.
- `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` (open) — **blocks AC-1 of this
  ticket.** Same code path; its divergence defeats the measurement protocol AC-1 prescribes.

## Related Docs

- `docs/mechanics/02_combat_laws.md` — tactical modifiers and retreat
- `docs/mechanics/06_worldbuilding_foundation.md` — region bounds
- `docs/world_rules/space-environment/movement-navigation.md` — **MOV-01, MOV-03, the governing Rules**
- `docs/world_rules/space-environment/location-topology.md` — **LOC-01, LOC-03, the governing Rules**
- `docs/world_rules/places-culture/places.md` — PLACE-01. Read only to see why it **does not** govern
  here: it constrains named destinations, not movement away from a threat.
- `docs/plans/systemic_world/owner_decision_memo.md` — decision 8 (running perception is
  authoritative), which is why the ruling's default reads no new world truth
- `docs/combat/combat_movement_overhaul_spec.md`

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20261003-GLOBAL-RAID-SPAWNS-AT-HARDCODED-ORIGIN-OUTSIDE-EVERY-REGION/`
  — its investigation records the trajectory measurement that found this.

## Related Code Areas

- `src/engine/tactical.py:137-146` — `PANIC_RETREAT`
- `src/engine/tactical.py:245-251` — `SAFETY_PRESSURE_RETREAT`
- `src/engine/tactical.py:483` — untagged `WANDER` branch

## Assumptions / Open Questions

- ~~Whether all three branches should share one "where is safety" helper, or whether panic, safety
  pressure and stalemate-break legitimately differ, is open.~~ **Answered by the ruling:** the two
  retreat branches share the retreat derivation; `:483` (stalemate-break `WANDER`) is a **different
  semantic** and must not. Whether the two *retreat* branches want one helper or two call sites of one
  derivation is an implementation detail, not a rule question.
- Whether any consumer depends on a retreating entity being at `(0,0)` is unverified.
- The untagged branch at `:483` emits no `reason`, so it is invisible to reason-based
  instrumentation. Two `crowded_frontier` raiders got a `(35,35)` target from some non-reason-tagged
  branch that was not identified; that may be this one or something else.

## Implementation Notes

_To be completed by the implementer._

## Test Summary

_To be completed by the implementer._

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._
