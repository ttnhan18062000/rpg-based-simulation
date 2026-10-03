# Implementation Sequence — http-admission-control

Tickets must be implemented in this order. Generated from the intra-batch dependency
found during `TCK-20260817-HTTP-ADMISSION-CONTROL-EPIC`'s Investigate phase (2026-08-23):
admission control needs a client identity to key per-client state on, which auth provides.

## Order

1. TCK-20260823-HTTP-API-KEY-AUTH  (no deps in this batch)
2. TCK-20260823-HTTP-PER-CLIENT-ADMISSION-CONTROL  (depends on: TCK-20260823-HTTP-API-KEY-AUTH)

## Why This Order Matters

Per-client admission-control state (mode/dwell-tick tracking per client) is keyed by client
identity. That identity doesn't exist as a first-class concept in the request pipeline until
auth lands — running admission control first would mean inventing a throwaway client-identity
concept now and reconciling it with the real one later.
