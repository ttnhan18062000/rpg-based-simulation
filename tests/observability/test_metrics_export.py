import pytest
import time
import subprocess
import requests
from prometheus_client.parser import text_string_to_metric_families

from src.api.server import create_v2_app
from src.api.engine_manager import V2EngineManager
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.governance import RuntimeMode

def test_prometheus_metrics_registry_and_structure():
    """Verify that V2EngineManager creates and populates the custom metric registry correctly."""
    profile = RuntimeProfile(
        name="test_profile",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_tick_budget_ms=50,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_work_debt=100
    )
    
    manager = V2EngineManager(profile, seed=42, entities_count=5)
    try:
        # Assert collector and registry are initialized
        assert manager.metrics_registry is not None
        assert manager._latest_metrics_snapshot is not None

        # Assert initial snapshot values
        snapshot = manager.get_metrics_snapshot()
        assert snapshot["tick"] == 0
        assert snapshot["active_entities"] == 5
        assert snapshot["tps"] == 0.0
        assert snapshot["governor_mode"] == int(RuntimeMode.NORMAL)

        # Generate Prometheus text and parse it
        from prometheus_client import generate_latest
        text_data = generate_latest(manager.metrics_registry).decode("utf-8")

        families = {f.name: f for f in text_string_to_metric_families(text_data)}

        # Assert P0 metrics are defined
        p0_metrics = [
            "sim_current_tick",
            "sim_active_entities",
            "sim_ticks_per_second",
            "sim_tick_compute_ms",
            "sim_worker_utilization",
            "sim_queue_utilization",
            "sim_memory_rss_bytes",
            "sim_work_debt_total",
            "sim_governor_mode",
            "sim_gold_circulation_total",
            "sim_hard_law_last_violation_tick"
        ]
        for metric_name in p0_metrics:
            assert metric_name in families, f"Missing core metric {metric_name}"
            assert len(families[metric_name].samples) > 0
    finally:
        manager.stop()

def test_prometheus_hard_law_violation_metrics_export():
    """Verify that hard law violations are exported correctly in Prometheus metrics."""
    profile = RuntimeProfile(
        name="test_profile_violations",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_tick_budget_ms=50,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_work_debt=100
    )
    
    manager = V2EngineManager(profile, seed=42, entities_count=5)
    try:
        # Manually inject a hard law violation to status
        kernel_status = manager._kernel.status
        kernel_status.cumulative_violations = {"LAW-HP-NONNEGATIVE": 2}
        kernel_status.last_hard_law_violation_tick = 42

        manager._latest_metrics_snapshot["hard_law_violations_cumulative"] = {"LAW-HP-NONNEGATIVE": 2}
        manager._latest_metrics_snapshot["last_hard_law_violation_tick"] = 42

        from prometheus_client import generate_latest
        text_data = generate_latest(manager.metrics_registry).decode("utf-8")
        families = {f.name: f for f in text_string_to_metric_families(text_data)}

        assert "sim_hard_law_violations" in families
        assert "sim_hard_law_last_violation_tick" in families

        v_total = families["sim_hard_law_violations"]
        assert len(v_total.samples) == 1
        assert v_total.samples[0].value == 2.0
        assert v_total.samples[0].labels["law_id"] == "LAW-HP-NONNEGATIVE"

        v_tick = families["sim_hard_law_last_violation_tick"]
        assert v_tick.samples[0].value == 42.0
    finally:
        manager.stop()

@pytest.mark.anyio
async def test_metrics_endpoint_direct():
    """Verify the /metrics API endpoint directly using async invocation without httpx."""
    profile = RuntimeProfile(
        name="test_profile_direct",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_tick_budget_ms=50,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_work_debt=100
    )
    manager = V2EngineManager(profile)
    try:
        app = create_v2_app(profile)

        # Locate the /metrics endpoint route in the app
        metrics_endpoint = None
        for route in app.routes:
            if getattr(route, "path", None) == "/metrics":
                metrics_endpoint = route.endpoint
                break

        assert metrics_endpoint is not None, "Failed to find /metrics endpoint in app"

        # Execute the endpoint directly
        response = await metrics_endpoint(manager)

        assert response.status_code == 200
        assert "text/plain" in response.media_type

        text_data = response.body.decode("utf-8")
        families = {f.name: f for f in text_string_to_metric_families(text_data)}

        assert "sim_current_tick" in families
        assert families["sim_current_tick"].samples[0].value == 0.0
        assert "sim_active_entities" in families
        assert families["sim_active_entities"].samples[0].value > 0.0
    finally:
        manager.stop()

def test_metrics_endpoint_integration():
    """Verify the /metrics API endpoint over HTTP using a background server subprocess."""
    port = 8011
    cmd = ["python3", "-m", "src", "serve", "--port", str(port), "--log-level", "ERROR"]
    server = subprocess.Popen(cmd)
    
    # Wait for server startup
    time.sleep(3)
    
    try:
        # Scrape metrics over HTTP
        resp = requests.get(f"http://127.0.0.1:{port}/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        
        text_data = resp.text
        families = {f.name: f for f in text_string_to_metric_families(text_data)}
        
        # Verify core metric exists and matches running condition
        assert "sim_current_tick" in families
        assert families["sim_current_tick"].samples[0].value >= 0.0
        assert "sim_gold_circulation_total" in families
        assert families["sim_gold_circulation_total"].samples[0].value > 0.0
        
    finally:
        server.terminate()
        server.wait()

def test_multiple_registries_prevent_collision():
    """Verify that multiple engine lifespans do not pollute each other or crash on duplicate registration."""
    profile1 = RuntimeProfile(
        name="p1",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_tick_budget_ms=50,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_work_debt=100
    )
    profile2 = RuntimeProfile(
        name="p2",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=0,
        max_queue_depth=10,
        max_tick_budget_ms=50,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_work_debt=100
    )
    
    m1 = V2EngineManager(profile1, seed=1)
    m2 = V2EngineManager(profile2, seed=2)
    try:
        assert m1.metrics_registry is not m2.metrics_registry

        from prometheus_client import generate_latest
        # Generating metrics from both registries must not raise any exceptions
        text1 = generate_latest(m1.metrics_registry).decode("utf-8")
        text2 = generate_latest(m2.metrics_registry).decode("utf-8")

        assert len(text1) > 0
        assert len(text2) > 0
    finally:
        m1.stop()
        m2.stop()
