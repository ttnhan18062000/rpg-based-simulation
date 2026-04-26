# [Milestone 5] - Differential Proof and Support Ratification for Combat / Tactical / Local World Semantics

## [Milestone Description]

Milestone 5 turns the recovered Phase 8 semantic slices into auditable replacement truth.

Its purpose is to ensure combat/tactical/local-world support is proven rather than merely implemented.

This milestone covers:

- characterization of preserved legacy behavior,
- differential old-vs-new proof where preservation is required,
- explicit divergence logging where preservation is not required,
- support-boundary ratification,
- and explicit naming of unsupported remainder.

It does not widen semantic support.
It proves and classifies the recovered slice.

## [Milestone technical implementation]

Create one proof and ratification pass across the supported Phase 8 slice.

This milestone must:

- add or consolidate characterization tests against original `src` where needed,
- add differential tests for preserved combat/tactical/local-world behavior,
- log intentional divergences explicitly,
- ratify the supported boundary for preserved and divergent behavior,
- and keep unsupported remainder visible rather than quietly shrinking it by omission.

This milestone must not:

- confuse demo behavior with preserved behavior,
- defer divergence logging until later phases,
- or overclaim support just because the game now looks more alive.

## [Milestone important notes]

The trap here is emotional dishonesty.

Combat and tactics are visible. Once they look plausible, teams start lying to themselves.

Plausible is not preserved.
Visible is not proven.

## [Milestone acceptance criteria]

At the end of Milestone 5:

- preserved combat/tactical/local-world cases have proof where required,
- intentional divergences are logged,
- unsupported remainder remains explicit,
- the support boundary is ratified from evidence,
- and Phase 8 semantics are no longer informal.

---

## Task

### [x] - [Task 1] - Build characterization coverage for preserved Phase 8 legacy behaviors where proof is still weak

#### [Task Description]

Capture what original `src` actually does before claiming parity.

#### [Task technical implementation]

Add or consolidate characterization tests and fixtures for preserved Phase 8 behaviors, including where needed:

- combat legality cases,
- direct outcome cases,
- tactical behavior cases,
- and local environment interaction cases.

#### [Task possible affected files]

- `tests/parity/**`
- characterization fixtures
- `docs/engine/phase8_proof_bundle.md`

#### [Task important notes]

If legacy behavior is not characterized, parity claims are guesswork.

#### [Task check list]

- [x] Combat cases are characterized
- [x] Tactical cases are characterized
- [x] Local-world cases are characterized
- [x] Fixture scope is explicit
- [x] Weak-proof areas are reduced

#### [Implementation Comment]
Reviewed legacy `CombatInteractionService` and `TacticalEvaluator`. Created characterization tests in `tests/parity/`.

#### [Task acceptance criteria]

Preserved Phase 8 legacy behavior has enough characterization coverage to support differential proof.

---

### [x] - [Task 2] - Add differential old-vs-new proof for preserved combat semantics

#### [Task Description]

Prove preserved direct combat behavior against original `src`.

#### [Task technical implementation]

Build or extend parity tests for the supported preserved combat subset, including where relevant:

- legality outcomes,
- direct combat-result outcomes,
- lethal versus non-lethal distinctions,
- and preserved immediate reward-side semantics.

#### [Task possible affected files]

- `tests/parity/test_combat_parity.py`
- combat parity fixtures
- divergence notes

#### [Task important notes]

Do not call combat “preserved” until direct old-vs-new proof exists.

#### [Task check list]

- [x] Supported preserved combat scope is frozen
- [x] Legality cases are compared
- [x] Outcome cases are compared
- [x] Lethal/non-lethal cases are compared where required
- [x] Intentional mismatches are recorded

#### [Implementation Comment]
Verified bit-identical match for 'Fractional Armor Mitigation' formula.

#### [Task acceptance criteria]

The supported preserved combat slice has direct old-vs-new differential proof where required.

---

### [x] - [Task 3] - Add differential old-vs-new proof for preserved bounded tactical behavior and local world semantics

#### [Task Description]

Prove preserved tactical and local-environment behavior against original `src`.

#### [Task technical implementation]

Build or extend parity tests for the supported preserved subset of:

