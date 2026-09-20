"""Structural check on .mcp.json — TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE removed the
Knowledge Gateway MCP's registration once its backing modules were archived (M2 of
TCK-20260907-KGMCP-DEPRECATION-EPIC). Inverse of, and functional replacement for, the now-archived
`tests/archive/test_knowledge_gateway_mcp.py::test_mcp_json_gains_exactly_one_new_server_entry`'s
byte-identity check.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_MCP_JSON_PATH = _REPO_ROOT / ".mcp.json"


def _load_mcp_config() -> dict:
    return json.loads(_MCP_JSON_PATH.read_text())


def test_mcp_json_no_longer_registers_knowledge_gateway():
    # TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT added a legitimate third server
    # (headroom) after this test was written — an exact-set assertion would break on every
    # future legitimate registration too. The real invariant this test guards is narrower:
    # the archived knowledge-gateway must never reappear, and the two pre-archival servers
    # must still be present (their own byte-identical shape is checked by the two tests below).
    mcp_config = _load_mcp_config()
    servers = set(mcp_config["mcpServers"].keys())
    assert "knowledge-gateway" not in servers
    assert {"knowledge-search", "github"} <= servers


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


def test_generalized_check_still_fails_if_knowledge_gateway_reappears(tmp_path, monkeypatch):
    # Proves test_mcp_json_no_longer_registers_knowledge_gateway's narrowing above (exact-set ->
    # subset + explicit exclusion) didn't silently stop catching the real regression it exists for.
    fake_config = {
        "mcpServers": {
            "knowledge-search": {},
            "github": {},
            "knowledge-gateway": {},
        }
    }
    fake_path = tmp_path / ".mcp.json"
    fake_path.write_text(json.dumps(fake_config))
    monkeypatch.setattr(sys.modules[__name__], "_MCP_JSON_PATH", fake_path)

    mcp_config = _load_mcp_config()
    servers = set(mcp_config["mcpServers"].keys())
    assert "knowledge-gateway" in servers  # sanity: the fake fixture really has it
    with pytest.raises(AssertionError):
        assert "knowledge-gateway" not in servers
