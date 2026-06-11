---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-AUTHORITATIVE-PATH
artifact_type: test_plan
tags: [cog, authoritative, path]
---

# Test Plan: TCK-20260527-COG-AUTHORITATIVE-PATH

We will add two new tests to `tests/unit/strategic/test_cognition_authoritative_path.py`:
1. `test_single_strategic_update_per_tick`
2. `test_tactical_consumes_selected_strategic_state`
And execute them along with existing unit tests to certify no regressions.
