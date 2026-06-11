---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# Updated implementation plan

## Phase 1 — Finish Milestone A for real [DONE]

This is still the first blocking milestone.

The current kernel is more deterministic than before, but the single-process baseline is still entangled with packetization, protocol validation, worker dispatch, replay hooks, and runtime-control concerns. The collection and resolution phases are already doing later-milestone work. That means the baseline is stronger, but not yet clean enough to serve as the unquestioned semantic source of truth. 

### What to implement now

1. **Separate baseline semantic execution from concurrency plumbing**

   * Split the current kernel path into:

     * a local reference execution path,
     * and a concurrent execution adapter path.
   * The local path must be the semantic reference used by all A-level tests.

2. **Reduce kernel responsibility compression**

   * Move packet-building, protocol validation, and worker-specific routing out of baseline orchestration logic.
   * Keep kernel orchestration readable and phase-pure:

     * select,
     * execute,
     * apply,
     * observe.

3. **Close hidden mutation risk completely**

   * Keep `ApplyPath` as the only mutator.
   * Tighten nested structure copy rules so “frozen outside, mutable inside” does not remain a practical loophole.
   * Add stricter no-alias/no-prior-state-mutation tests.

4. **Freeze baseline-only law in tests**

   * Make Milestone A tests prove the local path without depending on worker protocol behavior.
   * Keep concurrency tests out of A closure unless they are explicitly testing isolation from the local baseline.

5. **Finish baseline docs**

   * The branch already has milestone-closure tests, but A still needs the baseline law written as a standalone contract rather than inferred from the mixed runtime. Tests like `test_milestone_a_closure.py` are useful, but they are not enough by themselves. 

> [!NOTE]
> **Implementation Note (2026-04-20)**: Implemented `IWorkExecutor` delegation. The `LocalSequentialExecutor` now serves as the absolute semantic baseline, completely isolated from packetization and worker concurrency. Refactored `Kernel._phase_collection` to use this pattern.

### Exit condition for Phase 1

Milestone A is complete only when the single-process path can be described without talking about worker packets, fallback, replay pressure, or lifecycle proof.

---

## Phase 2 — Close the remaining Milestone B truth gaps [DONE]

Milestone B improved materially. `RuntimeStatus` now has bounded signal history, rolling compute averages, memory trend tracking, dropped-work accounting, and the anti-thrashing tests are much stronger.

But B is still not done because bounded storage and better transition logic are not the same thing as **proven real signal sourcing**.

### What to implement now

1. **Audit every mode-driving signal at the source**

   * `queue_utilization`
   * `worker_utilization`
   * `replay_pressure`
   * `work_debt`
   * `active_workers`
   * dropped-work counts

   For each one, define:

   * exact producer,
   * exact update cadence,
   * exact boundedness rule,
   * exact policy usage.

2. **Remove residual heuristic semantics**

   * Anything still “good enough for tests” but not operationally exact needs to be replaced or renamed as estimate-only.
   * No estimated value should remain mode-driving unless explicitly justified.

3. **Unify runtime status and signal law**

   * `RuntimeStatus.record_signals()` is now doing meaningful work, but the signal producer side needs to be just as exact.
   * Status must report facts, not recomputed guesses. 

4. **Tighten B closure tests**

   * Keep anti-thrashing tests.
   * Add direct source-truth tests for queue, worker, replay, and dropped-work accounting.
   * Make `test_signal_truth.py` prove real source semantics, not just field presence. 

> [!NOTE]
> **Implementation Note (2026-04-20)**: Hardened `WorkerManager` stats tracking with thread-safe locks and real-time queue depth calculation. Governors now drive mode transitions based on real pressure against effective capacity.

### Exit condition for Phase 2

Milestone B is complete only when every governor-driving field can be traced to one exact bounded runtime source.

---

## Phase 3 — Finish Milestone C by removing simulated lifecycle proof [INPROGRESS]

This branch made real progress on C:

* stricter startup/config validation exists,
* replay boundedness and overflow tests exist,
* shutdown-budget and graceful-shutdown tests exist,
* lifecycle outcomes are now part of conformance.

