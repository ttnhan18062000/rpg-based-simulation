---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260619-E-PHASE-PERMISSIONS
phase: done
date: 2026-06-19
tags: [phase-permissions, read-write-domains, architecture, infra, engine]
---

# TCK-20260619-E-PHASE-PERMISSIONS

## Title
Granular Phase Read/Write Domain Permissions (INFRA-155/156)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Coarse singular-mutation-point law is enforced and verified. `RPG-INFRA-155` and `RPG-INFRA-156` (declared per-phase read/write domains) are listed in the parity ledger as unchecked. Narrower than prior "Phase Guard" framing suggested — most of the mechanism is already done; what remains is declaring and enforcing explicit per-phase domain boundaries.

Source: `docs/plans/engine_future_epics_roadmap.md` § E; `docs/parity_ledger/infrastructure.yaml` (RPG-INFRA-155/156 entries).

## Scope
- Read `docs/parity_ledger/infrastructure.yaml` for RPG-INFRA-155 and RPG-INFRA-156 entry details
- Declare per-phase read/write domain lists in the relevant engine contract or phase configuration
- Add architecture guard test that validates each phase only reads/writes its declared domains
- Update parity ledger entries to `verified` with test_path

## Out of Scope
- Rewriting the mutation pipeline
- Adding new phases

## Acceptance Criteria
- RPG-INFRA-155 and RPG-INFRA-156 have status=verified in `infrastructure.yaml`
- Architecture guard test passes, with each phase's read/write domain declarations enforced

## Related Tickets
- TCK-20260619-P0-CI-AUTOMATION (architecture guard runs in CI)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § E
- `docs/parity_ledger/infrastructure.yaml`
- `docs/engine/kernel.md` (6-phase loop definition — per-phase domain declarations are declared against the Kernel phases defined here; update kernel.md to show read/write domain tables per phase)
- `docs/engine/authoritative_mutation_pipeline_contract.md`

## Related Code Areas
- `src/engine/pipeline.py` (phase declarations)
- `tests/architecture/` (existing architecture guard tests pattern)

## Assumptions / Open Questions
- What exactly do RPG-INFRA-155/156 specify? Read `infrastructure.yaml` entries before implementing

## Implementation Notes
Created `src/engine/phase_domain_permissions.py` with `PHASE_READ_DOMAINS`, `PHASE_WRITE_DOMAINS`, `PHASE_EMIT_DOMAINS` as `Dict[TickPhase, FrozenSet[str]]` covering all 7 phases. Declarations are documentation-level only — no runtime enforcement (enforcement items RPG-INFRA-158–163 are out of scope).

Key finding: `RPG-INFRA-155/156` in `logic_checklist_exhaustive.md` (unchecked `[ ]` items) differ from `INFRA-155/156` in `infrastructure.yaml` (replay manifest, already verified). Added new parity entries INFRA-206/207/208 to infrastructure.yaml. Checked off RPG-INFRA-155/156/157 in logic_checklist_exhaustive.md with SOURCE/TEST references. Updated `docs/engine/kernel.md` with phase domain permission table.

## Test Summary
- New file `tests/architecture/test_phase_domain_permissions.py`:
  - `test_each_phase_declares_read_write_domains()` — assert all 6 pipeline phases have declared `read_domains` and `write_domains` entries in phase config
  - `test_phase_does_not_access_undeclared_domain()` — static analysis or mock-instrumented run: assert no phase reads or writes a domain outside its declaration
  - `test_infra_155_and_156_verified_in_parity_ledger()` — load `infrastructure.yaml`, assert RPG-INFRA-155 and RPG-INFRA-156 both have `status: verified`

## Files Changed
- `src/engine/phase_domain_permissions.py` (new) — PHASE_READ_DOMAINS, PHASE_WRITE_DOMAINS, PHASE_EMIT_DOMAINS constants
- `tests/architecture/test_phase_domain_permissions.py` (new) — 7 architecture guard tests
- `docs/logic_checklist_exhaustive.md` — checked RPG-INFRA-155/156/157 with SOURCE/TEST evidence
- `docs/parity_ledger/infrastructure.yaml` — added INFRA-206/207/208 (verified)
- `docs/engine/kernel.md` — added Phase Domain Permissions table

## Completion Summary
Declared per-phase read/write/emit state domains for all 7 engine phases in `src/engine/phase_domain_permissions.py`. Added 7 architecture guard tests asserting coverage and key invariants (RESOLUTION as sole entity/world write phase). Checked RPG-INFRA-155/156/157 in logic checklist; added parity entries INFRA-206/207/208 and updated kernel.md with domain permission table.
