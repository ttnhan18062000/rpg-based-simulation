---
status: active
layer: testing
authority: P3
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

`tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`: the share test asserts the pooled share over both seeds; the module fixture runs both episodes once; the hard preconditions hold per seed. Run: `pytest tests/integration/campaigns`.

## Proof Plan
- **Level**: integration (campaign episode).
- **Proof kind**: before/after measurement with identical repeat runs; the pooled assertion passes after, and also passed before (0.4960), so it guards the co-location artefact, not the AGENCY-07 fix.
- **Oracle source**: the test's own threshold (`< 0.5`), unchanged, and test-architecture-reviewer's ruling on the pooled reformulation.
- **Expected effect**: the strict xfail no longer applies; the test passes with a real margin (0.4363 pooled).
- **Selected commands**: `pytest tests/integration/campaigns -q`; `share_probe.py` for seeds 42 and 1337, two runs each.
