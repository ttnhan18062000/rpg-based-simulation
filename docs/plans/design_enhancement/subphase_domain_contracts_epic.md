---
status: active
layer: engine
authority: P1
audience: agent
tags: [engine, architecture, performance, testing]
---

# Epic Plan — Per-Sub-Phase Domain/Dependency Contracts for the Refinement Phases

**Tracking ticket:** `TCK-20260825-EPIC-SUBPHASE-DOMAIN-CONTRACTS` (not yet created — this epic is
scope-only, per `docs/plans/design_enhancement/design_enhancement_roadmap.md` Section F)
**Source:** `tmp/external_ai_suggest_design.md` (not committed) §3, verified directly against
`src/engine/phase_domain_permissions.py`, `docs/engine/authoritative_pipeline.md`
**Priority:** P1. Counted unit (PERF-D6): a *refinement phase* is one `run_phase()` call in
`AuthoritativeApplyPipeline.refine` (written "sub-phase" below, as in the original plan); a *kernel
phase* is a `TickPhase` member. This document states no refinement-phase count; the generated list
is `docs/performance/phase_inventory.md`.

**Status of the purpose (C-14, PERF-D6, 2026-10-03).** The declarations are justified on their own
terms: phase **identity** (one typed, ordered entry per phase), **drift detection** (a test fails when
the declared graph and the code diverge), and **instrumentation** (per-phase cost and domain
reporting). They are not a presumed step toward concurrency. The earlier path from this epic into
`docs/plans/design_enhancement/performance_milestones_epic.md` M3 is replaced: concurrent
Resolution is a **Gate B, separate-architecture proposal**, and Resolution stays serial until one is
approved. A Gate B proposal would have to use these declarations as evidence of independence, but
completing this epic does not start it. The declaration format is shared with the data-oriented
core proposal's scheduling layer (`data_oriented_core_proposal_scope.md`) so that there is one
format, not two (PERF-D6 point 6). The phase catalog itself is the typed structure in
`src/engine/phase_graph.py` (PERF-D6, implementation pending `PERF-M3-T01`/`T02`).

## Problem

`src/engine/phase_domain_permissions.py` declares read/write/emit state domains only at the 7
*kernel*-phase granularity (`TickPhase.RESOLUTION` as one undivided block, reading
`{proposals, policy, entity}` and writing `{entity, world, policy, infra}`) — confirmed by reading
the file directly. There is no equivalent declaration for any of the named sub-phases *inside*
Resolution (`trust_boundary`, `actor_validity`, `combat_engagement`, `resource_transactions`, etc.
— the generated list in `docs/performance/phase_inventory.md`): no accepted-intent-type, read/write
domain, ordering-key, or "may this emit follow-up work, this tick or next" contract per sub-phase,
and nothing in `tests/architecture/` checks whether two sub-phases assumed to be independent
secretly touch the same state domain.

This is the same kind of gap the existing 7-phase-level declarations already closed once
(`RPG-INFRA-155/156/157`) — one level finer-grained, where that precedent doesn't yet reach. Left
unaddressed, it's not just a documentation gap: any future attempt to reorder sub-phases, or a Gate B
proposal to run any of them concurrently (see the Performance epic's M3), has no mechanical way to
prove the independence it would be relying on.

## Scope for the eventual `create-tickets` pass

Not created yet — this epic is scope-only.

1. **Declare per-sub-phase domains.** For each sub-phase, a structured declaration:
   accepted intent types, state domains read, state domains written, invariants required on entry
   and established on exit, whether it may emit follow-up work and for this tick or next, and its
   existing deterministic ordering key (already fixed by pipeline order — this makes it explicit
   and checkable, not a behavior change). Modeled directly on
   `PHASE_READ_DOMAINS`/`PHASE_WRITE_DOMAINS`/`PHASE_EMIT_DOMAINS` in
   `src/engine/phase_domain_permissions.py`, one level down.
2. **Build the dependency graph from the declarations**, and a CI test
   (`tests/architecture/`, alongside the existing `test_phase_domain_permissions.py`) that fails if
   two sub-phases declared independent write the same domain, or if the declared graph no longer
   produces the pipeline's actual canonical order.
3. **Keep execution single-threaded and in the existing fixed order** — this epic is a declarative
   safety net, not a parallelization change. The graph has value even unused for scheduling: it
   catches undeclared coupling and accidental ordering changes as soon as they're introduced,
   which is the evidence any Gate B concurrency proposal would need, whatever its own decision.
4. **Decide enforcement strength** — the existing 7-phase-level file's own comment says its
   declarations are "declarative only, no runtime enforcement," checked by test rather than
   mechanically. Decide whether the sub-phase version should match that (test-guarded) or go
   further (a runtime guard that raises if a sub-phase touches an undeclared domain, mirroring how
   `ContentHotPathViolation` enforces the content hot-path rule mechanically rather than by
   convention).

## Out of Scope

- Actually parallelizing any sub-phase — that's
  `docs/plans/design_enhancement/performance_milestones_epic.md` M3, a Gate B separate-architecture
  proposal, not part of this epic and not started by it.
- Changing the current fixed sub-phase order — this epic documents and enforces the existing order,
  it doesn't revisit it.

## Acceptance Signal

Every sub-phase has a domain declaration, a CI test fails on a deliberately-introduced
undeclared-domain-collision fixture and passes on the current real pipeline, and
`docs/engine/authoritative_pipeline.md` cross-links the new declarations the same way `kernel.md`
already links `phase_domain_permissions.py`.
