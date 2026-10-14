---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS
artifact_type: investigation
date: 2026-10-09
tags: [architecture, testing]
---

# Investigation

- 62 keys: 36 icon, 23 terrain, 3 border. Class/fallback existed only as prose: 35 icon keys say identifying, the plate decorative (the plate's description says 'decorative class'); terrain descriptions say 'the colour fill is its fallback'; borders are decorative per `fallback_safety.md` (D19).
- Which tests ride the registry: after this change (registry hash moved) the fixture guards, icon fixtures (`--check`) and the 8 inventory pins all pass; only five tests needed edits, all about loader rules: the contract YAML fixture had an axis, one test used a `real.*` key without a class, and the maximal-registry test used axes.
- Registry size: a realistic maximum with the new fields is 414942 B (90 % of `MAX_REGISTRY_BYTES`), loads in 0.75 s; recorded in `budgets.md`.
- `m1_contract_register.md`: W02.7, W03.1, W06.3 re-derived to MET: 58 MET / 4 GAP / 6 N/A; W02, W03, W06 CLOSED; the `AM-M1` result stays BLOCKED (M0 INCONCLUSIVE).
