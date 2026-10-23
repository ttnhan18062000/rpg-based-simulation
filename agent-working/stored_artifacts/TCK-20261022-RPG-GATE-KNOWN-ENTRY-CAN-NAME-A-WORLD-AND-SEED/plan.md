---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED
artifact_type: plan
tags: [testing, regression]
---

# Plan

1. `known_reds.py`: `cases` becomes an optional field of `RPG_GATE_SPEC` only. New `owner_of_finding(test_id, finding, known, state)` (scoped entry owns a run-scope fail only when its (world, seed) is a case and, if the case names an entity, `violations == len(examples)` and every example id is a case id), `stale_cases`, lint for malformed/empty/overlapping cases, `cases` on drift or in the slow registry, and the shadow lint skips a scoped earlier entry. `owner_of`, `classify` and `stale_mappings` skip scoped entries, so the slow registry and the missing-required-row path keep their string meaning.
2. `rpg_gate_report._ownership` and `rpg_gate_candidate._omissions` call `owner_of_finding`; `stale_known_entries.fail` also lists stale cases.
3. `rpg_gate_baseline.rebaseline` finds an omission's owner by match AND ticket, since scoped entries share `V3`.
4. `rpg_gate_known.yaml`: the blanket V3 entry becomes N14 and N15 scoped entries; V1 unscoped; expires_on 2026-11-05.
5. Docs: format doc and yaml header describe `cases`.
