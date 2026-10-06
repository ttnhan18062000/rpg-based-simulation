---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GUARD-OWN-BRANCH-GIT-ALLOWED
artifact_type: investigation
tags: [ai, process-improvement, governance]
---

# investigation

Written during the work.

- Why it asked: `decide` asked for commit/push/open_pr when no lease existed; the lease is taken only by the role launcher; implementer `needs_user` listed push/open_pr. Confirmed in `guard.py` and `session_authority.yaml` on this branch.
- `classify.py` is pure, so a bare `git push` cannot name its destination: it is flagged `push_implicit` and the guard asks git for the cwd's branch.
- Decisions beyond the ticket text: (a) `git push --all/--mirror` counts as `push_default_branch`; (b) `git -C`/`--git-dir` and a same-call `git checkout|switch` before a commit or push are uncertain, because the cwd's branch is not what is acted on; this changed one existing classify test row (`git -C ../other commit`), now asserted as uncertain; (c) a literal `cd`/`pushd` before the commit or push is resolved (the branch at that directory decides); an unresolvable one, or one after the action, is uncertain. First version ignored `cd`, which let `cd ../wt-on-main && git push` through on a feature-branch session: found in review and fixed; (d) `--tags` alone pushes no branch.
- Force-push to the role's own branch is allowed, as the owner's rule says; the PR notes it as a visible choice.
- Card budget: the yaml change adds `push_default_branch` to every function's `needs_user`; designers and planners already never push, so the card skips the redundant item. rpg-designer stays 398 and agent-working-planner 395.
- Not done: AC7 live probe in a real role-resolved session (this session's own commit and push ran under the owner's existing grants, so it proves nothing about the new rule).
