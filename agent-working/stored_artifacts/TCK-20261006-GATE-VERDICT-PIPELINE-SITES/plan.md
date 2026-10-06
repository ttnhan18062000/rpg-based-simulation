---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-PIPELINE-SITES
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Plan
1. `implement-ticket.js`: `pushGate` buffers a row at every `gate-policy.yaml` gate when it is reached, on pass and fail; `pushStaticGate` does the same only on the legacy runtime (on the native runtime `attest_gate.py` already records a static gate); `writeMonitoring` flushes the buffer once (Step 2c) with `gate_verdicts.py record-batch`.
2. `gate_verdicts.py`: `policy_gate_id` (the one id spelling per policy entry), `record_batch`, CLI `record-batch` that always exits 0.
3. Conformance test: every policy entry has an emit site and the site precedes the `writeMonitoring` that stops the run on it.

## Unresolved Questions

None.
