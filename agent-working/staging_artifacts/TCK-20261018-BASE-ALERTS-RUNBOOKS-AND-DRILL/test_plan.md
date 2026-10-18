---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL
artifact_type: test_plan
tags: [platform, observability]
---

# Test plan: TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL

Written by platform-planner at filing (2026-10-18); the implementer updates it as the work changes.

## Proof Plan
| criterion | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| TargetDown fires and reaches ntfy | running locally | drill | Grafana alert state history + ntfy topic | pending, firing, received, then resolved | `docker compose stop loki` / `start loki`; Grafana alert API; ntfy `json?poll=1` |
| timeline recorded | running locally | record | measured timestamps | T0-T5 and detection/recovery times in the record | the record file |
| docs valid | static | frontmatter validation | the docs schema | OK | `python3 tools/validate_frontmatter.py docs/runbooks/*.md docs/runbooks/records/*.md` |
| topic not leaked | static | grep | none | no match | `git grep -n <local topic>` |

No `tests/**` changes (D-4).
