---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION
phase: open
date: 2026-09-25
tags: [world, determinism]
---

# TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION

## Title

Two independent writers of `owner_faction_id` remain, with different triggers and phase positions —
consolidate onto one, or document why two are correct

## Status

OPEN

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

- `stored_artifacts/TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT/`

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

_To be completed by the implementer._

## Test Summary

_To be completed by the implementer._

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._
