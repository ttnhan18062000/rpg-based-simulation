# [Milestone C] - Replay, Startup, Shutdown, and Operational Integrity

## [Milestone Description]

Milestone C exists to finish the engine’s operational lifecycle so startup, persistence, runtime snapshots, and shutdown are no longer best-effort behavior disguised as infrastructure.

The current v2 code already has the right architecture shape for this milestone:

- replay staging and chunking exist,
- manifest-style recording exists,
- startup validation exists,
- shutdown/finalization paths exist,
- runtime status exists,
- certification and proof-oriented reporting already exist.

That is the good news.

The bad news is that operational integrity is still not fully closed. Some runtime pressure is still simplified, replay pressure and sink behavior are not yet a complete operational truth system, shutdown safety is not yet a fully declared contract, and the lifecycle still risks drifting into “mostly works” rather than “provably bounded and safe.” That is exactly what Milestone C is supposed to eliminate.

This milestone exists to make these things true:

- startup is strict,
- replay persistence is bounded,
- sink pressure is declared and handled,
- runtime snapshots are truthful and bounded,
- shutdown behavior is explicit and timeout-bounded,
- final authoritative identity is preserved even under non-authoritative persistence trouble,
- and operational truth survives failure without corrupting simulation semantics.

Milestone C is not optional busywork. Without it, later concurrency hardening and real RPG attachment will sit on top of a runtime that still cannot be trusted at the beginning and end of life.

---

## [Milestone technical implementation]

Create one fully declared operational lifecycle contract for engine startup, replay persistence, bounded snapshots, and shutdown integrity.

This milestone must implement these exact rules.

### Operational lifecycle completion rules

1. **Startup must be strict**
   - Invalid config must fail before runtime execution.
   - Unsafe combinations of profile, queue, worker, replay, and observability settings must be rejected explicitly.
   - The runtime must not “try anyway” when a profile or lifecycle contract is invalid.

2. **Replay persistence must be bounded**
   - Replay staging must obey declared memory and item-count limits.
   - Chunk rotation must be explicit and deterministic.
   - Overflow behavior must be explicit.
   - Sink pressure must not silently accumulate unbounded staging.

3. **Manifest integrity must be exact**
   - Replay output must include one explicit index/manifest contract.
   - Chunks must be linked and discoverable deterministically.
   - Missing, partial, or corrupt bundle state must be detectable.

4. **Operational snapshots must be bounded and truthful**
   - Runtime status and lifecycle snapshots must remain bounded.
   - No operational surface may imply certainty where only best-effort exists.
   - Snapshot cadence and retention must be explicit.

5. **Shutdown must be deterministic and timeout-bounded**
   - Finalization order must be explicit.
   - Non-authoritative flushes must have timeout or bounded-attempt behavior.
   - Final authoritative identity must be captured even if observational or persistence layers fail.

6. **Non-authoritative failure must not corrupt authoritative truth**
   - Replay failure,
   - sink failure,
   - manifest write failure,
   - snapshot failure,
   - and flush timeout
     must never silently mutate or corrupt authoritative state.

7. **Lifecycle status must be externally visible**
   - Startup success/failure,
   - replay state,
   - manifest state,
   - finalization state,
   - flush result,
   - and final authoritative checkpoint/hash availability
     must all be surfaced in one declared operational model.

8. **Operational integrity must remain profile-bounded**
   - Replay, snapshots, and shutdown behavior must obey resource envelopes.
   - Operational safety cannot depend on unlimited memory, time, or sink responsiveness.

### Milestone C coverage boundary

9. **What this milestone must cover**
   - startup validation closure,
   - replay staging/rotation/overflow closure,
   - sink-pressure behavior,
   - manifest integrity,
   - bounded runtime snapshot behavior,
   - deterministic shutdown and finalization order,
   - timeout-bounded non-authoritative flush,
   - final authoritative checkpoint/hash persistence,
   - and lifecycle test closure.

