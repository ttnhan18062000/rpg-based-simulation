---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING
phase: plan
date: 2026-10-28
tags: [observability, platform]
---

# Plan: TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING

1. docker/alloy/config.alloy (new): discovery.docker (proxy, 5s, project filter), discovery.relabel (drop loki|alloy, container, job), loki.source.docker, loki.process (stage.json 4 fields, stage.labels level+component), loki.write.
2. compose.yaml: alloy service replaces promtail (pin v1.20.1 index digest, mem_limit from measurement, bash /dev/tcp healthcheck on :12345/-/ready + loki:3100/ready, no socket mount, env COMPOSE_PROJECT_NAME, --disable-reporting, storage.path in container); grafana depends_on and proxy comments updated.
3. prometheus.yml job alloy:12345; rules-base.yaml LogShippingErrors expression and header comment; datasource.yml comment.
4. Delete docker/promtail-config.yml. Docs: log-shipping.md, target-down.md, README.md, loki_label_policy.md, dated record.
5. Drafts (not committed): test_loki_cardinality.py diff; before/after text files for devops_baseline_adr.md, system_overview.md, infrastructure_overview.md.
6. Proof run after lead's slot; fill record; close ticket and fold the epic close already in the branch.
