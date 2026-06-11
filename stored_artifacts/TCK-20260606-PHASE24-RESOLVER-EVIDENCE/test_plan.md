---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260606-PHASE24-RESOLVER-EVIDENCE
artifact_type: test_plan
tags: [phase24, resolver, evidence]
---

# Test Plan - Phase 24 Resolver layer claims and evidence fields

We will run the content unit tests to verify:
- Resolver-only families are correctly set to `RESOLVED_PARTIALLY`.
- New evidence fields exist and are validated.
- Validation checks for resolver fetching exist.

## Automated Tests

Run:
```bash
pytest tests/unit/content/
```
