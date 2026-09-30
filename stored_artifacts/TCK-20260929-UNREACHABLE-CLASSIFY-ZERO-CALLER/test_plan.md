---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER
artifact_type: test_plan
tags: [investigation, root-cause, corpus, world]
---

# Test Plan — TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER

No repo test change (no `src/`/`tests/` edit). Verification was direct: repo-wide greps with the exact commands and
outputs recorded in each covered ticket's body, `git log -S` / `git log --since=<filed>` drift checks, and one
execution of `tools/perf/profile_api_payload.py --ticks 5 --seed 42` (fails with ImportError). No regression risk;
the natural home for a regression pin (e.g. an architecture test that fails if the orphan class gains a caller, as
the wave did for `apply_calamity_consequences`) is the future fix ticket.
