---
status: active
layer: performance
authority: P1
audience: agent
tags: [performance, engine, determinism, testing, observability]
---

# Epic Plan — Performance Evolution, Sequenced by Risk

**Tracking ticket:** `TCK-20260825-EPIC-PERFORMANCE-EVOLUTION` (not yet created — this epic is
scope-only, per `docs/plans/design_enhancement/design_enhancement_roadmap.md` Section A)
**Source:** `docs/brainstorm/performance_evolution_roadmap.html` (22 ideas checked against the
actual code, 8 already built), cross-checked against
`docs/plans/design_enhancement/design_enhancement_roadmap.md` Section A's revised priority table
**Priority:** P1 — the roadmap's primary work stream, but gated: `design_enhancement_roadmap.md`
Priority 0 (benchmark instrument fix) must land first, and this epic's M3 is gated on
`docs/plans/design_enhancement/subphase_domain_contracts_epic.md`.

## Problem

`docs/brainstorm/performance_evolution_roadmap.html` checked a 20-idea external performance
proposal against the actual code and found 8 of the 20 already built (dirty-set/affected-set
processing, deterministic multi-rate scheduling, simulation LOD, demand-driven gating, and
type-batched Resolution among them) — those are explicitly **not** work items here. What's left is
8 real, distinct moves, ranging from zero-risk measurement to an intentional fidelity cut for
distant regions. They don't all belong in one ticket: their risk profiles (to both determinism and
emergent-behavior quality — see `design_enhancement_roadmap.md` Section A's two-column table) are
different enough that bundling them would force the riskiest item's review bar onto the safest one.

## Scope for the eventual `create-tickets` pass

Not created yet — this epic is scope-only. Four milestones, in strict dependency order — later
milestones assume earlier ones landed:

### M1 — Measurement foundation (no build, no risk)

1. **Profile by phase *and* by LOD tier / cadence bucket.** Existing `TickAudit` phase-cost
   recording extended to break down cost by the scheduling gates that actually determine per-tick
   workload (readiness, LOD tier, cadence bucket) — not just by kernel phase. Depends on
   `design_enhancement_roadmap.md` Priority 0 landing first (measuring against `DEGRADED`-mislabeled
   telemetry is measuring nothing real).
2. **Measure the real post-filter working set.** How many entities actually reach `COLLECTION`
   after the readiness/LOD/cadence gates, on a real scenario at realistic population — not the
   "10,000 entities" mental model the original external proposal assumed. This number directly
   changes the ROI case for M2.2 below; don't skip it to save time.

### M2 — Output-preserving optimizations (Low risk to determinism, no emergent-behavior risk by design)

3. **Spatial domain decomposition as the parallelism unit** — `WorkerManager` chunks by region
   instead of flat index range (confirmed today: `packets[i:i + chunk_size]`, no spatial awareness).
   Safe because Resolution re-sorts canonically regardless of which worker computed what — a bug
   here is a correctness bug, not a fidelity tradeoff.
4. **Data-Oriented hot-path projection for `COLLECTION`'s tightest loops** — narrowly scoped (a
   projection for measured hot fields, not an ECS rewrite), and **only after M1.2's measurement**
   confirms the working set is large enough for this to matter; the existing scheduling gates may
   have already captured most of the value DOD would provide.
5. **Deterministic memoization by input signature** for pathfinding/utility scoring — real risk is
   an incomplete signature causing stale results (a correctness bug to test for directly), not a
   fidelity question.
6. **Hierarchical/incremental hashing** for the full canonical-hash calls that do happen (rate
   already limited by `BudgetedCanonicalHasher` — this reduces the per-call cost of the calls that
   survive that budget, a different lever). Zero simulation-logic risk — this only changes how the
   verification hash is computed.

### M3 — Job graph for provably-independent phases (Medium risk to determinism, Real risk to emergent-behavior quality)

**Hard gate, not a suggestion:** do not start this milestone before
`docs/plans/design_enhancement/subphase_domain_contracts_epic.md` lands. That epic's per-sub-phase
domain declarations are the only mechanical way to prove two sub-phases are actually independent —
today there's no contract to check that against, and a wrong independence assumption here silently
changes outcomes rather than erroring.

7. **Build the job graph** from the sub-phase domain contracts, run provably-independent sub-phases
   concurrently within Resolution, keep the existing canonical-order guarantee for everything that
   isn't provably independent.
8. **Acceptance gate**: run `tests/arena/`'s suite before/after, then compare Simulation Quality
   pillar grades from those same before/after runs via `tools/evaluate_simq.py` (see
   `design_enhancement_roadmap.md` Section D2/D3) — a determinism hash can't tell you whether the
   independence proof actually held in practice at scale, SimQ/arena can.

### M4 — Hierarchical/aggregate simulation for distant regions (Higher risk to determinism, Real and intentional emergent-behavior tradeoff)

**Same acceptance gate as M3, not optional here either** — this milestone is an explicit,
deliberate fidelity cut (an aggregate population model instead of individual simulation for
unobserved regions), so the question isn't whether behavior changes, it's whether the change is
acceptable. Last in the sequence on purpose: highest ceiling, highest risk, and benefits most from
M1–M3's measurement and tooling already being in place.

9. **Design the aggregate model** for unobserved-region population/economy/threat, with an explicit,
   deterministic switch condition between individual and aggregate simulation (never wall-clock or
   load-triggered — see `docs/plans/design_enhancement/determinism_envelope_epic.md` for why that
   distinction matters).
10. **Validate via M3's SimQ/arena gate** before considering this milestone done — a regression here
    is a design failure (aggregate model too coarse), not a bug in the traditional sense, so the
    acceptance criteria are quality-gated, not just test-pass/fail.

## Out of Scope

- Anything already confirmed built (see Problem above) — do not re-propose dirty-set/cadence/LOD/
  demand-driven gating or type-batched Resolution as new work.
- `docs/plans/design_enhancement/design_enhancement_roadmap.md` Section G's unverified proposals
  (SIMD/vectorization, ECS-lite data-model changes beyond M2.4's narrow projection, etc.) — not
  scoped here unless independently verified and promoted.

## Acceptance Signal

Each milestone's items pass their own listed test/measurement bar; M3 and M4 additionally require a
clean `tests/arena/` run and no SimQ pillar-grade regression (via `tools/evaluate_simq.py`) between
before/after runs from the same checkpoint.
