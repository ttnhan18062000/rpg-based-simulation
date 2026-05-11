# TCK-20260510-CHECKLIST-HARDENING

## Title

Hardening RPG Engine Logic Ledger

## Status

DONE

## Request Summary

Restore the reliability of the RPG Engine logic checklist by transitioning it into an auditable truth ledger. Downgrade "false-green" items, fix stale paths and duplicate IDs, and establish a strict validation gate.

## Scope

- Create a checklist validator script.
- Remediate `logic_checklist_exhaustive.md` by downgrading unproven rows.
- Fix duplicate IDs and stale paths in the checklist.
- Integrate the validator into the release gate.

## Out of Scope

- Implementing new gameplay logic.
- Re-greening all rows (this is a multi-phase effort).

## Acceptance Criteria

- `logic_checklist_exhaustive.md` passes `scripts/validate_checklist.py`.
- No `[x]` rows exist without valid `SOURCE/TEST/PROOF` markers.
- Duplicate IDs are resolved.
- Stale source/test paths are corrected.
- `scripts/release_gate.py` fails if the checklist is invalid.

## Related Tickets

- None

## Related Docs

- logic_checklist_review.md

## Related Stored Artifacts

- None

## Related Code Areas

- logic_checklist_exhaustive.md
- scripts/validate_checklist.py
- scripts/remediate_checklist.py
- scripts/release_gate.py

## Assumptions / Open Questions

- Assumed that `[x]` rows without markers were "false-greens" and safe to downgrade for audit purposes.

## Implementation Notes

- Used a remediation script to automate the downgrade and ID renaming.
- Standardized marker IDs to match Row IDs.
- Fixed specific paths for `COMB-013`, `STRAT-001`, and `STRAT-007`.

## Test Summary

- Ran `scripts/validate_checklist.py` and confirmed pass.
- Ran `scripts/release_gate.py` and confirmed it triggers the checklist check.

## Files Changed

- logic_checklist_exhaustive.md
- scripts/validate_checklist.py
- scripts/remediate_checklist.py
- scripts/release_gate.py

## Completion Summary

- The checklist is now an authoritative ledger. Only proven logic remains marked `[x]`.
- A machine-readable validator ensures future additions are properly proven.
- The ledger is prepared for the next batch of re-greening.
