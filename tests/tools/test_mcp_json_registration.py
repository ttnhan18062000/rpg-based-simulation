"""Structural check on .mcp.json — TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE removed the
Knowledge Gateway MCP's registration once its backing modules were archived (M2 of
TCK-20260907-KGMCP-DEPRECATION-EPIC). Inverse of, and functional replacement for, the now-archived
`tests/archive/test_knowledge_gateway_mcp.py::test_mcp_json_gains_exactly_one_new_server_entry`'s
byte-identity check.
"""
from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_MCP_JSON_PATH = _REPO_ROOT / ".mcp.json"


def _load_mcp_config() -> dict:
    return json.loads(_MCP_JSON_PATH.read_text())


def test_mcp_json_no_longer_registers_knowledge_gateway():
    mcp_config = _load_mcp_config()
    assert set(mcp_config["mcpServers"].keys()) == {"knowledge-search", "github"}


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
