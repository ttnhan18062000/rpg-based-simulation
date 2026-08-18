---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH
tags: [testing, bug]
---

# Test Plan — TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH

## Commands and results
```
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"
```
`YAML valid` — no output on success confirms parseable syntax.

## Trigger-matrix reasoning (manual, not executable from this sandbox)
| Event | `github.event_name` | `github.ref` | `slow` job's `if:` result |
|---|---|---|---|
| `pull_request` (PR push) | `pull_request` | PR head ref | **false** (skipped — the change) |
| `push` to `main` | `push` | `refs/heads/main` | true (unchanged) |
| `schedule` (nightly) | `schedule` | default branch | true (new) |
| `workflow_dispatch` | `workflow_dispatch` | selected branch | true (new) |

## Known verification gap
Could not trigger a real `schedule` or `workflow_dispatch` GitHub Actions event from this
sandbox — both require either waiting for the actual cron time or a live `gh workflow run`
dispatch against the real repository, neither of which this investigation performed. The
trigger-matrix reasoning above is a manual correctness argument, not an executed test. Flagged
honestly rather than claimed as verified.

## Final status
YAML-valid, logically-reasoned-correct change. Live GitHub Actions trigger behavior for the 2 new
event types not directly observed.
