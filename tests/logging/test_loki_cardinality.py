from __future__ import annotations
import os
import re
import json
import logging
from pathlib import Path
import pytest

from src.logging.formatter import JsonFormatter

# List of allowed, low-cardinality labels for Loki streams
ALLOWED_LOKI_LABELS = {"level", "component", "service", "environment", "container", "job"}

# High-cardinality labels that must NEVER be promoted to Loki stream labels
DISALLOWED_LOKI_LABELS = {"tick", "entity_id", "worker_id", "causal_id", "transaction_id", "run_id", "target_id", "quest_id"}

def test_alloy_labels_are_safe():
    """
    Ensure docker/alloy/config.alloy does not promote any high-cardinality fields to Loki stream labels.
    Prevents Loki memory/index crash regressions.
    """
    config_path = Path(__file__).resolve().parents[2] / "docker" / "alloy" / "config.alloy"  # repo-root anchored, not cwd
    assert config_path.exists(), "docker/alloy/config.alloy must exist"
    text = config_path.read_text()
    text = re.sub(r"//[^\n]*", "", text)  # comments may name forbidden labels

    # Every stage.labels block: brace-match its body, then read the keys of its values = { ... } map.
    promoted = set()
    blocks = 0
    for m in re.finditer(r"stage\.labels\s*\{", text):
        blocks += 1
        depth, i = 1, m.end()
        while depth and i < len(text):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        body = text[m.end():i - 1]
        values = re.search(r"values\s*=\s*\{(.*?)\}", body, flags=re.S)
        if values:
            promoted |= set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=", values.group(1)))
    assert blocks, "docker/alloy/config.alloy must define a stage.labels block"
    assert promoted, "stage.labels must promote at least level and component"
    for label_name in promoted:
        assert label_name not in DISALLOWED_LOKI_LABELS, (
            f"CRITICAL REGRESSION: High-cardinality field '{label_name}' is promoted as "
            f"a Loki stream label in docker/alloy/config.alloy! "
            f"This will cause Loki database index explosion."
        )
        assert label_name in ALLOWED_LOKI_LABELS, (
            f"WARNING: Unknown label '{label_name}' detected. "
            f"Only low-cardinality labels are permitted."
        )

def test_formatter_serializes_fields():
    """
    Ensure the JsonFormatter correctly serializes high-cardinality context fields
    (tick, entity_id, worker_id, component) into the JSON payload body so they
    remain queryable in Grafana/Loki via field filtering.
    """
    formatter = JsonFormatter()
    
    # Create standard log record
    record = logging.LogRecord(
        name="test_component",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Test simulation update occurred.",
        args=(),
        exc_info=None
    )
    
    # Inject context properties
    record.tick = 9999
    record.entity_id = 12345
    record.worker_id = "worker-01"
    
    # Inject extra dict
    record.extra = {"action": "combat_strike", "dps": 150}
    
    # Format and verify output
    formatted_str = formatter.format(record)
    log_data = json.loads(formatted_str)
    
    assert log_data["message"] == "Test simulation update occurred."
    assert log_data["level"] == "INFO"
    assert log_data["component"] == "test_component"
    assert log_data["tick"] == 9999
    assert log_data["entity_id"] == 12345
    assert log_data["worker_id"] == "worker-01"
    assert log_data["action"] == "combat_strike"
    assert log_data["dps"] == 150
