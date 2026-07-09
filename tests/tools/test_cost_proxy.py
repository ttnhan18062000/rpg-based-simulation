"""Tests for tools/agent-monitoring/cost_proxy.py's compute_cost_proxy_score
(TCK-20260708-AGENT-COST-OBSERVABILITY).

Pure unit tests against the formula module only — no file I/O, no subprocess.
"""
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from cost_proxy import W_AGENT, W_BASH, W_EDIT, compute_cost_proxy_score  # noqa: E402


def test_cost_proxy_score_computation_matches_formula():
    bash_only = [
        {"tool": "Bash", "duration_ms": 1000},
        {"tool": "Bash", "duration_ms": 2000},
    ]
    assert compute_cost_proxy_score(bash_only) == W_BASH * 3000

    agent_only = [
        {"tool": "Agent", "duration_ms": 97},
        {"tool": "Agent", "duration_ms": 50000},
    ]
    assert compute_cost_proxy_score(agent_only) == W_AGENT * 2

    edit_only = [
        {"tool": "Read"},
        {"tool": "Edit"},
        {"tool": "Write"},
        {"tool": "MultiEdit"},
    ]
    assert compute_cost_proxy_score(edit_only) == W_EDIT * 4

    mixed = [
        {"tool": "Bash", "duration_ms": 5000},
        {"tool": "Agent", "duration_ms": 100},
        {"tool": "Read"},
        {"tool": "Edit"},
        {"tool": "Grep"},
    ]
    expected = (W_BASH * 5000) + (W_AGENT * 1) + (W_EDIT * 2)
    assert compute_cost_proxy_score(mixed) == expected


def test_cost_proxy_score_excludes_null_duration_bash_rows():
    rows = [
        {"tool": "Bash", "duration_ms": None},
        {"tool": "Bash", "duration_ms": 1000},
    ]
    assert compute_cost_proxy_score(rows) == W_BASH * 1000


def test_cost_proxy_score_empty_group_is_zero():
    assert compute_cost_proxy_score([]) == 0
