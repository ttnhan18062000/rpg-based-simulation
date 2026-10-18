---
status: historical
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

## Results (2026-10-18)
- validated: frontmatter of the runbooks, the index and the record (no violations); `runbook_url` paths match the four runbooks.
- running locally: the drill ran twice on the 8-service subset (stop Loki; firing at about 3 m 39 s; resolved message about 4 m 42 s after the restart). The second run also proved the rendered summary and the failed-notification path. Record: `docs/runbooks/records/2026-10-18-target-down-drill.md`.
- Disk rule proven by query only, committed threshold 15 percent untouched; `docker stats` peak table recorded for the subset.
- Gaps: the `[resolved] GrafanaAlertingFailures` message was not seen before `down`; not the full profile; one local host.