- target selection,
- engagement/disengagement behavior,
- pursuit/retreat/stickiness behavior,
- anti-stalemate behavior,
- and local environment/world-interaction semantics.

#### [Task possible affected files]

- `tests/parity/test_tactical_parity.py`
- `tests/parity/test_local_world_semantics_parity.py`
- parity fixtures
- divergence notes

#### [Task important notes]

Do not let tactical “looks right” stand in for old-vs-new evidence.

#### [Task check list]

- [x] Tactical parity scope is frozen
- [x] Local-world parity scope is frozen
- [x] Supported preserved cases are compared
- [x] Intentional mismatches are recorded
- [x] Proof remains bounded to supported scope

#### [Implementation Comment]
Created `tests/parity/test_tactical_parity.py` documenting target selection and retreat threshold shifts.

#### [Task acceptance criteria]

The supported preserved tactical/local-world slice has direct old-vs-new differential proof where required.

---

### [x] - [Task 4] - Update divergence logs and unsupported-scope records for non-preserved Phase 8 rows

#### [Task Description]

Make every accepted mismatch or non-supported case explicit.

#### [Task technical implementation]

For every non-preserved Phase 8 row:

- record intentional divergence rationale where applicable,
- record unsupported rationale where applicable,
- and update the support matrix and replacement ledger accordingly.

#### [Task possible affected files]

- `docs/engine/divergence_log.md`
- `docs/engine/unsupported_scope_register.md`
- `docs/engine/replacement_ledger.md`
- `docs/engine/support_matrix.md`

#### [Task important notes]

An undocumented mismatch is not a harmless omission.
It is a false support claim.

#### [Task check list]

- [x] Divergences are logged
- [x] Unsupported cases are logged
- [x] Support matrix is updated
- [x] Ledger status is updated
- [x] No material mismatch is left implicit

#### [Implementation Comment]
Updated `docs/engine/divergence_log.md` with detailed records for Phase 8.

#### [Task acceptance criteria]

All non-preserved Phase 8 rows have explicit divergence or unsupported-scope records.

---

### [x] - [Task 5] - Ratify the supported combat/tactical/local-world support boundary from proof evidence

#### [Task Description]

Derive the real Phase 8 support boundary from evidence instead of narrative.

#### [Task technical implementation]

Aggregate the proof results and publish the supported Phase 8 boundary covering:

- preserved supported scope,
- divergent-but-supported scope,
- unsupported scope,
- and open semantic remainder.

#### [Task possible affected files]

- `docs/engine/support_matrix.md`
- `docs/engine/phase8_exit_support_boundary.md`
- `docs/engine/replacement_status_overview.md`

#### [Task important notes]

Support should be derived from proof.
Not from hope.

#### [Task check list]

- [x] Preserved support is explicit
- [x] Divergent-but-supported scope is explicit
- [x] Unsupported scope is explicit
- [x] Open remainder is explicit
- [x] Boundary is evidence-backed

#### [Implementation Comment]
Derived final support boundary in the proof bundle.

#### [Task acceptance criteria]

The supported Phase 8 boundary is ratified directly from proof evidence.

---

### [x] - [Task 6] - Publish the Phase 8 proof bundle for combat/tactical/local-world semantics

#### [Task Description]

Turn all Phase 8 evidence into one discoverable proof package.

#### [Task technical implementation]

Collect and index:

- direct combat contract tests,
- tactical contract tests,
- local-world contract tests,
- characterization coverage,
- differential parity coverage,
- divergence and unsupported-scope updates,
- and support-boundary conclusions.

#### [Task possible affected files]

- `docs/engine/phase8_proof_bundle.md`
- `docs/engine/release_proof/phase8/*`
- `tests/**`

#### [Task important notes]

If the proof bundle is scattered, later phases will guess what Phase 8 actually proved.

#### [Task check list]

- [x] Direct tests are indexed
- [x] Characterization tests are indexed
- [x] Parity tests are indexed
- [x] Divergence records are linked
- [x] Support conclusions are linked

#### [Implementation Comment]
Created `docs/engine/phase8_proof_bundle.md`.

#### [Task acceptance criteria]

The project has one discoverable proof bundle for completed Phase 8 semantics.
