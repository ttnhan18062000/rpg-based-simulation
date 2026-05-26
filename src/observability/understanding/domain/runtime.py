"""
RuntimeDomainAnalyzer — Interprets runtime and engine health anomalies.

Analyzes:
- Sustained governor degradation
- High event drop rates
- Tick compute instability (if metrics available)

Required signals: anomaly events with GovernorDegradedLive or EventDropRateHigh rules
(Falls back gracefully if only some signals present.)
"""
from __future__ import annotations
from typing import Any, Dict, List

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.base import (
    DomainAnalyzer, DomainAnalysisResult, DomainAnalysisStatus,
    DomainFinding, ConfidenceLevel
)


class RuntimeDomainAnalyzer(DomainAnalyzer):
    """
    Domain analyzer for runtime stability and performance issues.

    Unlike other analyzers, this one requires anomalies (not events) as
    primary signal — it interprets GovernorDegradedLive and EventDropRateHigh
    anomalies rather than raw event streams.

    Gracefully skips if no runtime-related anomalies or events exist.
    """

    domain_id = "runtime"
    required_event_categories: List[str] = []   # No required event category
    optional_event_categories: List[str] = []
    required_anomaly_rules: List[str] = []       # Uses anomalies directly

    GOVERNOR_DEGRADED_THRESHOLD = 3   # ≥ N governor degraded anomalies → finding
    DROP_RATE_THRESHOLD = 2           # ≥ N event drop anomalies → finding

    def analyze(self, ctx: AnalysisContext) -> DomainAnalysisResult:
        governor_anomalies = ctx.anomalies_by_rule("GovernorDegradedLive")
        drop_anomalies = ctx.anomalies_by_rule("EventDropRateHigh")
        critical_anomalies = ctx.anomalies_by_severity("CRITICAL")

        # Require at least one runtime-related signal
        has_runtime_signal = any([
            governor_anomalies,
            drop_anomalies,
            any(
                a.rule_name in ("CriticalEventObserved", "HardLawViolationLive")
                for a in critical_anomalies
            )
        ])

        if not has_runtime_signal and not ctx.anomalies:
            return self._missing_signal_result(
                "No runtime anomaly signals found (no governor/drop/critical anomalies)."
            )

        findings: List[DomainFinding] = []

        # ── Finding 1: Governor pressure sustained ────────────────────────────
        if len(governor_anomalies) >= self.GOVERNOR_DEGRADED_THRESHOLD:
            ticks_degraded = [
                a.context.get("sustained_ticks", 0) for a in governor_anomalies
            ]
            total_degraded_ticks = sum(ticks_degraded)
            modes = list(set(
                a.context.get("current_mode", "UNKNOWN") for a in governor_anomalies
            ))

            confidence = (
                ConfidenceLevel.HIGH if len(governor_anomalies) >= 5
                else ConfidenceLevel.MEDIUM
            )

            findings.append(DomainFinding(
                domain=self.domain_id,
                severity="WARNING",
                title=f"Sustained Governor Pressure — {len(governor_anomalies)} Incidents",
                summary=(
                    f"The system governor entered degraded/survival mode {len(governor_anomalies)} times "
                    f"(modes: {modes}, total estimated degraded ticks: ~{total_degraded_ticks}). "
                    "This indicates the simulation is running under sustained resource pressure."
                ),
                evidence=[
                    f"Governor degraded anomalies: {len(governor_anomalies)}",
                    f"Detected governor modes: {modes}",
                    f"Total estimated degraded ticks: ~{total_degraded_ticks}",
                ],
                suspected_causes=[
                    "Observability overhead eating into tick budget",
                    "Worker thread backlog growing faster than draining",
                    "Entity count too high for hardware class profile",
                    "Memory growth forcing GC pressure spikes",
                ],
                confidence=confidence,
                recommended_next_steps=[
                    "Switch observatory to LIGHT or OFF mode and compare tick times",
                    "Review worker queue depth and drain rate",
                    "Check entity count vs hardware profile budget",
                    "Profile with `cProfile` to identify slow tick phases",
                ],
            ))

        # ── Finding 2: High event drop rate ──────────────────────────────────
        if len(drop_anomalies) >= self.DROP_RATE_THRESHOLD:
            total_drops = sum(
                a.context.get("drop_count", 0) for a in drop_anomalies
            )

            findings.append(DomainFinding(
                domain=self.domain_id,
                severity="WARNING",
                title=f"High Event Drop Rate — {len(drop_anomalies)} Anomalies",
                summary=(
                    f"Event drop rate anomalies fired {len(drop_anomalies)} times "
                    f"(estimated total drops: {total_drops}). "
                    "Live analysis consumers may be receiving incomplete data."
                ),
                evidence=[
                    f"EventDropRateHigh anomalies: {len(drop_anomalies)}",
                    f"Estimated total dropped events: {total_drops}",
                ],
                suspected_causes=[
                    "Subscriber queue capacity too low for event volume",
                    "Slow subscriber blocking drain loop",
                    "Event burst from combat/movement causing temporary overflow",
                    "Stream worker thread not keeping up",
                ],
                confidence=ConfidenceLevel.MEDIUM,
                recommended_next_steps=[
                    "Increase subscriber queue capacity or reduce event verbosity",
                    "Check stream worker thread health and drain throughput",
                    "Review which event categories produce highest volume",
                    "Consider switching to LIGHT mode to reduce event emission rate",
                ],
            ))

        # If no anomalies at all, return PASSED (not SKIPPED)
        if not findings and not ctx.anomalies:
            return DomainAnalysisResult(
                domain_id=self.domain_id,
                status=DomainAnalysisStatus.PASSED,
                findings=[]
            )

        status = (
            DomainAnalysisStatus.FINDINGS_FOUND if findings
            else DomainAnalysisStatus.PASSED
        )
        return DomainAnalysisResult(
            domain_id=self.domain_id,
            status=status,
            findings=findings
        )
