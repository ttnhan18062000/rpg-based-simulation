---
status: open
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E-CAP-REGISTRY
phase: open
date: 2026-06-19
tags: [capability-registry, feature-support, official-experimental-deprecated, architecture, infra]
---

# TCK-20260619-E-CAP-REGISTRY

## Title
Capability / Support Registry

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Only a narrow unsupported-legacy-features list exists (`docs/engine/known_limitations.md`). No backend-readable `OFFICIAL/SUPPORTED/EXPERIMENTAL/DEPRECATED` capability matrix exists. Required as a foundation for Feature Pack architecture (Epic 6.3) and as a replacement for the stale `known_limitations.md`.

Source: `docs/plans/engine_future_epics_roadmap.md` § E.

## Scope
- Design a YAML capability manifest: `docs/engine/capability_registry.yaml` with entries keyed by capability_id; each entry: name, status (OFFICIAL/SUPPORTED/EXPERIMENTAL/DEPRECATED/UNSUPPORTED), description, since_version, deprecated_reason
- Migrate existing `known_limitations.md` unsupported claims into DEPRECATED/UNSUPPORTED entries in the registry
- Add a Python reader (`src/engine/capability.py`) that exposes the registry as a queryable object: `capability_registry.is_supported("quest_generation")` → bool
- Add an architecture test that validates all capability IDs referenced in code/docs exist in the registry
- Update `known_limitations.md` to defer to the registry for machine-readable state; keep only human-readable notes in the doc

## Out of Scope
- Feature Pack manifest integration (Epic 6.3 uses this)
- Runtime capability discovery / dynamic loading

## Acceptance Criteria
- `capability_registry.yaml` exists with ≥20 entries covering all current feature areas
- Python reader correctly returns SUPPORTED/UNSUPPORTED status per capability_id
- `known_limitations.md` is simplified to reference the registry for machine-readable state

## Related Tickets
- TCK-20260619-P0-DOC-REPAIR (known_limitations.md refresh — this ticket completes the machine-readable half)
- TCK-20260619-E63-FEATURE-PACKS (uses this registry)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § E
- `docs/engine/known_limitations.md`
- `docs/compliance/checklist.md`
- `docs/parity_ledger/infrastructure.yaml` (update capability registry entries to verified once the reader is wired)
- New doc: `docs/engine/capability_registry.yaml` (create)

## Related Code Areas
- `src/engine/capability.py` (create)
- `docs/engine/capability_registry.yaml` (create)

## Assumptions / Open Questions
- What capability IDs should be in the initial registry? Derive from `known_limitations.md` + feature set of existing done tickets

## Implementation Notes
Derive capability IDs from `known_limitations.md` and closed tickets in `tickets/working_log.csv`. Design the YAML schema first, populate all entries, then implement the Python reader against it. Add the architecture guard test last.

After implementation: update `docs/parity_ledger/infrastructure.yaml` (add capability registry entry as verified). Simplify `docs/engine/known_limitations.md` to reference `capability_registry.yaml` for machine-readable state. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/engine/test_capability_registry.py`:
  - `test_capability_registry_is_valid_yaml()` — load `docs/engine/capability_registry.yaml`, validate schema against expected fields (capability_id, name, status, description, since_version)
  - `test_capability_reader_returns_correct_status()` — call `capability_registry.is_supported("quest_generation")`, assert returns bool
  - `test_all_registry_statuses_are_valid()` — assert all status values are in `{OFFICIAL, SUPPORTED, EXPERIMENTAL, DEPRECATED, UNSUPPORTED}`
- New file `tests/architecture/test_capability_references.py`:
  - `test_all_capability_ids_in_registry()` — architecture guard: any capability ID referenced in docs/code must exist in `capability_registry.yaml`

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
