---
status: historical
layer: economy
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK
tags: []
---

# test_plan - TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK

## Tests
`tests/unit/engine/test_no_meat_decay_record_for_a_readded_carcass.py`: (1) partial meal on the decay tick, then the remainder decays the next tick; (2) the last meat eaten on the decay tick, no meat record at all; (3) control: a body that decays with nobody eating keeps its record. `tests/unit/engine/test_meat_decay_record_and_whole_loot.py` unchanged.

## Proof Plan
Proof type: regression plus a hash-neutral measurement. Cases 1 and 2 fail without the change (a 3.0 and a 1.0 record for a body that did not leave) and pass with it. The paired run (15 runs, start and final hashes and all counters equal except MEAT_DECAYED) shows no simulation effect.