10. **Non-goals of this milestone**

- no worker execution deepening,
- no real RPG domain logic,
- no certification scenario expansion beyond lifecycle proof needs,
- no full production observability platform,
- no distributed persistence system,
- no full failure-bundle/reporting framework beyond the lifecycle contract.

11. **Clean-code boundary**

- startup validation validates,
- replay manages bounded persistence state,
- manifest logic records persistence structure,
- runtime status surfaces lifecycle truth,
- shutdown orchestrates closure,
- and authoritative checkpoint identity remains separate from non-authoritative persistence concerns.

---

## [Milestone important notes]

The first trap is treating replay as “just output.” It is not. Replay is one of the easiest ways to reintroduce memory growth, shutdown stalls, and false durability assumptions.

The second trap is letting shutdown remain “best effort.” That language is how systems lose truth right when you need it most.

The third trap is mixing authoritative and non-authoritative finalization. The engine must preserve the final authoritative identity even when replay or sink behavior fails.

The fourth trap is pretending startup validation is a nice-to-have. It is not. A runtime that starts in an invalid configuration is already broken before tick 0.

The fifth trap is building operational status surfaces that sound precise but do not actually tell the truth about replay backlog, flush outcome, manifest completeness, or final hash emission.

---

## [Milestone acceptance criteria]

At the end of Milestone C, the codebase has:

- one exact startup-validation contract,
- one exact replay staging, chunk rotation, and overflow contract,
- one exact sink-pressure handling contract,
- one exact manifest-integrity contract,
- one bounded runtime snapshot/status contract,
- one deterministic shutdown and finalization contract,
- one timeout-bounded non-authoritative flush contract,
- one guaranteed final authoritative checkpoint/hash emission path,
- and one complete lifecycle test suite proving operational integrity.

No worker deepening, full concurrency trust, certification expansion, or real RPG logic attachment is required for Milestone C completion.

---

# ## Task

---

## [ ] (checkbox) - [Task 1] - Freeze the lifecycle and operational integrity law set

### [Task Description]

Create one exact contract for startup validation, replay persistence, runtime snapshots, shutdown order, and finalization truth.

### [Task technical implementation]

Write one Milestone C contract document that defines:

- exact startup validation rules,
- exact replay lifecycle states,
- exact chunk rotation rules,
- exact overflow rules,
- exact sink-pressure behavior,
- exact manifest structure and integrity rules,
- exact runtime snapshot/status rules,
- exact shutdown order,
- exact timeout and bounded-attempt rules,
- exact final authoritative checkpoint/hash rules,
- exact authoritative vs non-authoritative finalization boundaries,
- and exact out-of-scope list.

This document must explicitly define lifecycle states such as:

- not started,
- startup-validating,
- running,
- degraded-running if surfaced,
- replay-backpressured if surfaced,
- shutdown-started,
- flush-in-progress,
- flush-timed-out,
- flush-failed,
- shutdown-complete,
- shutdown-complete-with-non-authoritative-failure.

It must also define:

- what “safe startup” means,
- what “operationally complete shutdown” means,
- what “replay bundle complete” means,
- what “final authoritative identity emitted” means,
- and what failures are allowed without invalidating authoritative truth.

### [Task possible affected files]

- `docs/engine/operational_integrity_contract_mc.md`
- `docs/engine/mc_test_matrix.md`
- startup validation docs
- replay docs
- shutdown docs
- runtime status docs

### [Task important notes]

Do not leave lifecycle semantics implicit across code and tests.
Do not let “best effort” remain undocumented hand-waving.

### [Task check list]

- [ ] Freeze startup-validation law
- [ ] Freeze replay lifecycle law
- [ ] Freeze chunk rotation and overflow law
- [ ] Freeze sink-pressure law
- [ ] Freeze runtime snapshot law
- [ ] Freeze shutdown/finalization law
- [ ] Freeze final authoritative hash/checkpoint law
- [ ] Freeze authoritative/non-authoritative separation
- [ ] Freeze non-goals

