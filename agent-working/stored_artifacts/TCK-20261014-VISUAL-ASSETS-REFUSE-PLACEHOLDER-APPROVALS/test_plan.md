---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS
artifact_type: test_plan
tags: [architecture, testing]
---

# Test plan: TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS

Proof Plan: level unit; proof kind: refusal tests; oracle: the refusal code and an unchanged catalog snapshot; expected effect: each of approver, role, licence evidence (adopt, adopt-set) and reason, approver, role (revoke) holding a `<...>` span or a placeholder word is refused with `placeholder_value` and nothing is written; real values still pass; the committed placeholder set adoption still loads and `verify` stays empty. Commands: pytest tests/visual_assets/store/unit/test_adoption.py test_revoke.py test_drafts.py tests/visual_assets/test_review_sheets.py.
