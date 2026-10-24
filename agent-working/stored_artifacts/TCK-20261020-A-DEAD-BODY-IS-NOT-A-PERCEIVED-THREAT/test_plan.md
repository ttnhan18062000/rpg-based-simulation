---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT
tags: []
---

# test_plan - TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT

## Tests
`tests/integration/observability/test_a_dead_body_is_not_a_perceived_threat_through_the_real_kernel.py` (real kernel, crowded_frontier):
1. A corpse in view gives no PANIC_RETREAT (fails without the fix).
2. A live hostile in view still gives PANIC_RETREAT (passes both ways).
3. A hungry hp-2 raider with three townsfolk dead on its walk eats (fails without the fix).

## Other checks
Gate V3 on crowded 45 is 0. tests/unit/tactical and the cognition unit tests pass. Full tests/unit (serial, f9b21b55b): 8442 passed, 12 failed, of which 9 are pre-existing SimQ grade anchors (also red on 7b1528861) and 3 were this branch's own (one registry pin, fixed; two load-sensitive tests that pass when run alone).

## Proof Plan
Proof type: regression, through the real kernel. The three tests above fail on 7b1528861 for the corpse cases (1 and 3) and pass on the fix; test 2 (a live hostile still gives PANIC_RETREAT) passes both ways and guards against over-correction. The measured effect is the standard paired run (no drift, three worlds).