### [Task acceptance criteria]

The project has one exact lifecycle and operational integrity contract defining the finished Milestone C law set.

---

## [ ] (checkbox) - [Task 2] - Harden startup validation and unsafe-configuration rejection

### [Task Description]

Make runtime startup strict so invalid operational conditions fail before execution begins.

### [Task technical implementation]

Audit all startup-time configuration and validate at runtime creation or startup boundary:

1. **Profile validation**
   - invalid RAM budget,
   - invalid tick budget,
   - invalid worker count,
   - invalid queue depth,
   - invalid replay budget,
   - invalid observability budget,
   - invalid hardware/profile combinations.

2. **Replay configuration validation**
   - invalid output directory,
   - invalid chunk size or rotation settings,
   - invalid manifest settings,
   - incompatible replay-off vs replay-required conditions.

3. **Operational flag validation**
   - invalid combinations of headless mode, replay mode, monitoring mode, proof mode, and shutdown behavior.
   - reject impossible or contradictory settings explicitly.

4. **Lifecycle boundary validation**
   - startup must fail cleanly before tick execution if any required component cannot enter a valid initial state.

5. **Explicit failure surface**
   - startup failure must return structured reason(s),
   - runtime status must surface startup failure state,
   - and no partial “running” state may be exposed after fatal startup rejection.

### [Task possible affected files]

- `src_v2/config/profiles.py`
- `src_v2/config/validation.py`
- `src_v2/engine/kernel.py`
- `src_v2/replay/replay.py`
- `src_v2/observability/runtime_status.py`
- startup-related tests

### [Task important notes]

Do not move validation into scattered lazy checks after runtime start.
Fail early, fail exactly, fail before tick 0.

### [Task check list]

- [ ] Audit startup configuration inputs
- [ ] Add strict unsafe-combination checks
- [ ] Add replay config validation
- [ ] Add operational-flag validation
- [ ] Add structured startup-failure surface
- [ ] Add startup-status reporting
- [ ] Add startup rejection tests

### [Task acceptance criteria]

Invalid startup conditions are rejected deterministically before runtime execution begins.

---

## [ ] (checkbox) - [Task 3] - Complete bounded replay staging and overflow behavior

### [Task Description]

Turn replay staging from a useful mechanism into a declared bounded persistence contract.

### [Task technical implementation]

Define and implement exact replay staging behavior for:

- pending item count,
- staged bytes or declared approximate size,
- maximum staging budget,
- flush threshold,
- overflow threshold,
- drop behavior,
- backpressure signaling,
- and bundle/chunk lifecycle.

The replay manager must explicitly track:

- staged event count,
- staged bytes or size estimate,
- staged chunk count,
- overflow count,
- dropped event count,
- flush count,
- failed flush count,
- and whether replay is currently pressure-limited.

Define overflow behavior exactly:

- drop newest,
- drop oldest,
- stop recording,
- partial flush attempt,
- or equivalent declared policy.

Then make that policy deterministic and visible in runtime status.

### [Task possible affected files]

- `src_v2/replay/replay.py`
- `src_v2/replay/models.py`
- `src_v2/observability/runtime_status.py`
- replay-related tests

### [Task important notes]

Do not leave replay overflow as an implementation side effect.
It must be one declared law.

### [Task check list]

- [ ] Freeze replay staging budget rules
- [ ] Freeze overflow threshold rules
- [ ] Freeze drop/overflow policy
- [ ] Track staged counts and size
- [ ] Track overflow and drop counters
- [ ] Surface replay pressure state
- [ ] Add replay overflow tests

### [Task acceptance criteria]

Replay staging is fully bounded, overflow behavior is explicit, and pressure state is operationally visible.

---

## [ ] (checkbox) - [Task 4] - Harden chunk rotation and manifest integrity

### [Task Description]

Make replay persistence structurally trustworthy so outputs are discoverable, consistent, and diagnosable.

