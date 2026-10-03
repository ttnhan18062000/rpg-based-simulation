---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-SOCIAL-CONTRACTS
artifact_type: test_plan
tags: [cog, social, contracts]
---

# Test Plan: TCK-20260527-COG-SOCIAL-CONTRACTS

We will add a new test file: `tests/unit/strategic/test_social_contracts.py` covering:
- accepted recruitment/loan contract creates an active strategic project/objective.
- failed contract resolves with reduced trust/sentiment.
- previous betrayal reduces future contract acceptance.

We will run this combined test suite to verify correct behavior.
