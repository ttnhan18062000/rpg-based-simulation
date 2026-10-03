---
ticket_id: TCK-20260619-E12B-BLOCKER-RECAL
phase: test_plan
date: 2026-06-20
---

# Test Plan: blocker_penalty Recalibration

No code changed. Existing tests cover the scorer.

Verify:
```bash
pytest tests/unit/domains/adventure/test_phase3_route_scoring.py -x -v
```

After docs changes:
```bash
make knowledge-index-update
```