### [Task technical implementation]

Define and enforce:

1. **Chunk rotation law**
   - what triggers rotation,
   - how chunk IDs/names are assigned,
   - whether chunk order is strictly monotonic,
   - when a chunk becomes final.

2. **Manifest law**
   - manifest format,
   - required fields,
   - chunk list structure,
   - chunk ordering,
   - final authoritative hash/checkpoint reference if available,
   - completion marker,
   - and bundle status markers.

3. **Manifest completeness**
   - partial bundle state must be detectable,
   - missing chunk references must be detectable,
   - incomplete shutdown bundle state must be detectable,
   - and success vs partial-success must be explicit.

4. **Manifest finalization**
   - define when manifest is updated during runtime,
   - define when final manifest write occurs,
   - define what happens if final manifest write fails.

### [Task possible affected files]

- `src_v2/replay/replay.py`
- `src_v2/replay/manifest.py`
- `src_v2/replay/models.py`
- proof-bundle or release-bundle related tests

### [Task important notes]

Do not assume “directory exists” means replay bundle is valid.
Structural integrity must be provable.

### [Task check list]

- [ ] Freeze chunk rotation trigger law
- [ ] Freeze chunk naming/order law
- [ ] Freeze manifest schema
- [ ] Add completion/integrity markers
- [ ] Add partial-bundle detection
- [ ] Add manifest failure semantics
- [ ] Add manifest integrity tests

### [Task acceptance criteria]

Replay chunks and manifest form one exact, checkable, deterministic persistence structure.

---

## [ ] (checkbox) - [Task 5] - Implement real sink-pressure behavior and persistence failure handling

### [Task Description]

Make replay and persistence failure behavior explicit instead of accidental.

### [Task technical implementation]

Define and implement sink-pressure handling for:

- slow sink,
- blocked sink,
- transient sink write failure,
- repeated sink failure,
- manifest write failure,
- flush timeout,
- and shutdown-time final flush failure.

For each case, define:

- whether retries are allowed,
- how many retries or attempts are allowed,
- whether replay continues, degrades, or stops,
- how pressure state is surfaced,
- how counters are updated,
- whether final shutdown remains possible,
- and whether authoritative truth is unaffected.

This task must also define:

- distinction between replay failure and authoritative failure,
- distinction between sink backpressure and buffer overflow,
- distinction between “dropped because bounded” and “failed because sink failed.”

### [Task possible affected files]

- `src_v2/replay/replay.py`
- `src_v2/observability/runtime_status.py`
- `src_v2/governance/governor.py` if replay pressure affects mode
- lifecycle and replay tests

### [Task important notes]

Do not bury sink failure handling in generic exception swallowing.
It must be explicit, counted, and surfaced.

### [Task check list]

- [ ] Freeze sink-pressure semantics
- [ ] Freeze retry/attempt limits
- [ ] Freeze replay-stop/degrade behavior
- [ ] Distinguish sink failure vs bounded drop
- [ ] Surface replay failure state
- [ ] Add sink-pressure and sink-failure tests
- [ ] Preserve authoritative isolation

### [Task acceptance criteria]

Sink-pressure and replay failure behavior are explicit, bounded, and operationally visible without corrupting authoritative truth.

---

## [ ] (checkbox) - [Task 6] - Complete bounded runtime snapshot and operational status lifecycle

### [Task Description]

Make lifecycle monitoring truthful, bounded, and useful for headless/system tests.

### [Task technical implementation]

Define one runtime operational status model that includes lifecycle fields such as:

- startup state,
- startup failure reason,
- runtime state,
- replay pressure state,
- replay drop count,
- replay flush count,
- replay flush failure count,
- manifest state,
- last successful chunk,
- last snapshot tick,
- last authoritative hash,
- shutdown state,
- shutdown flush result,
- shutdown timeout flag,
- finalization completion,
- and partial-success markers.

For each field, define:

