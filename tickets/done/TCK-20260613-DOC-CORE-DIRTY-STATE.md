---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-CORE-DIRTY-STATE
phase: done
date: 2026-06-13
tags: [documentation, core, dirty-state, update-intents, dependency-model]
---

# TCK-20260613-DOC-CORE-DIRTY-STATE

## Title
Document Core Dirty State Dependency Model and Update Intent Pipeline

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`src/core/dirty.py` and `src/core/updates.py` are central to the engine's optimization strategy — they determine which downstream systems need to recalculate when a piece of state changes. This is the dirty-state dependency expansion model: movement dirtiness triggers strategic/social recalculation, inventory dirtiness triggers strategic recalculation, combat dirtiness triggers lifecycle/social/strategic recalculation, and so on. However, none of this is documented anywhere in `docs/core/`. An agent or developer cannot understand *why* certain systems run in sequence without reading `src/core/dirty.py` directly.

Similarly, `src/core/updates.py` implements the update intent pipeline — the typed record system for expressing durable state changes — but has no corresponding doc explaining the intent lifecycle, what kinds of intents exist, what must use them vs what can bypass them, and how they flow into the authoritative apply path.

This ticket creates two new docs in `docs/core/` to close these gaps.

## Scope
Create two new docs in `docs/core/`:

1. **`docs/core/dirty_state_and_dependency.md`** — Explains the dirty flag system and dependency expansion model. Must cover:
   - What "dirty" means in the context of the tick pipeline
   - The complete dependency graph: which dirty state triggers which downstream recalculations
   - Why the model exists (optimization: skip clean systems, avoid full-entity recompute every tick)
   - How dirty flags are set and cleared (lifecycle within a tick)
   - What systems read dirty flags vs what systems ignore them
   - What happens if a dirty flag is missed (stale state risk)
   - Edge cases: entity dies while dirty, mid-tick dirtiness from concurrent resolution
   - Source areas: `src/core/dirty.py`, `src/core/state.py`
   - Regression tests: tests that verify dirty propagation correctness

2. **`docs/core/update_intents.md`** — Explains the typed update intent pipeline. Must cover:
   - What an update intent is (typed record expressing a desired durable state change)
   - The taxonomy of intents (inventory, position, attribute, combat, social, etc.)
   - Lifecycle: where intents are created (read-only paths), where they are applied (authoritative apply only)
   - Why intents exist: prevent unauthorized mutation from read-only decision logic
   - Compaction: how multiple intents for the same field are merged before apply
   - What must not bypass intents (durable state rule)
   - What may bypass intents (ephemeral, in-tick local state)
   - Edge cases: conflicting intents, invalid intent targets, dropped intents
   - Source areas: `src/core/updates.py`, `src/core/update_models/`
   - Regression tests: architecture tests that verify read-only logic did not mutate live state

Both docs must follow the standard logic-contract template.

## Out of Scope
- Modifying `docs/core/state.md` (already covers immutability law)
- Documenting `src/core/models/` at the model level (entity anatomy already covered)
- Covering the authoritative apply path in detail (that is `docs/engine/authoritative_apply_contract.md`)
- `self_model.md` — the entity self-model lives in `src/cognition/`, not `src/core/`. It is covered by TCK-20260613-DOC-COGNITION-SUBSYSTEM.

## Acceptance Criteria
- [ ] `docs/core/dirty_state_and_dependency.md` created. Contains the full dependency graph (what dirty state triggers what). Written at logic-contract depth, not just a pointer to `dirty.py`. Frontmatter: `status: active`, `layer: core`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.
- [ ] `docs/core/update_intents.md` created. Contains intent taxonomy, lifecycle (create in read-only → apply in authoritative only), compaction semantics. Frontmatter: same.
- [ ] Both docs have `## Regression tests` sections citing concrete test paths.
- [ ] Both docs have `## Extension rules` sections.
- [ ] `docs/core/README.md` updated to list the two new docs.
- [ ] `make knowledge-index-update` and `make docs-registry` run after completion.

