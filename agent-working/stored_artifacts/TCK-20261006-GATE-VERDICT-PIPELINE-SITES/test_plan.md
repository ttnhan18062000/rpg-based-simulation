---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-VERDICT-PIPELINE-SITES
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test plan
Source-level conformance (the pipeline cannot run in a test): one emit site per policy entry, helper kind matches the gate type, each site precedes the last `writeMonitoring` of its fail status, a stripped site fails the check. `record_batch` and the CLI on a scratch repo: pass run writes one non-blocking row per gate; a run blocked at Review has the Review row `blocking: true` and no row for later gates; a bad row does not stop the rest; bad JSON exits 0 with a warning.

## Proof Plan
- level: unit
- proof kind: pytest
- oracle source: rows read back from a scratch shard; the script source
- expected effect: every gate has a recorded verdict path and ledger failure cannot stop a run
- selected commands: `pytest tests/tools/test_gate_verdict_pipeline_sites.py` and the workflow, gate-policy and native-refusal suites
