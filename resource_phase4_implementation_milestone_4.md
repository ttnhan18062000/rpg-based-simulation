# [Milestone 4] - Second Supported RPG Slice: Deterministic Resource Interaction Core

## [Milestone Description]

Milestone 4 widens the supported gameplay surface beyond movement, but still in a controlled way.

Its purpose is to add the second narrow RPG-core slice after movement has already been attached and benchmarked.

The second slice is **not** a generic interaction system.
It is the deterministic resource interaction core that preserves the original `src` gameplay loop.

That means this milestone focuses on:

- channeled looting,
- channeled harvesting,
- resource-node interaction,
- inventory slot and weight pressure,
- loot/harvest abort semantics,
- and the smallest authoritative resource-loop surface needed to preserve the old game’s progression path.

This milestone exists to prove that the V2 porting pattern is repeatable and not just lucky for movement.

## [Milestone technical implementation]

Create one second supported RPG-core slice that is:

- native to the V2 contract,
- validated against original intended behavior where relevant,
- local-first in semantic meaning,
- explicitly scoped for concurrent support if allowed,
- and covered by lifecycle, replay, and certification proof.

This milestone must preserve discipline.
It is not yet the right time for:

- broad combat,
- quest systems,
- rich AI trees,
- broad crafting webs,
- or full town-economy resolution.

This milestone must preserve or explicitly account for these original resource-loop semantics where required:

- progress-based looting,
- progress-based harvesting,
- blocked or aborted looting when inventory constraints are hit,
- slot and weight inventory constraints,
- resource-node availability and depletion semantics,
- and any narrow respawn or regeneration rules that are part of the old intended loop.

This milestone must not silently collapse all of that into “pickup/use.”

## [Milestone important notes]

The danger here is greed.

Once movement works, teams usually want to add everything.
That is how discipline collapses.

This milestone is successful only if it proves that the supported gameplay surface can widen without losing trust standards.

## [Milestone acceptance criteria]

At the end of this milestone:

- a deterministic resource interaction core is officially supported,
- the slice is ported into `src_v2` natively,
- parity and divergence rules are explicit,
- runtime/lifecycle/certification behavior are covered,
- and the engine now supports more than one gameplay slice under the V2 contract without drifting into a different game.

---

## Task

### [ ] (checkbox) - [Task 1] - Select and freeze the exact scope of the resource interaction slice

#### [Task Description]

Define exactly what belongs inside the second official gameplay slice.

#### [Task technical implementation]

Scope the slice narrowly around:

- looting intent shape,
- harvesting intent shape,
- loot/harvest progress tracking,
- resource-node availability,
- inventory slot constraints,
- inventory weight constraints,
- blocked or aborted looting semantics,
- and authoritative success / blocked / no-op outcomes.

Exclude:

- broad crafting systems,
- full town service resolution,
- complex item-affix systems,
- quest-driven interaction trees,
- and generic “use anything” interaction architecture.

#### [Task possible affected files]

- `docs/engine/attach_gate2_resource_scope.md`
- resource interaction design docs
- scheduler/work docs

#### [Task important notes]

This slice succeeds by preserving the old resource loop narrowly, not by inventing a general interaction framework.

#### [Task check list]

- [ ] Included behavior is explicit
- [ ] Excluded behavior is explicit
- [ ] Support boundary is narrow
- [ ] Inventory pressure semantics are explicit
- [ ] Loot/harvest progress semantics are explicit

#### [Task acceptance criteria]

The resource interaction scope is explicit enough that implementation and parity work cannot drift.

---

### [ ] (checkbox) - [Task 2] - Capture original `src` resource interaction behavior using characterization tests or fixtures

#### [Task Description]

Use original `src` as the behavior oracle for the second slice.

#### [Task technical implementation]

Capture:

- normal looting,
- normal harvesting,
- loot/harvest progress cases,
- blocked or aborted looting,
- inventory-full edge cases,
- slot-limit and weight-limit behavior,
- resource depletion behavior,
- and any legacy behavior that should or should not be preserved.

Use characterization tests or scenario fixtures to document old behavior before the V2 slice is finalized.

#### [Task possible affected files]

- `tests/` or comparison harness against original `src`
- resource characterization fixtures
- divergence log

#### [Task important notes]

Do not invent this slice from design taste.
The old engine already tells you what the core loop is.

#### [Task check list]

- [ ] Normal cases captured
- [ ] Edge cases captured
- [ ] Invalid/blocked cases captured
- [ ] Slot-limit behavior captured
- [ ] Weight-limit behavior captured
- [ ] Resource depletion behavior captured
- [ ] Old behavior oracle exists
- [ ] Non-preserved behavior is explicitly noted

#### [Task acceptance criteria]

Original resource interaction behavior is captured well enough to support parity review during the port.

---

### [ ] (checkbox) - [Task 3] - Define the V2 authoritative state and work contract for resource interaction

#### [Task Description]

Map resource interaction into native `src_v2` contract terms.

#### [Task technical implementation]

Define:

- what authoritative fields resource interaction reads,
- what work items represent looting and harvesting,
- what progress state is authoritative,
- what inventory constraints are authoritative,
- what legal updates exist for loot/harvest success, block, abort, or no-op,
- and what resource-node mutations are allowed through the apply path.

#### [Task possible affected files]

- `src_v2/core/state.py`
- `src_v2/core/work.py`
- `src_v2/core/updates.py`
- resource contract docs

#### [Task important notes]

Do not port old runtime structure directly.
Port the old gameplay meaning into V2 contracts.

#### [Task check list]

