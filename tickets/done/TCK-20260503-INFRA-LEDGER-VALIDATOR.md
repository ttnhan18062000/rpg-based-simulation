---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260503-INFRA-LEDGER-VALIDATOR
phase: done
date: 2026-05-03
tags: [infra, ledger, validator]
---

# TCK-20260503-INFRA-LEDGER-VALIDATOR

## Title
Implement Engine Logic Ledger Validator

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Develop a diagnostic tool (`scripts/ledger_validator.py`) to programmatically verify the integrity of the `logic_checklist_exhaustive.md` registry. The validator must ensure ID uniqueness, domain taxonomy compliance, and presence of mandatory metadata (SOURCE, TEST, PROOF) for all checked items.

## Scope
- Create `scripts/ledger_validator.py`.
- Implement ID uniqueness check.
- Implement domain taxonomy check (`INFRA`, `WORLD`, `COMBAT`, `SOC`, `STRAT`, `PROG`, `DATA`, `ECON`, `RES`).
- Implement metadata presence check for `[x]` items.
- Implement codebase cross-reference check (verify that IDs used in `logic_checklist_exhaustive.md` actually exist in the `.py` source files).
- Provide detailed reporting of gaps.

## Out of Scope
- Fixing the gaps in the checklist (this tool only reports them).
- Modifying engine logic.

## Acceptance Criteria
- `scripts/ledger_validator.py` runs without errors.
- It accurately identifies duplicate IDs.
- It identifies items missing `SOURCE`, `TEST`, or `PROOF`.
- It identifies items with invalid domain prefixes.
- It reports total coverage statistics.
- It returns a non-zero exit code if critical violations (duplicates or missing metadata for checked items) are found.

## Related Tickets
- TCK-20260429-PH0-PROTOCOL-VALIDATOR (Prior art)

## Related Docs
- logic_checklist_exhaustive.md

## Related Code Areas
- scripts/
- src/

## Assumptions / Open Questions
- None.

## Implementation Notes
- Will use regex to parse the markdown table-like structure of the checklist.

## Test Summary
- Manual execution against the current checklist.
- Verify it catches intentional errors (I will temporarily introduce a duplicate to test).

## Files Changed
- scripts/ledger_validator.py
