"""Tests for tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines() dual-tree-shape
resolution (TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION).

proofs.py's private _lines() helper is the exact unit this ticket's AC #5 names: it must resolve
every monitoring source correctly whether the captured tree came from the real repo
(agent-monitoring/data/<week>/<source>.jsonl keys) or from a synthetic scratch tree these
packages' own fixtures still build directly (a single literal agent-monitoring/<source>.jsonl
key, e.g. tests/agent_codex_realrepo_pilot_harness/test_harness_context.py's _write_shape()).
Tested directly rather than only indirectly through assert_post_run_proof() because it is this
defect's exact root cause.
"""
from __future__ import annotations

from tools.agent_codex_realrepo_pilot_harness.proofs import _lines


def test_lines_resolves_a_synthetic_scratch_tree_with_a_literal_tools_file():
    tree = {"agent-monitoring/tools.jsonl": b'{"a":1}\n{"a":2}\n'}
    assert _lines(tree, "tools.jsonl") == [b'{"a":1}\n', b'{"a":2}\n']


def test_lines_resolves_a_real_shaped_tree_with_multiple_sorted_shards():
    tree = {
        "agent-monitoring/data/2026-W02/tools.jsonl": b'{"w":2}\n',
        "agent-monitoring/data/2026-W01/tools.jsonl": b'{"w":1}\n',
        "agent-monitoring/data/unknown-week/tools.jsonl": b'{"w":"unknown"}\n',
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
        "agent-monitoring/data/2026-W01/tools.jsonl": b'{"real":true}\n',
    }
    assert _lines(tree, "tools.jsonl") == [b'{"real":true}\n']


def test_lines_returns_empty_when_neither_shape_is_present():
    assert _lines({}, "tools.jsonl") == []


def test_lines_resolves_a_synthetic_scratch_tree_for_runs_and_events():
    tree = {"agent-monitoring/runs.jsonl": b'{"a":1}\n'}
    assert _lines(tree, "runs.jsonl") == [b'{"a":1}\n']
    assert _lines({}, "events.jsonl") == []


def test_lines_resolves_a_real_shaped_tree_for_runs_and_events():
    tree = {
        "agent-monitoring/data/2026-W02/runs.jsonl": b'{"w":2}\n',
        "agent-monitoring/data/2026-W01/runs.jsonl": b'{"w":1}\n',
        "agent-monitoring/data/unknown-week/runs.jsonl": b'{"w":"unknown"}\n',
        "agent-monitoring/data/2026-W01/events.jsonl": b'{"e":1}\n',
        "agent-monitoring/data/unknown-week/events.jsonl": b'{"e":"unknown"}\n',
    }
    assert _lines(tree, "runs.jsonl") == [
        b'{"w":1}\n',
        b'{"w":2}\n',
        b'{"w":"unknown"}\n',
    ]
    assert _lines(tree, "events.jsonl") == [
        b'{"e":1}\n',
        b'{"e":"unknown"}\n',
    ]


def test_proofs_lines_resolves_all_three_sources_from_a_real_shaped_captured_tree():
    tree = {
        "agent-monitoring/data/2026-W01/runs.jsonl": b'{"src":"runs","w":1}\n',
        "agent-monitoring/data/2026-W02/runs.jsonl": b'{"src":"runs","w":2}\n',
        "agent-monitoring/data/unknown-week/runs.jsonl": b'{"src":"runs","w":"unknown"}\n',
        "agent-monitoring/data/2026-W01/events.jsonl": b'{"src":"events","w":1}\n',
        "agent-monitoring/data/unknown-week/events.jsonl": b'{"src":"events","w":"unknown"}\n',
        "agent-monitoring/data/2026-W01/tools.jsonl": b'{"src":"tools","w":1}\n',
        "agent-monitoring/data/unknown-week/tools.jsonl": b'{"src":"tools","w":"unknown"}\n',
    }
    assert _lines(tree, "runs.jsonl") == [
        b'{"src":"runs","w":1}\n',
        b'{"src":"runs","w":2}\n',
        b'{"src":"runs","w":"unknown"}\n',
    ]
    assert _lines(tree, "events.jsonl") == [
        b'{"src":"events","w":1}\n',
        b'{"src":"events","w":"unknown"}\n',
    ]
    assert _lines(tree, "tools.jsonl") == [
        b'{"src":"tools","w":1}\n',
        b'{"src":"tools","w":"unknown"}\n',
    ]


def test_fallback_bucket_never_filtered_for_runs_events_or_tools():
    for source in ("runs.jsonl", "events.jsonl", "tools.jsonl"):
        tree = {f"agent-monitoring/data/unknown-week/{source}": b'{"only":"fallback"}\n'}
        assert _lines(tree, source) == [b'{"only":"fallback"}\n']
