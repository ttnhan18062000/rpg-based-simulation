---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, engine, performance, determinism, observability, testing]
---

# Design Enhancement Roadmap — Performance-First, With Scoped Non-Performance Additions

## Purpose

This groups a system-design discussion (2026-08-25, no code/test changes made) into epic-sized
work streams the same way `docs/plans/architecture_resilience_remediation_roadmap.md` and
`docs/plans/engine_future_epics_roadmap.md` already do for their own source audits — so a single
stream can be picked, investigated properly, and turned into real tickets via the `create-tickets`
pipeline, without committing to all of them at once.

**Source material, in order produced:**
1. `docs/brainstorm/simulation_design_taxonomy.html` — a 108-pattern audit of the engine's actual
   architecture against the general taxonomy of simulation-design patterns, revised twice (once
   against an external AI review, once after a performance follow-up corrected 5 misclassifications
   discovered while researching item 2 below).
2. `docs/brainstorm/performance_evolution_roadmap.html` — 22 performance ideas from a second
   external AI note, checked against the actual code. 8 were already built, 4 partially, 2 have a
   verified-real enabling primitive with nothing built on it, 7 are genuinely open.
3. This session's own follow-up investigation (below), which surfaced a live defect not mentioned
   in either prior document.
4. A third external AI note (`tmp/external_ai_suggest_design.md`, not committed), given only the
   engine's factual architecture (not this roadmap) and asked for independent enhancement ideas —
   then cross-checked against this same roadmap and the taxonomy doc by that same reviewer. Unlike
   the performance note, most of its high-priority claims held up under verification: see Priority
   0.5 and Section F below, both added as a direct result. Its remaining, unverified proposals are
   listed in Section G rather than silently treated as established facts.

**Related prior work, already fully resolved — read before assuming any of this is new territory:**
`docs/plans/kernel_concurrency_design_review_proposal.md` (2026-08-17 discussion, all 8 findings
C1–C8 closed 2026-08-21) landed `docs/architecture/kernel_concurrency_design_philosophy.md`,
fixed three doc contradictions, added `RuntimeMode` as a required performance-claim dimension, and
documented the per-mode policy table reproduced in Priority 0 below. Its Appendix A and C4/C6 are
the source for facts in this roadmap not present in either brainstorm doc (`PhaseBudgetGovernor`,
`work_debt` ledger, the full NORMAL→SURVIVAL policy table, `LODService.should_execute`).

---

## Priority 0 — Fix the benchmark instrument before trusting any benchmark

**Not in either brainstorm doc — found while cross-checking `docs/plans/` for prior work on this
exact topic, to avoid scoping performance work on top of a broken measurement.**

`docs/plans/kernel_concurrency_design_review_proposal.md` C4's closing note records: an empirical
measurement pass against all 6 live-parametrized perf scenarios found `WorkerManager.get_stats()`
defaults `worker_utilization` to `1.0` (not `0.0`) whenever `max_worker_count == 0` — true for
every `PERF_*_LOCAL` profile. This unconditionally trips the Governor's `DEGRADED` threshold
regardless of real load, so **all 6 scenarios currently report `DEGRADED` for every sampled tick**,
independent of what the code under test actually does. The perf-regression gate added by that
ticket is deliberately soft (warning-only) specifically because of this, "pending a follow-up
ticket to fix the `WorkerManager`/Governor signal defect itself." No such follow-up ticket exists
yet (checked `tickets/` before writing this).

**Why this is Priority 0, not folded into Section A:** every other item in this roadmap will be
measured, tuned, or validated against these same 6 scenarios. Building anything performance-related
on top of permanently-`DEGRADED` telemetry means every before/after comparison is comparing against
a baseline that's already lying about its own load state — Section A's own #2 ("measure the real
post-filter working set before committing to anything else") depends on this being fixed first.

