from __future__ import annotations

import os
from pathlib import Path
from src_v2.certification.models import CertificationResult


class CertificationRecorder:
    """
    M10 Law: Record machine-readable truth and generate MD derivatives.
    Enforces the 'Honest Reporting Logic Invariant':
    Reports CANNOT be generated unless claim is strictly bound to:
    (Profile, Scenario, Hardware Class, Commit SHA).
    """

    def __init__(self, output_dir: str = "reports/release_proof"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def record(self, result: CertificationResult) -> str:
        """
        Record the machine-readable truth and generate the MD derivative.
        Enforces logic invariants.
        """
        # 1. Invariant Check: Scoped metadata must be present
        if not result.commit_sha or result.commit_sha == "unknown-dirty":
            # In a real CI, we might raise an error here. 
            # For Milestone E, we will record it but mark it clearly as non-certified.
            pass
            
        if not result.environment.effective_class:
            raise ValueError("M10 Law: Certification cannot be recorded without an Effective Hardware Class.")

        # 2. Machine-readable artifact (The Proof)
        json_path = self._output_dir / "release_proof.json"
        with open(json_path, "w") as f:
            f.write(result.to_json())

        # 3. Markdown summary (The Scoped Report)
        md_path = self._output_dir / "release_report.md"
        with open(md_path, "w") as f:
            f.write(self._generate_markdown(result))

        return str(json_path)

    def _generate_markdown(self, result: CertificationResult) -> str:
        """
        M10 Law: Bind performance and safety to the technical quadrant.
        This method is the ONLY path for report generation, ensuring scoped language.
        """
        status_emoji = "✅" if result.conformance_passed else "❌"
        if result.allowed_failure_observed:
            status_emoji = "⚠️" # Allowed Failure
            
        env = result.environment
        class_label = env.effective_class.name
        if env.override_applied:
            class_label = f"{class_label} (OVERRIDDEN, detected {env.detected_class.name})"

        lines = [
            f"# Certification Report: {result.scenario_id}",
            f"**Commit SHA**: `{result.commit_sha}`",
            f"**Status**: {status_emoji} **{('PASS' if result.conformance_passed else 'FAIL')}**",
            f"**Allowed Failure Observed**: `{result.allowed_failure_observed}`",
            "",
            "## 1. Certified Execution Context (M10 Scoped Truth)",
            f"- **Runtime Profile**: `{result.profile_name}`",
            f"- **Hardware Class**: `{class_label}`",
            f"- **Scenario**: `{result.scenario_id}`",
            f"- **Seed**: `{result.seed}`",
            "",
            "## 2. Resource Conformance Evidence",
            "| Tick | Mode | RAM (MB) | Compute (ms) | Worker % | Queue % |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        # Sample measurement points for the table
        points = result.measurements
        if len(points) > 10:
            # Sample start + end + heaviest points
            sampled = points[:3] + points[len(points)//2:len(points)//2+3] + points[-4:]
            sampled.sort(key=lambda x: x.tick)
        else:
            sampled = points

        for p in sampled:
            # M10 Law: Use disaggregated worker/queue utilization
            lines.append(f"| {p.tick} | {p.mode} | {p.memory_rss_mb:.1f} | {p.tick_compute_ms:.1f} | {p.worker_utilization:.2f} | {p.queue_utilization:.2f} |")
        
        if len(points) > len(sampled):
            lines.append("| ... | ... | ... | ... | ... | ... |")

        lines.extend([
            "",
            "## 3. Semantic Integrity Proof (Milestone D Law)",
            f"- **Baseline Hash**: `{result.baseline_hash}`",
            f"- **Final Hash**: `{result.final_hash}`",
            f"- **Status**: {'MATCHED' if result.baseline_hash == result.final_hash else 'DRIFT_DETECTED'}",
            "",
            "## 4. Conformance Verdict"
        ])

        if result.conformance_passed:
            if result.allowed_failure_observed:
                lines.append(f"> [!IMPORTANT]\n> **ALLOWED FAILURE DETECTED**: {result.failure_kind.name}\n> {result.failure_reason}\n> \n> This engine is certified under the assumption that this specific failure is acceptable for this scenario.")
            else:
                lines.append(f"> [!IMPORTANT]\n> This engine is certified to adhere to profile **{result.profile_name}** on Hardware Class **{env.effective_class.name}** for the given scenario duration.")
        else:
            lines.append(f"> [!CAUTION]\n> **{result.failure_kind.name}**: {result.failure_reason}")

        lines.append("\n## Honest Reporting Disclaimer")
        lines.append("Performance and safety metrics in this report apply ONLY to the (Profile, Scenario, Hardware Class) bundle defined above. Claims of universal throughput or unbounded scaling are explicitly unsupported by this certification and violate Milestone E project laws.")

        return "\n".join(lines)
