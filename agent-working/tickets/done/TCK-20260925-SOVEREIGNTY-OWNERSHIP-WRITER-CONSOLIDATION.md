---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION
phase: done
date: 2026-09-25
tags: [world, determinism]
---

# TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION

## Title

Two independent writers of `owner_faction_id` remain, with different triggers and phase positions —
consolidate onto one, or document why two are correct

## Status

DONE

## Tier

standard

## Type

refactor

## Priority

P2

## Request Summary

Region ownership is written by two independent code paths. As of
`TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` they **agree on the threshold and share
one pair of constants**, so the P1 consistency hazard is resolved. What remains is that two writers
exist at all, with materially different semantics — an architecture question that was deliberately
split out rather than resolved in passing.

**This ticket exists because the consolidation turned out to be a pipeline-ordering question, not a
code-move.** Three successive verification rounds on the parent ticket each found hidden structure in
what was originally scoped as deleting ten lines. Everything below was independently verified against
`src/` on 2026-09-24 — **do not re-derive it.**

| | `FactionInfluenceService.process_influence_shift` | `WorldDynamicsSystem.resolve_dynamics` |
|---|---|---|
| Trigger | One production caller, `src/systems/lifecycle_systems/lifecycle.py:272`, behind `if recent_deaths:` — only regions where a death occurred this tick | Unconditional sweep over every region in `state.regions`, against final settled influence, regardless of cause |
| Phase position | `lifecycle`, `src/engine/pipeline.py:414` | `world_dynamics`, `src/engine/pipeline.py:348` — **runs first** |
| Factions written | `MONSTER_HORDE` (conquest) or the `None`-sentinel (liberation) only — **no HERO_GUILD branch** | `HERO_GUILD` and `MONSTER_HORDE`, with `is_protector`/`is_invader` guards at `world_dynamics.py:82,86` preventing redundant re-flips |
| Emits `SOVEREIGNTY_SHIFT` | No | Yes, `world_dynamics.py:91-100`, reading `new_owner` — a local set only inside the ownership block |

**The hard part, and the reason this is not a mechanical move.** Consolidating onto a single
unconditional sweep at `world_dynamics`'s current phase position would make **death-driven ownership
flips land one tick later than they do today**, because death influence deltas are not written until
the later `lifecycle` phase. `process_influence_shift` currently flips ownership same-tick. Any
consolidation must decide this deliberately:

- Keep the sweep where it is and accept a one-tick delay for death-driven flips (a determinism and
  observable-behavior change requiring an `intentional_divergences.md` entry), **or**
- Move the settlement sweep to a phase position *after* `lifecycle`, so one unconditional pass sees
  every influence contribution including deaths — arguably the correct design, since ownership is a
  settlement step, but a genuine pipeline-ordering change that must be checked against the Sliding
  State ordering rule and the kernel/authoritative-pipeline contracts, **or**
- Conclude two writers are correct and document why, which is a legitimate outcome.

`tests/integration/world/test_regional_sovereignty.py::test_regional_ownership_flip` is load-bearing
evidence here: its second half injects a raw `WorldUpdate(influence_delta=10.0)` with **no death and
no `recent_deaths`**, runs the full `AuthoritativeApplyPipeline.refine()`, and asserts a `HERO_GUILD`
flip. That flip comes entirely from the unconditional sweep. Any design that only evaluates ownership
inside the death-gated path silently breaks this and narrows *when* ownership is re-checked, for both
conquest and liberation.

## Scope

- Decide whether ownership should have one writer or two, with the phase-ordering and same-tick
  consequences stated explicitly rather than discovered during implementation.
- If consolidating: choose and justify the phase position, preserve the `is_protector`/`is_invader`
  guards and the `SOVEREIGNTY_SHIFT` emission, and move the emission with whatever writes ownership.
- If not consolidating: document in `docs/world/regional_sovereignty_runtime_contract.md` why two
  writers are correct, what each is authoritative for, and how they are kept from diverging.
- Record any resulting determinism/timing change in `docs/guidelines/intentional_divergences.md`.
- Update the `WORLD-107` parity ledger entry in `docs/parity_ledger/world_dynamics.yaml`.

## Out of Scope

- The threshold value. Settled at **±50** by the parent ticket; not reopened here.
- The `owner_faction_id` overload holding `TERR-01`/`TERR-03` at `CONFLICTING` — separate defect.
- Balance tuning of conquest rates.

## Acceptance Criteria

1. A decision is recorded — one writer or two — with the phase-ordering consequence stated, not left
   implicit.
2. If consolidated: no ownership-transfer capability is lost relative to today, specifically
   influence-driven `HERO_GUILD` conquest and non-death influence sources.
3. `test_regional_ownership_flip` still passes, or its change is justified as an intended behavior
   change with an `intentional_divergences.md` entry.
4. A test asserts ownership is re-evaluated for a region with **no death** that tick, so the
   death-gating narrowing cannot be reintroduced silently.
5. Any same-tick/next-tick timing change is recorded with rationale class and verification path.
6. `WORLD-107` updated with `status` and `v2_evidence`.

## Related Tickets

- `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` — parent; fixed the threshold
  disagreement and shared the constants, deferring this. Read its `## Decision Revision` R4 for the
  full verified findings.
- `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS` — adjacent sovereignty-service
  work; check for overlap before scheduling.

## Related Docs

