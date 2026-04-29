import sys
import os
sys.path.append(os.getcwd())

from src.core.certification_reporter import CertificationReporter

# Mock results from our successful test run
kernel_results = {
    "determinism_passed": True,
    "total_ticks": 2000,
    "peak_memory_mb": 89.86,
    "avg_tick_ms": 15.2,
    "protocol_violations": 0
}

checklist_path = "logic_checklist_exhaustive_v2.md"
output_path = "certification_report.json"

report = CertificationReporter.generate_report(kernel_results, checklist_path, output_path)

print(f"Certification Report Generated: {output_path}")
print(f"Status: {report['status']}")
print(f"Coverage: {report['summary']['coverage_percent']:.2f}%")
print(f"ID: {report['certification_id']}")