- source,
- update cadence,
- cumulative vs instant vs final value,
- reset behavior,
- and whether it is part of lifecycle contract assertions.

Also define one bounded runtime snapshot cadence:

- when snapshots are emitted,
- how many are retained if retained in memory,
- and what happens under snapshot failure.

### [Task possible affected files]

- `src_v2/observability/runtime_status.py`
- `src_v2/observability/signals.py`
- `src_v2/engine/kernel.py`
- `src_v2/replay/replay.py`
- headless/system test helpers

### [Task important notes]

Do not let runtime status drift into a dump of miscellaneous fields.
Keep it small, exact, and operationally meaningful.

### [Task check list]

- [ ] Freeze lifecycle status field set
- [ ] Define source/cadence/reset for each field
- [ ] Freeze snapshot cadence and retention
- [ ] Add bounded snapshot behavior
- [ ] Add lifecycle status truth tests
- [ ] Document status semantics

### [Task acceptance criteria]

The engine exposes one bounded, truthful operational status surface for startup, running, persistence, and shutdown.

---

## [ ] (checkbox) - [Task 7] - Harden deterministic shutdown order and timeout-bounded finalization

### [Task Description]

Turn shutdown from “attempts to clean up” into one declared lifecycle law.

### [Task technical implementation]

Define exact shutdown order, for example:

1. stop accepting new optional/replay work,
2. stop scheduling new non-essential persistence work,
3. complete or cut off bounded runtime snapshot emission,
4. emit final authoritative checkpoint/hash,
5. attempt bounded replay flush/final manifest update,
6. record shutdown result,
7. mark shutdown complete or partial-success.

Then implement explicit timeout/bounded-attempt handling for:

- replay flush,
- manifest write,
- snapshot finalization,
- other non-authoritative cleanup.

The shutdown contract must specify:

- what can time out,
- what cannot block forever,
- what counts as successful shutdown,
- what counts as partial-success shutdown,
- and what final fields must always be emitted if possible.

### [Task possible affected files]

- `src_v2/engine/kernel.py`
- `src_v2/replay/replay.py`
- `src_v2/observability/runtime_status.py`
- shutdown-related tests

### [Task important notes]

Do not let non-authoritative cleanup block shutdown indefinitely.
Do not emit final authoritative identity after risky non-authoritative work if that creates loss risk.

### [Task check list]

- [ ] Freeze shutdown order
- [ ] Freeze timeout/bounded-attempt rules
- [ ] Ensure non-authoritative flush cannot block forever
- [ ] Ensure final status is always recorded
- [ ] Add deterministic shutdown tests
- [ ] Add timeout-shutdown tests
- [ ] Document shutdown law

### [Task acceptance criteria]

Shutdown is deterministic, timeout-bounded, and never relies on unbounded non-authoritative cleanup.

---

## [ ] (checkbox) - [Task 8] - Guarantee final authoritative checkpoint/hash emission under lifecycle failure

### [Task Description]

Ensure the engine preserves authoritative identity even when operational layers are degraded or failing.

### [Task technical implementation]

Define one exact rule for final authoritative emission:

- when final checkpoint/hash is produced,
- where it is recorded,
- whether it is recorded independently of replay success,
- how it is surfaced in runtime status,
- and what happens if replay/manifest finalization fails afterward.

This task must ensure:

1. final authoritative identity is generated before risky non-authoritative closure if needed,
2. authoritative identity is retained even when replay flush fails,
3. final hash/checkpoint reference is included in final lifecycle status,
4. tests prove final authoritative truth survives replay failure and shutdown timeout scenarios.

### [Task possible affected files]

- `src_v2/engine/checkpoint.py`
- `src_v2/engine/kernel.py`
- `src_v2/replay/replay.py`
- `src_v2/observability/runtime_status.py`
- lifecycle and checkpoint tests

### [Task important notes]

Do not make final authoritative truth depend on replay bundle success.
Replay is observational/persistence support, not the source of simulation truth.

