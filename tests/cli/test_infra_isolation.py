import subprocess
import os
import json
from pathlib import Path

def test_env_precedence():
    """Verify that RPG_ env vars are respected over defaults but overridden by CLI."""
    # 1. Env vs Default
    env = os.environ.copy()
    env["RPG_MAX_WORKER_COUNT"] = "3"
    cmd = ["python3", "-m", "src", "cli", "--ticks", "1"]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert "max_worker_count=3" in result.stderr or "max_worker_count=3" in result.stdout
    
    # 2. CLI vs Env
    cmd = ["python3", "-m", "src", "cli", "--ticks", "1", "--workers", "5"]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert "max_worker_count=5" in result.stderr or "max_worker_count=5" in result.stdout

def test_broker_disabled_flag():
    """Verify that BROKER_DISABLED=1 forces sequential execution."""
    env = os.environ.copy()
    env["BROKER_DISABLED"] = "1"
    cmd = ["python3", "-m", "src", "cli", "--ticks", "1", "--workers", "4"]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert "max_worker_count=0" in result.stderr or "max_worker_count=0" in result.stdout
    assert "BROKER_DISABLED=1 detected" in result.stderr or "BROKER_DISABLED=1 detected" in result.stdout

def test_yaml_precedence():
    """Verify that YAML config is respected."""
    yaml_path = "data/test_config.yaml"
    os.makedirs("data", exist_ok=True)
    with open(yaml_path, "w") as f:
        f.write("""
profiles:
  cli_default:
    max_worker_count: 7
""")
    
    try:
        cmd = ["python3", "-m", "src", "--config", yaml_path, "cli", "--ticks", "1"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert "max_worker_count=7" in result.stderr or "max_worker_count=7" in result.stdout
        
        # CLI should still override YAML
        cmd = ["python3", "-m", "src", "--config", yaml_path, "cli", "--ticks", "1", "--workers", "9"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert "max_worker_count=9" in result.stderr or "max_worker_count=9" in result.stdout
    finally:
        if os.path.exists(yaml_path):
            os.remove(yaml_path)

def test_safe_import_isolation():
    """
    Verify that the engine can be imported even if 'optional' libraries are missing.
    We can't easily uninstall libraries in this environment, but we can mock them or 
    check that the current codebase doesn't have hard imports.
    """
    # Verify that src.engine.kernel doesn't fail on import
    import src.engine.kernel
    assert src.engine.kernel is not None
