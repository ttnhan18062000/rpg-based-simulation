# [Milestone 2] - Attach Gate 1: Deterministic Grid Movement as the First Official RPG Slice

## [Milestone Description]

Milestone 2 is the first official gameplay milestone for `src_v2`.

Its purpose is to make deterministic **grid movement** the first officially supported RPG-core slice in the new engine.

Movement is chosen first because it is:

- visible in authoritative state,
- narrow enough to reason about,
- foundational to the original `src` RPG loop,
- appropriate for parity validation against original `src`,
- suitable for lifecycle/replay/certification coverage,
- and appropriate for supported concurrent execution within declared bounds.

This milestone is not about movement merely existing.
It is about movement becoming the first **officially supported gameplay slice**.

This movement slice must preserve the old RPG meaning of movement rather than introducing a generic movement abstraction.

## [Milestone technical implementation]

Create one first-class movement feature pack spanning:

- original behavior capture,
- V2 state/work/apply contract,
- local reference execution,
- supported concurrent execution where declared,
- replay and runtime visibility,
- lifecycle safety,
- parity validation,
- and certification.

This milestone must not:

- widen into combat,
- widen into broad pathfinding architecture,
- widen into AI decision trees,
- bundle several gameplay systems together,
- or silently replace tile/grid movement with float-based displacement semantics.

The movement slice must preserve or explicitly account for these old-`src` semantics where required:

- tile/grid position meaning,
- orthogonal / Manhattan movement rules,
- blocked occupancy handling,
- no silent diagonal expansion,
- no silent float drift,
- movement success / blocked / no-op semantics,
- and any movement cost or readiness behavior that is intentionally preserved.

## [Milestone important notes]

This milestone sets the pattern for every later gameplay slice.

If this slice is sloppy, later slices will be sloppier.
If this slice is disciplined, later slices can stay disciplined.

## [Milestone acceptance criteria]

At the end of this milestone:

- deterministic grid movement is officially supported,
- original behavior is preserved where intended,
- divergences are explicit where intended,
- the local movement path is authoritative,
- supported concurrent movement is explicit and proven where allowed,
- and movement is visible to replay, runtime status, and certification.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the exact scope of the first supported movement slice

#### [Task Description]

Define exactly what “movement” means in this first official attach gate.

#### [Task technical implementation]

Scope movement narrowly:

- movement intent shape,
- valid move execution,
- blocked move handling,
- readiness or cost behavior if applicable,
- authoritative position mutation,
- supported local path,
- supported concurrent path if allowed,
- tile/grid semantics,
- and occupancy / Manhattan constraints.

Exclude:

- combat,
- path planning graphs,
- terrain system explosion,
- formation AI,
- and derived movement systems not needed for the first slice.

#### [Task possible affected files]

- movement design docs
- `docs/engine/attach_gate1_movement_scope.md`
- scheduler/work docs

#### [Task important notes]

The first slice succeeds by being narrow.

#### [Task check list]

- [ ] Included behavior is explicit
- [ ] Excluded behavior is explicit
- [ ] Support boundary is narrow
- [ ] Both local and concurrent expectations are scoped
- [ ] Tile/grid and occupancy semantics are explicit
- [ ] Later movement complexity is left out intentionally

#### [Task acceptance criteria]

Movement scope is explicit enough that implementation and parity work cannot drift.

---

### [ ] (checkbox) - [Task 2] - Capture original `src` movement behavior through characterization tests or scenario fixtures

#### [Task Description]

Use original `src` as the temporary behavior oracle for movement.

#### [Task technical implementation]

Capture:

- normal movement,
- blocked movement,
- edge conditions,
- deterministic movement outcomes,
- tile/grid outcomes,
- occupancy constraints,
- and any legacy behavior that should or should not be preserved.

Use characterization tests or scenario fixtures to document old movement behavior before the V2 slice is finalized.

#### [Task possible affected files]

- `tests/` or comparison harness against original `src`
- movement characterization fixtures
- divergence log

#### [Task important notes]

Do not rewrite movement from memory.

#### [Task check list]

- [ ] Normal cases captured
- [ ] Edge cases captured
- [ ] Invalid/blocked cases captured
- [ ] Tile/grid semantics captured
- [ ] Occupancy semantics captured
- [ ] Old behavior oracle exists
- [ ] Non-preserved behavior is explicitly noted

#### [Task acceptance criteria]

Original movement behavior is captured well enough to support parity review during the port.

---

### [ ] (checkbox) - [Task 3] - Define the V2 authoritative state, work contract, and apply contract for movement

#### [Task Description]

Map movement into native `src_v2` contract terms.

#### [Task technical implementation]

Define:

- what authoritative fields movement reads,
- what work items represent movement,
- what movement inputs are legal,
- what movement outputs are legal,
- what apply-path mutation is allowed,
- and what counts as movement success, block, or no-op.

Ensure this contract preserves tile/grid semantics rather than drifting into generic displacement.

#### [Task possible affected files]

- `src_v2/core/state.py`
- `src_v2/core/work.py`
- `src_v2/core/updates.py`
- movement contract docs

#### [Task important notes]

Do not port old runtime assumptions directly.
Port behavior into V2 contracts.

#### [Task check list]

- [ ] Authoritative movement inputs are explicit
- [ ] Movement work item shape is explicit
- [ ] Movement update shape is explicit
- [ ] Blocked/no-op semantics are explicit
- [ ] Apply-path expectations are explicit
- [ ] Tile/grid meaning is preserved in the contract