- [ ] Authoritative inputs are explicit
- [ ] Work item shape is explicit
- [ ] Progress state shape is explicit
- [ ] Inventory constraint semantics are explicit
- [ ] Resource-node mutation rules are explicit
- [ ] Success/block/abort/no-op semantics are explicit

#### [Task acceptance criteria]

The resource interaction slice is fully expressed in native `src_v2` contract terms.

---

### [ ] (checkbox) - [Task 4] - Implement the local reference execution path for channeled looting and harvesting

#### [Task Description]

Make local execution the semantic source of truth for the second slice.

#### [Task technical implementation]

Implement the local reference path for:

- deterministic loot progress,
- deterministic harvest progress,
- blocked and aborted behavior,
- inventory-pressure handling,
- resource-node consumption or depletion behavior,
- and authoritative update generation compatible with the apply path.

#### [Task possible affected files]

- resource execution modules
- `src_v2/engine/kernel.py`
- local resource tests

#### [Task important notes]

Local execution must define the slice.
Concurrent execution cannot define the semantics.

#### [Task check list]

- [ ] Local path is complete
- [ ] Progress-based behavior is implemented
- [ ] Blocked/abort behavior is explicit
- [ ] Inventory pressure is enforced
- [ ] Outputs are apply-path compatible
- [ ] Local path is tested directly

#### [Task acceptance criteria]

The local resource interaction path defines the authoritative semantics of the second gameplay slice.

---

### [ ] (checkbox) - [Task 5] - Implement the supported concurrent path for resource interaction if explicitly allowed

#### [Task Description]

Provide supported concurrent resource interaction only where it is explicitly safe and proven.

#### [Task technical implementation]

Implement or finalize:

- resource interaction packet generation,
- worker execution,
- result validation,
- deterministic authoritative commit order,
- and local fallback where needed.

Keep support scope narrow and explicit.

#### [Task possible affected files]

- `src_v2/engine/worker_manager.py`
- resource worker modules
- packet/result validation tests
- concurrency docs

#### [Task important notes]

Do not broaden concurrency support in this milestone.
Resource interaction concurrency is only valid where already declared safe.

#### [Task check list]

- [ ] Concurrent support scope is explicit
- [ ] Packet and result flow is explicit
- [ ] Fallback behavior is explicit
- [ ] Commit order remains deterministic
- [ ] Concurrent behavior is tested against local semantics
- [ ] Concurrency does not weaken inventory/resource semantics

#### [Task acceptance criteria]

Supported concurrent resource interaction exists only within declared safe scope and remains subordinate to local semantics.

---

### [ ] (checkbox) - [Task 6] - Integrate resource interaction into engine visibility, replay, and certification surfaces

#### [Task Description]

Make the second slice visible across the engine truth surfaces.

#### [Task technical implementation]

Integrate resource interaction into:

- replay/tracing where appropriate,
- runtime status/observability where useful,
- and certification evidence where resource scenarios depend on it.

Do not add vanity telemetry.
Only surface what is necessary for truth, debugging, and proof.

#### [Task possible affected files]

- replay modules
- runtime status modules
- certification harness/recorder/scenarios
- resource observability docs

#### [Task important notes]

Official gameplay must not be invisible.
If the slice is supported, the truth surfaces must show enough to debug and certify it.

#### [Task check list]

- [ ] Replay visibility exists
- [ ] Runtime visibility is sufficient
- [ ] Certification can observe the slice
- [ ] No unnecessary telemetry clutter was introduced
- [ ] Visibility remains bounded

#### [Task acceptance criteria]

Resource interaction is visible enough across replay/runtime/certification that the slice can be debugged, audited, and certified.

---

### [ ] (checkbox) - [Task 7] - Add parity, contract, lifecycle, and certification tests for the resource interaction slice

#### [Task Description]

Prove that the second slice is real, preserved where required, and lawful in V2.

#### [Task technical implementation]

Add:

- parity tests vs original `src` where required,
- local contract tests,
- local-vs-concurrent equivalence tests where supported,
- lifecycle safety tests,
- replay/proof-related resource tests,
- and certification scenarios for the resource interaction slice.

#### [Task possible affected files]

- resource test modules
- certification test modules
- lifecycle tests
- equivalence tests

#### [Task important notes]

This slice is not done because it runs.
It is done because it is proven.

#### [Task check list]

- [ ] Parity tests exist where needed
- [ ] Local contract tests exist
- [ ] Equivalence tests exist where needed
- [ ] Lifecycle tests exist
- [ ] Certification scenarios exist
- [ ] Inventory/resource semantics are directly pinned by tests

#### [Task acceptance criteria]

The resource interaction slice is pinned by direct proof across behavior preservation, V2 contract law, lifecycle, and certification.

---

### [ ] (checkbox) - [Task 8] - Declare the support boundary for the resource interaction slice and publish any intentional divergences from original `src`

#### [Task Description]

Make the second gameplay attach gate official.

#### [Task technical implementation]

Publish:

- what resource interaction support means,
- what profiles/execution modes/scenarios it is supported under,
- what inventory/resource semantics are part of support,
- what is still excluded,
- and what known limitations remain.

#### [Task possible affected files]

- `docs/engine/attach_gate2_resource_support.md`
- support surface docs
- certification matrix docs
- divergence log

#### [Task important notes]

The point is not to say “interaction works.”
The point is to say exactly what resource interaction support means now.

#### [Task check list]

- [ ] Support scope is documented
- [ ] Execution mode support is documented
- [ ] Inventory/resource semantics are documented
- [ ] Known limitations are documented
- [ ] Divergences are documented
- [ ] Official support is reviewable

#### [Task acceptance criteria]

Deterministic resource interaction becomes the second explicitly supported gameplay slice in V2.
