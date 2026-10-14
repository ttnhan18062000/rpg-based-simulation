# knowledge-stack-and-pre-push-lanes

One batch, one PR (owner policy). Dispatched 2026-10-14 by the user.

1. TCK-20261014-PRE-PUSH-CI-LANE-PARITY: start with testing-planner's agreement on the mapping.
2. TCK-20261014-KNOWLEDGE-STACK-PIN-AND-EMBEDDING-MAJOR: run the index rebuilds when RPG measurement load is
   light, after a disk headroom check. Independent of item 1.

If both are ready together with rpg-next, this PR merges after rpg-next.
3. TCK-20261014-KNOWLEDGE-STACK-FILES-OWNED (hotfix, added 2026-10-14 on the user's yes): roster owns lines for the
   knowledge stack; the owner confirms the session_roles.yaml diff on the PR. Independent of 1 and 2.