#### [Task acceptance criteria]

Movement is fully expressed in native `src_v2` contract terms.

---

### [ ] (checkbox) - [Task 4] - Implement or finalize the local movement reference path in `src_v2`

#### [Task Description]

Make local movement execution the semantic source of truth for the movement slice.

#### [Task technical implementation]

Implement the local reference path for:

- deterministic movement resolution,
- authoritative movement update generation,
- blocked move handling,
- tile/grid transition rules,
- occupancy-aware resolution,
- and movement cost behavior.

Ensure this path is the reference used for parity and equivalence proof.

#### [Task possible affected files]

- movement execution modules
- `src_v2/engine/kernel.py`
- local movement tests

#### [Task important notes]

Local movement must come first.
Concurrent movement cannot define movement semantics.

#### [Task check list]

- [ ] Local path is complete
- [ ] Deterministic movement behavior is implemented
- [ ] Blocked move behavior is explicit
- [ ] Tile/grid semantics are implemented
- [ ] Outputs are apply-path compatible
- [ ] Local path is tested directly

#### [Task acceptance criteria]

The local movement path defines the authoritative semantics of the first gameplay slice.

---

### [ ] (checkbox) - [Task 5] - Implement or finalize the supported concurrent movement path for declared safe scope

#### [Task Description]

Provide supported concurrent movement only where it is explicitly safe and proven.

#### [Task technical implementation]

Implement or finalize:

- movement packet generation,
- movement worker execution,
- movement result validation,
- deterministic authoritative commit order,
- and local fallback where needed.

Keep support scope narrow and explicit.

#### [Task possible affected files]

- `src_v2/engine/worker_manager.py`
- movement worker modules
- packet/result validation tests
- concurrency docs

#### [Task important notes]

Do not broaden concurrency support in this milestone.
Movement concurrency is only valid where already declared safe.

#### [Task check list]

- [ ] Concurrent movement scope is explicit
- [ ] Packet and result flow is explicit
- [ ] Fallback behavior is explicit
- [ ] Commit order remains deterministic
- [ ] Concurrent movement is tested against local semantics
- [ ] Concurrent movement does not weaken tile/grid semantics

#### [Task acceptance criteria]

Supported concurrent movement exists only within declared safe scope and remains subordinate to the local movement semantics.

---

### [ ] (checkbox) - [Task 6] - Integrate movement into replay, runtime visibility, and certification surfaces

#### [Task Description]

Make movement visible across the engine truth surfaces.

#### [Task technical implementation]

Integrate movement into:

- replay/tracing where appropriate,
- runtime status/observability where useful,
- and certification evidence where movement scenarios depend on it.

Do not add vanity telemetry.
Only surface what is necessary for truth, debugging, and proof.

#### [Task possible affected files]

- replay modules
- runtime status modules
- certification harness/recorder/scenarios
- movement observability docs

#### [Task important notes]

Movement must not be “invisible gameplay.”
If it is officially supported, it must be visible to the truth surfaces.

#### [Task check list]

- [ ] Replay visibility exists
- [ ] Runtime visibility is sufficient
- [ ] Certification can observe the slice
- [ ] No unnecessary telemetry clutter was introduced
- [ ] Visibility remains bounded

#### [Task acceptance criteria]

Movement is visible enough across replay/runtime/certification that the slice can be debugged, audited, and certified.

---

### [ ] (checkbox) - [Task 7] - Add parity, equivalence, lifecycle, and certification tests for movement

#### [Task Description]

Prove that the movement slice is real, preserved where required, and lawful in V2.

#### [Task technical implementation]

Add:

- parity tests vs original `src` where required,
- local movement contract tests,
- local-vs-concurrent equivalence tests where supported,
- lifecycle safety tests,
- replay/proof-related movement tests,
- and certification scenarios for movement.

#### [Task possible affected files]

- movement test modules
- certification test modules
- lifecycle tests
- equivalence tests

#### [Task important notes]

Movement is not done because it executes.
It is done because it is proven.

#### [Task check list]

- [ ] Parity tests exist where needed
- [ ] Local contract tests exist
- [ ] Equivalence tests exist where needed
- [ ] Lifecycle tests exist
- [ ] Certification scenarios exist
- [ ] Tile/grid semantics are directly pinned by tests

#### [Task acceptance criteria]

Movement is pinned by direct proof across behavior preservation, V2 contract law, lifecycle, and certification.

---

### [ ] (checkbox) - [Task 8] - Declare movement as the first officially supported RPG slice and publish its support boundary

#### [Task Description]

Make the first gameplay attach gate official.

#### [Task technical implementation]

Publish:

- what movement support means,
- what profiles/execution modes/scenarios it is supported under,
- what grid/tile rules are part of support,
- what is still excluded,
- and what known limitations remain.

#### [Task possible affected files]

- `docs/engine/attach_gate1_movement_support.md`
- support surface docs
- certification matrix docs
- divergence log

#### [Task important notes]

The point is not to say “movement works.”
The point is to say exactly what movement support means now.

#### [Task check list]

- [ ] Support scope is documented
- [ ] Execution mode support is documented
- [ ] Grid/tile semantics are documented
- [ ] Known limitations are documented
- [ ] Divergences are documented
- [ ] Official support is reviewable

#### [Task acceptance criteria]

Movement becomes the first explicitly supported gameplay slice in V2.
