---
status: active
ticket_id: TCK-20260619-E51D-RENDERER
artifact_type: test_plan
date: 2026-06-22
---

# Test Plan — TCK-20260619-E51D-RENDERER

## Unit Tests (tests/unit/chronicle/test_chronicle_compiler.py)

| ID | Description | AC |
|---|---|---|
| TC-R1 | render_markdown returns string with `---` YAML frontmatter delimiters | AC-1 |
| TC-R2 | render_markdown includes era name headings (`##`) | AC-1 |
| TC-R3 | render_markdown includes episode headings (`###`) | AC-1 |
| TC-R4 | render_markdown includes milestone bullet lines | AC-1 |
| TC-R5 | render_json returns dict with top-level `eras`, `episodes`, `named_milestones` keys | AC-2 |
| TC-R6 | render_json named_milestones contains name, tick, episode, event_type fields | AC-2 |
| TC-R7 | render_markdown on empty hierarchy produces valid YAML frontmatter with 0 counts | AC-1 |
| TC-R8 | render_json on empty hierarchy returns empty arrays for all three keys | AC-2 |
| TC-R9 | test_chronicle_json_matches_structured_schema — named AC from ticket | AC-2 |

## Integration Tests (tests/integration/scenarios/test_campaign_chronicle.py)

| ID | Description | Marker |
|---|---|---|
| TC-I1 | full compile() pipeline writes Chronicle.md + chronicle.json to tmp disk | slow |

## Run Commands
```bash
pytest tests/unit/chronicle/test_chronicle_compiler.py -x -v
pytest tests/integration/scenarios/test_campaign_chronicle.py -x -v -m slow
```