### [Task check list]

- [ ] Freeze final authoritative emission rule
- [ ] Decouple final hash/checkpoint from replay success
- [ ] Surface final hash/checkpoint in lifecycle status
- [ ] Add replay-failure survival tests
- [ ] Add shutdown-timeout survival tests
- [ ] Document authoritative finalization law

### [Task acceptance criteria]

Final authoritative checkpoint/hash emission is guaranteed independently of non-authoritative persistence success.

---

## [ ] (checkbox) - [Task 9] - Complete lifecycle fault-handling classification and partial-success semantics

### [Task Description]

Define the exact operational meaning of lifecycle failures so the engine reports truth instead of vague “done with warnings” behavior.

### [Task technical implementation]

Create one lifecycle failure classification covering:

- startup rejection,
- startup partial initialization failure,
- replay overflow,
- replay sink backpressure,
- replay sink write failure,
- manifest write failure,
- snapshot failure,
- shutdown flush timeout,
- shutdown flush failure,
- shutdown completed with non-authoritative loss,
- shutdown completed with authoritative success but replay partial loss.

For each class, define:

- severity,
- whether runtime may continue,
- whether authoritative truth is intact,
- whether replay truth is partial,
- what status flags/counters must be set,
- and what tests must prove it.

Also define explicit **partial-success semantics**, such as:

- authoritative success + replay partial loss,
- authoritative success + manifest incomplete,
- authoritative success + shutdown timeout on non-critical flush,
- startup rejected cleanly with no runtime side effects.

### [Task possible affected files]

- `src_v2/replay/models.py`
- `src_v2/observability/runtime_status.py`
- lifecycle error/status modules
- lifecycle tests
- docs

### [Task important notes]

Do not collapse all lifecycle failures into generic booleans.
Truthful partial-success semantics matter.

### [Task check list]

- [ ] Define lifecycle failure classes
- [ ] Define severity/continuation rules
- [ ] Define authoritative-integrity markers
- [ ] Define replay-integrity markers
- [ ] Define partial-success states
- [ ] Surface classifications in status
- [ ] Add classification tests

### [Task acceptance criteria]

Lifecycle failures and partial-success outcomes are explicit, structured, and operationally visible.

---

## [ ] (checkbox) - [Task 10] - Complete the lifecycle, replay, and shutdown test suite

### [Task Description]

Pin Milestone C with direct operational-lifecycle proof.

### [Task technical implementation]

Complete or add tests for these groups.

### Startup validation tests

- invalid profile rejected before run,
- invalid replay config rejected before run,
- invalid operational flag combinations rejected,
- startup failure produces exact status.

### Replay staging and overflow tests

- bounded staging limit respected,
- overflow behavior follows declared policy,
- dropped counts and pressure flags update correctly,
- rotation happens deterministically.

### Sink-pressure and failure tests

- slow sink creates declared pressure state,
- repeated sink failure updates counters,
- replay stop/degrade behavior follows contract,
- replay failure does not corrupt authoritative state.

### Manifest integrity tests

- chunk list completeness,
- missing chunk detection,
- incomplete finalization detection,
- manifest reflects partial-success vs full-success accurately.

### Shutdown tests

- deterministic shutdown order,
- bounded flush timeout behavior,
- final authoritative hash emitted under replay failure,
- shutdown completion state accurate,
- partial-success semantics accurate.

### Runtime snapshot/status tests

- lifecycle fields update with correct cadence,
- snapshot retention stays bounded,
- final status includes finalization truth,
- non-authoritative failures surface correctly.

### Suggested test groups

- `tests_v2/replay/test_staging_bounds.py`
- `tests_v2/replay/test_rotation_manifest_integrity.py`
- `tests_v2/replay/test_sink_pressure.py`
- `tests_v2/runtime/test_startup_validation.py`
- `tests_v2/runtime/test_shutdown_contract.py`
- `tests_v2/runtime/test_final_authoritative_emission.py`
- `tests_v2/observability/test_lifecycle_status.py`
- `tests_v2/runtime/test_partial_success_semantics.py`

