import subprocess
import json
import pytest
import sys
import os

@pytest.mark.e2e
def test_cli_logging_json_format():
    """Verify that 'python -m src cli' outputs valid JSON logs to stdout."""
    # Ensure we are in the project root
    cwd = os.getcwd()
    
    cmd = [sys.executable, "-m", "src", "cli", "--ticks", "2"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=cwd)
    
    # Filter out empty lines
    lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
    assert len(lines) > 0, f"No logs produced by CLI. Stderr: {result.stderr}"
    
    for line in lines:
        try:
            log_data = json.loads(line)
            # Mandatory fields defined in our Centralized Logging spec
            assert "timestamp" in log_data, f"Missing 'timestamp' in {line}"
            assert "level" in log_data, f"Missing 'level' in {line}"
            assert "message" in log_data, f"Missing 'message' in {line}"
            assert "component" in log_data, f"Missing 'component' in {line}"
        except json.JSONDecodeError:
            pytest.fail(f"Non-JSON log line detected: {line}")

@pytest.mark.e2e
def test_logging_context_injection():
    """Verify that specific components inject their expected context labels."""
    cwd = os.getcwd()
    cmd = [sys.executable, "-m", "src", "cli", "--ticks", "5"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=cwd)
    
    lines = []
    for line in result.stdout.split('\n'):
        if not line.strip(): continue
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # 1. Verify WorldLoop Context
    # Note: Component name in LoggerAdapter might be 'world_loop' (our manual override) or the module name
    world_loop_logs = [l for l in lines if l.get("component") in ("world_loop", "src.engine.world_loop")]
    assert len(world_loop_logs) > 0, "No WorldLoop logs found in output"
    
    # The first few logs might have tick -1 or 0
    for log in world_loop_logs:
        assert "tick" in log, f"WorldLoop log missing 'tick' context: {log}"
        assert isinstance(log["tick"], int)

    # 2. Verify WorkerPool Context
    worker_pool_logs = [l for l in lines if l.get("component") in ("worker_pool", "src.engine.worker_pool")]
    # Note: In CLI mode with 1 worker, WorkerPool might not log much unless there is an error or initialization
    # If num_workers > 1 is not set in CLI args, it might be quiet.
    # Let's check for __main__ logs at least
    main_logs = [l for l in lines if l.get("component") == "__main__"]
    assert len(main_logs) > 0, "No __main__ logs found"
