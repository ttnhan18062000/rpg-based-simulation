# Implementation Plan E4 — Full RPG Logic Coverage

This plan covers the transition from strong partial coverage (~50-60%) to system-wide semantic coverage (~75-85%), starting with Phase E4.0: Coverage Ledger Completion.

## Goal
Turn `logic_checklist_exhaustive_v2.md` into a controlled proof ledger where every item has a stable ID, status, and linked evidence in source/tests.

## User Review Required

> [!IMPORTANT]
> This phase involves mass-editing the `logic_checklist_exhaustive_v2.md` to add stable IDs (e.g., `RPG-100`, `RPG-101`). This is necessary for machine-readable verification but will significantly change the file's structure.

## Proposed Changes

### Governance & Tooling

#### [MODIFY] [logic_checklist_exhaustive_v2.md](file:///home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive_v2.md)
- Assign stable IDs to all ~1600+ items.
- Format: `- [ ] [ID] Description <!-- VERIFIED v2: ItemKey -->`
- Ensure every `[x]` item has a `VERIFIED v2` marker.

#### [MODIFY] [protocol_validator.py](file:///home/vboxuser/Work/rpg-based-simulation/scripts/protocol_validator.py)
- Update parser to handle the new ID-based format.
- Add support for "DIVERGENT", "UNSUPPORTED", and "ENHANCED" statuses.
- Generate a detailed coverage report by subsystem.

### Source Verification

#### [MODIFY] Source files in `src/` and `tests/`
- Audit and add missing `VERIFIED v2` markers for previously completed work (Phases 1-10).

## Verification Plan

### Automated Tests
- Run `python3 scripts/protocol_validator.py` and ensure it correctly identifies checked items and their traces.
- Verify that the coverage percentage matches the claimed status.

### Manual Verification
- Spot-check 10 items from different subsystems to ensure the mapping between ID, description, and source is accurate.
