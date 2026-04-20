# [Milestone 2] - Supported Town Resource Resolution Core

## [Milestone Description]

Milestone 2 is the first gameplay expansion of Phase 5.

Its purpose is to recover the town side of the resource progression loop.

The current branch already has stronger world-side interaction behavior, but the game is not restored just because actors can gather and carry value.

The original `src` routes gathered value through town systems that:

- resolve inventory pressure,
- transform material state,
- produce or clear blocker conditions,
- and create the next progression step.

This milestone restores the first bounded official version of that loop in `src_v2`.

## [Milestone technical implementation]

Create one town resource-resolution slice in native `src_v2` contract terms.

This milestone must complete the following areas:

1. **Town-entry resolution contract**
   - what happens automatically on town entry,
   - what requires explicit action,
   - what is preserved,
   - and what is not yet supported.

2. **Supported shop behavior**
   - what can be sold,
   - what can be bought if Phase 5 supports buying at all,
   - and what value conversion rules exist.

3. **Supported blacksmith behavior**
   - what material or gold blockers are recognized,
   - what limited crafting or upgrade behavior is supported,
   - and where scope stops.

4. **Inventory-to-progression truth**
   - how inventory changes,
   - how gold/material outcomes are represented,
   - what is consumed or retained,
   - and what counts as success or no-op.

This milestone must not widen into:

- generalized economy simulation,
- rich price markets,
- full crafting trees,
- or broad service AI.

## [Milestone important notes]

The trap here is replacing the original town loop with a shallow convenience mechanism and then pretending the port is still faithful.

This milestone succeeds only if town becomes a meaningful part of the supported progression loop.

## [Milestone acceptance criteria]

At the end of Milestone 2:

- supported town-entry resolution is explicit,
- supported shop behavior is explicit,
- supported blacksmith behavior is explicit,
- inventory-to-progression behavior is explicit,
- preserved vs divergent original behavior is declared,
- and the town slice is visible to replay, lifecycle, and proof surfaces where relevant.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the exact scope of the supported town resource-resolution slice

#### [Task Description]

Define exactly what town resource resolution means in Phase 5.

#### [Task technical implementation]

Freeze the slice narrowly.

Include only the behaviors that are necessary to recover the next progression step, such as:

- town-entry resource resolution,
- selling supported items/materials,
- limited blacksmith material handling,
- and blocker-clearing or blocker-emission where directly tied to supported scope.

Exclude:

- generalized service behavior,
- full equipment economy,
- broad blocker-clearing or blocker-emission where directly tied to supported scope.

Exclude:

- generalized service behavior,
- full equipment economy,
- broad item categories,
- dynamic pricing,
- and unsupported crafting complexity.

#### [Task possible affected files]

- `docs/engine/phase5_town_resolution_scope.md`
- support boundary docs
- progression design docs

#### [Task important notes]

A vague town slice will explode into fake economy scope.

#### [Task check list]

- [ ] Included behavior is explicit
- [ ] Excluded behavior is explicit
- [ ] Support boundary is narrow
- [ ] Town-entry semantics are explicit
- [ ] Blacksmith/shop scope is explicit

#### [Task acceptance criteria]

The supported town-resolution slice is narrow enough to implement and prove without drift.

---

### [ ] (checkbox) - [Task 2] - Capture original `src` town/shop/blacksmith behavior for supported cases through characterization tests or fixtures

#### [Task Description]

Use original `src` as the behavior oracle for the supported town cases.

#### [Task technical implementation]

Capture old behavior for:

- selling supported materials/items,
- blacksmith-related material or gold blockers,
- supported resolution outcomes on town visit,
- and any supported no-op or failure cases.

Document which old behavior is intentionally not preserved in this phase.

#### [Task possible affected files]

- original `src` comparison fixtures
- `tests_v2/parity/test_town_resolution_parity.py`
- divergence log
- town characterization docs

#### [Task important notes]

Do not rebuild town semantics from memory.

#### [Task check list]

- [ ] Supported old behavior is captured
- [ ] Normal cases are captured
- [ ] Failure/no-op cases are captured
- [ ] Non-preserved behavior is noted
- [ ] Fixtures are reusable for differential proof

#### [Task acceptance criteria]

Supported town behavior is captured well enough to drive parity review during implementation.

---

### [ ] (checkbox) - [Task 3] - Define the V2 authoritative state, work contract, and apply contract for supported town resolution

#### [Task Description]

Map town resource resolution into native `src_v2` terms.

#### [Task technical implementation]

Define:

- what authoritative state town resolution reads,
- what work items represent supported town actions,
- what updates are emitted,
- how gold/material/blocker changes are represented,
- and what counts as success, blocked, or no-op behavior.

Keep authoritative mutation singular in the apply path.

#### [Task possible affected files]

- `src_v2/core/state.py`
- `src_v2/core/work.py`
- `src_v2/core/updates.py`
- town resolution modules
- town contract docs

#### [Task important notes]

Do not sneak town mutation through helper shortcuts.

#### [Task check list]

- [ ] Inputs are explicit
- [ ] Work item shape is explicit
- [ ] Update shape is explicit
- [ ] Success/no-op semantics are explicit
- [ ] Apply-path ownership is explicit

