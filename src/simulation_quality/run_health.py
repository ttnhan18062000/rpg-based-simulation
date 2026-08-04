"""Typed sidecar record for calibration-run integrity state (TCK-20260702-OBSISO-ISOLATION-PROOF).

Additive sibling to QualityReport — never a field on it (that schema is
owned/consumed elsewhere; see quality_report.py). Persisted next to
quality_report.json as quality_report.run_health.json by
tools/calibrate_simq.py's post-tick-loop drop/pressure guard, and read back by
tools/evaluate_simq.py's --dry-run path so a later, engine-free diff can still
retroactively flag a run that lost SimQ events to queue overflow or SURVIVAL
mode-shed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RunHealthRecord:
    dropped_count: int
    pressure_mode_final: str
    survival_triggered: bool
    guard_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "dropped_count": self.dropped_count,
            "pressure_mode_final": self.pressure_mode_final,
            "survival_triggered": self.survival_triggered,
            "guard_passed": self.guard_passed,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "RunHealthRecord":
        return RunHealthRecord(
            dropped_count=int(data["dropped_count"]),
            pressure_mode_final=str(data["pressure_mode_final"]),
            survival_triggered=bool(data["survival_triggered"]),
            guard_passed=bool(data["guard_passed"]),
        )
