---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD
artifact_type: investigation
tags: [ai, process-improvement, governance]
---

# investigation — TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD

- After #506 SessionStart leases only `<main checkout>/.claude/worktrees/<placement>`; every seat launched elsewhere gets the "lease not taken" note, correct for the main checkout but wrong for asset/perf on ubuntu (`~/Work/rpg-aseprite-mcp`, `~/Work/rpg-perf`) and for implementer batch worktrees.
- The `worktrees:` section requires a writer per worktree and the validator makes each role's worktree exist; a main-checkout role therefore must name no worktree and no writer entry, which is why `Role.worktree` becomes `""` for it. Users of `role.worktree` were audited: guard (instance 2+ only), launch default path, hook manifest path, card, status, prune_branches.
- "First commit in a batch worktree" cannot be detected cheaply: the guard sees a command, not a batch. The recorded path comes from `launch.py --worktree`; a relaunch is the explicit bind. This was the open question; decided here.
- Card budget: the agent-working-planner card is within ~3 tokens of 400. Adding the graphify tools (batch item 1) and nothing else overflowed it; `tools/graphify_*.py` would have claimed `graphify_to_html.py` too. Fixed losslessly by a sibling-file brace merge in the card generator and by dropping "Owns `mechanisms.yaml` tooling only." from the domain card, which the Owns list (`tools/mechanism_registry/**`) and the route for `registries/mechanisms.yaml` already say.
- `validate.py` does not check the card budget; `tests/tools/test_session_cards.py` does. Run both.
