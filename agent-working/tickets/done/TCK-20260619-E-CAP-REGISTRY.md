---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260619-E-CAP-REGISTRY
phase: done
date: 2026-06-19
tags: [capability-registry, feature-support, official-experimental-deprecated, architecture, infra]
---

# TCK-20260619-E-CAP-REGISTRY

## Title
Capability / Support Registry

## Status
DONE

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
- `docs/engine/known_limitations.md` (migrate unsupported claims into registry; simplify to human-readable-only on completion)
- `docs/compliance/checklist.md` (update capability tracking entry once registry is live)
- `docs/guidelines/design_patterns.md` (add capability registry as an architectural pattern: how to register and query capabilities; this prevents future capability-checking from scattering across files)
- `docs/parity_ledger/infrastructure.yaml` (update capability registry entries to verified once the reader is wired)
- New doc: `docs/engine/capability_registry.yaml` (YAML manifest: capability_id, name, status, description, since_version, deprecated_reason)

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
- `docs/engine/capability_registry.yaml` (new) — 29-entry capability matrix (16 OFFICIAL, 5 SUPPORTED, 1 EXPERIMENTAL, 7 UNSUPPORTED)
- `src/engine/capability.py` (new) — CapabilityRegistry reader with is_supported()/get_status()/all_capabilities()
- `tests/unit/engine/test_capability_registry.py` (new) — 9 unit tests
- `tests/architecture/test_capability_references.py` (new) — uniqueness guard
- `docs/engine/known_limitations.md` — added reference to capability_registry.yaml
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-209 (verified)

## Completion Summary
Created machine-readable capability registry (29 entries) covering all current engine features with OFFICIAL/SUPPORTED/EXPERIMENTAL/UNSUPPORTED status. Python reader exposes is_supported()/get_status() API. 10 tests pass. known_limitations.md updated to defer to registry for machine-readable state. INFRA-209 added to parity ledger.
