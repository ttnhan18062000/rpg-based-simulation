"""``done_checker_static`` finds a ticket in ``inprogress/``, the flat ``done/``, or a one-level ``done/<folder>/``.

A closed epic folder is moved to ``done/<folder>/`` (CLAUDE.md "After Work"), so an epic ticket never sits at the flat
``done/<id>.md`` path. ``_resolve_tier`` and ``_resolve_ticket_body_path`` used to look only at the flat locations, so a
nested epic ticket resolved to "standard" with no warning and then failed the standard-tier staging checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.gate_checks import done_checker_static as dcs

_EPIC = "---\nstatus: historical\nlayer: ai\nauthority: P1\naudience: agent\nticket_id: {tid}\nphase: done\ndate: 2026-10-03\ntags: []\n---\n\n# {tid}\n\n## Title\nx\n\n## Status\nDONE\n\n## Tier\n{tier}\n"


def _write(root: Path, rel: str, tid: str, tier: str = "epic") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_EPIC.format(tid=tid, tier=tier), encoding="utf-8")
    return path


@pytest.fixture
def tickets(tmp_path, monkeypatch) -> Path:
    monkeypatch.setattr(dcs, "TICKETS", tmp_path)
    return tmp_path


def test_a_nested_done_folder_epic_resolves_to_epic_not_standard(tickets, capsys):
    _write(tickets, "done/some-epic-folder/TCK-20261003-NESTED-EPIC.md", "TCK-20261003-NESTED-EPIC")
    assert dcs._resolve_tier("TCK-20261003-NESTED-EPIC", None) == "epic"
    assert capsys.readouterr().err == ""


def test_flat_done_and_inprogress_tickets_still_resolve(tickets):
    _write(tickets, "done/TCK-20261003-FLAT.md", "TCK-20261003-FLAT", "hotfix")
    _write(tickets, "inprogress/TCK-20261003-ACTIVE.md", "TCK-20261003-ACTIVE", "standard")
    assert dcs._resolve_tier("TCK-20261003-FLAT", None) == "hotfix"
    assert dcs._resolve_tier("TCK-20261003-ACTIVE", None) == "standard"


def test_an_explicit_tier_override_wins_without_a_lookup(tickets):
    assert dcs._resolve_tier("TCK-20261003-NOWHERE", "epic") == "epic"


def test_a_missing_ticket_falls_back_to_standard_and_says_so(tickets, capsys):
    assert dcs._resolve_tier("TCK-20261003-NOWHERE", None) == "standard"
    err = capsys.readouterr().err
    assert "NOTE" in err and "falls back to 'standard'" in err and "TCK-20261003-NOWHERE.md" in err


def test_an_unparseable_tier_falls_back_to_standard_and_says_so(tickets, capsys):
    path = _write(tickets, "done/TCK-20261003-BADTIER.md", "TCK-20261003-BADTIER", "not-a-tier")
    assert dcs._resolve_tier("TCK-20261003-BADTIER", None) == "standard"
    assert str(path) in capsys.readouterr().err


def test_body_path_finds_a_nested_done_ticket_and_check_ticket_finalized_agrees(tickets):
    path = _write(tickets, "done/some-epic-folder/TCK-20261003-NESTED-EPIC.md", "TCK-20261003-NESTED-EPIC")
    assert dcs._resolve_ticket_body_path("TCK-20261003-NESTED-EPIC") == path
    assert dcs._resolve_ticket_body_path("TCK-20261003-NESTED-EPIC").exists()
    status, _evidence = dcs.check_ticket_finalized("TCK-20261003-NESTED-EPIC")
    assert status == "PASS"


def test_body_path_for_a_missing_ticket_is_the_flat_done_path(tickets):
    assert dcs._resolve_ticket_body_path("TCK-20261003-NOWHERE") == tickets / "done" / "TCK-20261003-NOWHERE.md"


def test_the_lookup_goes_one_folder_deep_only(tickets):
    _write(tickets, "done/outer/inner/TCK-20261003-TOO-DEEP.md", "TCK-20261003-TOO-DEEP")
    assert dcs._find_ticket_file("TCK-20261003-TOO-DEEP") is None
