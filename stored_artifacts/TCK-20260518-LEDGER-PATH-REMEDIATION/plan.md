# Remediation Plan: Release Gate Ledger Path Synchronization

## Purpose
Ensure 100% semantic and structural alignment between the exhaustive logic checklist (`docs/logic_checklist_exhaustive.md`) and the repository file locations, passing the M10 certification release gate without warnings or errors.

## Proposed Changes

### 1. `scripts/ledger_validator.py`
- Add `"OPT"` to the `DOMAINS` set (line 8) to approve the `RPG-OPT-NNN` taxonomy used in Milestone 3 performance optimization mechanisms.

### 2. `docs/logic_checklist_exhaustive.md`
- Systematically replace all incorrect relative test and source paths across sections Z14–Z18 and Z20 with their verified true locations.
- Specifically update paths for:
  - `RPG-WORLD-235`..`246`, `249`
  - `RPG-COMBAT-166`..`170`, `200`
  - `RPG-STRAT-195`, `197`, `200`
  - `RPG-SOC-113`, `114`, `116`, `200`
  - `RPG-RES-115`..`119`, `200`..`202`
  - `RPG-ECON-200`..`203`
  - `RPG-INFRA-175`, `178`, `187`, `189`, `193`..`203`
  - `RPG-DATA-136`..`140`, `142`
  - `RPG-PROG-141`
  - `RPG-OPT-001`..`014`

## Verification
- Run `python3 scripts/ledger_validator.py` to verify 0 critical errors and 0 warnings.
- Run `python3 scripts/release_gate.py` to confirm successful pre-existing artifact bundle and ledger validation.
- Run `pytest tests/certification/test_final_gate.py` to verify the automated CI suite passes successfully.
