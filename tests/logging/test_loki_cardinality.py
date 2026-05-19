from __future__ import annotations
import os
import yaml
import json
import logging
from pathlib import Path
import pytest

from src.logging.formatter import JsonFormatter

# List of allowed, low-cardinality labels for Loki streams
ALLOWED_LOKI_LABELS = {"level", "component", "service", "environment", "container", "job"}

# High-cardinality labels that must NEVER be promoted to Loki stream labels
DISALLOWED_LOKI_LABELS = {"tick", "entity_id", "worker_id", "causal_id", "transaction_id", "run_id", "target_id", "quest_id"}

def test_promtail_labels_are_safe():
    """
    Ensure promtail-config.yml does not promote any high-cardinality fields to Loki stream labels.
    Prevents Loki memory/index crash regressions.
    """
    config_path = Path("promtail-config.yml")
    assert config_path.exists(), "promtail-config.yml must exist at the root"
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    scrape_configs = config.get("scrape_configs", [])
    assert scrape_configs, "scrape_configs must be defined in promtail-config.yml"
    
    for job in scrape_configs:
        pipeline_stages = job.get("pipeline_stages", [])
        for stage in pipeline_stages:
            if "labels" in stage:
                labels_dict = stage["labels"]
                # If labels is None, empty, or not a dict, skip
                if not labels_dict or not isinstance(labels_dict, dict):
                    continue
                
                for label_name in labels_dict.keys():
                    assert label_name not in DISALLOWED_LOKI_LABELS, (
                        f"CRITICAL REGRESSION: High-cardinality field '{label_name}' is promoted as "
                        f"a Loki stream label in job '{job.get('job_name', 'unknown')}'! "
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
