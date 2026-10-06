---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT

Recorded at close (hand-orchestrated; folded into the Slow regression batch at the reviewer's request).

1. Measure both tests with `--resource-budget off`, sequentially, in a CI-equivalent environment; name the dominant cost by timing `subprocess.run` calls.
2. Re-budget with the existing `resource_budget_large` marker (no new tier, no assertion change) and write the reason in a comment and in the ticket.
3. Classify the edit-ratchet hook flake: 3 sequential runs; no quarantine.
4. Stop and report if a make target had genuinely become slow (it had not: the cost is a fixed 28 s git walk paid twice).
