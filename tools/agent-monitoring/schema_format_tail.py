"""Generates an agent output-format sentence from a workflow's own `*_SCHEMA` key list
(TCK-20261002-ARCH-VERIFY-TEST-QUALITY-FINDINGS).

On the native Workflow path the schema is enforced at the tool-call layer and nothing needs
appending. On the hand-executed skill path the orchestrator has to tell the dispatched agent
what shape to return; improvising that sentence per call drifted from the schema (a key was
left out and the reviewer put its remark somewhere else). This module makes the sentence a pure
function of the schema: ALL top-level property names, in schema order, nothing else.

Usage:
    python3 tools/agent-monitoring/schema_format_tail.py --schema ARCH_VERIFY_SCHEMA
    python3 tools/agent-monitoring/schema_format_tail.py --workflow .claude/workflows/implement-ticket.js --schema ARCH_VERIFY_SCHEMA

Prints the sentence on stdout. Exits 1 (printing nothing on stdout) when the schema or its
`properties` block cannot be found: the caller must stop rather than hand-write a tail.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_KEY_RE = re.compile(r"""(?:([A-Za-z_$][\w$]*)|['"]([^'"]+)['"])\s*:""")
_DEFAULT_WORKFLOW = Path(__file__).resolve().parent.parent.parent / ".claude" / "workflows" / "implement-ticket.js"


def _matching_brace(text: str, open_idx: int) -> int:
    """Index of the `}` closing the `{` at open_idx, skipping string/template literals and comments."""
    depth = 0
    i = open_idx
    quote = None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif text.startswith("//", i):
            nl = text.find("\n", i)
            i = len(text) if nl == -1 else nl
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = len(text) if end == -1 else end + 2
            continue
        elif ch in "'\"`":
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced braces")


def _top_level_keys(block: str) -> list[str]:
    """Top-level keys of an object-literal body (the text between its braces), in order."""
    keys = []
    depth = 0
    i = 0
    quote = None
    start_of_entry = True
    while i < len(block):
        ch = block[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if block.startswith("//", i):
            nl = block.find("\n", i)
            i = len(block) if nl == -1 else nl
            continue
        if depth == 0 and start_of_entry and not ch.isspace():
            m = _KEY_RE.match(block, i)
            if m:
                keys.append(m.group(1) or m.group(2))
                i = m.end()
            start_of_entry = False
            if m:
                continue
        if ch in "'\"`":
            quote = ch
            i += 1
            continue
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif ch == "," and depth == 0:
            start_of_entry = True
        i += 1
    return keys


def extract_schema_keys(js_text: str, schema_name: str) -> list[str]:
    """Property names of `const <schema_name> = { ... properties: { ... } }`, in order."""
    decl = re.search(rf"\bconst\s+{re.escape(schema_name)}\s*=\s*\{{", js_text)
    if not decl:
        raise KeyError(f"schema {schema_name} not found")
    open_idx = decl.end() - 1
    body = js_text[open_idx + 1:_matching_brace(js_text, open_idx)]
    props = re.search(r"\bproperties\s*:\s*\{", body)
    if not props:
        raise KeyError(f"schema {schema_name} has no properties block")
    p_open = props.end() - 1
    keys = _top_level_keys(body[p_open + 1:_matching_brace(body, p_open)])
    if not keys:
        raise KeyError(f"schema {schema_name} has an empty properties block")
    return keys


def format_tail(keys: list[str]) -> str:
    return "Return your answer as a single JSON object with keys: " + ", ".join(keys) + "."


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workflow", default=str(_DEFAULT_WORKFLOW), help="workflow JS file holding the schema")
    parser.add_argument("--schema", required=True, help="schema constant name, e.g. ARCH_VERIFY_SCHEMA")
    args = parser.parse_args(argv)
    try:
        keys = extract_schema_keys(Path(args.workflow).read_text(encoding="utf-8"), args.schema)
    except (OSError, KeyError, ValueError) as e:
        print(f"ERROR: cannot derive an output-format tail: {e}", file=sys.stderr)
        return 1
    print(format_tail(keys))
    return 0


if __name__ == "__main__":
    sys.exit(main())
