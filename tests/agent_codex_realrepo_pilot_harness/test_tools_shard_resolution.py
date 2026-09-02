"""Tests for tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines() dual-tree-shape
resolution (TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS).

proofs.py's private _lines() helper is the exact unit this hotfix's fourth acceptance criterion
names: it must resolve the 'tools' monitoring source correctly whether the captured tree came
from the real repo (agent-monitoring/tools/tools-*.jsonl shard keys) or from a synthetic scratch
tree these packages' own fixtures still build directly (a single literal
agent-monitoring/tools.jsonl key, e.g. tests/agent_codex_realrepo_pilot_harness/
test_harness_context.py's _write_shape()). Tested directly rather than only indirectly through
assert_post_run_proof() because it is this defect's exact root cause.
"""
from __future__ import annotations

from tools.agent_codex_realrepo_pilot_harness.proofs import _lines


def test_lines_resolves_a_synthetic_scratch_tree_with_a_literal_tools_file():
    tree = {"agent-monitoring/tools.jsonl": b'{"a":1}\n{"a":2}\n'}
    assert _lines(tree, "tools.jsonl") == [b'{"a":1}\n', b'{"a":2}\n']


def test_lines_resolves_a_real_shaped_tree_with_multiple_sorted_shards():
    tree = {
        "agent-monitoring/tools/tools-2026-W02.jsonl": b'{"w":2}\n',
        "agent-monitoring/tools/tools-2026-W01.jsonl": b'{"w":1}\n',
        "agent-monitoring/tools/tools-unknown-week.jsonl": b'{"w":"unknown"}\n',
        "agent-monitoring/runs.jsonl": b'{"unrelated":true}\n',
    }
    assert _lines(tree, "tools.jsonl") == [
        b'{"w":1}\n',
        b'{"w":2}\n',
        b'{"w":"unknown"}\n',
    ]


def test_lines_prefers_shard_keys_over_a_stray_literal_key_when_both_present():
    tree = {
        "agent-monitoring/tools.jsonl": b'{"legacy":true}\n',
        "agent-monitoring/tools/tools-2026-W01.jsonl": b'{"real":true}\n',
    }
    assert _lines(tree, "tools.jsonl") == [b'{"real":true}\n']


def test_lines_returns_empty_when_neither_shape_is_present():
    assert _lines({}, "tools.jsonl") == []


def test_lines_leaves_non_tools_sources_unaffected():
    tree = {"agent-monitoring/runs.jsonl": b'{"a":1}\n'}
    assert _lines(tree, "runs.jsonl") == [b'{"a":1}\n']
    assert _lines({}, "events.jsonl") == []
