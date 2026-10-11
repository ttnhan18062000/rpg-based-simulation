---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD
artifact_type: plan
tags: [ai, process-improvement, governance]
---

# plan — TCK-20261010-SESSION-MAIN-CHECKOUT-LAUNCH-AND-BATCH-WORKTREE-RECORD

## Decision: a new `placement.launch` value, not a function default
`placement: {launch: main-checkout, max_sessions: 1}` (default `worktree`). A function default would flip every planner and designer at once, including those on host u24desktop that have their own worktrees and cut PR branches from them; a per-role value changes only the roles the owner decision names. Applied to `asset-planner` (needs no worktree) and `lead-planner`; the other planners and designers are one yaml line each once the owner says so.

## Steps
1. `roster.py`: `Role.launch` (default `worktree`), `worktree` optional when `launch: main-checkout`.
2. `validate.py`: rule `launch-contradiction` (names a worktree, is a worktree's writer, or is an implementer); `bad-field` for an unknown mode.
3. `card.py`: the role line reads "Launches from the main checkout, no lease"; plus a lossless brace merge for sibling plain files (`tools/graphify_{link,prune}.py`) so the card stays within 400 tokens.
4. `launch.py`/`guard.py`/`status.py`/`prune_branches.py`: a main-checkout role's default path is the main checkout; empty `worktree` is skipped.
5. Record: `state.write_bound_worktree/read_bound_worktree` (`worktree.json` in the instance's role state); `launch.py` writes it on a real launch for `worktree` roles (`explicit` = `--worktree` was passed); SessionStart leases the manifest worktree OR the recorded one; `status.py` shows `writing in: <path>`.
6. Cards/docs: planner and designer `## Worktree`, plan §4, §8, §12.3.

## Scope guard
No pruning or creation of batch worktrees; no first-commit detection; no cross-host record (E3).
