"""Static checks for the concern-investigator agent definition and its dispatch
site in create-tickets.js (TCK-20260709-CONCERN-INVESTIGATOR-AGENT).

These are structural/static checks only — they parse frontmatter and text
content, not live runtime behavior. Live tool-enforcement and agentType
dispatch were separately confirmed via a real smoke-test invocation during
this ticket's Verify phase (see its Implementation Notes) — the harness
picked up the new agent type without a session restart in that instance,
though hot-reload behavior may still vary across harness versions/sessions.
"""

from pathlib import Path

import yaml

_ROOT = Path(__file__).parent.parent.parent
_AGENT_PATH = _ROOT / ".claude" / "agents" / "concern-investigator.md"
_CREATE_TICKETS_PATH = _ROOT / ".claude" / "workflows" / "create-tickets.js"
_AGENTS_DOC_PATH = _ROOT / "docs" / "ai" / "agents.md"

_DISALLOWED_TOOLS = ("Edit", "Write", "NotebookEdit")

# INVESTIGATION_SCHEMA's required field list as it exists in create-tickets.js today.
# A change here is a schema-drift signal — INVESTIGATION_SCHEMA must stay byte-identical
# per this ticket's AC #3 and Scope Guards.
_EXPECTED_SCHEMA_REQUIRED_FIELDS = [
    "concern_id",
    "files_found",
    "constraints",
    "existing_tests",
    "related_tickets",
    "ac_signals",
    "risks",
    "is_duplicate",
    "tier_recommendation",
    "summary",
]


def _read_agent_text() -> str:
    return _AGENT_PATH.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> dict:
    assert text.startswith("---\n"), "agent file must start with a YAML frontmatter block"
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


def test_concern_investigator_agent_file_exists_and_has_frontmatter():
    assert _AGENT_PATH.exists(), f"{_AGENT_PATH} does not exist"

    text = _read_agent_text()
    frontmatter = _parse_frontmatter(text)

    assert frontmatter["name"] == "concern-investigator"
    assert frontmatter.get("description")
    assert isinstance(frontmatter["description"], str)
    assert len(frontmatter["description"]) > 0

    assert "tools" in frontmatter, "concern-investigator.md must declare a tools: field"
    declared_tools = [t.strip() for t in frontmatter["tools"].split(",")]

    for disallowed in _DISALLOWED_TOOLS:
        assert disallowed not in declared_tools, (
            f"tools: field must not grant {disallowed} — concern-investigator is read-only"
        )


def test_concern_investigator_encodes_context_scan_ordering():
    text = _read_agent_text()

    markers = [
        "search_docs",
        "graphify query",
        "docs/REGISTRY.yaml",
        "tickets/working_log.csv",
    ]
    positions = [text.index(m) for m in markers]

    assert positions == sorted(positions), (
        "Context-scan ordering (search_docs -> graphify -> registry -> working_log) "
        f"not preserved in expected relative order: {list(zip(markers, positions))}"
    )


def test_investigate_phase_uses_concern_investigator_agent_type():
    text = _CREATE_TICKETS_PATH.read_text(encoding="utf-8")

    label_marker = "label: `investigate:${concern.id}`"
    assert label_marker in text, "Investigate-phase agent() call site not found by its label"

    label_index = text.index(label_marker)
    # The agentType option lives in the same options-object literal as the label,
    # a short window before it in the current source layout.
    window = text[max(0, label_index - 200):label_index + len(label_marker)]
    assert "agentType: 'concern-investigator'" in window, (
        "Investigate-phase agent() call must pass agentType: 'concern-investigator'"
    )

    # Positive signal the methodology was actually extracted, not merely duplicated.
    removed_step_headers = [
        "Step 0: Semantic prior-work retrieval",
        "Step 1: Knowledge graph",
        "Step 2: Docs and prior tickets",
        "Step 3: Prior ticket history",
        "Step 4: Code files",
        "Step 5: Existing tests",
        "Step 6: Derive acceptance criteria",
        "Step 7: Assess tier",
    ]
    for header in removed_step_headers:
        assert header not in text, (
            f"Inline methodology header '{header}' still present in create-tickets.js — "
            "should have been extracted into concern-investigator.md's system prompt"
        )


def test_investigation_schema_definition_unchanged():
    text = _CREATE_TICKETS_PATH.read_text(encoding="utf-8")

    schema_marker = "const INVESTIGATION_SCHEMA = {"
    assert schema_marker in text
    schema_start = text.index(schema_marker)
    schema_end = text.index("\n}\n", schema_start)
    schema_block = text[schema_start:schema_end]

    required_marker = "required: ["
    required_start = schema_block.index(required_marker) + len(required_marker)
    required_end = schema_block.index("]", required_start)
    required_raw = schema_block[required_start:required_end]
    required_fields = [f.strip().strip("'\"") for f in required_raw.split(",")]

    assert required_fields == _EXPECTED_SCHEMA_REQUIRED_FIELDS, (
        "INVESTIGATION_SCHEMA's required field list has drifted from its expected, "
        "byte-identical form (ticket AC #3 / Scope Guards)"
    )


def test_agents_doc_has_concern_investigator_heading():
    text = _AGENTS_DOC_PATH.read_text(encoding="utf-8")

    assert "### `concern-investigator`" in text
    assert "### `investigator`" in text

    concern_heading_index = text.index("### `concern-investigator`")
    investigator_heading_index = text.index("### `investigator`")
    assert concern_heading_index != investigator_heading_index
