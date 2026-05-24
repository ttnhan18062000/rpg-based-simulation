# Investigation: Workflow Registry and Skill Contracts (M93)

We need to implement a dynamic parser that scans markdown specifications and registers their frontmatter schemas as validated Python models.

## Frontmatter Parsing Strategy

Markdown frontmatter is written as:
```markdown
---
name: SomeWorkflow
description: Some desc
...
---
```
We can parse this safely by:
1. Reading the markdown file content.
2. Checking if it starts with `---`.
3. Finding the second occurrence of `---`.
4. Extracting the YAML text between these markers.
5. Passing the YAML text to `yaml.safe_load()`.
6. Passing the resulting dictionary to `WorkflowSkill` constructor.

This approach is lightweight, standard, and requires no heavy external python-frontmatter dependencies since we already have `yaml` (`PyYAML`) as a core project dependency.

## Scanned Paths
We need to scan:
- `.agents/workflows/` (for workflows like `GenerateSimulationSetup.md`, `PrepareSimulationExecution.md`, etc.)
- `.agents/skills/` (for skill directories containing `SKILL.md` files)

## Pydantic Contract Verification
Each loaded contract must conform to the required `WorkflowSkill` fields:
- `name`: str
- `purpose`: str (can be mapped from `description` or `purpose` field in yaml)
- `input_schema`: dict
- `allowed_actions`: List[str]
- `forbidden_actions`: List[str]
- `output_artifacts`: List[str]
- `approval_required`: bool (default `False` unless specified)
- `context_budget`: dict (default empty dict)
- `failure_behavior`: str (default `"STOP"` or `"RETRY"`)
