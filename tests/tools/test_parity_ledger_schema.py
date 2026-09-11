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

import jsonschema
import pytest

_SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "parity_ledger" / "schema.json"


def test_schema_json_parses_and_has_fixed_allof_structure():
    schema = json.loads(_SCHEMA_PATH.read_text())
    items = schema["items"]

    assert "if" not in items
    assert "then" not in items
    assert len(items["allOf"]) == 3


def _base_entry(**overrides):
    entry = {
        "id": "SUB-001",
        "text": "x",
        "status": "missing",
        "priority": "P1",
    }
    entry.update(overrides)
    return entry


class TestEvidenceKindField:
    """Step 2 (TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT): evidence_kind is optional,
    schema-only, with no enforcement rule in this ticket."""

    @pytest.mark.parametrize("value", ["existence", "invocation", "runtime_observation", None])
    def test_accepts_each_declared_value_and_null(self, value):
        schema = json.loads(_SCHEMA_PATH.read_text())
        jsonschema.validate([_base_entry(evidence_kind=value)], schema)

    def test_rejects_unknown_value(self):
        schema = json.loads(_SCHEMA_PATH.read_text())
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate([_base_entry(evidence_kind="eyeballed")], schema)

    def test_field_is_not_required(self):
        schema = json.loads(_SCHEMA_PATH.read_text())
        jsonschema.validate([_base_entry()], schema)
