---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# test_plan

Proof: node run of checker on honest pass, honest fail, tampered exit_code (bad mac), cheat-subagent forgery (accepted), wrong-nonce control (rejected). Results in evidence.jsonl.

## Proof Plan
- level: prototype, node-run (no repo test; throwaway)
- proof kind: adversarial forgery attempt plus tamper and honest controls
- oracle source: `prototype/checker.js` `verifyAttestation` return value
- expected effect: honest results verify, tampered results are rejected, forged-by-cheating-agent result is accepted (documenting the weakness)
- selected commands: `node -e` over `prototype/*.txt` as recorded in `evidence.jsonl`
