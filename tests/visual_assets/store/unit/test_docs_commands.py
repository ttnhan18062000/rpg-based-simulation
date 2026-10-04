"""The store contract documents exactly the commands the CLI has and exactly the MCP tools the server registers (no drift either way)."""

from __future__ import annotations

import re
from pathlib import Path

from visual_assets.store import cli

DOC = Path(__file__).resolve().parents[4] / "docs" / "assets" / "store_contract.md"


def table_first_column(heading: str) -> list[str]:
    text = DOC.read_text()
    section = text[text.index(heading):]
    rows = []
    for line in section.splitlines()[1:]:
        if line.startswith("## "):
            break
        match = re.match(r"\| `([a-z_-]+)` \|", line)
        if match:
            rows.append(match.group(1))
    return rows


def cli_commands() -> set[str]:
    parser = cli._parser()
    sub = next(action for action in parser._actions if action.__class__.__name__ == "_SubParsersAction")
    return set(sub.choices)


def test_every_documented_command_exists_and_every_cli_command_is_documented():
    documented = table_first_column("## Commands")
    assert len(documented) == len(set(documented)) and documented, documented
    assert set(documented) == cli_commands()


def test_the_documented_gates_match_the_parser_help():
    parser = cli._parser()
    sub = next(action for action in parser._actions if action.__class__.__name__ == "_SubParsersAction")
    human_only = {name for name, p in sub.choices.items() if "HUMAN ONLY" in (sub._name_parser_map[name].description or "") or any(
        "HUMAN ONLY" in (a.help or "") for a in sub._choices_actions if a.dest == name)}
    doc_rows = {m.group(1): m.group(2) for m in re.finditer(r"^\| `([a-z_-]+)` \| ([^|]+) \|", DOC.read_text().split("## Commands")[1].split("## MCP tools")[0], re.M)}
    assert human_only == {n for n, gate in doc_rows.items() if "human only" in gate} == {"adopt", "adopt-set", "revoke"}


def test_every_documented_mcp_tool_is_registered_and_the_store_tools_are_all_documented():
    from visual_assets.drawing.server import mcp

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    documented = table_first_column("## MCP tools on the drawing server")
    assert set(documented) <= registered and len(documented) == len(set(documented))
    assert {"export_handoff", "submit_candidate", "store_list", "store_show"} == set(documented)


def test_the_contract_has_no_designed_not_built_item_left():
    text = DOC.read_text()
    assert "designed, not built" not in text.lower() and "## What is designed" not in text
    assert "Visual asset store contract (built)" in text


def test_the_documented_gates_never_name_an_mcp_tool_for_a_human_command():
    text = DOC.read_text().split("## MCP tools")[1].split("## Not built")[0]
    for gate in ("`adopt`", "`adopt-set`", "`revoke`"):
        assert not re.search(rf"^\| {gate} \|", text, re.M)
