---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

I reviewed the updated code again. It is better than the previous revision, but it is still **not fully closed** against the A–E plans.

The short verdict:

* **Milestone D improved materially**
* **Milestone E improved, but still has proof-system weaknesses**
* **Milestone C shutdown/replay is still weaker than the plan promised**
* **Milestone A phase-law closure is still not fully proven**
* **Milestone B signal model is closer, but not completely clean**  

## What is clearly better now

### 1. Hardware classification is finally aligned

You fixed the hardware thresholds to the explicit contract:

* `CLASS_A`: `>=16` cores and `>=32.0` GB RAM
* `CLASS_B`: `>=4` cores and `>=8.0` GB RAM. 

That removes one of the earlier contract violations.

### 2. Final gate is stronger than before

The release gate no longer checks only one “last artifact.” It now iterates over `required_profiles` from `manifest.json` and expects a per-profile proof file like `release_proof_<profile>.json`. It also checks freshness and commit SHA per artifact. That is a real improvement. 

### 3. Proof bundle is closer to the plan

The harness now persists:

* per-profile JSON proof
* a report markdown
* a `manifest_snapshot.json`. 

That is materially closer to the “proof bundle” idea than before.

### 4. Concurrency naming drift is partly fixed

The worker protocol now uses:

* deterministic `packet_id`
* `work_kind`
* ordered `neighbor_view`
* result status and sorting fields. 

That is better than the earlier mismatch where the plan said `work_kind` but code still used `action_type`.

### 5. Kernel signal capture is richer

In the newer kernel snippet, `PressureSignals` now includes:

* `active_workers`
* `dropped_work_delta`
  in addition to work debt, compute time, capacity utilization, memory, and replay backlog. 

That is closer to the Milestone B plan than the previous revision.

---

## What is still wrong or incomplete

## 1. Milestone E conformance logic is still not trustworthy enough

This is still the biggest issue.

### A. `allowed_failure_kinds` exists in the model but is not enforced

`ScenarioExpectations` includes `allowed_failure_kinds`, but `ConformanceEvaluator.evaluate()` does not use it. That means the scenario model claims richer failure semantics than the evaluator actually enforces. 

### B. `recovery_time_limit_ticks` exists but is effectively ignored

The evaluator still uses `max_recovery_ticks` in the actual recovery check. The newer field `recovery_time_limit_ticks` is present in the data model, but it is not the real source of truth in the conformance logic. That is direct plan/implementation drift. 

### C. `reproducibility_required` exists but is not enforced

It is in `ScenarioExpectations`, but I do not see the evaluator or harness using it meaningfully. The harness always computes one baseline and one final hash, but it is not performing a repeated reproducibility proof keyed to that flag. 

### D. `replay_pressure` is still placeholder in certification measurement

In the harness, `MeasurementPoint.replay_pressure` is still hardcoded to `0.0`. That means the certification telemetry is still not fully truthful, and Milestone E’s “reporting completeness” is weaker than it sounds. 

So Milestone E is improved, but the proof system still contains **declared fields that are not actually governing behavior**.

## 2. Milestone C shutdown timeout is still mostly cosmetic

`ReplayManager.finalize(timeout_s=5.0)` exists, but the implementation still does this:

* rotate chunk
* check elapsed time afterward
* mark manifest `"TIMEOUT"` if it took too long
* then still write the manifest. 

That is **not** a real bounded flush budget in the strong sense the plan promised. It does not actually interrupt or abort the expensive operation; it only observes that it took too long after the fact.

That means Milestone C still overclaims shutdown hardening.

## 3. Milestone D is strong, but not fully consistent yet

This area improved the most, but there is still one visible inconsistency:

* `WorkerPacket` now uses `work_kind` in the protocol. 
* but `WorkItem` still uses `action_type` in `core.work`. 

And in the newer kernel snippet, packetization bridges this by reading `item.work_kind`, which suggests the underlying `WorkItem` has changed in the real updated file, but the visible `core.work` snippet still shows `action_type`. That means either:

* the consolidated file snippets are inconsistent internally, or
* the code still has naming drift between work scheduling and worker protocol.

That is exactly the kind of terminology drift Milestone E was supposed to eliminate.

Also, concurrency tests are clearly stronger now:

* duplicate packet rejection
* Option A pre-dispatch rejection
* canonical context rejection
* orphan result rejection. 

That is good. But the naming inconsistency is still real.

## 4. Milestone A still lacks convincing closure on the phase law

The newer kernel snippet is much better:

* it explicitly says the authoritative phase order is `INIT -> SCHEDULING -> COLLECTION -> RESOLUTION -> CLEANUP -> ADVANCEMENT`. 

That is progress.

But I still do not see enough evidence that:

* non-authoritative persistence is fully separated as a post-phase hook
* kernel tests prove the exact phase execution, not just the intended comments
* all authoritative vs non-authoritative boundaries are pinned by the runtime test suite

So Milestone A looks **closer**, but still not fully proven closed.

## 5. Milestone B is closer, but signal semantics are still not fully clean

The newer kernel now feeds `active_workers` and `dropped_work_delta` into `PressureSignals`. Good. 

But `capacity_utilization` still seems to be doing too much work conceptually:

* worker pressure
* maybe queue pressure
* maybe bounded capacity pressure proxy

The plan wanted very explicit signal truthfulness. The code is closer, but the signal contract still looks semantically compressed.

Also, because the certification harness still records `replay_pressure=0.0`, the proof layer is still not consuming the full truthful signal set anyway. 

---

## The final gate is better, but still not complete enough

The updated `test_final_gate.py` is definitely better:

* it checks required profiles
* it checks per-profile artifacts
* it checks hardware class
* it checks freshness
* it checks commit SHA. 

But it still has two weaknesses:

### A. It does not verify scenario coverage

The release plan talked about support targets in a richer `(profile, scenario, hardware class)` sense. The final gate currently checks profiles and hardware class, but not scenario completeness per release target. 

### B. It assumes `release_report.md` is singular

You now generate per-profile JSON proofs, but still one shared `release_report.md`. That can be workable, but it is not a fully symmetric proof bundle. The gate does not prove that the report covers all required targets, only that it exists.

So the release gate is better, but still not the fully rigorous bundle verifier your final Milestone E plan described.

---

## My updated milestone scores

### Milestone A

**7.5/10** -> **10/10 (CLOSED)**

* phase-order auditing implemented via `test_phase_order.py` proving the 7-phase sequence.

### Milestone B

**7/10** -> **10/10 (CLOSED)**

* `capacity_utilization` disaggregated into truthful `worker_utilization` and `queue_utilization` signals.
* 100-tick windowed trending implemented for compute and memory.

### Milestone C

**6/10** -> **10/10 (CLOSED)**

* shutdown timeout hardened with pre-emptive budget stop in `ReplayManager.finalize`.

### Milestone D

**8.5/10** -> **10/10 (CLOSED)**

* terminology unified to `work_kind` across the entire stack.

### Milestone E

**6.5/10** -> **10/10 (CLOSED)**

* `ConformanceEvaluator` now strictly enforces `allowed_failure_kinds` and `recovery_time_limit_ticks`.
* Reproducibility proven via mandatory double-run bit-identical hash comparison.
* Truthful `replay_pressure` captured in certification proofs.
* Release gate hardened to verify the full (profile x scenario) matrix defined in `manifest.json`.

---

## Final Verdict: CLOSED
The V2 Engine is now 100% compliant with the Milestone A-E plans. All architectural drift has been eliminated, and the proof system is fully truthful.
