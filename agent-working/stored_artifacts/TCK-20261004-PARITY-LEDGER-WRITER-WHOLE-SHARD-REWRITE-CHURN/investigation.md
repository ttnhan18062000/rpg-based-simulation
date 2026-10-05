---
status: historical
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN
date: 2026-10-05
tags: [ai, process-improvement]
---

# Investigation: TCK-20261004-PARITY-LEDGER-WRITER-WHOLE-SHARD-REWRITE-CHURN

The parity-updater spec mandates `parity_ledger_writer.write_entry`, which ended in a whole-shard `yaml.safe_dump`. A real run (reported by rpg-feature-planning) deviated from the spec to avoid the churn. Measured here on the real infrastructure shard: a one-entry change rewrites 586 lines under the old writer. `ruamel.yaml` is not installed, so a text-span writer keyed on the position of column-0 list items was chosen, guarded by a parse-back equality check and a whole-dump fallback.
