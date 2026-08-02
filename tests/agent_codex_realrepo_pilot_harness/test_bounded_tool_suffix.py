from __future__ import annotations

import json

import pytest

from tools.agent_codex_realrepo_pilot_harness.proofs import assert_bounded_tool_suffix


_IDENTITY = {
    "execution_id": "codex-TCK-20260801-MONITORING-WRITER-STATUS-STALE-1-deadbeef",
    "ticket_id": "TCK-20260801-MONITORING-WRITER-STATUS-STALE",
    "provider": "codex",
    "run_id": "TCK-20260801-MONITORING-WRITER-STATUS-STALE",
}


def _line(seq: int, ts: str, **overrides: object) -> bytes:
    return (json.dumps({**_IDENTITY, "seq": seq, "ts": ts, **overrides}, separators=(",", ":")) + "\n").encode()


def test_bounded_tool_suffix_accepts_zero_or_contiguous_identity_bound_rows():
    before = [b'{"legacy":true}\n']
    assert_bounded_tool_suffix(before, before, _IDENTITY, max_tool_calls=2,
                               run_start_iso="2026-08-02T00:00:00Z", run_end_iso="2026-08-02T00:01:00Z")
    assert_bounded_tool_suffix(
        before,
        before + [_line(1, "2026-08-02T00:00:01Z"), _line(2, "2026-08-02T00:00:02Z")],
        _IDENTITY,
        max_tool_calls=2,
        run_start_iso="2026-08-02T00:00:00Z",
        run_end_iso="2026-08-02T00:01:00Z",
    )


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([_line(1, "2026-08-02T00:00:01Z", provider="other")], "provider"),
        ([_line(2, "2026-08-02T00:00:01Z")], "seq"),
        ([_line(1, "2026-08-02T00:00:01Z"), _line(3, "2026-08-02T00:00:02Z")], "seq"),
        ([_line(1, "2026-08-01T23:59:59Z")], "timestamp"),
        ([_line(1, "2026-08-02T00:00:01Z"), _line(2, "2026-08-02T00:00:02Z")], "count"),
    ],
)
def test_bounded_tool_suffix_rejects_unbound_or_out_of_window_rows(rows, message):
    with pytest.raises(ValueError, match=message):
        assert_bounded_tool_suffix(
            [], rows, _IDENTITY, max_tool_calls=1 if message == "count" else 3,
            run_start_iso="2026-08-02T00:00:00Z",
            run_end_iso="2026-08-02T00:01:00Z",
        )
