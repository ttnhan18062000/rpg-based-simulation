# Implementation Sequence — implement-ticket-native-port

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES  (no deps in this batch)
2. TCK-20260930-NATIVE-PORT-INPUT-SITES  (depends on: TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES)
3. TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP  (no deps in this batch)
4. TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES  (depends on: TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP, TCK-20260930-NATIVE-PORT-INPUT-SITES)
5. TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN  (depends on: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES; needs the user's Workflow opt-in)

## Why This Order Matters

Written by hand. The attestation design found a nonce-hash gate result forgeable by an agent told to cheat, so the
orchestrator-side re-run (child 3) must land before any gate is routed through the attested path (child 4): enforcement must not rest
on attestation. Advisory and bookkeeping sites come first because they carry the dispatch-cost batching decision the later children
inherit. The native run is last: it is the only child that needs a real Workflow run.