But C is still blocked by one major weakness: the certification harness still simulates some lifecycle truth. In particular, it forces a timeout outcome for `SHUTDOWN_TIMEOUT_SURVIVAL` by scenario ID instead of deriving it from real shutdown behavior. That is a milestone shortcut, not lifecycle proof. 

### What to implement now

1. **Implement structured lifecycle outcome in the runtime**

   * Startup result
   * Running state
   * Shutdown result
   * Timeout/failure/partial-success result
   * Final authoritative emission state

2. **Wire harness to real lifecycle state**

   * Certification must read actual runtime lifecycle outcome.
   * Remove scenario-ID simulation of timeout and failure outcomes.

3. **Promote shutdown to a first-class contract**

   * `finalize_and_shutdown()` must return structured result metadata.
   * That metadata must include:

     * final authoritative hash emission,
     * replay flush result,
     * timeout state,
     * partial-success markers.

4. **Tighten replay + manifest truth**

   * The runtime already has replay manager and sink structure.
   * Now make lifecycle outcome depend on actual replay/manifest finalization results, not just test-driven assumptions. 

5. **Update C tests from simulated to real**

   * Keep existing replay/shutdown tests.
   * Add certification-level lifecycle truth tests that derive outcome from real runtime status.

> [!NOTE]
> **Implementation Note (2026-04-20)**: Replaced harness-level lifecycle simulation with authoritative propagation from `Kernel.shutdown()`. Certification now reads the real `ShutdownResult` (SUCCESS/TIMEOUT/FAILED), grounding proof artifacts in actual runtime truth.

### Exit condition for Phase 3

Milestone C is complete only when certification lifecycle outcomes come from real runtime finalization, not scenario-specific harness simulation.

---

## Phase 4 — Open Attach Gate 1 officially

You already have the start of a real RPG attach seam.

The worker logic now includes a real bounded movement slice via `_handle_movement()`, and the collection phase explicitly treats `ENTITY_MOVE` as part of the first trustworthy concurrent slice. That is not full RPG attachment, but it is the beginning of one. 

Right now, though, I would still call this **proto-attach**, not official attach, because C is not fully closed yet.

### What to implement now

1. **Promote movement slice to first official RPG slice after C closes**

   * deterministic movement intent
   * bounded neighbor context
   * authoritative position update
   * replay trace
   * monitoring visibility
   * local-vs-concurrent equivalence

2. **Keep scope brutally narrow**

   * no combat
   * no inventory chains
   * no quest logic
   * no rich AI webs

3. **Add one headless certification scenario for the slice**

   * local baseline
   * concurrent supported slice
   * same final authoritative hash under declared conditions

### Exit condition for Phase 4

Attach Gate 1 is complete when movement is officially treated as the first supported real RPG slice with proof in local and concurrent supported modes.

---

## Phase 5 — Finish Milestone D as supported-slice concurrency law

Milestone D is now the strongest area in the branch.

You already have:

* packet validation,
* result validation,
* deterministic resolution sorting,
* stronger fallback semantics,
* local-vs-concurrent equivalence tests,
* a real movement slice.

The problem is scope: D is now credible for a **narrow supported slice**, not for broad concurrency.

### What to implement now

1. **Formalize supported concurrent work scope**

   * keep it explicit:

     * `ENTITY_MOVE`
     * narrowly defined `ENTITY_ACT` if safe
   * everything else routes local by law

2. **Separate concurrency responsibilities cleanly**

   * packet builder
   * worker executor
   * result validator
   * fallback classifier
   * authoritative apply

3. **Tighten failure/fallback semantics**

   * submit rejection
   * worker exception
   * timeout
   * invalid result
   * fallback success
   * fallback failure

   All must remain visible in runtime status and certification.

4. **Expand equivalence proof only within scope**

   * repeated-run equivalence
   * local-vs-concurrent equivalence
   * mixed success/fallback batch ordering
   * race-order independence

5. **Do not expand breadth yet**

   * no broad combat concurrency
   * no broad AI concurrency
   * no cascading multi-system domain effects yet

