---
status: archive
authority: P2
audience: historical
layer: strategy
original_date: unknown
---

# Milestone 1 — Strategic state foundation

## What this milestone actually delivers

At the end of Milestone 1, you still do **not** have smart long-term behavior yet.

What you **do** have is the substrate that makes later behavior real instead of fake:

- a typed `mind.strategic` domain
- stable strategy records
- a `StrategicUpdate` intent path
- authoritative application in `ActionSystem`
- snapshot and serialization safety
- minimal inspection visibility

That is the contract layer. Without it, every later milestone becomes heuristics glued onto tactical AI.

---

## Implementation Notes (2026-04-12)

- **Authoritative Application**: Fully implemented in `ActionSystem._apply_updates`. It handles `StrategicUpdate` intents by merging records (add/update/remove) using stable IDs to prevent duplication.
- **Deterministic RNG**: `DeterministicRNG` has been hardened with `sub_id` support to allow multiple stable rolls within the same tick/entity context, ensuring byte-identical replication.
- **Mind Integration**: `MindAspect` now includes the `strategic: StrategicState` field with full Pydantic validation and deep-copy support in `Entity.copy()`.

---

## The correct implementation order

Do this in this order, or you will create avoidable rework.

### Step 1 — Write the tests before touching models

Start with structural tests, not behavior tests.

You need tests that prove:

- `MindAspect` can construct with empty strategy
- strategy records validate
- `ActionProposal` can carry `StrategicUpdate`
- `ActionSystem` can apply updates deterministically
- snapshot copy keeps strategy without aliasing
- serialization/inspection survives the new field

If you skip these and start coding models first, you will overdesign the schema and then spend time unwinding it. Phase 1 is mostly plumbing. Treat it like plumbing.

### Step 2 — Create the strategy schema

Add `src/core/models/strategy.py` and keep it narrow.

Start with:

- `StrategicState`
- `DirectiveRecord`
- `ProjectRecord`
- `ObjectiveRecord`
- `ConcernRecord`
- `LeadRecord`
- `BlockerRecord`
- `ObligationRecord`
- `SocialContractRecord`

Do not try to encode full planner semantics yet. That is not Phase 1. You need stable IDs, lifecycle fields, priority/salience where obvious, and enough typed structure to survive serialization and later mutation.

A sensible first-pass shape is:

- `StrategicState`
  - `directives: list[DirectiveRecord]`
  - `projects: list[ProjectRecord]`
  - `concerns: list[ConcernRecord]`
  - `obligations: list[ObligationRecord]`
  - `contracts: list[SocialContractRecord]`
  - `offers: list[...]` only if already aligned with source
  - `leads: list[LeadRecord]`
  - `current_project_id: str | None`
  - `current_objective_id: str | None`
  - `interrupted_project_id: str | None`
  - `project_lock_until: int | None`

For each record, include:

- stable ID
- status
- origin/provenance
- created/update/resolved ticks
- optional tags/metadata only if strongly bounded

Do **not** shove everything into `dict[str, Any]`. That would defeat the entire point of making this typed.

### Step 3 — Attach strategy to `MindAspect`

Add:

- `strategic: StrategicState = Field(default_factory=StrategicState)`

Then fix imports, rebuilds, and entity construction.

This part sounds trivial, but it is where people usually create hidden null assumptions. Your builder/generator path must create valid entities without any strategic bootstrapping hacks. Empty-but-valid is the rule.

### Step 4 — Add `StrategicUpdate`

This is where discipline matters.

Do **not** overload `MindUpdate`. It is already handling enough. Strategy deserves its own update type because it is its own domain. The reference notes call this out directly.

Your first-pass `StrategicUpdate` should use explicit typed fields, not command blobs. For example:

