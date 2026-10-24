---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY
artifact_type: test_plan
tags: [delivery, process-improvement]
---

# Test plan

`tests/tools/test_delivery_pre_push_advisory.py` check E cases: fires with a docs change and with a ticket change; silent with no registry source (and the `--check` run is not invoked); silent when current (rc 0); silent on rc 1 (timeout/error) and rc 3; silent when the command raises or the diff fails.

## Proof Plan

- level: unit (tools lane)
- proof kind: behavioural tests with the injected `run_command`
- oracle source: the ticket's acceptance criteria
- expected effect: one advisory line only on a stale registry with a registry-source change; the hook still exits 0
- selected commands: `pytest tests/tools/test_delivery_pre_push_advisory.py tests/tools/test_agent_working_paths_guard*.py`