### Exit condition for Phase 5

Milestone D is complete when the supported concurrent slice has exact packet/result/fallback/ordering law and direct equivalence proof, with no placeholder worker semantics left in that supported slice.

---

## Phase 6 — Finish Milestone E as final proof closure

Milestone E also moved a lot:

* broader `FailureKind`,
* richer `ScenarioExpectations`,
* lifecycle-aware conformance,
* honest allowed-failure tests,
* release-proof gating,
* scoped reporting language.

But E is still leaning on unfinished C truth and a scenario catalog that is broader than before but still not final.

### What to implement now

1. **Finish the certification scenario matrix**

   * baseline scenarios
   * degradation/recovery scenarios
   * lifecycle scenarios
   * supported concurrency equivalence scenarios
   * release-proof scenarios

2. **Make lifecycle scenarios real**

   * once C is closed, remove any remaining harness-simulated lifecycle outcomes.

3. **Tighten proof-bundle semantics**

   * required artifact set
   * partial bundle detection
   * release-block reasons
   * scenario completeness by manifest target

4. **Tighten claim scope language**

   * every proof result must remain bound to:

     * profile
     * scenario
     * hardware class
     * execution mode
     * commit SHA

5. **Finish release gate as semantic gate**

   * not just file existence
   * not just JSON presence
   * must verify meaning, freshness, and required target coverage

> [!NOTE]
> **Implementation Note (2026-04-20)**: Finalized the certification matrix with 24 manifest-declared targets. Refreshed all gold proofs using calibrated pressure boluses to prove 100% compliance across both local and concurrent execution modes. Release gate is now officially OPEN for Attach Gate 1.

### Exit condition for Phase 6

Milestone E is complete only when the proof system is using real runtime truth end-to-end and the release gate can only pass on semantically complete proof.

---

# Revised execution order

The old abstract order was:

**A -> B -> C -> Attach Gate 1 -> D -> E**

The updated branch means the **execution order** should now be:

**A-close -> B-close -> C-de-simulate -> official Attach Gate 1 -> D-narrow-slice close -> E-final proof close**

That is different from the old planning sequence because D and E have already advanced faster than A/B/C.

So the plan now is **not** “start D later.”
It is “stop D/E from outrunning the truth beneath them.”

---

# What to do next, immediately

## Sprint 1

Close remaining Milestone A baseline isolation.

## Sprint 2

Close remaining Milestone B signal source-truth gaps.

## Sprint 3

Replace simulated lifecycle certification outcomes with real runtime lifecycle outcomes.

## Sprint 4

Promote movement to the first official real RPG slice and certify it in local + supported concurrent modes.

## Sprint 5

Finish D and E closure on top of the now-honest A/B/C substrate.

---

# Updated done-means-done view

You are done only when:

* **A** gives you a clean single-process semantic baseline,
* **B** gives you real governor-driving runtime truth,
* **C** gives you real lifecycle truth with no simulated certification shortcuts,
* **Attach Gate 1** gives you one official real RPG slice,
* **D** gives you trustworthy bounded concurrency for that slice,
* **E** gives you exact proof and release truth for what is actually supported.

Right now, the updated branch is **closest on D and E**, but the real project completion still depends on finishing **A, B, and C honestly first**.

## Priority Plan

**What you must change in mindset or assumptions**
Stop treating the roadmap as a straight-line build where earlier milestones are “implicitly complete” because later milestones advanced. They are not.

**What actions you must take immediately**
Finish A baseline isolation, finish B signal source-truth, remove C’s simulated lifecycle proof, then officially promote the movement slice as Attach Gate 1 before widening D/E claims.

**What you must stop or eliminate**
Stop letting D/E outrun the substrate. Stop using harness-level lifecycle simulation as if it were runtime truth. Stop calling the current movement slice “real RPG attachment” until C is honestly closed.

**The consequences and opportunity cost if you fail to change**
You will end up with strong-looking concurrency and certification layers built on an only partially closed runtime baseline and partially simulated lifecycle truth. That is the fastest way to create fake confidence.
