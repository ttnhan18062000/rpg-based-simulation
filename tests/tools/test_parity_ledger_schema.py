"""Direct regression proof for docs/parity_ledger/schema.json's raw JSON structure.

TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL Step 1: the source file used to declare two
top-level "if" keys inside the same `items` object -- JSON object keys must be unique, so
standard parsing silently kept only the second pair and the verified/divergent ->
v2_evidence+test_path rule went unenforced. This was restructured into an `items.allOf`
array so both conditionals (plus the previously prose-only P0 -> non-null test_path rule)
survive standard parsing. `tools/parity_ledger_writer.py::validate_entry` hand-rolls these
same rules in plain Python and never loads this file at runtime, so it cannot catch a future
regression to the raw JSON structure -- only a test that actually parses this file can.
"""
import json
from pathlib import Path

_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "parity_ledger" / "schema.json"


def test_schema_json_parses_and_has_fixed_allof_structure():
    schema = json.loads(_SCHEMA_PATH.read_text())
    items = schema["items"]

    assert "if" not in items
    assert "then" not in items
    assert len(items["allOf"]) == 3
