from __future__ import annotations

import os
from pathlib import Path
from src_v2.certification.models import CertificationResult


class CertificationRecorder:
    """
    M9 Law: JSON first, Markdown derivative second.
    Enforces honest, bound language in reporting.
    """

    def __init__(self, output_dir: str = "data/certification"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def record(self, result: CertificationResult) -> str:
        """
        Record the machine-readable truth and generate the MD derivative.
        """
        # 1. Machine-readable artifact
        json_path = self._output_dir / f"run_{result.run_id}.json"
        with open(json_path, "w") as f:
            f.write(result.to_json())

        # 2. Markdown summary
        md_path = self._output_dir / f"REPORT_{result.run_id}.md"
        with open(md_path, "w") as f:
            f.write(self._generate_markdown(result))

        return str(json_path)

    def _generate_markdown(self, result: CertificationResult) -> str:
        """
        M9 Law: Bind performance and safety to (Profile, Scenario, Hardware Class).
        """
        status_emoji = "✅" if result.conformance_passed else "❌"
        class_label = result.effective_hardware_class.value if hasattr(result.effective_hardware_class, "value") else str(result.effective_hardware_class)
        if result.hardware_class_override_applied:
            class_label = f"{class_label} (OVERRIDDEN, detected {result.detected_hardware_class})"

        lines = [
            f"# Certification Report: {result.scenario_id}",
            f"**Run ID**: `{result.run_id}`",
            f"**Status**: {status_emoji} **{('PASS' if result.conformance_passed else 'FAIL')}**",
            "",
            "## 1. Certified Execution Context",
            f"- **Runtime Profile**: `{result.profile_name}`",
            f"- **Hardware Class**: `{class_label}`",
            f"- **Seed**: `{result.seed}`",
            "",
            "## 2. Resource Conformance Evidence",
            "| Tick | Mode | RAM (MB) | Compute (ms) | Debt | Queue |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        # Sample 5 measurement points for the table
        for p in result.measurements[:5]:
            lines.append(f"| {p.tick} | {p.mode} | {p.memory_rss_mb:.1f} | {p.tick_compute_ms:.1f} | {p.work_debt} | {p.queue_utilization:.2f} |")
        
        if len(result.measurements) > 5:
            lines.append("| ... | ... | ... | ... | ... | ... |")

        lines.extend([
            "",
            "## 3. Semantic Integrity Proof",
            f"- **Baseline Hash**: `{result.baseline_hash}`",
            f"- **Final Hash**: `{result.final_hash}`",
            f"- **Status**: {'MATCHED' if result.baseline_hash == result.final_hash else 'DRIFT_DETECTED'}",
            "",
            "## 4. Conformance Verdict"
        ])

        if result.conformance_passed:
            lines.append(f"> [!IMPORTANT]\n> This engine is certified to adhere to profile **{result.profile_name}** on Hardware Class **{result.effective_hardware_class}** for the given scenario.")
        else:
            lines.append(f"> [!CAUTION]\n> **{result.failure_kind}**: {result.failure_reason}")

        lines.append("\n## Disclaimer")
        lines.append("Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput are not supported by this certification.")

        return "\n".join(lines)
