# [Milestone 3] - Strategic Resource Intelligence and Blocker/Lead Recovery

## [Milestone Description]

Milestone 3 restores the first strategic feedback layer necessary for the RPG progression loop.

The original `src` does not leave resource resolution isolated.
Town and resource state produce new needs, hints, and targets.

This milestone recovers the part of strategy that is necessary for resource progression continuity, not all strategic AI.

It exists so the game loop becomes:

- gather,
- return,
- resolve,
- generate next need,
- seek next target,
- repeat.

Without this milestone, the progression loop still feels mechanical and disconnected.

## [Milestone technical implementation]

Create one bounded strategic resource-intelligence slice.

This milestone must cover:

1. **Supported blocker emission**
   - material blockers,
   - gold blockers,
   - capability blockers if narrowly required by supported scope.

2. **Supported hint and lead generation**
   - resource hints,
   - location hints,
   - zone hints,
   - or other bounded intelligence outputs directly tied to supported progression.

3. **Loop integration**
   - define how blockers/hints/leads feed future supported actions,
   - without widening into broad planning systems.

This milestone must not widen into:

- rich long-horizon strategic planning,
- full project systems,
- broad social AI,
- or generalized concern graphs.

## [Milestone important notes]

The trap here is calling a few hints “strategy restored.”

That is false.

This milestone is only about restoring the strategic outputs needed to make the supported resource loop feel like the same RPG again.

## [Milestone acceptance criteria]

At the end of Milestone 3:

- supported blockers are emitted explicitly,
- supported hints and leads are emitted explicitly,
- those outputs feed the next progression step,
- preserved vs divergent old behavior is explicit,
- and the progression loop is no longer just gather-and-sell.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the exact scope of supported blocker, hint, and lead behavior for Phase 5

#### [Task Description]

Define exactly what strategic outputs are in scope for the phase.

#### [Task technical implementation]

Choose a narrow supported set, such as:

- material blockers,
- gold blockers,
- resource-location hints,
- resource-node or camp leads,
- candidate zones for supported resources.

Exclude broad strategic outputs that are not required for progression-loop recovery.

#### [Task possible affected files]

- `docs/engine/phase5_resource_intelligence_scope.md`
- support boundary docs
- progression design docs

#### [Task important notes]

If you do not freeze scope here, the milestone turns into vague AI reconstruction.

#### [Task check list]

- [ ] Supported blocker kinds are explicit
- [ ] Supported hint kinds are explicit
- [ ] Supported lead kinds are explicit
- [ ] Excluded strategic scope is explicit
- [ ] Scope is narrow and testable

#### [Task acceptance criteria]

The supported strategic-output slice is narrowly defined and implementable without AI-scope explosion.

---

### [ ] (checkbox) - [Task 2] - Capture original `src` guild/resource-intelligence behavior for supported cases through characterization tests or fixtures

#### [Task Description]

Use original `src` as the behavior oracle for the supported strategic outputs.

#### [Task technical implementation]

Capture supported behavior for cases such as:

- missing material pressure,
- missing gold pressure,
- guild/resource hint generation,
- supported location or zone lead emission,
- and any supported no-op behavior.

Document any original behaviors that remain intentionally out of scope.

#### [Task possible affected files]

- original `src` characterization fixtures
- `tests_v2/parity/test_resource_intelligence_parity.py`
- divergence log
- strategy characterization docs

#### [Task important notes]

Do not invent strategic semantics just because the V2 data model is cleaner.

#### [Task check list]

- [ ] Supported old behavior is captured
- [ ] Normal cases are captured
- [ ] Failure/no-op cases are captured
- [ ] Out-of-scope old behavior is noted
- [ ] Fixtures are reusable for comparison tests

#### [Task acceptance criteria]

Supported strategic resource-intelligence behavior is captured well enough for parity review during the port.

---

### [ ] (checkbox) - [Task 3] - Define the V2 authoritative state and update contracts for blockers, hints, and leads in supported scope

#### [Task Description]

Map strategic outputs into native `src_v2` data and update contracts.

#### [Task technical implementation]

Define:

- where blockers live,
- where hints live,
- where leads live,
- what updates can create, remove, or revise them,
- and how they connect to supported progression decisions.

Ensure the representation stays bounded and explicit.

#### [Task possible affected files]

- `src_v2/core/state.py`
- `src_v2/core/updates.py`
- strategic models
- strategy contract docs

#### [Task important notes]

Do not allow hidden mutation or unbounded collections here.

#### [Task check list]

- [ ] Storage locations are explicit
- [ ] Update types are explicit
- [ ] Boundedness rules are explicit
- [ ] Removal/update semantics are explicit
- [ ] Contracts align with the supported slice

#### [Task acceptance criteria]

Blockers, hints, and leads are fully expressed in native `src_v2` authoritative terms for the supported scope.

---

### [ ] (checkbox) - [Task 4] - Implement or finalize the local reference path for supported strategic resource-intelligence outputs

