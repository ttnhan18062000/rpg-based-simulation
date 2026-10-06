---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# investigation

Written after the fact, from what was read; no new measurement.

- Sources: `design.md` and `prototype/` of `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN`; `classification.md` of `TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION`; the nine remaining bare `bash(` sites in `implement-ticket.js` after the two earlier children (`workflow_bash_sites.py` listed 9).
- The ticket says "7 gate and 3 control sites"; the file had 9 sites left because the input child already ported the others. `touchedOutput` is class input, attested because it feeds the parity cross-reference gate.
- Every one of the nine scripts prints its result with exit 0 (python `print`, `git status`), so a non-zero exit means the command itself broke; treating it as a failed attestation is correct.
- Facts that changed the prototype: gate commands contain quotes, newlines and `'''`, so passing them as argv through an agent prompt is fragile (base64); the runtime's probed globals have no `unescape`, `btoa` or `Buffer` (own encoders, checked against Python in `test_attest_gate.py`).
- Not done, and why: a native `Workflow` run (that is the next child, which needs the owner's opt-in); a payload-hash check of the agent-reported stdout (an agent transcribing stdout can change trailing whitespace, which would fail honest runs).
- Cost: nothing is added beyond the dispatch each site already needs natively; the design's ~450k tokens / ~3 min per run if all nine are reached is an extrapolation, unmeasured here.
- Residual risk, unchanged from the design: a cheating agent forges a pass inside a native run; caught only by the orchestrator re-run of `done_checker_static.py` and CI. `test_forgery_with_the_known_nonce_passes` pins this limit.
