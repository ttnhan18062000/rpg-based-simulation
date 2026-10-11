---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD
artifact_type: test_plan
tags: [ai, process-improvement, governance]
---

# test_plan — TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD

## Cases
- validator: a main-checkout planner is accepted; naming a worktree, staying a writer, or being an implementer is `launch-contradiction`; an unknown mode is `bad-field`; the real manifest has asset-planner and lead-planner main-checkout, neither a writer
- launcher: a main-checkout role's default path is the main checkout; a real launch with `--worktree` records `(realpath, True)`; a dry run records nothing; unreadable records read as none
- hook: the recorded batch worktree takes the lease and the main checkout does not; an out-of-tree placement (perf) leases where it writes; a session outside both names both; no record keeps the manifest behaviour; a main-checkout seat takes no lease and prints no lease note
- status: `writing in: <path>` for an explicit record only; main-checkout seats listed as such
- cards: sibling-file brace merge and its non-merging cases; every card within 400 tokens

## Proof Plan
- level: unit/integration over real git worktrees (tmp repos) and the real manifest
- proof kind: behavioural tests plus validator and generator runs
- oracle source: ticket acceptance criteria 1-5 and the owner decision of 2026-10-10
- expected effect: read-mostly seats launch from the main checkout without a lease; an implementer's batch worktree (or an out-of-tree placement) holds the lease and is shown by status.py
- selected commands: `python -m pytest -q tests/tools/test_session_*.py tests/tools/test_graphify_link_and_prune.py tests/docs`; `python3 -m tools.sessions.validate`; `python3 -m tools.sessions.generate_agents --check`
