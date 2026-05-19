from __future__ import annotations
import os
import json
import logging
from typing import List, Dict, Any
from src.observability.events import SimulationEvent
from src.observability.anomaly.rules import (
    Anomaly, AnomalyRule, HardLawViolationRule, NavigationStuckRule,
    QuestStalledRule, CombatNeverEndsRule, ResourceNodeCrowdingRule
)

logger = logging.getLogger(__name__)

class PostRunAnomalyAnalyzer:
    """Performs post-hoc simulation analysis, executing rules against event logs to isolate bugs."""
    def __init__(self, rules: Optional[List[AnomalyRule]] = None) -> None:
        if rules is None:
            self.rules: List[AnomalyRule] = [
                HardLawViolationRule(),
                NavigationStuckRule(tick_threshold=50),
                QuestStalledRule(tick_threshold=100),
                CombatNeverEndsRule(tick_threshold=40),
                ResourceNodeCrowdingRule(entity_limit=4)
            ]
        else:
            self.rules = rules

    def load_events(self, run_dir: str) -> List[SimulationEvent]:
        """Parses and loads all SimulationEvents from the JSONL event log of the run."""
        filepath = os.path.join(run_dir, "simulation_events.jsonl")
        events: List[SimulationEvent] = []
        if not os.path.exists(filepath):
            logger.warning(f"Event log not found: {filepath}")
            return events

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            events.append(SimulationEvent.model_validate_json(line))
                        except Exception as e:
                            logger.error(f"Failed parsing event at line {line_idx} in {filepath}: {e}")
        except Exception as e:
            logger.error(f"Error reading event log file {filepath}: {e}")

        return events

    def analyze(self, run_dir: str) -> List[Anomaly]:
        """Runs the rule engine against simulation events and saves diagnostic artifacts."""
        events = self.load_events(run_dir)
        anomalies: List[Anomaly] = []

        # Run all diagnostic rules
        for rule in self.rules:
            try:
                detected = rule.evaluate(events)
                anomalies.extend(detected)
            except Exception as e:
                logger.error(f"Error running rule {rule.__class__.__name__}: {e}")

        # Ensure run directory exists
        os.makedirs(run_dir, exist_ok=True)

        # 1. Save structured anomalies JSON
        json_path = os.path.join(run_dir, "anomalies.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([a.model_dump() for a in anomalies], f, indent=2)
            logger.info(f"Saved anomalies JSON to {json_path}")
        except Exception as e:
            logger.error(f"Failed to save anomalies JSON: {e}")

        # 2. Save human-friendly Markdown summary
        md_path = os.path.join(run_dir, "anomaly_summary.md")
        try:
            self.write_markdown_summary(md_path, anomalies)
            logger.info(f"Saved anomaly Markdown summary to {md_path}")
        except Exception as e:
            logger.error(f"Failed to save anomaly summary Markdown: {e}")

        return anomalies

    def write_markdown_summary(self, filepath: str, anomalies: List[Anomaly]) -> None:
        """Constructs a beautifully readable Markdown dashboard of detected anomalies."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Simulation Run Anomaly Diagnosis Summary\n\n")
            
            if not anomalies:
                f.write("> [!NOTE]\n")
                f.write("> **Simulation healthy!** Zero behavioral anomalies or hard simulation law violations detected.\n\n")
                return

            # Count by severity
            severities = {"CRITICAL": 0, "ERROR": 0, "WARNING": 0}
            for a in anomalies:
                severities[a.severity] = severities.get(a.severity, 0) + 1

            f.write("## Severity Dashboard\n\n")
            f.write("| Severity | Count | Status |\n")
            f.write("| :--- | :--- | :--- |\n")
            f.write(f"| 🟥 **CRITICAL** | {severities['CRITICAL']} | {'🔴 ACTION REQUIRED' if severities['CRITICAL'] > 0 else '🟢 PASS'} |\n")
            f.write(f"| 🟧 **ERROR** | {severities['ERROR']} | {'🔴 ACTION REQUIRED' if severities['ERROR'] > 0 else '🟢 PASS'} |\n")
            f.write(f"| 🟨 **WARNING** | {severities['WARNING']} | {'🟡 INVESTIGATE' if severities['WARNING'] > 0 else '🟢 PASS'} |\n\n")

            f.write("## Detected Anomalies Checklist\n\n")
            for idx, a in enumerate(anomalies, 1):
                severity_emoji = "🟥" if a.severity == "CRITICAL" else "🟧" if a.severity == "ERROR" else "🟨"
                f.write(f"### {idx}. {severity_emoji} {a.rule_name} ({a.severity})\n")
                f.write(f"- **Tick Detected**: `{a.tick_detected}`\n")
                if a.entity_id is not None:
                    f.write(f"- **Associated Entity**: `{a.entity_id}`\n")
                f.write(f"- **Diagnostic Message**: {a.message}\n")
                if a.context:
                    f.write("- **Telemetry Context**:\n")
                    f.write("  ```json\n")
                    f.write(json.dumps(a.context, indent=4) + "\n")
                    f.write("  ```\n")
                f.write("\n---\n\n")
