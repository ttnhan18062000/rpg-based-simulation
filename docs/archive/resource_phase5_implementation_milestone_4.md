---
status: archive
authority: P2
audience: historical
layer: economy
original_date: unknown
---

# [Milestone 4] - Integrated Resource Progression Differential Proof

## [Milestone Description]

Milestone 4 is the integrated proof milestone for Phase 5.

By this point, the project should have a supported progression loop consisting of:

- movement,
- resource interaction,
- town resource resolution,
- and strategic blocker/hint/lead generation,

at least within a narrow supported boundary.

This milestone exists to prove that the supported loop preserves intended original RPG-core behavior where preservation is claimed.

This is not a normal test cleanup milestone.
It is the milestone that turns “we implemented the pieces” into “we proved the supported loop.”

## [Milestone technical implementation]

Create one integrated old-vs-new proof layer for the supported progression loop.

This milestone must:

- define equivalent supported scenarios in original `src` and `src`,
- compare authoritative outcomes,
- identify mismatches,
- classify accepted divergences,
- and make integrated parity drift visible in the normal validation path.

This milestone must not pretend unsupported original behavior is already covered.
Scope must remain narrow and explicit.

## [Milestone important notes]

The trap here is narrative inflation.

Once several progression systems work together, teams start claiming loop recovery before proving it.

That is exactly what this milestone exists to stop.

## [Milestone acceptance criteria]

At the end of Milestone 4:

- the supported progression loop has integrated old-vs-new comparison coverage,
- accepted divergences are documented,
- parity drift is guarded in the normal validation path,
- and the project can state precisely which part of original resource progression has been recovered.

---

## Task

### [ ] (checkbox) - [Task 1] - Freeze the exact parity scope for the integrated Phase 5 progression loop

#### [Task Description]

Define exactly what integrated loop behavior is supposed to match original `src`.

#### [Task technical implementation]

Freeze a narrow set of supported scenarios such as:

- gather then return,
- resolve supported town behavior,
- emit supported blockers or leads,
- redirect into a supported next-step loop,
- and supported failure paths involving slot/weight or missing requirements.

Exclude any behavior not officially supported yet.

#### [Task possible affected files]

- `docs/engine/phase5_progression_parity_scope.md`
- parity docs
- support matrix docs

#### [Task important notes]

Integrated parity becomes useless if its scope is fuzzy.

#### [Task check list]

- [ ] Supported parity scenarios are explicit
- [ ] Excluded scenarios are explicit
- [ ] Preservation claims are explicit
- [ ] Divergence candidates are visible
- [ ] Scope matches actual supported systems

#### [Task acceptance criteria]

The integrated parity scope is narrow, explicit, and aligned with the actual supported progression loop.

---

### [ ] (checkbox) - [Task 2] - Build old-vs-new scenario fixtures for supported gather, return, resolve, and redirect behavior

#### [Task Description]

Create comparable scenarios for original `src` and `src`.

#### [Task technical implementation]

Build fixtures that normalize equivalent starting states and expected supported outcomes for scenarios involving:

- resource gathering,
- inventory pressure,
- town return and resolution,
- blocker/lead emission,
- and supported next-step redirection.

Make fixtures deterministic and reusable.

#### [Task possible affected files]

- parity fixture modules
- `tests/parity/test_progression_loop_parity.py`
- old-src scenario capture helpers

#### [Task important notes]

Do not let fixture differences hide real behavior differences.

#### [Task check list]

- [ ] Equivalent initial states exist
- [ ] Supported scenario inputs are deterministic
- [ ] Expected outputs are normalized
- [ ] Fixtures are reusable
- [ ] Scenario scope matches official support

#### [Task acceptance criteria]

Reusable old-vs-new fixtures exist for the supported integrated progression scenarios.

---

### [ ] (checkbox) - [Task 3] - Compare authoritative results for supported loop scenarios and investigate mismatches

#### [Task Description]

Run the integrated comparisons and treat mismatches as real work, not noise.

#### [Task technical implementation]

Compare authoritative outputs for each supported scenario, including:

- inventory outcomes,
- gold/material outcomes,
- depletion or retention outcomes,
- blocker/hint/lead outputs,
- and resulting next-step state where supported.

Investigate each mismatch and classify it as:

- bug,
- fixture problem,
- unsupported case,
- or intentional divergence.

