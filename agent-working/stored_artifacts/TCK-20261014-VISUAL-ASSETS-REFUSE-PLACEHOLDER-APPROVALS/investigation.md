---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS
artifact_type: investigation
tags: [architecture, testing]
---

# Investigation: TCK-20261014-VISUAL-ASSETS-REFUSE-PLACEHOLDER-APPROVALS

The command template printed `<your name>`, `<your role>` and `<your own evidence reference>`; `check_licence_and_approver` refused only empty text and the NOT_APPLICABLE/UNAVAILABLE markers, so the placeholders were recorded in `sa-6690e2619d4abb3e` and its 18 adoption records. Records are immutable and revoked bytes cannot be re-adopted (setadoption: same bytes not adopted or revoked), so the owner chose to keep the records and add an erratum. Templates with `<...>` also remain in the closed docs `icon_set_v2_review.md` and `icon_key_set_review.md` (left unchanged, historic) and in `visual_assets/review/review_sheets.py` (warning added).