#### [Task acceptance criteria]

Town resolution is fully expressed in native `src_v2` authoritative contract terms.

---

### [ ] (checkbox) - [Task 4] - Implement or finalize the local reference path for town-entry resource resolution

#### [Task Description]

Make local town resolution the semantic source of truth.

#### [Task technical implementation]

Implement or finalize the local path for:

- supported sell conversion,
- material handling,
- limited blocker clearing or emission,
- and inventory state transitions on town resolution.

This local path must become the reference for later differential and equivalence proof.

#### [Task possible affected files]

- `src_v2/systems/town_resolution.py`
- `src_v2/engine/kernel.py`
- local gameplay tests
- progression loop fixtures

#### [Task important notes]

Local town semantics must exist before any broader execution-mode support is claimed.

#### [Task check list]

- [ ] Local path is complete for supported cases
- [ ] Inventory transitions are explicit
- [ ] Gold/material outcomes are explicit
- [ ] Blockers are handled explicitly
- [ ] Local path is tested directly

#### [Task acceptance criteria]

The local town-resolution path defines the supported semantics of the town slice.

---

### [ ] (checkbox) - [Task 5] - Implement the supported shop and blacksmith behavior for the declared narrow scope

#### [Task Description]

Recover the first meaningful town service behavior needed for progression.

#### [Task technical implementation]

Implement supported behavior such as:

- selling supported materials/items,
- limited blacksmith resolution of material/gold requirements,
- limited crafted or upgraded outputs where officially in scope,
- and clear blocked/no-op behavior when requirements are not met.

Keep the scope small and explicit.

#### [Task possible affected files]

- `src_v2/systems/shop.py`
- `src_v2/systems/blacksmith.py`
- town progression helpers
- gameplay tests

#### [Task important notes]

Do not smuggle in a whole economy while claiming the slice is narrow.

#### [Task check list]

- [ ] Shop behavior is explicit
- [ ] Blacksmith behavior is explicit
- [ ] Requirement checks are explicit
- [ ] Blocked/no-op behavior is explicit
- [ ] Scope remains narrow

#### [Task acceptance criteria]

The supported town service behavior is implemented for the declared narrow progression scope.

---

### [ ] (checkbox) - [Task 6] - Integrate town resolution into replay, runtime visibility, and certification surfaces where needed

#### [Task Description]

Make the supported town slice visible to the truth surfaces.

#### [Task technical implementation]

Integrate town-resolution events and outcomes into:

- replay where needed for debugging or proof,
- runtime visibility where useful,
- and certification/benchmark scenario outputs where town progression is part of the supported loop.

Avoid vanity telemetry.

#### [Task possible affected files]

- replay modules
- runtime visibility modules
- certification scenario definitions
- observability docs

#### [Task important notes]

Official gameplay cannot stay invisible to the proof surfaces.

#### [Task check list]

- [ ] Replay visibility exists where needed
- [ ] Runtime visibility is sufficient
- [ ] Certification can observe supported town behavior
- [ ] Visibility remains bounded
- [ ] No unnecessary clutter was added

#### [Task acceptance criteria]

Town resource resolution is visible enough across replay/runtime/certification to support debugging and proof.

---

### [ ] (checkbox) - [Task 7] - Add parity, contract, lifecycle, and certification tests for town resource resolution

#### [Task Description]

Prove the town slice is real, lawful, and preserved where required.

#### [Task technical implementation]

Add:

- old-vs-new parity tests for supported town cases,
- direct contract tests for local town behavior,
- lifecycle tests where town behavior interacts with shutdown/replay,
- and certification scenarios where town behavior is part of supported progression.

#### [Task possible affected files]

- `tests_v2/gameplay/test_town_resolution_contract.py`
- `tests_v2/parity/test_town_resolution_parity.py`
- lifecycle tests
- certification tests

#### [Task important notes]

Town behavior is not done because it executes.
It is done because it is proven.

#### [Task check list]

- [ ] Parity tests exist
- [ ] Local contract tests exist
- [ ] Lifecycle tests exist where relevant
- [ ] Certification scenarios exist
- [ ] Failures are visible in normal validation

#### [Task acceptance criteria]

Town resource resolution is pinned by proof across preservation, contract law, and certification surfaces.

---

### [ ] (checkbox) - [Task 8] - Declare the support boundary and intentional divergences for the town resource-resolution slice

#### [Task Description]

Make the town slice official and reviewable.

#### [Task technical implementation]

Publish:

- what the supported town slice includes,
- what execution conditions it supports,
- what remains excluded,
- and what intentional divergences from original `src` remain.

#### [Task possible affected files]

- `docs/engine/phase5_town_resolution_support.md`
- support surface docs
- divergence log
- certification matrix docs

#### [Task important notes]

The point is not “town works.”
The point is “this is exactly what town support means now.”

#### [Task check list]

- [ ] Support scope is documented
- [ ] Conditions are documented
- [ ] Exclusions are documented
- [ ] Divergences are documented
- [ ] Official support is reviewable

#### [Task acceptance criteria]

The supported town resource-resolution slice is declared explicitly with honest boundaries.
