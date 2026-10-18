# Implementation Sequence — devops-s4-base-alerts-local

Written by hand. One PR for the folder, from `platform-implementer-local-base-alerts`. Host ubuntu (#618).

## Order

1. TCK-20261018-BASE-ALERT-SCRAPES-AND-NODE-EXPORTER  (no deps)
2. TCK-20261018-GRAFANA-ALERTING-NTFY-AND-BASE-RULES  (needs 1: the rules read its series)
3. TCK-20261018-BASE-ALERTS-RUNBOOKS-AND-DRILL  (needs 1-2: the drill fires a rule from 2; heavy-ish, one stack run asked of lead-planner)

Epic: TCK-20261018-EPIC-DEVOPS-S4-BASE-ALERTS-LOCAL (closes last).

## Why This Order Matters

1 and 2 both edit `compose.yaml`, so they run in sequence. The drill is the end-to-end proof of 1 and 2, so it is last.
Image pulls (node-exporter, ntfy) and the drill's stack run are asked of lead-planner first, one at a time; pulls alone.

## Relation to step 3

Step-3 `TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK` (blocked on #622 R2) reuses the ntfy service, contact point and notification policy built here and adds
only its own rule group and runbook. Its ticket is amended in this folder's filing commit.
