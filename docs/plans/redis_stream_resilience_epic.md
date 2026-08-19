---
status: active
layer: observability
authority: P1
audience: agent
tags: [observability]
---

# Epic Plan — Redis Stream Consumer Resilience

**Tracking ticket:** `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC`
**Source:** `docs/audits/D23_architecture_resilience.md` §D, §G, §K (R3)
**Priority:** P1

## Status
Resolved by `TCK-20260817-REDIS-STREAM-RESILIENCE-EPIC`. Both Problem items below now describe
pre-fix history: handler exceptions now retry via Redis's own `XPENDING`/`XCLAIM` PEL-reclaim
mechanism up to `MAX_DELIVERY_ATTEMPTS = 3` before routing to a derived `{stream_name}:dlq` DLQ
stream; malformed-payload ack+drop is unchanged; a process-death-before-ack orphaned PEL entry is
now reclaimed and redelivered rather than lost forever; `connect()` backs off with jitter (base
0.2s, doubling, capped at 30s, ±20% jitter) across consecutive failures, resetting on success,
with the first attempt after any reset never sleeping. Parity ledger entries
`INFRA-359`/`INFRA-360`/`INFRA-361` and a new §7 in `observability_hot_path_safety_contract.md`
document the new behavior.

## Problem

`src/observability/stream/consumer.py:79-102`, verified directly:

```python
except Exception as ex:
    logger.error(f"Error processing stream event {msg_id}: {ex}")
    self.client.xack(self.stream_name, self.group_name, msg_id)
```

A malformed payload and a transient handler failure (e.g. a downstream call timing out) are
handled identically — ACK'd and discarded. No dead-letter stream, no retry budget, no
distinction between "this will never parse" and "this failed once and might succeed on retry."
Separately: if the handler succeeds but the process dies before the `xack()` call, the message
sits in the consumer group's PEL (pending-entries list) forever — no `XCLAIM`/`XPENDING` logic
exists to reclaim it. On a sustained Redis outage, the reconnect loop
(`consumer.py:104-108`) retries roughly every ~100ms with no backoff or jitter — same shape as a
retry storm against a downstream dependency, just against Redis. Blast radius is bounded: this
stream is downstream of, not part of, the authoritative gameplay pipeline (Tier 3,
observability/anomaly-detection only) — real and silent, not catastrophic.

## Scope for the eventual `create-tickets` pass

- Separate malformed-payload handling (ack+drop is already correct) from handler-exception
  handling (bounded retry, then a literal DLQ stream on exhaustion).
- Add `XCLAIM`/`XPENDING`-based PEL reclaim so a message orphaned by a process death between
  handler success and ACK gets redelivered instead of vanishing permanently.
- Add backoff+jitter to the ~100ms reconnect loop.

## Out of scope

- Any change to the authoritative gameplay pipeline — this stream is explicitly Tier 3,
  observability/anomaly-detection only.
- Introducing a different message broker or a generic retry framework — the fix is scoped to
  this one consumer's existing failure-handling code.

## Acceptance signal for this epic (not yet broken into child tickets)

- A transient handler failure results in a bounded retry, then a DLQ entry — not silent discard.
- A malformed payload still results in ack+drop (unchanged, already correct).
- A simulated process-death-before-ack scenario results in eventual redelivery via PEL reclaim,
  not permanent loss.
- The reconnect loop backs off with jitter under sustained Redis unavailability.

## References

- `docs/plans/architecture_resilience_remediation_roadmap.md` (Epic D)
- `docs/audits/D23_architecture_resilience.md` (R3, Stage 1 items 2-3)
