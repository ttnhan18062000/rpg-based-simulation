import os
import re
import time
import logging
import requests
from typing import Dict, Any, Optional

from src.logging.formatter import setup_v2_logging
from src.observability.alerts.manager import AlertsManager
from src.observability.alerts.models import AlertEvent

setup_v2_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("watchdog")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
# The tick comes from the backend's internal metrics port (rpg R1, src/api/metrics_port.py), the same registry /metrics on the API port serves, without the API key that /metrics there
# requires (and that this poller has none of): TCK-20261021-WATCHDOG-POLLS-AN-ADMISSION-GATED-METRICS-ENDPOINT. /health stays on BACKEND_URL (it has no gate).
METRICS_URL = os.environ.get("METRICS_URL", "http://backend:9109")
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))

_TICK_LINE = re.compile(r"^sim_current_tick(?:\{[^}]*\})?\s+(\S+)")


def parse_tick(text: str) -> Optional[float]:
    """The value of the ``sim_current_tick`` sample in Prometheus text, or None. The metric name must match exactly: a longer name such as ``sim_current_tick_total`` is another metric."""
    for line in text.splitlines():
        match = _TICK_LINE.match(line)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
    return None


class SimulationWatchdog:
    """Persistent monitor that audits the simulation stack's health."""
    
    def __init__(self):
        self.last_tick = -1
        self.consecutive_failures = 0
        self.max_failures = 3
        self.run_id = "external-watchdog-unknown"
        self.metrics_url = METRICS_URL
        self.metrics_blind = False  # set by check_metrics: the metrics endpoint refused this poller (HTTP 401/403), so nothing about the tick is known
        logger.info("Watchdog initialized. Targets: Backend=%s, Metrics=%s, Loki=%s", BACKEND_URL, self.metrics_url, LOKI_URL)

    def check_health(self) -> bool:
        """Poll the /health endpoint."""
        try:
            resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if resp.status_code == 200:
                try:
                    body = resp.json()
                    candidate = body.get("engine", {}).get("run_id")
                    if candidate:
                        self.run_id = candidate
                except Exception:
                    pass
                return True
            logger.error("Health check failed: HTTP %d", resp.status_code)
        except Exception as e:
            logger.error("Health check exception: %s", e)
        return False

    def check_metrics(self) -> tuple[bool, str]:
        """Poll metrics to ensure the simulation is actually ticking.

        A 401/403 means the endpoint refuses this poller: the watchdog is misconfigured and blind, which says nothing about the simulation. It is therefore not a failure
        (no stall is counted) but it sets ``metrics_blind``, which ``run_cycle`` turns into its own alert. Any other non-200, a refused connection and a timeout are failures.
        """
        self.metrics_blind = False
        try:
            resp = requests.get(f"{self.metrics_url}/metrics", timeout=5)
            if resp.status_code in (401, 403):
                self.metrics_blind = True
                return True, f"Metrics gated (HTTP {resp.status_code})"
            if resp.status_code != 200:
                return False, f"Metrics HTTP {resp.status_code}"

            curr_tick = parse_tick(resp.text)
            if curr_tick is None:
                return True, "Metric Not Found (Pending)"
            if curr_tick > self.last_tick:
                self.last_tick = curr_tick
                return True, f"Tick {curr_tick}"
            if curr_tick == self.last_tick:
                if curr_tick == 0:
                    return True, "Tick 0 (Starting)"
                return False, f"Tick Stalled at {curr_tick}"
            return True, "Metric Not Found (Pending)"
        except Exception as e:
            return False, f"Metrics Error: {str(e)[:50]}"

    def check_loki_errors(self) -> list[str]:
        """Query Loki for any error/fail logs and return specific messages."""
        try:
            query = '{level=~"(?i)error|critical", component!="watchdog"}'
            end_time = int(time.time() * 1e9)
            start_time = end_time - (POLL_INTERVAL * 2 * 10**9)
            
            params: dict[str, str | int] = {'query': query, 'start': start_time, 'end': end_time, 'limit': 3}
            resp = requests.get(f"{LOKI_URL}/loki/api/v1/query_range", params=params, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get('data', {}).get('result', [])
                error_msgs = []
                for res in results:
                    container = res.get('stream', {}).get('container', 'unknown')
                    container = container.replace('/rpg-based-simulation-', '').replace('-1', '')
                    for val in res.get('values', []):
                        try:
                            error_msgs.append(f"[{container}] {val[1][:150]}")
                        except: pass
                return error_msgs
        except Exception as e:
            logger.error("Loki query exception: %s", e)
        return []

    def run_cycle(self):
        """Execute one full monitoring cycle with detailed reasons."""
        health_ok = self.check_health()
        metrics_ok, metrics_reason = self.check_metrics()
        errors = self.check_loki_errors()

        status_report = {
            "health": "OK" if health_ok else "FAIL",
            "metrics": metrics_reason,
            "error_count": len(errors),
            "sample_errors": errors[:2]
        }

        if not health_ok or not metrics_ok or errors:
            self.consecutive_failures += 1
            logger.warning("Watchdog detected anomaly: %s. Failure count: %d", 
                          status_report, self.consecutive_failures)
        else:
            if self.consecutive_failures > 0:
                logger.info("Watchdog recovered. Status: %s", status_report)
            else:
                logger.info("Watchdog Health Check OK: %s", status_report)
            self.consecutive_failures = 0

        if self.metrics_blind:
            self._route_blind_alert(status_report)

        if self.consecutive_failures >= self.max_failures:
            logger.critical("SYSTEM_CRITICAL: Persistent failure! Reason: %s",
                           status_report, extra={'component': 'watchdog', 'diagnostics': status_report})
            try:
                router = AlertsManager.get_router()
                tick_value = int(self.last_tick) if self.last_tick and self.last_tick > 0 else 0
                event = AlertEvent.create_watchdog_trip(
                    run_id=self.run_id,
                    tick=tick_value,
                    message=f"External SimulationWatchdog detected persistent failure: {status_report}",
                    details=status_report,
                )
                router.route(event)
            except Exception:
                logger.exception("Failed to dispatch WatchdogTrip alert")

    def _route_blind_alert(self, status_report: Dict[str, Any]) -> None:
        """The watchdog cannot read the metrics endpoint: tell the operator once per dedup window (the router's own, SIM_ALERTS_DEDUP_WINDOW_SECONDS, default 60 s), without a stall alert."""
        try:
            tick_value = int(self.last_tick) if self.last_tick and self.last_tick > 0 else 0
            AlertsManager.get_router().route(AlertEvent.create_watchdog_blind(
                run_id=self.run_id,
                tick=tick_value,
                message=f"External SimulationWatchdog cannot read {self.metrics_url}/metrics ({status_report['metrics']}); stall detection is off until it can",
                details=status_report,
            ))
        except Exception:
            logger.exception("Failed to dispatch WatchdogBlind alert")

    def start(self):
        """Main loop."""
        while True:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error("Watchdog loop error: %s", e)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    watchdog = SimulationWatchdog()
    watchdog.start()