**Severity, revised after the external note's follow-up question and checked directly:** the
external note asked whether this is "more than a benchmarking defect... also a simulation-semantics
defect." Confirmed yes. `worker_utilization` is not cosmetic telemetry — it's one of the "Primary
Pressure Inputs" (`src/core/governance.py`'s `PressureSignals`, Law M7.1) that
`ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py`) reads directly:
`worker_utilization >= 0.7` alone is sufficient to indicate `CONSTRAINED`, `>= 0.9` alone is
sufficient to indicate `DEGRADED` (confirmed it does *not* reach `SURVIVAL` — that tier only checks
`work_debt_total`, `tick_compute_ms`, and `memory_estimate_mb`, not `worker_utilization`). Every
`PERF_*_LOCAL` profile therefore doesn't just *report* `DEGRADED` — it actually *runs* under the
real `DEGRADED` policy bundle (tighter cadence, `EXACT_DIRTY` scan policy, opportunistic work off,
reduced replay richness) regardless of real load. This is a live scheduling/fidelity defect for
every profile that hits this code path, not only a corrupted metric.

**Scope:** a small, self-contained hotfix — correct the `worker_utilization` default in
`WorkerManager.get_stats()`, re-run the 6 scenarios, confirm they report `NORMAL` under real idle
load, and consider whether `test_perf_regression_baseline.py`'s soft gate can now be tightened now
that the signal it depends on is trustworthy.

**Docs and parity — checked, and this one is required, not optional.** The defect already has a
parity ledger entry: `docs/parity_ledger/infrastructure.yaml` `id: INFRA-368`, `status: verified`
(verified as an accurate description of current behavior, including the bug — not verified as
fixed). Per this project's Parity rule, fixing the defect means updating `INFRA-368`'s `status`
and `v2_evidence` in the same session the fix lands, not a follow-up. **Test gap, also checked**:
no existing test asserts `WorkerManager.get_stats()['worker_utilization'] == 0.0` when
`max_worker_count == 0` directly — `tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline`
only asserts no *excursion during a benchmark window*, which currently passes vacuously since every
window already starts DEGRADED. The fix needs its own new unit test for the default itself, not
just a re-run of the existing regression suite.

---

## Priority 0.5 — The determinism envelope doesn't cover wall-clock-driven mode escalation

**Full milestone breakdown:** `docs/plans/design_enhancement/determinism_envelope_epic.md`.

**Not in either brainstorm doc — the external note's headline concern, verified directly rather
than taken on trust, because it's the kind of claim that's cheap to check and expensive to be
wrong about.**

The note's claim: if elapsed time or machine pressure changes which work is dropped, deferred, or
run at reduced fidelity, then "same seed + same starting state" does **not** necessarily produce
the same world state — "different hardware or transient load can produce a different
operating-mode sequence and debt ledger."