- `directives_add: list[DirectiveRecord]`
- `directives_remove: list[str]`
- `projects_add_or_update: list[ProjectRecord]`
- `projects_remove: list[str]`
- `concerns_add_or_update: list[ConcernRecord]`
- `concerns_remove: list[str]`
- `leads_add_or_update: list[LeadRecord]`
- `leads_remove: list[str]`
- `blockers_add_or_update: list[BlockerRecord]`
- `blockers_remove: list[str]`
- `obligations_add_or_update: list[ObligationRecord]`
- `obligations_remove: list[str]`
- `contracts_add_or_update: list[SocialContractRecord]`
- `contracts_remove: list[str]`
- `current_project_id: str | None`
- `current_objective_id: str | None`
- `interrupted_project_id: str | None`
- `project_lock_until: int | None`

Keep it mechanical. Phase 1 is not deciding strategy. It is only enabling legal strategic mutation.

### Step 5 — Implement authoritative apply in `ActionSystem`

This is the real gate.

Until `ActionSystem` can apply `StrategicUpdate`, the whole milestone is fake.

Use deterministic merge semantics:

- replace by stable ID
- remove by stable ID
- preserve stable ordering rules
- apply only to the target entity
- keep side effects inside `mind.strategic`

Do not let AI mutate `entity.mind.strategic` directly. If you cheat here, the whole snapshot/worker architecture stops meaning anything.

A clean pattern is:

- add `_apply_strategic_update(entity, strategic_update)`
- use small helpers like `_merge_by_id(existing, incoming, key="...")`
- never append blindly

The failure mode to guard against is obvious: duplicate projects or directives accumulating because updates are append-only. Write that test first.

### Step 6 — Make it snapshot-safe and serialization-safe

This is the hidden failure point.

The engine already relies on immutable snapshots and authoritative state application. If strategy leaks mutable references into snapshots, you will create ghost mutation bugs that look like AI brilliance or AI madness depending on the day. Both are fake.

You need to verify:

- snapshot entity includes `mind.strategic`
- nested strategy lists/maps are deep-copied or model-owned safely
- replay serialization does not crash
- API/inspector serializers do not choke on new types

This is not optional cleanup. It is core milestone work.

### Step 7 — Seed minimal default strategy

Keep this minimal.

You are not building project generation yet. You are only ensuring new entities do not start as strategic nulls.

That means:

- valid empty collections
- maybe one or two foundational directives if role/archetype/faction strongly suggests them
- no project creation yet
- no fake long-term intelligence yet

If you start seeding projects in Milestone 1, you are jumping ahead and mixing schema work with behavior work.

### Step 8 — Add inspection visibility

Do not leave the state invisible.

Add a compact strategy section to the inspector and any debug-friendly API view:

- directives
- projects
- concerns
- leads
- blockers
- obligations
- contracts

Structured output is enough. Do not generate story prose. That would be theater, not observability.

---

## TDD sequence for Milestone 1

Use this exact progression.

### Test batch A — models

Write failing tests for:

- default `StrategicState`
- record validation
- stable ID presence
- serialization round-trip

Then implement `strategy.py`.

### Test batch B — mind integration

Write failing tests for:

- `MindAspect` includes `strategic`
- entity builder produces valid `mind.strategic`

Then attach the field.

### Test batch C — update transport

Write failing tests for:

- `ActionProposal` accepts `StrategicUpdate`
- update model rebuild works

Then add `StrategicUpdate`.

### Test batch D — authoritative application

Write failing tests for:

- add directive/project
- update same ID replaces rather than duplicates
- remove by ID works
- `target_id` routes to the right entity

Then implement `ActionSystem` apply logic.

### Test batch E — snapshot and serialization safety

Write failing tests for:

- snapshot preserves strategy
- snapshot does not alias live nested objects
- replay/API serialization survives

Then fix snapshot/copy/serialization issues.

### Test batch F — visibility

Write failing smoke tests for:

- inspector does not crash on empty strategy
- inspector renders populated strategy

Then add presentation support.

That is the clean path. Anything else is you indulging yourself.

---

## Suggested file targets

Likely new or changed files:

- `src/core/models/strategy.py`
- `src/core/aspects/mind.py`
- `src/actions/base.py`
- `src/systems/gameplay/action_system.py`
- `src/core/models/snapshot.py`
- `src/utils/replay.py`
- `src/ui/cli/inspector.py`

