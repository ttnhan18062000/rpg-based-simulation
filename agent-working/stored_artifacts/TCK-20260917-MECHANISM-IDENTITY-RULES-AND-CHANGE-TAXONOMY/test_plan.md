---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY
artifact_type: test_plan
tags: [architecture, documentation, schema]
---

# Test Plan — TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY

## Registry validation

`python3 tools/mechanism_registry/registry.py registries/mechanisms.yaml` → `OK: registries/mechanisms.yaml valid, 93 mechanisms` (up from 89: 4 splits × 2 successors each = 8, minus the 4 original bundled ids removed = net +4).

## Consumer artifact propagation

- `mechanism_atlas_regenerate.py --check` and `mechanism_capabilities_regenerate.py --check`: both
  ran to completion cleanly after correcting the 3 stale mapping-table entries (each split card's
  single existing badge repointed at the successor id its own real prose describes) and applying
  the 2 resulting `cls`/`tier` fixes (`action_pacing_readiness` done, `regional_trauma`
  built/contradicted).
- `mechanism_wiring_map_classdef.py --check`: unaffected (only cites the unchanged
  `action_pacing_readiness` id), confirmed still passing.
- All 4 generated views (`mechanism_verification_view.md`, `mechanism_priority_view.md`,
  `mechanism_registry_view.md`, `mechanism_registry.html`) regenerated, now reporting 93
  mechanisms.

## Regression suite

```
.venv313/bin/python3 -m pytest tests/unit/tools/ tests/unit/engine/test_capability_registry.py \
  tests/mechanic_scenarios/ -q
```
→ 181 passed. Four pre-existing pinned tests needed real, explained updates (see investigation.md)
— none were routed around; each reflects a genuinely new fact about the registry
(`readiness_speed_scaling`'s own new dependent edge, `tactical_decision`'s own removed edge, the
corrected `regional_sovereignty` binding resolving a real finding rather than accepting a wrong
one, and the atlas-mapping unmapped set growing by the 4 new uncited split halves).

`graphify-out/` was moved aside and restored for this ticket's own test run, since
`registries/mechanisms.yaml` and two `tools/mechanism_registry/*_card_mapping.py` files changed
(data/mapping changes, not `src/`/`tests/` code — no `graphify update .` needed per the project's
own convention, but the standard move-aside-and-restore re-verification was still performed as a
sanity check).

## Doc validation

`python3 tools/validate_frontmatter.py docs/plans/mechanism_identity_and_change_taxonomy.md --content-type doc` → `OK: 1 file(s) checked — no violations`.
