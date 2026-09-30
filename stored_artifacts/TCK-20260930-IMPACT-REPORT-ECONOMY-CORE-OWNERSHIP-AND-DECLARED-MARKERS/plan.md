---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS
artifact_type: plan
tags: [testing]
---

# Plan

1. `core_rpg_report.DOMAIN_IMPORT_PREFIXES["economy"]` gains `src.core.conservation*` and `src.core.inventory*`. Conservation implements ch03 §1 (Atomic Conservation). Inventory implements ch03 §2 (slot and weight limits, `INVENTORY_FULL`; parity TOWN-011/012 in `town_resource.yaml`). Both stay substrate too, so a change names both owners and recommends the scenario level. Other `src/core/` modules are unchanged.
2. `impact_report._owners_of` returns every owner (gameplay domain first, then substrate).
3. For a changed test file, its declared `domain`/`level` markers are added as `declared-marker` domains and levels beside every other rule; they never override or duplicate one.
4. The ownership map (`architecture_design_notes.md` §3.1) Economy row is updated in the same change.
5. Tests: a 6th sample case (conservation), inventory, plain-substrate unchanged, declared markers added, never overriding.
