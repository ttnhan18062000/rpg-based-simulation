---
status: open
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260619-E-PHASE-PERMISSIONS
phase: open
date: 2026-06-19
tags: [phase-permissions, read-write-domains, architecture, infra, engine]
---

# TCK-20260619-E-PHASE-PERMISSIONS

## Title
Granular Phase Read/Write Domain Permissions (INFRA-155/156)

## Status
OPEN

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
- `docs/engine/authoritative_mutation_pipeline_contract.md`

## Related Code Areas
- `src/engine/pipeline.py` (phase declarations)
- `tests/architecture/` (existing architecture guard tests pattern)

## Assumptions / Open Questions
- What exactly do RPG-INFRA-155/156 specify? Read `infrastructure.yaml` entries before implementing

## Implementation Notes
Read the parity ledger entries first to understand the exact declaration format expected. Likely small (~30 lines of new declaration + ~20 lines of guard test).

After implementation: update `docs/parity_ledger/infrastructure.yaml` — set RPG-INFRA-155 and RPG-INFRA-156 to `status: verified` with `test_path` pointing to the new architecture guard test. Run `make knowledge-index-update` if any docs/ files are created or modified.

## Test Summary
- New file `tests/architecture/test_phase_domain_permissions.py`:
  - `test_each_phase_declares_read_write_domains()` — assert all 6 pipeline phases have declared `read_domains` and `write_domains` entries in phase config
  - `test_phase_does_not_access_undeclared_domain()` — static analysis or mock-instrumented run: assert no phase reads or writes a domain outside its declaration
  - `test_infra_155_and_156_verified_in_parity_ledger()` — load `infrastructure.yaml`, assert RPG-INFRA-155 and RPG-INFRA-156 both have `status: verified`

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