#### [Task Description]

Make local strategic output generation the semantic source of truth.

#### [Task technical implementation]

Implement the local reference path that:

- inspects town/resource outcomes,
- emits supported blockers,
- emits supported hints or leads,
- and records the outputs in the bounded authoritative structures.

This local path becomes the base for later proof and support-boundary documentation.

#### [Task possible affected files]

- `src_v2/systems/resource_intelligence.py`
- strategy output helpers
- local strategy tests

#### [Task important notes]

Do not let worker timing define strategic semantics.

#### [Task check list]

- [ ] Local path exists
- [ ] Supported outputs are emitted deterministically
- [ ] Boundedness is enforced
- [ ] Outputs are apply-path compatible
- [ ] Local path is tested directly

#### [Task acceptance criteria]

The local path defines the supported semantics of blocker, hint, and lead generation.

---

### [ ] (checkbox) - [Task 5] - Integrate strategic outputs into the supported gameplay loop without widening into broad AI scope

#### [Task Description]

Make the outputs matter to the loop without turning the phase into full AI reconstruction.

#### [Task technical implementation]

Define the narrow integration rules for how supported blockers, hints, and leads affect next-step behavior, such as:

- where actors may redirect,
- what counts as a next supported target,
- and when blockers suppress or reshape supported actions.

Keep the logic bounded and literal.

#### [Task possible affected files]

- progression loop modules
- strategy integration helpers
- kernel or action-selection integration points
- progression loop tests

#### [Task important notes]

This is loop closure, not broad decision-theory reconstruction.

#### [Task check list]

- [ ] Next-step influence is explicit
- [ ] Supported redirection behavior is explicit
- [ ] Broad AI scope is excluded
- [ ] Behavior remains deterministic
- [ ] Integration is tested

#### [Task acceptance criteria]

Supported blockers and leads influence the resource progression loop without expanding into unsupported strategic scope.

---

### [ ] (checkbox) - [Task 6] - Add replay/runtime/certification visibility for blocker and lead generation where needed

#### [Task Description]

Make strategic outputs visible to truth surfaces where they matter.

#### [Task technical implementation]

Expose supported blocker/hint/lead generation to:

- replay traces where useful,
- runtime visibility where needed for debugging,
- and certification scenarios where strategic outputs are part of the declared loop.

Keep the surfaced data bounded and purposeful.

#### [Task possible affected files]

- replay modules
- runtime visibility modules
- certification scenarios
- observability docs

#### [Task important notes]

Do not add decorative strategy telemetry.

#### [Task check list]

- [ ] Replay visibility exists where needed
- [ ] Runtime visibility is sufficient
- [ ] Certification can observe supported outputs
- [ ] Visibility remains bounded
- [ ] No vanity telemetry is introduced

#### [Task acceptance criteria]

Strategic resource-intelligence outputs are visible enough to support debugging and proof for the supported slice.

---

### [ ] (checkbox) - [Task 7] - Add parity, contract, lifecycle, and certification tests for the supported strategic resource-intelligence slice

#### [Task Description]

Prove the strategic-output slice is real and preserved where required.

#### [Task technical implementation]

Add:

- parity tests vs original `src` for supported strategic-output cases,
- direct contract tests for blocker/hint/lead generation,
- lifecycle and replay tests where those outputs matter,
- and certification scenarios where progression-loop proof depends on them.

#### [Task possible affected files]

- `tests_v2/parity/test_resource_intelligence_parity.py`
- `tests_v2/gameplay/test_resource_intelligence_contract.py`
- lifecycle tests
- certification tests

#### [Task important notes]

If the outputs are not proven, they are still just implementation details.

#### [Task check list]

- [ ] Parity tests exist
- [ ] Contract tests exist
- [ ] Lifecycle/replay tests exist where relevant
- [ ] Certification scenarios exist
- [ ] Failures are visible in normal validation flow

#### [Task acceptance criteria]

Supported strategic resource-intelligence behavior is pinned by parity, contract, and proof tests.

---

### [ ] (checkbox) - [Task 8] - Declare the support boundary and intentional divergences for supported blocker/hint/lead behavior

#### [Task Description]

Make the strategic-output slice official and reviewable.

#### [Task technical implementation]

Publish:

- what blockers are supported,
- what hints/leads are supported,
- under what conditions they are emitted,
- what remains excluded,
- and what intentional divergences remain from original `src`.

#### [Task possible affected files]

- `docs/engine/phase5_resource_intelligence_support.md`
- support matrix docs
- divergence log
- certification docs

#### [Task important notes]

This slice must be declared narrowly or it will be misunderstood as “strategy support.”

#### [Task check list]

- [ ] Supported outputs are documented
- [ ] Conditions are documented
- [ ] Exclusions are documented
- [ ] Divergences are documented
- [ ] Official support is reviewable

#### [Task acceptance criteria]

The supported blocker/hint/lead slice is declared explicitly with honest scope and limits.
