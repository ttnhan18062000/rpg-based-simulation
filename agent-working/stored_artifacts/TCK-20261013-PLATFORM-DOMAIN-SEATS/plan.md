---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-PLATFORM-DOMAIN-SEATS
artifact_type: plan
tags: [ai, governance, process-improvement]
---

# plan — TCK-20261013-PLATFORM-DOMAIN-SEATS

1. Cut `platform-domain-seats` from origin/main, take the planner's ticket commit.
2. Apply the confirmed `session_roles.yaml` diff; run `validate`. On rejection stop and report (done: 9 glob findings; owner chose to list only existing paths).
3. Add the `platform` domain card source; regenerate `.claude/agents/`.
4. Update role-count tests and add routing/card tests.
5. Close by hand, open one PR quoting the registry hunk, file the `for:lead-planner` issue.
