"""The lead's status message classes and board skeleton stay consistent (TCK-20261011-LEAD-STATUS-MESSAGES-AND-BOARD)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs/guides/cross_session_messages.md"
PLAN = ROOT / "docs/plans/agent_infrastructure/session_layer_working_process.md"
BOARD = ROOT / "agent-working/lead/board.md"


def _rows(path: Path, cls: str) -> list[str]:
    return [ln for ln in path.read_text().splitlines() if ln.startswith(f"| `{cls}`")]


def test_guide_and_plan_list_both_status_classes_with_the_same_sender_and_receiver():
    for cls in ("status-request", "status-report"):
        guide, plan = _rows(GUIDE, cls), _rows(PLAN, cls)
        assert len(guide) == 1 and len(plan) == 1, cls
        g = [c.strip() for c in guide[0].split("|")[2:4]]
        p = [c.strip() for c in plan[0].split("|")[2:4]]
        assert g == p, (cls, g, p)


def test_status_request_never_authorizes_work():
    text = _rows(GUIDE, "status-request")[0]
    assert "never authorizes work" in text


def test_board_has_the_seven_columns_and_no_rows():
    lines = [ln for ln in BOARD.read_text().splitlines() if ln.startswith("|")]
    assert len(lines) == 2, "header and separator only; the lead fills rows"
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    assert len(header) == 7
    assert header[0] == "epic or batch" and header[-1].startswith("owner decision needed")
