# Implementation Sequence — implement-ticket-native-port

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order.

## Order

1. TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES  (no deps in this batch)
2. TCK-20260930-NATIVE-PORT-INPUT-SITES  (depends on: TCK-20260930-NATIVE-PORT-BOOKKEEPING-ADVISORY-SITES)
3. TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP  (no deps in this batch)
4. TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES  (depends on: TCK-20260930-NATIVE-PORT-ORCHESTRATOR-BACKSTOP, TCK-20260930-NATIVE-PORT-INPUT-SITES)
5. TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN  (depends on: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES; needs the user's Workflow opt-in)

## Partial run (user decision, 2026-10-01)

Only items 1-3 are run now. Items 4 (ATTESTED-GATE-SITES) and 5 (SMALL-TICKET-NATIVE-RUN) are deliberately deferred: the design
measured about 450k tokens and about 3 minutes extra per run if all 9 gate sites are reached, so the user decides on them after
seeing the cheap children's measured cost. The epic stays OPEN; this is a recorded exception to the epic all-or-nothing rule,
not a violation of it. Do not run `implement-epic` on this folder expecting items 4-5 to be skipped silently: they are the
remaining work.

## Why This Order Matters

Written by hand. The attestation design found a nonce-hash gate result forgeable by an agent told to cheat, so the
orchestrator-side re-run (child 3) must land before any gate is routed through the attested path (child 4): enforcement must not rest
on attestation. Advisory and bookkeeping sites come first because they carry the dispatch-cost batching decision the later children
inherit. The native run is last: it is the only child that needs a real Workflow run.
