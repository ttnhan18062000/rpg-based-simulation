"""Structural check on .mcp.json — TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE removed the
Knowledge Gateway MCP's registration once its backing modules were archived (M2 of
TCK-20260907-KGMCP-DEPRECATION-EPIC). Inverse of, and functional replacement for, the now-archived
`tests/archive/test_knowledge_gateway_mcp.py::test_mcp_json_gains_exactly_one_new_server_entry`'s
byte-identity check.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_MCP_JSON_PATH = _REPO_ROOT / ".mcp.json"


def _load_mcp_config() -> dict:
    return json.loads(_MCP_JSON_PATH.read_text())


def _assert_no_knowledge_gateway(servers: set) -> None:
    # TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT added a legitimate third server
    # (headroom) after this test was written — an exact-set assertion would break on every
    # future legitimate registration too. The real invariant this guards is narrower: the
    # archived knowledge-gateway must never reappear, and the two pre-archival servers must
    # still be present (their own byte-identical shape is checked by the two tests below).
    # Extracted so the adversarial test below exercises this exact logic, not a copy of it.
    assert "knowledge-gateway" not in servers
    assert {"knowledge-search", "github"} <= servers


def test_mcp_json_no_longer_registers_knowledge_gateway():
    mcp_config = _load_mcp_config()
    servers = set(mcp_config["mcpServers"].keys())
    _assert_no_knowledge_gateway(servers)


def test_knowledge_search_entry_is_byte_identical_to_its_pre_archival_shape():
    mcp_config = _load_mcp_config()
    assert mcp_config["mcpServers"]["knowledge-search"] == {
        "command": "bash",
        "args": ["tools/start_search_mcp.sh"],
        "env": {},
        "description": "Local semantic search over project docs, tickets, and investigations",
    }


def test_github_entry_is_byte_identical_to_its_pre_archival_shape():
    mcp_config = _load_mcp_config()
    assert mcp_config["mcpServers"]["github"] == {
        "command": "docker",
        "args": [
            "run", "-i", "--rm",
            "--env-file", ".env",
            "ghcr.io/github/github-mcp-server",
        ],
        "description": "GitHub API — workflow runs, PRs, issues, logs",
    }


def test_generalized_check_still_fails_if_knowledge_gateway_reappears():
    # Exercises _assert_no_knowledge_gateway itself (not a re-implemented copy of its logic), so
    # this guard genuinely fails if the real production assertion is ever weakened or drifts.
    servers = {"knowledge-search", "github", "knowledge-gateway"}
    with pytest.raises(AssertionError):
        _assert_no_knowledge_gateway(servers)
