# Plan — TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP

Narrowed to the same-tick HAZARD route (passive bio deaths moved to a follow-up; see the ticket).
1. `lifecycle.py`: add the same-tick `HAZARD` branch after the `COMBAT` check; reuse the `is_dead` dispatch.
2. Tests: rewrite the two pinned-defect tests in `test_entity_death_authority_boundary.py`.
3. Docs: death-trigger table row and open-gap note in `lifecycle_systems_contract.md`; parity entry PROG-126.
4. Out of scope: passive bio deaths, `apply.py`, DEFEAT/REBIRTH, hazard-overwrites-KILL.
