---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH
tags: [testing, bug]
---

# Plan — TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH

## Approach
1. Add `schedule` (nightly cron) and `workflow_dispatch` triggers to `.github/workflows/test.yml`
   at the workflow level.
2. Change the `slow` job's `if:` condition to drop `github.base_ref == 'main'`, add
   `github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'`, keep
   `github.ref == 'refs/heads/main'`.
3. Update the 2 historical docs that describe the old "gated to PRs targeting main" behavior as
   current, via appended dated notes (not rewrites).

## Scope guards
- No change to fast-lane job trigger conditions — unaffected, still run on every PR push.
- No change to the `slow` job's own steps or `needs:` chain.
- No change to any test file or `src/` file.
- No GitHub repository branch-protection settings touched (outside this repo's own files).

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| YAML valid | `python3 -c "import yaml; yaml.safe_load(...)"` |
| `slow` no longer gated to PR push | Direct diff review of the `if:` condition |
| New triggers added | Direct diff review of the `on:` block |
| Docs updated for parity | 2 appended notes, reviewed |
