---
status: active
ticket_id: TCK-20260619-E51D-RENDERER
artifact_type: plan
date: 2026-06-22
---

# Plan — TCK-20260619-E51D-RENDERER

## Files to Create

1. `src/domains/chronicle/renderer.py` — ChronicleRenderer (render_markdown, render_json)
2. `src/domains/chronicle/compiler.py` — ChronicleCompiler (compile entry point)
3. Update `src/domains/chronicle/__init__.py` — export ChronicleRenderer, ChronicleCompiler
4. Add E51D tests to `tests/unit/chronicle/test_chronicle_compiler.py`
5. Create `tests/integration/scenarios/test_campaign_chronicle.py`

## Design Decisions

### ChronicleRenderer.render_markdown()
- YAML frontmatter block: campaign_id, total_episodes, era_count
- `# Chronicle of {campaign_id}` title
- For each era: `## {era_name}` (derived via ChronicleNamer.name_era)
- For each episode in era: `### Episode {episode.index + 1}` (1-based for readability)
- For each incident entry: `- **{milestone_name}** (Tick {entry.tick})`
- Accepts optional `entity_names: dict[int, str]` for name resolution

### ChronicleRenderer.render_json()
- Returns dict with:
  - `campaign_id: str`
  - `eras: list[dict]` — each has id, ordinal, name, significance, episode_ids
  - `episodes: list[dict]` — each has id, index, significance, incident_ids
  - `named_milestones: list[dict]` — flat list of all milestone events with name, tick, episode, event_type, significance

### ChronicleCompiler.compile()
- Args: `campaign_state: CampaignState, output_dir: str, entity_names: dict[int, str] | None = None`
- Returns: `tuple[str, dict]` — (markdown_str, json_dict) for testability
- Side effect: writes Chronicle.md and chronicle.json to output_dir

## Test Plan Summary
- TC-R1: render_markdown returns string with valid YAML frontmatter block
- TC-R2: render_markdown includes era headings
- TC-R3: render_markdown includes episode headings
- TC-R4: render_markdown includes milestone bullet points
- TC-R5: render_json returns dict with eras[], episodes[], named_milestones[]
- TC-R6: render_json named_milestones contains correct fields
- TC-R7: render_markdown on empty hierarchy returns minimal valid output
- TC-R8: render_json on empty hierarchy returns empty arrays
- TC-I1 (slow): full compile() pipeline writes Chronicle.md + chronicle.json to disk