### [Task possible affected files]

- existing replay/runtime/observability tests
- missing new Milestone C lifecycle test modules

### [Task important notes]

Do not rely on broad certification tests to cover this.
Milestone C needs direct lifecycle law proof.

### [Task check list]

- [ ] Add startup validation tests
- [ ] Add replay staging/overflow tests
- [ ] Add sink-pressure tests
- [ ] Add manifest integrity tests
- [ ] Add shutdown order and timeout tests
- [ ] Add final authoritative survival tests
- [ ] Add lifecycle status and partial-success tests

### [Task acceptance criteria]

The lifecycle layer is pinned by a complete replay, startup, shutdown, and operational-integrity test suite.

---

## [ ] (checkbox) - [Task 11] - Refactor lifecycle responsibilities into clean operational boundaries

### [Task Description]

Reduce lifecycle ambiguity so startup, replay, snapshots, and shutdown are not mixed into one hard-to-trust blob.

### [Task technical implementation]

Refactor the operational lifecycle path so responsibilities are explicit:

- startup validation validates configuration and initial readiness,
- replay manager owns bounded staging, flushing, and manifest coordination,
- runtime status owns lifecycle truth exposure,
- kernel orchestrates lifecycle transitions,
- checkpoint logic owns authoritative identity,
- shutdown logic owns ordered finalization and timeout handling.

Ensure that:

- replay does not own authoritative truth,
- runtime status does not recompute lifecycle logic,
- kernel does not absorb detailed sink-handling logic unnecessarily,
- and manifest integrity is not scattered across modules.

### [Task possible affected files]

- `src_v2/engine/kernel.py`
- `src_v2/replay/replay.py`
- `src_v2/replay/manifest.py`
- `src_v2/observability/runtime_status.py`
- `src_v2/engine/checkpoint.py`

### [Task important notes]

Do not build a framework.
Just remove responsibility leakage and lifecycle spaghetti.

### [Task check list]

- [ ] Audit lifecycle responsibility boundaries
- [ ] Centralize replay lifecycle ownership
- [ ] Centralize shutdown sequencing
- [ ] Keep authoritative checkpoint logic isolated
- [ ] Keep runtime-status reporting read-only
- [ ] Preserve deterministic behavior during refactor
- [ ] Document final boundaries

### [Task acceptance criteria]

Milestone C ends with one clean operational lifecycle architecture rather than scattered startup/replay/shutdown logic.

---

## [ ] (checkbox) - [Task 12] - Add exact Milestone C documentation pack

### [Task Description]

Document the finished lifecycle and operational integrity law so later milestones treat Milestone C as completed runtime lifecycle law.

### [Task technical implementation]

Create:

- `docs/engine/operational_integrity_contract_mc.md`
- `docs/engine/mc_test_matrix.md`

`operational_integrity_contract_mc.md` must contain these exact sections:

- Purpose
- Scope of Milestone C
- Startup validation law
- Replay staging and overflow law
- Chunk rotation law
- Manifest integrity law
- Sink-pressure and replay failure law
- Runtime snapshot and lifecycle-status law
- Shutdown and finalization law
- Final authoritative checkpoint/hash law
- Partial-success semantics
- Authoritative vs non-authoritative separation
- Non-goals
- Completion guarantees

`mc_test_matrix.md` must contain these exact sections:

- Startup validation tests
- Replay staging/overflow tests
- Sink-pressure and replay failure tests
- Manifest integrity tests
- Runtime snapshot/lifecycle-status tests
- Shutdown order and timeout tests
- Final authoritative survival tests
- Partial-success semantics tests
- Regression intent

For every test group, document:

- test name or group,
- input condition,
- exact lifecycle rule,
- regression caught,
- whether it is startup, persistence, shutdown, integrity, or partial-success coverage.

### [Task possible affected files]

