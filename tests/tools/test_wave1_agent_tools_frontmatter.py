"""Structural checks for the Wave 1 tools: frontmatter rollout
(TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE).

These are static/structural checks only — they parse frontmatter and assert on
its declared tools: field. They do not exercise live harness enforcement
(that was independently confirmed via direct binary-schema extraction and a
live subagent dispatch during this ticket's investigation, see investigation.md
Step 0).
"""

from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).parent.parent.parent
_AGENTS_DIR = _ROOT / ".claude" / "agents"

# Candidate tools: scope per Wave 1 agent, copied verbatim from investigation.md's
# per-agent candidate-scope table (usage-backed table + policy-derived table).
_WAVE1_CANDIDATE_TOOLS = {
    "concern-investigator": ["Read", "Grep", "Glob", "Bash", "WebFetch", "WebSearch",
                              "mcp__knowledge-search__search_docs"],  # unchanged, existing precedent
    "doc-updater": ["Read", "Edit", "Write", "Bash", "Agent", "ListAgents",
                    "mcp__knowledge-search__search_docs", "ToolSearch", "TaskUpdate",
                    "Artifact", "ScheduleWakeup", "AskUserQuestion", "SendMessage", "Skill"],
    "investigator": ["Read", "Write", "Edit", "Bash", "Agent",
                      "mcp__knowledge-search__search_docs", "ToolSearch", "Skill", "Artifact",
                      "ListAgents", "TaskUpdate", "TaskCreate", "WebSearch", "AskUserQuestion",
                      "ScheduleWakeup", "Monitor", "TaskStop", "WebFetch", "SendFeedback"],
    "ticket-scoper": ["Bash", "Read", "Edit", "Agent", "Write", "ToolSearch",
                       "mcp__knowledge-search__search_docs", "ListAgents", "AskUserQuestion",
                       "TaskCreate", "ScheduleWakeup", "SendMessage", "TaskUpdate", "Monitor",
                       "TaskStop"],
    "done-checker": ["Bash", "Read", "Edit", "Agent", "Write",
                       "mcp__knowledge-search__search_docs", "TaskUpdate", "ToolSearch",
                       "ScheduleWakeup", "TaskCreate", "AskUserQuestion", "Artifact", "Monitor",
                       "ListAgents", "WebSearch", "TaskOutput", "Skill", "SendMessage", "TaskStop",
                       "WebFetch", "SendUserFile", "ReportFindings"],
    "test-scoper": ["Bash", "Read", "Agent", "ToolSearch", "Monitor", "Write", "SendMessage",
                     "ListAgents", "mcp__knowledge-search__search_docs", "ScheduleWakeup",
                     "TaskStop", "AskUserQuestion", "SendFeedback", "TaskUpdate", "Artifact",
                     "Skill",
                     "mcp__knowledge-search__search_health", "SendUserFile"],  # Edit deliberately excluded
    "mechanics-auditor": ["Read", "Grep", "Glob", "Bash", "mcp__knowledge-search__search_docs"],
    "spec-document-reviewer": ["Read", "Grep", "Glob", "mcp__knowledge-search__search_docs"],
    "simulation-analyst": ["Read", "Grep", "Glob", "Bash"],
    "world-debugger": ["Read", "Grep", "Glob", "Bash"],
    "world-render-reviewer": ["Read"],
}

# Tools this investigation explicitly classified as excluded per agent — the anti-drift pin
# for the single most consequential judgment call in this ticket (test-scoper's Edit exclusion)
# plus the four policy-derived report-only agents and world-render-reviewer's narrow scope.
_WAVE1_FORBIDDEN_PAIRS = [
    ("test-scoper", "Edit"),
    ("mechanics-auditor", "Write"), ("mechanics-auditor", "Edit"), ("mechanics-auditor", "Agent"),
    ("spec-document-reviewer", "Write"), ("spec-document-reviewer", "Edit"),
    ("spec-document-reviewer", "Agent"),
    ("simulation-analyst", "Write"), ("simulation-analyst", "Edit"), ("simulation-analyst", "Agent"),
    ("world-debugger", "Write"), ("world-debugger", "Edit"), ("world-debugger", "Agent"),
    ("world-render-reviewer", "Write"), ("world-render-reviewer", "Edit"),
    ("world-render-reviewer", "Bash"), ("world-render-reviewer", "Agent"),
    ("world-render-reviewer", "Grep"), ("world-render-reviewer", "Glob"),
]

_WAVE2_WAVE3_AGENTS = ["architecture-reviewer", "security-reviewer", "planner",
                        "implementer", "parity-updater"]

_CONCERN_INVESTIGATOR_EXPECTED_TOOLS_LINE = (
    "Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs"
)


def _parse_frontmatter(agent_name: str) -> dict:
    text = (_AGENTS_DIR / f"{agent_name}.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


@pytest.mark.parametrize("agent_name", sorted(_WAVE1_CANDIDATE_TOOLS))
def test_wave1_agent_files_declare_tools_field(agent_name):
    fm = _parse_frontmatter(agent_name)
    assert "tools" in fm, f"{agent_name}.md must declare a tools: field"
    declared = [t.strip() for t in fm["tools"].split(",")]
    assert declared, f"{agent_name}.md tools: field must not be empty"
    expected = _WAVE1_CANDIDATE_TOOLS[agent_name]
    assert declared == expected, (
        f"{agent_name}.md tools: field {declared} does not match the candidate scope "
        f"pinned from investigation.md: {expected}"
    )


@pytest.mark.parametrize("agent_name,forbidden_tool", _WAVE1_FORBIDDEN_PAIRS)
def test_wave1_candidate_scope_excludes_known_denied_tools(agent_name, forbidden_tool):
    fm = _parse_frontmatter(agent_name)
    declared = [t.strip() for t in fm["tools"].split(",")]
    assert forbidden_tool not in declared, (
        f"{agent_name}.md must not grant {forbidden_tool} per investigation.md's classification"
    )


@pytest.mark.parametrize("agent_name", sorted(_WAVE1_CANDIDATE_TOOLS))
def test_wave1_agents_do_not_declare_disallowed_tools_field(agent_name):
    fm = _parse_frontmatter(agent_name)
    assert "disallowedTools" not in fm, (
        f"{agent_name}.md must use the tools: allowlist pattern only for Wave 1, "
        "not the unprecedented disallowedTools: denylist (investigation.md Step 0 conclusion)"
    )


@pytest.mark.parametrize("agent_name", _WAVE2_WAVE3_AGENTS)
def test_wave2_wave3_agents_do_not_gain_tools_field(agent_name):
    fm = _parse_frontmatter(agent_name)
    assert "tools" not in fm, (
        f"{agent_name}.md is Wave 2/3 scope, explicitly deferred by this ticket — "
        "it must not gain a tools: field as a side effect of Wave 1"
    )


def test_concern_investigator_tools_field_unchanged_byte_identical():
    fm = _parse_frontmatter("concern-investigator")
    assert fm["tools"] == _CONCERN_INVESTIGATOR_EXPECTED_TOOLS_LINE, (
        "concern-investigator.md's tools: value must stay byte-identical — "
        "investigation.md found zero usage evidence to justify changing it"
    )