#### [Task possible affected files]

- parity tests
- mismatch review logs
- divergence log
- gameplay bug tickets

#### [Task important notes]

Do not normalize mismatches by calling them “contract differences” unless they are explicitly accepted.

#### [Task check list]

- [ ] Supported scenarios are executed
- [ ] Outputs are compared directly
- [ ] Mismatches are investigated
- [ ] Causes are classified
- [ ] Results feed bug fixing or divergence logging

#### [Task acceptance criteria]

Integrated supported-loop mismatches are investigated and resolved or documented explicitly.

---

### [ ] (checkbox) - [Task 4] - Record explicit intentional divergences where preservation is not required or not yet possible

#### [Task Description]

Make accepted differences visible and stable.

#### [Task technical implementation]

For any supported-surface mismatch that is intentionally accepted, record:

- the original behavior,
- the new behavior,
- the reason for the divergence,
- whether it is temporary or permanent,
- and what proof/support docs must mention it.

#### [Task possible affected files]

- divergence log
- support surface docs
- milestone review docs
- release-truth docs

#### [Task important notes]

Undocumented divergence is just hidden drift.

#### [Task check list]

- [ ] Each accepted divergence is explicit
- [ ] Reason is explicit
- [ ] Temporary vs permanent status is explicit
- [ ] Support docs reference it where needed
- [ ] Tests do not silently treat it as parity

#### [Task acceptance criteria]

Every accepted divergence in the supported loop is documented precisely and consistently.

---

### [ ] (checkbox) - [Task 5] - Add regression guards for integrated parity drift in the normal validation path

#### [Task Description]

Make supported-loop drift cheap to catch.

#### [Task technical implementation]

Add or strengthen regression guards so supported integrated-loop parity failures appear in normal local and CI validation.

Use stable fixtures and bounded expectations.

#### [Task possible affected files]

- parity tests
- CI targets
- regression scripts
- milestone guard docs

#### [Task important notes]

If integrated parity can drift silently, the phase is not closed.

#### [Task check list]

- [ ] Regression guards exist
- [ ] Guards run in standard validation
- [ ] Fixture stability is acceptable
- [ ] Failures are visible
- [ ] Guard scope matches official support

#### [Task acceptance criteria]

Integrated parity drift in the supported progression loop causes visible standard-validation failure.

---

### [ ] (checkbox) - [Task 6] - Add lifecycle and replay validation for the integrated supported loop

#### [Task Description]

Prove the loop remains truthful under lifecycle and replay pressure.

#### [Task technical implementation]

Add validation for supported integrated-loop scenarios involving:

- orderly shutdown,
- replay capture,
- restart or finalization edges where relevant,
- and proof-bundle alignment for gameplay-active progression scenarios.

#### [Task possible affected files]

- lifecycle tests
- replay tests
- certification scenarios
- progression proof docs

#### [Task important notes]

Gameplay proof that ignores lifecycle truth is still incomplete.

#### [Task check list]

- [ ] Lifecycle tests exist where relevant
- [ ] Replay tests exist where relevant
- [ ] Integrated scenarios are covered
- [ ] Proof outputs remain bounded
- [ ] Failures are visible in normal validation or supported proof flows

#### [Task acceptance criteria]

The supported integrated progression loop has lifecycle and replay validation where relevant to declared support.

---

### [ ] (checkbox) - [Task 7] - Publish the first precise statement of what resource progression behavior is now recovered vs not recovered

#### [Task Description]

Turn the proof results into one exact claim boundary.

#### [Task technical implementation]

Publish a short recovery statement that says:

- what supported resource progression behavior is now recovered,
- what behavior remains outside support,
- what behavior remains intentionally divergent,
- and what should not yet be claimed.

#### [Task possible affected files]

- `docs/engine/phase5_progression_recovery_statement.md`
- support matrix docs
- release docs
- benchmark/certification claim docs

#### [Task important notes]

Do not bury the actual claim boundary inside raw test outcomes.

#### [Task check list]

- [ ] Recovered behavior is explicit
- [ ] Unrecovered behavior is explicit
- [ ] Divergent behavior is explicit
- [ ] Unsupported claims are explicit
- [ ] Language matches actual proof results

#### [Task acceptance criteria]

The project can state exactly what part of the original resource progression loop is now recovered.
