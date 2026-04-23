import subprocess
import os
import shutil
import json
from pathlib import Path

def test_cli_basic_execution():
    """Verify that python -m src_v2 cli runs and produces output."""
    replay_dir = "data/test_cli_basic"
    if os.path.exists(replay_dir):
        shutil.rmtree(replay_dir)
        
    cmd = [
        "python3", "-m", "src_v2", "cli",
        "--seed", "123",
        "--entities", "5",
        "--ticks", "20",
        "--replay", replay_dir
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "V2 Simulation Started" in result.stdout
    assert "Final State Hash" in result.stdout
    
    # Verify artifacts
    assert os.path.exists(os.path.join(replay_dir, "manifest.json"))
    with open(os.path.join(replay_dir, "manifest.json"), "r") as f:
        manifest = json.load(f)
        assert manifest["status"] == "COMPLETED"

def test_cli_invalid_arg():
    """Verify that invalid arguments cause an error."""
    cmd = ["python3", "-m", "src_v2", "cli", "--invalid-flag", "val"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "unrecognized arguments" in result.stderr

def test_cli_default_mode():
    """Verify that running without a subcommand starts the server (default mode)."""
    cmd = ["python3", "-m", "src_v2", "--port", "8006"]
    try:
        # Should start the server and keep running. We use a short timeout.
        subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except subprocess.TimeoutExpired as e:
        # If it timed out, it means the server started successfully!
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else e.stdout
        assert "Starting V2 server" in stdout

def test_cli_determinism():
    """Verify that identical CLI calls produce identical hashes."""
    def get_hash(seed):
        cmd = [
            "python3", "-m", "src_v2", "cli",
            "--seed", str(seed),
            "--entities", "5",
            "--ticks", "10"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "Final State Hash:" in line:
                return line.split(":")[-1].strip()
        return None

    hash1 = get_hash(42)
    hash2 = get_hash(42)
    hash3 = get_hash(43)
    
    assert hash1 is not None
    assert hash1 == hash2
    assert hash1 != hash3
