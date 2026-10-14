---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS
artifact_type: plan
tags: [architecture, testing]
---

# Plan: TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS

Add one pure check, `check_not_placeholder`, to `visual_assets/store/adoption.py`; call it from `check_licence_and_approver` (adopt, adopt-set) and from `revoke` before any read or write. Refuse any `<...>` span and whole-value placeholder words with code `placeholder_value`. Existing records are never re-validated. Add a warning line to the owner-command builders. Record the owner's erratum in `docs/assets/store_contract.md` and child 2's ticket.
