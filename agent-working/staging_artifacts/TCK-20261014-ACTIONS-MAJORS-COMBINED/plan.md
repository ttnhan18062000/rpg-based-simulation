---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261014-ACTIONS-MAJORS-COMBINED
artifact_type: plan
tags: [platform]
---

# plan — TCK-20261014-ACTIONS-MAJORS-COMBINED

1. Branch from main and apply the four Dependabot diffs (cherry-pick, or re-apply the same version edits), keeping the tag-pin style.
2. Grep the touched workflows for uploads of hidden paths or duplicate artifact names, and report any to the owner. Do not change workflow logic in this ticket.
3. With the user's authorization: push, open a PR, and run one `workflow_dispatch` of rpg-gate-report on the branch.
4. Collect the evidence (test plan) into the PR body, including the deploy-docs and slow-regression post-merge notes.
5. Ask testing-planner and the other workflow owners for review by comment. The user merges, then closes #572-#575.
