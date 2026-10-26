---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261025-RPG-UBUNTU-SEATS
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# Test plan
## Proof Plan
- Route diff, origin/main vs new registry, all 18288 tracked paths: 0 owner/status/seat changes (measured).
- New tests: twins copy their plain role, take dispatch only from user and same-host roles, route names rpg-planner, distinct writer slots, every rpg card within 460.
- Full tests/tools/test_session_*.py plus the paths guard, serial, MemoryMax 3G: 813 passed, 1 timing failure (test_a_hanging_gh_is_cut_off_at_the_timeout took 5.07 s against a 5 s limit under load); it passes alone and in a file rerun (75 passed).
- Level: unit and registry-wide measurement. Proof kind: tests plus a route diff. Oracle source: the origin/main registry's routes and the 460-token card budget in tools/sessions/card.py. Expected effect: three roles resolve and fit; no route changes. Selected commands: `pytest tests/tools/test_session_*.py tests/tools/test_agent_working_paths_guard*.py`, `python3 -m tools.sessions.generate_agents --check`.
