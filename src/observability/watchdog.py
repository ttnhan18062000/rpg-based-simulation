import os
import time
import logging
import requests
from typing import Dict, Any

from src.logging.formatter import setup_v2_logging

setup_v2_logging(os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("watchdog")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8000")
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))

class SimulationWatchdog:
    """Persistent monitor that audits the simulation stack's health."""
    
    def __init__(self):
        self.last_tick = -1
        self.consecutive_failures = 0
        self.max_failures = 3
        logger.info("Watchdog initialized. Targets: Backend=%s, Loki=%s", BACKEND_URL, LOKI_URL)

    def check_health(self) -> bool:
        """Poll the /health endpoint."""
        try:
            resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if resp.status_code == 200:
                return True
            logger.error("Health check failed: HTTP %d", resp.status_code)
        except Exception as e:
            logger.error("Health check exception: %s", e)
        return False

    def check_metrics(self) -> tuple[bool, str]:
        """Poll metrics to ensure the simulation is actually ticking."""
        try:
            resp = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
            if resp.status_code != 200:
                return False, f"Metrics HTTP {resp.status_code}"
            
            # Find sim_current_tick in Prometheus text format
            for line in resp.text.splitlines():
                if line.startswith("sim_current_tick"):
                    curr_tick = float(line.split()[1])
                    if curr_tick > self.last_tick:
                        self.last_tick = curr_tick
                        return True, f"Tick {curr_tick}"
                    elif curr_tick == self.last_tick:
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
            
            params = {'query': query, 'start': start_time, 'end': end_time, 'limit': 3}
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

        if self.consecutive_failures >= self.max_failures:
            logger.critical("SYSTEM_CRITICAL: Persistent failure! Reason: %s",
                           status_report, extra={'component': 'watchdog', 'diagnostics': status_report})

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
