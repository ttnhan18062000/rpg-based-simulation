---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-TEST-BASELINE-POST-REPAIR
artifact_type: investigation
tags: [testing]
---

# Investigation: post-repair core-RPG test baseline

- The first attempt at these runs was killed when the session closed; both runs were relaunched fully detached (setsid), from a clean reset of the worktrees.
- Combined-run failures observed earlier (10 failures + 1 error, identical on origin/main) are the expected unknowns; they must be re-measured here, not copied.
- Producer classification is a v0 heuristic. After the reviewer's correction its import signals follow the ownership map (`architecture_design_notes.md` §3.1), giving 183 candidate files against the planner's 204; the first draft used a broader rule (326) that treated pipeline/kernel as gameplay and had a prefix-matching bug.