- `docs/mechanics/05_world_evolution.md` — authoritative ±50 ownership thresholds
- `docs/mechanics/regional_sovereignty.md`
- `docs/world/regional_sovereignty_runtime_contract.md`
- `docs/engine/kernel.md`, `docs/engine/authoritative_pipeline.md` — phase-ordering law
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-107`

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT/`

## Related Code Areas

- `src/world/influence.py:33,64-70` — `process_influence_shift`, no HERO_GUILD branch
- `src/engine/world_dynamics.py:79-100` — unconditional sweep, faction guards, `SOVEREIGNTY_SHIFT`
- `src/engine/pipeline.py:348,414` — `world_dynamics` before `lifecycle`
- `src/systems/lifecycle_systems/lifecycle.py:272` — the death-gated call site
- `tests/integration/world/test_regional_sovereignty.py::test_regional_ownership_flip`

## Assumptions / Open Questions

- Whether moving the settlement sweep after `lifecycle` is permissible under the Sliding State
  ordering rule is **unverified** — it is the first thing to check, and it may decide the whole ticket.
- Whether any consumer depends on `SOVEREIGNTY_SHIFT` arriving in the `world_dynamics` phase
  specifically is unverified.

## Implementation Notes

**Closed decision-only: outcome 3 of the three this ticket offered -- two writers stay, their
precedence is documented, consolidation is deferred.** No `src/` behaviour change. Owner-approved
2026-10-03.

The consolidation was ranked as hard-bug work on the reading that ownership is "one durable fact held
with two conflicting live values". **That premise measured false** and is retracted: 0 same-tick
overlaps in ~48,000 region-ticks, 0 ownership writes from the death-gated writer. The real shape is
last-writer-wins on one field via `WorldUpdate.merge`'s other-wins rule -- an undocumented precedence
between two producers, not a split-brain fact. With the premise gone, consolidation is a refactor on a
near-inert path, which `owner_decision_memo.md` row 7 parks.

Deferred on **yield, not permission**: the contract review found no obstruction to moving settlement
after `lifecycle` (investigation.md §3), so the option stays available whenever the foundation gate
opens. Option 2 is the one with no contract obstruction; the evidence is recorded so it need not be
re-derived.

Three corrections to this ticket's own body, all datable rather than arguable: its `P2 / refactor`
assessment predates `#276` (2026-10-01) which widened `recent_deaths` to DEFEAT/HAZARD/passive; the
call site is `lifecycle.py:298` behind the gate at `:294`, not the `272` cited; and the premise above.

## Test Summary

One new test, `test_ownership_reevaluated_for_region_with_no_death_that_tick` (AC-4 guard): an unowned
region flips via the unconditional sweep with a live bystander and **no death that tick**, asserted so
the fixture cannot silently acquire one. Guards against re-narrowing ownership evaluation to the
death-gated path.

Baseline measured before changing anything: 10 passed. After: 19 passed across
`test_regional_sovereignty.py`, `test_region_owner_sentinel.py`, `test_sovereignty_events.py` (WORLD-107's
P1 `test_path`) and `test_influence.py` (§2.58's threshold pins).

No determinism sweep claimed -- there is no behaviour change to perturb one. Anyone running one here
must set `audit_mode=True`; a single-threaded executor is **not** a substitute, which was measured.

Two pre-existing failures reported, not masked, both proven independent: see `test_plan.md`.

## Files Changed

- `docs/world/regional_sovereignty_runtime_contract.md` -- precedence, last-tick influence, the
  non-emitting writer, measured inertness; stale call-site anchor corrected
- `docs/parity_ledger/world_dynamics.yaml` -- `WORLD-107` `v2_evidence` (11 insertions; `status` stays
  `verified`, justified in the entry)
- `tests/integration/world/test_regional_sovereignty.py` -- AC-4 guard test
- `agent-working/staging_artifacts/TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION/` --
  `investigation.md`, `plan.md`, `test_plan.md`, `runtime_evidence_regional_sovereignty.md`

**No `src/` file changed by this ticket.**

## Completion Summary

Closed 2026-10-03, decision-only. All 6 acceptance criteria discharged; the map is in `plan.md`.

AC-5 is discharged by recording that **no timing change exists**, so no `intentional_divergences.md`
entry was written -- stated explicitly so the absence reads as a decision rather than an omission.
AC-6 updated `v2_evidence` only, with `status: verified` retained and justified: the entry's text makes
no phase-position claim and its P1 `test_path` passes.

Two findings this ticket surfaced but did not fix, both recorded rather than carried silently:

1. **A real crash** -- the `-1` unowned sentinel persisted raw, reproduced as `KeyError: -1` in the
   authoritative pipeline. Split out and **fixed** as
   `TCK-20261003-REGION-OWNER-NONE-SENTINEL-PERSISTED-RAW`, landed with work-order item 1 because item
   1 un-inerts the influence that keeps it dormant.
2. **Ownership dynamics are near-inert** -- most regions sit at influence exactly `0.0` for 2000 ticks;
   3 ownership writes in 14,000 ticks. Arguably the most consequential observation here, and squarely
   balance work that row 7 parks. Deliberately not filed as a defect.

Honest limit on the evidence: the runs predate the `audit_mode` discipline `INFRA-273` requires, so the
counts are order-of-magnitude and the zeros rest on a structural argument plus a constructed scenario
rather than on the counts alone. A confirm-or-refute probe established the nondeterminism as the
already-known, deliberately-deferred wall-clock mechanism -- confirmed, and deliberately **not** filed
as a new defect.
