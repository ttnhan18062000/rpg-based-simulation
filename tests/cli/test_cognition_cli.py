from __future__ import annotations
import subprocess
import pytest
import os
import json
import shutil

def test_cli_cognition_security_violation():
    """Verify that path traversal attempts are blocked by security sanitization at CLI level."""
    cmd = ["python3", "-m", "src", "cognition", "snapshot", "../../etc/passwd", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 1
    assert "Security Error" in result.stdout or "Security Error" in result.stderr
    # No raw python stack trace should be dumped
    assert "Traceback (most recent call last):" not in result.stdout
    assert "Traceback (most recent call last):" not in result.stderr


def test_cli_cognition_missing_run():
    """Verify that a query for non-existent run ID returns a clean error and exits with 1."""
    cmd = ["python3", "-m", "src", "cognition", "snapshot", "non_existent_run_xyz", "1"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 1
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "non_existent_run_xyz" in (result.stdout + result.stderr)
    assert "Traceback (most recent call last):" not in result.stdout
    assert "Traceback (most recent call last):" not in result.stderr


def test_cli_cognition_patterns_missing():
    """Verify that patterns sub-command prints clean error for missing file."""
    cmd = ["python3", "-m", "src", "cognition", "patterns", "non_existent_run_xyz"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 1
    assert "Error" in result.stdout or "Error" in result.stderr
    assert "Traceback (most recent call last):" not in result.stdout
    assert "Traceback (most recent call last):" not in result.stderr
