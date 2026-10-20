---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS
artifact_type: test_plan
tags: [architecture, testing, mcp]
---

# Test plan

Nothing is drawn or registered in this first stop, so there is nothing to run yet beyond the documentation gates (frontmatter and registry on the planning commit).

Later phases (filled in as they start):
- Spec table: `tests/visual_assets/test_icon_specs.py` must pass with the 11 new specs (the generated table in `icon_style_guide.md` regenerated with `python -m visual_assets.review.icon_specs --table`).
- Registry: the registry validator and `test_budgets_parity` pass; the registry stays under `MAX_REGISTRY_BYTES` (expected about 47.6 KB of 458,752 B).
- Draft set: lint and the existing icon criteria (I1 shape, I2 value, I3 contrast) pass for all 11; the compliance table lists every kind against its spec.
- Recognisability: blind naming check by two fresh agents, with the distractors from `investigation.md`; each marker must be named by at least the synonyms in its spec; misreads are reported, not tuned away.
- Sample-map tool test: every kind in the red set resolves to the new family, none to a class icon.
- Heavy runs (full `tests/visual_assets`, art runs) only in a slot cleared by asset-planner and lead, one at a time, foreground, MemoryMax=3G, own `--basetemp`.

## Proof Plan
- Level: unit plus review (documentation and asset gates).
- Proof kind: generated-table parity, registry validation, blind recognition check.
- Oracle source: `icon_specs.yaml` specs written before drawing; the owner's silhouette approval and `adopt-set`.
- Expected effect: 11 role markers adopted as one set; no live-app change.
- Selected commands: `pytest tests/visual_assets/test_icon_specs.py tests/visual_assets/test_budgets_parity.py` plus the store CLI validators.
