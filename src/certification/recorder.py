from __future__ import annotations

import os
import json
from pathlib import Path
from src.certification.models import CertificationResult


class CertificationRecorder:
    """
    M10 Law: Record machine-readable truth and generate MD derivatives.
    """

    def __init__(self, output_dir: str = "reports/certification"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
    def record(self, result: CertificationResult) -> str:
        """
        M10 Law: Record machine-readable truth in a consolidated bundle.
        """
        # 1. Invariant Check: Scoped metadata must be present
        if not result.environment.effective_class:
            raise ValueError("M10 Law: Certification cannot be recorded without an Effective Hardware Class.")

        # 2. Update Machine-readable Bundle (proofs_bundle.json)
        bundle_path = self._output_dir / "proofs_bundle.json"
        bundle = {}
        if bundle_path.exists():
            try:
                with open(bundle_path, "r") as f:
                    bundle = json.load(f)
            except Exception:
                bundle = {}

        # Keyed by profile x scenario for easy lookup
        key = f"{result.profile_name}:{result.scenario_id}"
        bundle[key] = json.loads(result.to_json())
        
        with open(bundle_path, "w") as f:
            json.dump(bundle, f, indent=2)

        # 3. Consolidate Markdown (Unified Release Report)
        # We rewrite the report to include all results in the bundle for completeness.
        md_path = self._output_dir / "release_report.md"
        with open(md_path, "w") as f:
            f.write("# Consolidated Certification Report\n\n")
            f.write(f"**Last Run ID**: `{result.run_id}`\n")
            f.write(f"**Commit SHA**: `{result.commit_sha}`\n\n")
            f.write("## Scenario Summary\n\n")
            f.write("| Profile | Scenario | Status | Fail Kind | Reason |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            
            # Sort by profile then scenario
            sorted_keys = sorted(bundle.keys())
            for k in sorted_keys:
                r = bundle[k]
                status = "✅" if r["conformance_passed"] else "❌"
                if r.get("allowed_failure_observed"): status = "⚠️"
                f.write(f"| {r['profile_name']} | {r['scenario_id']} | {status} | {r['failure_kind']} | {r.get('failure_reason', '')} |\n")
            
            f.write("\n---\n\n")
            
            # Detailed breakdown for the CURRENT result (or all? Let's do latest and summary)
            f.write("## Latest Run Detail\n\n")
            f.write(self._generate_markdown(result))

        return str(bundle_path)

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
            f"- **Peak RAM (RSS)**: `{result.peak_rss_mb:.1f} MB`",
            f"- **Total CPU Time**: `{result.total_cpu_sec:.3f} sec`",
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
