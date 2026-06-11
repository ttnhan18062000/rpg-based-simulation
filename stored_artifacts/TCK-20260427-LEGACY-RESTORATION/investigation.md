---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260427-LEGACY-RESTORATION
artifact_type: investigation
tags: [legacy, restoration]
---

# Investigation: Legacy Code Disappearance

## Discovery
The legacy code (`src` and `tests` from the previous version) was removed in commit `6e5c289` ("Implement resource v2 enhanced phases").

## Restoration Strategy
- Locate the commit prior to deletion: `6e5c289^`.
- Restore directories to new names: `src_legacy/` and `tests_legacy/`.
- Verify if the restored code is the procedural V1 engine or a previous V2 draft.
    - Findings: The code at `6e5c289^` is a version of the V2 engine (using aspects). The user considers this "legacy" relative to the current hardening.

## Namespace Conflict
- Restored code originally used `src` and `tests`.
- Current project root already has `src` (Authoritative V2).
- Action: Global refactor of restored code to use `src_legacy` and `tests_legacy`.

## Import Issues
- Discovered `ModuleNotFoundError` due to `social.py` vs `social/` directory conflict in `src_legacy/systems/`.
- Resolved by renaming `social.py` and updating imports.
