import os
import signal
import sys
import threading
import time
import pytest
from src_legacy.ai.flow_fields import FlowFieldManager
from src_legacy.core.gameplay.items.item_registry import ITEM_REGISTRY

def pytest_sessionstart(session):
    """Set hard OS-level resource limits and start the watchdog for the entire session. [Tier 1 & 2]"""
    # 1. OS-Level Hard Limit (RLIMIT_AS)
    try:
        import resource
        # Set Virtual Memory limit to 2GB. 
        # This prevents the process from ever growing large enough to lock up the system.
        LIMIT_BYTES = 2048 * 1024 * 1024 
        resource.setrlimit(resource.RLIMIT_AS, (LIMIT_BYTES, LIMIT_BYTES))
    except (ImportError, Exception):
        pass # Fallback to Watchdog only if resource module is missing

    # 2. Start Background Watchdog Thread
    _start_resource_watchdog()

def _start_resource_watchdog():
    """Launch a daemon thread that kills the process if it approaches the safety boundary."""
    def watchdog_loop():
        try:
            import psutil
            import gc
        except ImportError:
            return

        process = psutil.Process()
        MAX_RSS_MB = 1024 # Tier 2 Soft-limit
        STRIKES_LIMIT = 3
        strikes = 0

        while True:
            try:
                # 1. Memory Check
                rss_mb = process.memory_info().rss / (1024 * 1024)
                if rss_mb > MAX_RSS_MB:
                    strikes += 1
                    if strikes >= STRIKES_LIMIT:
                        print(f"\n\n[FATAL] RESOURCE EXHAUSTION DETECTED: {rss_mb:.1f}MB > {MAX_RSS_MB}MB", file=sys.stderr)
                        print("[FATAL] Terminating process immediately to protect system stability.", file=sys.stderr)
                        os._exit(1) # Hard kill
                else:
                    strikes = 0

                # 2. Wall-clock Timeout Check (Hardening against hangs)
                current_time = time.time()
                for nodeid, res in list(_test_start_resources.items()):
                    elapsed = current_time - res["start_wall_time"]
                    timeout = res.get("timeout", 300.0) # Default 5 minutes
                    if elapsed > timeout:
                        print(f"\n\n[FATAL] TEST HANG DETECTED: '{nodeid}' has been running for {elapsed:.1f}s", file=sys.stderr)
                        print(f"[FATAL] Exceeded hard limit of {timeout}s. Killing process.", file=sys.stderr)
                        os.kill(os.getpid(), signal.SIGKILL)
            except Exception:
                pass
            time.sleep(1.0) # Check every 1s

    t = threading.Thread(target=watchdog_loop, daemon=True, name="resource-watchdog")
    t.start()

@pytest.fixture(autouse=True)
def test_env_setup():
    """Configure unit test environment for total isolation and speed."""
    os.environ["DISABLE_KAFKA"] = "1"
    os.environ["DISABLE_REDIS"] = "1"
    yield

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all simulation singletons before each test to ensure total isolation."""
    FlowFieldManager.reset_instance()
    ITEM_REGISTRY.clear()
    from src_legacy.core.registry.registry_loader import load_all_registries
    # Auto-load registries for tests if they expect items/classes to exist
    try:
        load_all_registries()
    except Exception:
        pass
    yield

# Track starting resources to detect per-test leaks and CPU exhaustion
_test_start_resources = {}

def pytest_runtest_setup(item):
    """Capture starting RSS and CPU time before each test. [Flex-Timeout]"""
    # 1. Determine Timeout
    timeout = 300.0 # Default 5 mins
    timeout_marker = item.get_closest_marker("timeout")
    if timeout_marker:
        timeout = float(timeout_marker.args[0])
    elif item.get_closest_marker("slow"):
        timeout = 600.0 # 10 mins for slow tests
    
    # 2. Capture Stats
    import psutil
    import gc
    gc.collect()
    process = psutil.Process()
    _test_start_resources[item.nodeid] = {
        "rss": process.memory_info().rss,
        "cpu": process.cpu_times(),
        "start_wall_time": time.time(),
        "timeout": timeout
    }

def pytest_runtest_teardown(item, nextitem):
    """Fail tests that cause excessive resource growth or CPU exhaustion."""
    import psutil
    import gc
    gc.collect() # Try to clean up before measuring
    
    process = psutil.Process()
    mem_info = process.memory_info()
    cpu_info = process.cpu_times()
    rss_mb = mem_info.rss / (1024 * 1024)
    
    # 1. Global Session Limit: Catch runaway process exhaustion
    LIMIT_MB = 1024 
    if rss_mb > LIMIT_MB:
        from _pytest.outcomes import fail
        fail(f"Process-wide resource exhaustion: {rss_mb:.1f}MB > {LIMIT_MB}MB. Check for session-level leaks.")

    # 2. Per-Test Resource Delta Limit: Catch leaks and CPU spikes
    start_res = _test_start_resources.pop(item.nodeid, None)
    if start_res is not None:
        delta_mb = (mem_info.rss - start_res["rss"]) / (1024 * 1024)
        
        start_cpu = start_res["cpu"]
        delta_cpu = (cpu_info.user + cpu_info.system) - (start_cpu.user + start_cpu.system)
        
        # Memory Tripwire
        DELTA_LIMIT_MB = 600
        if delta_mb > DELTA_LIMIT_MB:
            from _pytest.outcomes import fail
            fail(f"Test '{item.name}' leaked {delta_mb:.1f}MB. Check for unreleased references.")

        # CPU Tripwire: Fail if a single test takes more than 60s of CPU time
        # This prevents tests that are "stuck" or doing massive redundant work.
        CPU_LIMIT_SEC = 60.0
        if delta_cpu > CPU_LIMIT_SEC:
            from _pytest.outcomes import fail
            fail(f"Test '{item.name}' exhausted CPU: {delta_cpu:.2f}s used. Optimize hotspots.")