**Checked directly, confirmed true.** `PressureSignals` (`src/core/governance.py`) is built from
real wall-clock/hardware measurements, not deterministic/state-derived values:
`tick_compute_ms` ("Absolute nanosecond-derived compute time"), `memory_estimate_mb` ("RSS
measurement from collector"), `worker_utilization`, `queue_utilization`. `ResourceGovernor.
_get_indicated_mode()` escalates `RuntimeMode` directly off these — and `RuntimeMode` gates
cadence, LOD, `scan_policy`, concurrency, and debt accumulation (the per-mode policy table already
in this roadmap's Purpose section). So two runs of the same seed and initial state, under different
real-world timing or machine load, can genuinely diverge in *what gets computed*, not just in
execution trace or wall-clock duration.

**This is not simply a restatement of the already-documented "concurrent mode isn't bit-exact"
scope note** (`docs/engine/deterministic_execution.md` — "Out of scope: Concurrent execution mode
... message delivery order is non-deterministic at the OS level"). That note's stated reason is
about *worker completion order*, a problem the canonical-sort-before-Resolution design already
solves regardless of which worker finishes first. Wall-clock-driven `RuntimeMode` escalation is a
**different, additional mechanism** producing the same top-level symptom (live mode isn't
bit-exact) — and unlike worker completion order, it's not already structurally neutralized by
existing design; it directly changes what gets scheduled.

**Narrower than it first looked — checked the parity ledger before treating this as unaddressed
territory, and it isn't entirely.** `docs/parity_ledger/infrastructure.yaml` `id: INFRA-363`
(`status: verified`, tests passing: `tests/unit/kernel/test_verification_level.py`) already
records a real, tested mitigation: any run whose `RuntimeStatus.max_mode_reached` ever hits
`DEGRADED` or `SURVIVAL` gets `verification_level = "REDUCED"` on `ShutdownResult`, `RunManifest`,
and `run_report.json/.md` — an honest, explicit label that a run's determinism proof isn't the full
one. So the project already knows to distrust a DEGRADED/SURVIVAL run's hash proof; it isn't silent
about that. **What `verification_level` does *not* give**, and what the residual gap actually is:
it's a post-hoc honesty label on *one* run, not a claim about whether a second run of the *same*
seed under different real-world timing/load would reach the *same* result — the question "is 'same
seed' still a reproducibility promise for the live/concurrent server, or only for sequential/
certification runs" is the part with no documented answer yet, `verification_level` or not. Also
worth noting: Priority 0's defect means every affected `PERF_*_LOCAL` scenario is *already*
incorrectly carrying `verification_level = "REDUCED"` today — fixing Priority 0 also fixes that
mislabeling, for free, as a side effect.

**Scope for investigation, not yet a ticket:** the note's proposed fix is reasonable and worth
scoping seriously — define what a full "reproducibility manifest" covers for this engine (initial
state hash, engine/content version, RNG version, ordered external inputs, runtime-policy trace),
and decide explicitly between a **canonical mode** (certification/sequential runs use deterministic
proxies — fixed work-unit counts, queue sizes — instead of wall-clock timing to drive `RuntimeMode`)
and a **live bounded mode** (the live server keeps using real wall-clock signals, but every mode
transition becomes part of a recorded control trace, so a live run is reproducible *given that
trace*, even though the trace itself isn't predictable in advance). Whichever is chosen,
`docs/engine/deterministic_execution.md`'s "Scope of the guarantee" section needs a new paragraph —
it currently doesn't mention `RuntimeMode`-driven divergence as a mechanism at all, only OS-level
worker ordering — and `tests/unit/kernel/test_verification_level.py` /
`tests/unit/kernel/test_worker_equivalence.py` are the existing suites to extend, not a new one to
start from scratch. This ranks ahead of Section A's performance work in the sense that Section A's
"Risk to determinism" column implicitly assumes the sequential-mode guarantee applies — for the
live/concurrent server specifically, that assumption is now known to need this qualifier.

---

## Section A — Performance (primary)

**Full milestone breakdown:** `docs/plans/design_enhancement/performance_milestones_epic.md`
(M1 measurement → M2 output-preserving optimizations → M3 job graph, gated on Section F below →
M4 hierarchical/aggregate simulation, gated on the same acceptance signal as M3).

Full detail, evidence, and per-item citations: `docs/brainstorm/performance_evolution_roadmap.html`.
Reproduced here as the roadmap's spine, in the doc's own revised priority order — note that this
order already excludes everything the doc found was already built (dirty-set/affected-set
processing, deterministic multi-rate scheduling, simulation LOD, demand-driven gating, and
type-batched Resolution are all live in production today and are *not* work items):

| # | Move | Risk to determinism | Risk to emergent-behavior quality |
|---|---|---|---|
| 1 | Profile by phase **and** by LOD tier / cadence bucket | None | None — read-only |
| 2 | Measure the real post-filter working set (via `TickAudit`) before committing to anything below | None | None — read-only |
| 3 | Spatial domain decomposition as the parallelism unit (regions, not flat index-range chunks) | Low | None by design — output is canonically sorted before Resolution regardless of which worker computed it; a bug here is a correctness bug, not a fidelity tradeoff |
| 4 | Data-Oriented hot-path projection for Collection's tightest loops (narrow, not an ECS rewrite) | Low | None by design, same reasoning as #3 — a representation change, not a semantics change, if done correctly |
| 5 | Deterministic memoization by input signature (pathfinding, utility scoring) | Low | Low — real risk is an incomplete signature causing stale results, a correctness bug rather than an intentional fidelity cut |
| 6 | Hierarchical / incremental hashing for the full-hash calls that do happen | Low | None — this only changes how the verification hash is computed, not simulation logic |
| 7 | Job graph for provably-independent Resolution phases | Medium | **Real** — correctness depends entirely on the independence proof being right; a wrong proof silently changes outcomes rather than erroring |
| 8 | Hierarchical / aggregate simulation for distant regions | Higher | **Real, and by design** — this is an intentional fidelity cut (aggregate model instead of individual simulation) for entities that aren't being observed; the question isn't whether it changes behavior, it's whether the change is acceptable |

**Two things this session's own synthesis added, beyond adjudicating the source note:** the DOD
item (#4) should wait on #2's measurement — the existing readiness/cadence/LOD gates may have
already shrunk the real working set well below the "10,000 entities" mental model the original
proposal assumed, which changes SoA's ROI. And `ScenarioCheckpointer` (Section B) already gives a
cheap, repeatable way to benchmark from a fixed checkpoint instead of a cold start every time —
worth using for #1/#2 immediately, no new engineering required.

---

## Section B — Checkpoint-based experimentation tooling

What-If, Branching, Shadow, and Counterfactual Simulation (all four, `simulation_design_taxonomy.html`
§recovery) are the same underlying opportunity wearing four different names: `ScenarioCheckpointer`
(`src/engine/scenario_checkpoint.py`, INFRA-215/E31C) already pickles the full `AuthoritativeState` +
tick + RNG checkpoint to disk and restores a live, resumable `Kernel` from it, exposed over REST
(`POST /api/v1/scenarios/{id}/checkpoint`, `/restore/{name}`) and covered by tests. Restoring one
checkpoint into two or more independent `Kernel` instances, each resumed with a different
spec/policy, is the entire mechanism — the primitive is real and tested, the orchestration on top
of it (comparing outcomes, managing N branches) is not.

**Scope for a future ticket:** a small CLI or API layer that (1) restores a named checkpoint N
times with different overrides, (2) runs each to a target tick, (3) reports a diff of the resulting
runs at **two** levels, not one — a raw canonical-state diff (`CanonicalStateHasher.to_canonical_data()`
already produces the sortable dict this needs, cheap, answers "did anything diverge at all") and a
Simulation Quality comparison (see Section D2 — `tools/evaluate_simq.py`'s existing `_compare()`/
`_within_band()`, pointed at each branch's calibration output, answers "does the divergence
matter," which raw state equality can't tell you). Both halves already exist as building blocks —
this ticket is the orchestration connecting checkpoint restore to both of them, not new comparison
logic for either.

**Feature candidates from the external note, unverified/unbuilt, listed for future triage rather
than committed scope:** binary-search the first divergent tick between two branches; compare
phase/sub-phase hashes once Section A #6's hierarchical hashing exists; inspect the intent/mutation
history for one entity; a "field X changed because intent Y passed preconditions Z" causal
explanation; repeat-benchmark a specific tick range without rebuilding the whole scenario. None of
these were checked against the code — they're directionally consistent with a CLI built on
`ScenarioCheckpointer`, but each is its own scoping question.

## Section C — Interest Management

Already a documented, ticketed gap — `region_id` is reserved on every WS delta payload today,
always `null`, unpopulated, explicitly deferred to `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`
(see `docs/plans/live_map_scaling_roadmap.md` for the wider milestone sequencing this belongs to).
Included here only as a cross-reference, not a new proposal — do not re-scope it independently of
that existing epic.

## Section D — Verification gate: resilience testing, Simulation Quality, and Arena

Added after the original draft of this roadmap was reviewed for scope — it had considered kernel/
scheduling/checkpoint architecture but not the project's own existing quality- and integration-test
infrastructure. Two genuinely different things live in this section:

**D1 — Resilience testing coverage (unconfirmed, investigate first).**
`simulation_design_taxonomy.html` marks Fault-Injection Simulation, Chaos/Resilience Simulation,
and Property-Based Simulation Testing as **Unconfirmed** — genuinely not known, not known-absent.
Before performance work lands on top of this code, a short investigation should confirm whether
these exist anywhere in `tests/` under different names. This is a gate on how much confidence to
put in the "Risk to determinism" ratings in Section A's table — if resilience testing turns out to
be thin, those ratings are less trustworthy than they look.

**D2 — Simulation Quality (`src/simulation_quality/` + `tools/evaluate_simq.py`) as the acceptance
gate for behavior-changing items, not a new build target — and not new tooling either, corrected
after checking one directory further than the first pass of this section did.** SimQ is a real,
already-built module — 11 files, `QualityHub`, `QualityReport`/`QualityReportBuilder` — scoring 10
pillars (Cognition, Agency, Combat, Faction, Economy, Progression, Social, Information, World
Dynamics, Narrative) from live run events. It already has its own dedicated roadmaps, run to
completion and archived (`docs/plans/archive/simq_*.md`) — nothing here proposes reopening that
work. The first pass of this section claimed no run-to-run comparison tool existed, checked only
against `quality_report.py`/`quality_hub.py`; `tools/evaluate_simq.py` (a separate CLI, "SimQ
evaluation harness") was missed and does exactly this — `_compare(run_key, actual_grades,
anchor_grades)` and `_within_band(actual, anchor)` already produce per-pillar `PASS`/`REGRESS`/
`MISSING` rows against an anchor file (`grade_anchors.json`), with adjacent-grade tolerance built
in (confirmed via `tests/simulation_quality/test_evaluate_harness.py::TestCompare`). **This is
reuse, not a build item**: point `--anchors` at one run's calibration output and evaluate a second
run against it, and Section A items #7/#8's before/after comparison is already answerable with
existing tooling. This is the right instrument for exactly the two items in Section A's table
marked "Real" risk to emergent-behavior quality — a determinism hash can't answer either question,
since both are expected to *validly* produce different output under some conditions; SimQ pillar
grades can answer whether that difference is a regression.

**D3 — `tests/arena/` as the concrete harness to run D2 through.** `tests/arena/` is a real,
CI-gated integration/stress suite (40 tests, `legacy_compat` marker, `make lane-legacy-regression`,
5–15 min lane per `docs/testing/migration_ci_lanes.md` — actively maintained, not deprecated
despite the name) covering quests, regional control, tactics, stress, and stop conditions.
`test_arena_stress_50v50` already demonstrates the exact reusable pattern needed: build a named
scenario (`src/certification/scenarios.py`), run it N ticks through a harness, check against
expectations. Running the existing arena suite before/after a Section A item #7 or #8 change, then
comparing SimQ pillar grades from those same before/after runs via D2's existing `evaluate_simq.py`,
is the acceptance gate for those two items specifically. Items #1–#6 don't need this gate: their
own "Risk to emergent-behavior quality" column reasons are either "None by design" or a correctness
bug rather than a fidelity question, so raw determinism/regression testing already covers them.

## Section E — Explicitly excluded from this roadmap

- **Event Sourcing / Command Log** as a full reconstruct-from-log capability — `ScenarioCheckpointer`
  already covers the real use case (resumability) more cheaply; building a parallel input-log
  mechanism has no identified need.
- **Constraint-Based Simulation** (having `HardLawMonitor` derive state instead of only validating
  it) — a genuine architecture change with no identified payoff from this investigation.
- **AI/decision architecture verification** (Behavior Trees, GOAP, Utility AI, Steering Behaviors —
  all Partial/Unconfirmed in the taxonomy) — nothing in this investigation depends on knowing this;
  worth a future pass on its own terms, not folded into a performance-first roadmap.
- **Doc-naming hygiene** (crediting BSP and Functional Core/Imperative Shell by name in
  `kernel_concurrency_design_philosophy.md`) — one-line fixes, ride along with any other ticket
  touching that file rather than getting their own.

## Section F — Per-sub-phase domain/dependency declarations for the 37 Resolution phases

**Full milestone breakdown:** `docs/plans/design_enhancement/subphase_domain_contracts_epic.md`.

**Verified real, and directly relevant to Section A #7.** `src/engine/phase_domain_permissions.py`
declares read/write/emit domains only at the 7 *kernel*-phase granularity (`TickPhase.RESOLUTION`
as one undivided block: reads `{proposals, policy, entity}`, writes `{entity, world, policy,
infra}`) — confirmed by reading the file directly. There is no equivalent declaration for any of
the 37 named sub-phases *inside* Resolution (`trust_boundary`, `combat_engagement`,
`resource_transactions`, etc.) — no accepted-intent-type, read/write-domain, or ordering-key
contract per sub-phase, and nothing in `tests/architecture/` checks whether two sub-phases assumed
to be independent secretly touch the same state.

**Why this belongs in the plan, not just as an observation:** Section A #7 ("job graph for
provably-independent Resolution phases") is only safe if independence between sub-phases can
actually be proven. Today it can't be — there's no declared contract to check it against. This
makes Section F a **prerequisite for #7**, not a parallel nice-to-have: build the per-sub-phase
domain declarations (and the CI check that a declared-independent pair never writes the same
domain) before attempting #7's parallelization, not after. Same value the existing 7-phase-level
declarations already provide (`RPG-INFRA-155/156/157`) — this is the same pattern, one level
finer-grained, where the existing pattern doesn't yet reach. Note the existing file's own comment:
these are "declarative only — no runtime enforcement," enforced by test, not mechanically — worth
deciding whether the 39-phase version should be held to a higher (mechanical) standard, or the same
test-guarded one.

## Section G — Additional external-note proposals, not verified this pass

Listed for future triage, explicitly **not** treated as confirmed facts about the codebase the way
Sections A–F are — these are the remaining ideas from `tmp/external_ai_suggest_design.md` that
either weren't checked against the code, or are forward-looking design proposals rather than
claims about current state:

- **Transactional intent application ("MutationSet").** Partially already true: `src/core/updates.py`
  already represents proposals as typed, mergeable objects (`EntityUpdate`, `StateUpdate`, and ~14
  typed sub-update classes, each with its own `.merge()`). Not confirmed: a formalized per-intent
  outcome lifecycle (applied/rejected/superseded/deferred/failed) on top of that representation.
- **Mechanical (not just conventional) enforcement of the single-writer boundary** — deeply
  immutable Collection snapshots, a mutation-capability token, a linter/architecture test against
  importing mutable state internals.
- **Harden the RNG address format** into a structured tuple instead of ad hoc strings, with
  duplicate-address detection in certification runs.
- **Explicit numerical/serialization determinism scope** — pin down whether the guarantee is
  same-build, same-platform-matrix, or cross-platform, and forbid `repr()`/pickle bytes/process
  `hash()` from canonical hashes specifically (pickle noted as fine for `ScenarioCheckpointer`'s
  internal format, just not for canonical identity).
- **Give `work_debt` explicit semantics** — idempotency keys, revalidation/expiry rules, a fairness
  policy, and stated service guarantees (e.g. "near-tier combat state never more than one tick
  stale") so independently-reasonable gates don't combine into starvation.
- **Deterministic worker-failure semantics** — defined behavior for exception/timeout/crash/
  duplicate-result/late-result, idempotent per (tick, entity, system, attempt) task identity.
- **Atomic tick commit + live crash recovery** — a defined commit boundary (resolve → validate →
  persist → publish deltas → advance tick) plus periodic live checkpoints and a small ordered
  journal, so the server never publishes a delta for state it can't recover as committed. Touches
  areas (persistence, live-map WS) this pass didn't investigate.
- **Version every durable/wire artifact** — checkpoints, canonical schema, intents, RNG addressing,
  WS snapshots/deltas — with an explicit load/migrate/reject decision on restore.
- **Self-healing WebSocket protocol** — `base_tick`/sequence numbers on every delta, gap detection,
  forced resnapshot, bounded per-client queues with defined backpressure behavior.
- **A determinism-focused test matrix** — rerun identical scenarios while perturbing worker count,
  thread vs. process, `PYTHONHASHSEED`, injected delays; property-based and metamorphic tests; a
  minimizer that shrinks a divergent run to the smallest reproducer.
- **ECS-lite data-model safety** without a full rewrite — stable entity IDs with generation numbers,
  explicit component ownership, secondary indexes through the mutation gateway. Overlaps Section A
  #4's narrower DOD-projection scope; not reconciled with it here.

None of these are ruled in or out — they're each their own future investigation, sized roughly
epic-to-ticket depending on which one, not evaluated for correctness the way Priority 0/0.5 and
Section F were.

---

## Related Docs
- `docs/brainstorm/simulation_design_taxonomy.html`
- `docs/brainstorm/performance_evolution_roadmap.html`
- `docs/plans/kernel_concurrency_design_review_proposal.md`
- `docs/plans/live_map_scaling_roadmap.md`
- `docs/architecture/kernel_concurrency_design_philosophy.md`
- `docs/engine/candidate_selection.md`
- `docs/engine/deterministic_execution.md` (Priority 0.5 — existing scope note this extends)
- `docs/testing/migration_ci_lanes.md` (Section D3 — `legacy_compat`/arena lane)
- `docs/plans/archive/simq_scoring_improvement_roadmap.md` and sibling archived SimQ plans
  (Section D2 — context only, not reopened)
- `tmp/external_ai_suggest_design.md` (not committed — source for Priority 0.5, Section F, Section G)
- `docs/plans/design_enhancement/determinism_envelope_epic.md` (Priority 0.5 milestone breakdown)
- `docs/plans/design_enhancement/performance_milestones_epic.md` (Section A milestone breakdown)
- `docs/plans/design_enhancement/subphase_domain_contracts_epic.md` (Section F milestone breakdown)

## Related Tickets
- `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT` (Section C, already exists)
- None yet for Priority 0, 0.5, or Sections A/B/D/F — this roadmap is pre-ticket scoping.

## Assumptions / Open Questions
- Priority 0's fix scope assumes the `worker_utilization` default is a simple sign/default error,
  not a deeper Governor-signal design flaw — needs its own investigation before a ticket is filed.
- Priority 0.5 is scoped as an investigation, not a ticket yet — "canonical mode vs. live bounded
  mode" is a real design decision that needs maintainer input, not something to default into
  silently.
- Section D1's outcome (resilience-testing coverage) could lower confidence in Section A's
  "Risk to determinism" column across the board if that coverage turns out to be thin.
- Section F should land before Section A #7 is attempted, not after — #7's safety depends on it.
- Section G items are unevaluated by design — do not promote any of them to a ticket without the
  same verify-first pass Priority 0.5 and Section F got.
- No maturity/scheduling commitment is made here — this is a scoping document, not a sprint plan.

## Next Steps
Each section above becomes its own ticket (or, for Priority 0, likely a `hotfix`) through the
normal `create-tickets` / `implement-ticket` pipeline, scoped independently rather than as one
large change. This document is the handoff, following the same pattern as
`kernel_concurrency_design_review_proposal.md`.