Suggested tests:

- `tests/core/test_strategy_models.py`
- `tests/core/test_mind_strategy_defaults.py`
- `tests/systems/test_action_system_strategy_updates.py`
- `tests/core/test_snapshot_strategy_serialization.py`
- `tests/ui/test_inspector_strategy_output.py`

---

## Definition of done for Milestone 1

Milestone 1 is done only when all of this is true:

- strategic state exists as typed persisted entity state
- it is attached to `MindAspect`
- AI-side logic can express legal strategic mutations through `StrategicUpdate`
- `ActionSystem` applies those updates deterministically
- snapshots and serialization preserve the domain safely
- inspector/debug paths can show it
- all of that is covered by automated tests

If any one of those is missing, you do not have a strategic foundation. You have a partial refactor.

---

## Milestone 1 checklist

- [x] Add tests for default `StrategicState` construction
- [x] Add tests for strategy record validation and serialization
- [x] Create `src/core/models/strategy.py`
- [x] Add `StrategicState`
- [x] Add `DirectiveRecord`
- [x] Add `ProjectRecord`
- [x] Add `ObjectiveRecord`
- [x] Add `ConcernRecord`
- [x] Add `LeadRecord`
- [x] Add `BlockerRecord`
- [x] Add `ObligationRecord`
- [x] Add `SocialContractRecord`
- [x] Add stable IDs and lifecycle fields to strategy records
- [x] Add validation/default factories/model rebuild handling
- [x] Add `strategic` field to `MindAspect`
- [x] Ensure entity builders/generators create valid default strategic state
- [x] Add tests for `MindAspect` / entity default strategy integration
- [x] Add `StrategicUpdate`
- [x] Define typed add/update/remove fields for strategy mutation
- [x] Add tests for `ActionProposal` carrying `StrategicUpdate`
- [x] Harden `DeterministicRNG` to produce ID-safe seeds [PHASE 1 STAGE 1]
- [x] Integrate `DeterministicRNG` next_hex for stable strategic IDs [PHASE 1 STAGE 1]
- [x] Implement typed `StrategicUpdate` with authoritative application logic [PHASE 1 STAGE 4]
- [x] Implement deterministic merging of strategic records by ID in `ActionSystem` [PHASE 1 STAGE 4]
- [x] Add baseline integration test for strategic determinism [PHASE 1 STAGE 16]
- [x] Verify total determinism via headless regression harness [PHASE 1 STAGE 16]
- [x] Add rebuild support for action/update models
- [x] Extend `ActionSystem` to dispatch `StrategicUpdate`
- [x] Implement deterministic merge-by-ID application logic
- [x] Add tests for add/update/remove routing and duplicate prevention
- [x] Verify `target_id` routes strategic updates correctly
- [x] Verify snapshot includes `mind.strategic`
- [x] Add aliasing safety tests for live vs snapshot strategy objects
- [x] Verify replay serialization does not break
- [x] Verify API/debug serialization does not break
- [x] Seed minimal default strategic state for generated entities
- [x] Seed minimal foundational directives only where identity data clearly supports it
- [x] Add strategic section to inspector/debug output
- [x] Add inspector smoke tests for empty and populated strategy state
- [x] Confirm milestone definition of done with passing automated tests

Priority Plan

What you must change in mindset or assumptions:
Stop thinking Milestone 1 is “just models.” It is the trust boundary for the whole feature.

What actions you must take immediately:
Write the failing structural tests first, then implement schema, then `mind.strategic`, then `StrategicUpdate`, then authoritative apply, then snapshot/serialization fixes.

What you must stop or eliminate:
Stop using tactical fields, memory text, or metadata blobs as placeholder strategic storage. Stop appending updates without ID-based replacement rules.

The consequences and opportunity cost if you fail to change:
You will spend the next milestones building behavior on top of unstable state, and every bug will become harder to isolate because you will not know whether the failure is cognition, mutation flow, serialization, or snapshot leakage.