- `docs/engine/operational_integrity_contract_mc.md`
- `docs/engine/mc_test_matrix.md`

### [Task important notes]

Documentation is implementation here too.
Do not finish Milestone C with only code and green tests.

### [Task check list]

- [ ] Document startup-validation law
- [ ] Document replay lifecycle law
- [ ] Document chunk/manifest integrity law
- [ ] Document sink-pressure law
- [ ] Document lifecycle status law
- [ ] Document shutdown/finalization law
- [ ] Document final authoritative emission law
- [ ] Document partial-success semantics
- [ ] Document exact test matrix

### [Task acceptance criteria]

Milestone C has a complete documentation pack describing the finished operational lifecycle law and its proof matrix.

---

## [ ] (checkbox) - [Task 13] - Add Milestone C regression guardrails

### [Task Description]

Make it hard for lifecycle integrity to silently decay after Milestone C is declared complete.

### [Task technical implementation]

Add project-level guardrails that fail if:

- replay staging becomes unbounded,
- manifest schema drifts from documented integrity rules,
- startup validation tests are skipped or weakened,
- shutdown timeout behavior becomes unbounded,
- final authoritative emission becomes dependent on replay success,
- lifecycle status fields drift from the contract,
- or partial-success semantics disappear into generic booleans.

This can be done with:

- doc-integrity tests,
- replay-bundle integrity tests,
- focused lifecycle CI targets,
- boundedness regression tests,
- and contract-consistency tests for lifecycle status and manifest fields.

### [Task possible affected files]

- `tests_v2/docs/*`
- `tests_v2/runtime/test_mc_doc_integrity.py`
- `tests_v2/replay/test_manifest_schema_integrity.py`
- CI config
- integrity helpers

### [Task important notes]

Do not create process theater.
Just make lifecycle regression visible and cheap to catch.

### [Task check list]

- [ ] Add lifecycle doc/test integrity checks
- [ ] Add focused lifecycle CI target
- [ ] Add replay-boundedness guard
- [ ] Add final-authoritative-emission guard
- [ ] Add manifest schema integrity guard
- [ ] Record Milestone C completion gate

### [Task acceptance criteria]

Milestone C cannot silently regress without failing tests or integrity checks.

---

# [Recommended execution order inside Milestone C]

1. Task 1 — Freeze the lifecycle law set
2. Task 2 — Harden startup validation
3. Task 3 — Complete bounded replay staging
4. Task 4 — Harden chunk rotation and manifest integrity
5. Task 5 — Implement sink-pressure behavior
6. Task 6 — Complete runtime snapshot/lifecycle status
7. Task 7 — Harden shutdown order and timeouts
8. Task 8 — Guarantee final authoritative emission
9. Task 9 — Define lifecycle failure classes and partial-success semantics
10. Task 10 — Complete the lifecycle test suite
11. Task 11 — Refactor lifecycle boundaries
12. Task 12 — Finalize docs
13. Task 13 — Add guardrails

This order matters because it follows dependency reality:

- first define the lifecycle law,
- then stop invalid startup,
- then bound persistence,
- then make persisted structure trustworthy,
- then make sink failure explicit,
- then surface lifecycle truth,
- then make shutdown safe,
- then preserve final authoritative identity,
- then define failure meaning,
- then pin everything with tests,
- then clean structure,
- then lock docs and guardrails.

---

# [Milestone C done-means-done gate]

Milestone C is done only when all of these are true:

- invalid startup conditions fail before tick 0,
- replay staging is bounded and overflow behavior is explicit,
- chunk rotation and manifest integrity are deterministic and checkable,
- sink-pressure and replay failure behavior are explicit,
- lifecycle status is truthful and bounded,
- shutdown order is exact and timeout-bounded,
- final authoritative checkpoint/hash survives replay or flush failure,
- partial-success semantics are explicit and surfaced,
- docs and tests describe the same lifecycle law,
- and CI can catch lifecycle integrity regression.