## Related Tickets
- TCK-20260613-DOC-HARDENING-EPIC (parent)
- TCK-20260613-DOC-ENGINE-RUNTIME-DETAILS (engine compaction doc complements update_intents.md)

## Related Docs
- `docs/core/state.md` — immutability law and state partitioning (P0)
- `docs/engine/authoritative_apply_contract.md` — apply path contract
- `docs/engine/authoritative_mutation_pipeline_contract.md` — mutation rules
- `docs/engine/authoritative_pipeline.md` — 17-phase refinement sequence

## Related Stored Artifacts
None

## Related Code Areas
- `src/core/dirty.py` — dirty flag definitions and dependency expansion
- `src/core/updates.py` — update intent types and pipeline
- `src/core/update_models/` — typed update record schemas
- `src/core/state.py` — entity state root
- `tests/architecture/` — architecture tests for mutation boundary

## Assumptions / Open Questions
- Read `src/core/dirty.py` fully before writing the dependency graph — the goal is to document what is actually there, not what the proposal imagines.
- If `src/core/updates.py` doesn't exist as named (may be split across files), use grep to find the update intent types and document from those.

## Implementation Notes
1. Read `src/core/dirty.py` → extract the dependency rules → write them as a table in the doc.
2. Read `src/core/update_models/` → enumerate intent types → write the taxonomy section.
3. Read `docs/core/state.md` first to avoid contradicting the immutability law doc.
4. Check `tests/architecture/` for tests that verify these boundaries — cite them under `## Regression tests`.

### Completion summary
Both documentation files were written directly from source code inspection. Key findings documented:

`docs/core/dirty_state_and_dependency.md`: Covers the full 10-edge `DirtyDependencyGraph.expand()` dependency graph (dirty.py:419–437), the 9-entity-domain + 9-world-object `DirtySet` taxonomy, `CandidateSelector` domain routing (all 15 named domain mappings), flag lifecycle within a tick (production → merge → consumption → clearance), the `e_upd.task` discrepancy between `DirtySetBuilder` and `DirtySet.from_update()` (documented as a known risk), `DirtySetLeakError` audit mode, `force_full_scan` fallback, and the conservative lifecycle-event marking (entities_add/remove marked in ALL sets). Extension checklist covers 8 steps.

`docs/core/update_intents.md`: Covers all 22 `EntityUpdate` slots and 10 `StateUpdate` world-level fields in taxonomy tables, the `InventoryUpdate` result-type restriction, `ResourceTransferIntent` mandatory pathway with contingent sub-updates, `QuestUpdate` MULTI sentinel, `CombatIntent` sub-record structure, the three-phase intent lifecycle (creation → merge/compact → apply-path-only), merge semantics (delta sum / set last-write-wins / list concat), durable state mutation rules, and four edge cases. Extension rules cover 10 steps.

`docs/core/README.md`: Two new doc links appended to the files list; existing 4 entries and frontmatter unchanged.

Frontmatter validation: both docs passed `OK`. `make docs-registry` succeeded (951 entries, 8 core layer docs). `make knowledge-index-update` ran incrementally (3 files updated) but exited non-zero due to `sentence-transformers` not installed in the environment — not an authoring error.

## Test Summary
Not applicable — documentation ticket.

## Files Changed
- `docs/core/dirty_state_and_dependency.md` (new)
- `docs/core/update_intents.md` (new)
- `docs/core/README.md` (updated: add new docs to index)

## Completion Summary
Created docs/core/dirty_state_and_dependency.md documenting the 10-edge dirty dependency graph from dirty.py and docs/core/update_intents.md documenting the 22+10 intent taxonomy from updates.py. Both docs follow the logic-contract template with all sections. Updated docs/core/README.md to list both new docs. Frontmatter validation passed. Pre-existing tests/docs/ failures unrelated to this ticket.
