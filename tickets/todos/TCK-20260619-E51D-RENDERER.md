---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51D-RENDERER
phase: open
date: 2026-06-20
tags: [chronicle, markdown-renderer, chronicle-json, output, phase-5]
---

# TCK-20260619-E51D-RENDERER

## Title
Epic 5.1D · Chronicle.md + chronicle.json Generator

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Converts `ChronicleHierarchy` into human-readable `Chronicle.md` (structured Markdown with YAML frontmatter) and machine-readable `chronicle.json` (REST backing store).

**Requires:** TCK-20260619-E51C-NAMING

## Scope

New file `src/domains/chronicle/renderer.py`:

```python
class ChronicleRenderer:
    @staticmethod
    def render_markdown(hierarchy: ChronicleHierarchy, campaign_id: str) -> str:
        """Produce Chronicle.md: YAML frontmatter + Era/Episode/Incident/Event sections."""
        lines = [
            "---",
            f"campaign_id: {campaign_id}",
            f"total_episodes: {len(hierarchy.episodes)}",
            f"era_count: {len(hierarchy.eras)}",
            "---",
            f"# Chronicle of {campaign_id}",
        ]
        for era in hierarchy.eras:
            lines.append(f"## {era.name}")
            for episode in era.episodes:
                lines.append(f"### Episode {episode.index}")
                for milestone in episode.named_milestones:
                    lines.append(f"- **{milestone.name}** (Tick {milestone.tick})")
        return "\n".join(lines)

    @staticmethod
    def render_json(hierarchy: ChronicleHierarchy, campaign_id: str) -> dict:
        """Produce chronicle.json: full structured JSON for REST."""
        ...
```

Also write a top-level `ChronicleCompiler.compile(campaign_state, output_dir)` entry point that chains: load NarrativeLedger → score → group → name → render → write files.

## Acceptance Criteria
- `Chronicle.md` has valid YAML frontmatter
- `chronicle.json` has `eras[]`, `episodes[]`, `named_milestones[]` arrays
- `test_chronicle_json_matches_structured_schema` passes

## Related Tickets
- TCK-20260619-E51-CHRONICLE (parent epic)
- TCK-20260619-E51C-NAMING (required)
- TCK-20260619-E51E-REST-API (blocked on this)

## Related Code Areas
- `src/domains/chronicle/renderer.py` (new)
- `src/domains/chronicle/compiler.py` (new — ChronicleCompiler entry point)

## Test Summary
```bash
pytest tests/unit/chronicle/test_chronicle_compiler.py -x -v
pytest tests/integration/scenarios/test_campaign_chronicle.py -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
