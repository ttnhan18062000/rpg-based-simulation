"""Session role manifest: loader and validator (session-layer M1a).

Each rule gets a fixture that must trip it, and the unmodified fixture must pass, so a rule that
never fires is caught by its own positive control. The real registry files are also validated here;
that is how CI runs the validator (tests/tools is a CI lane).
"""

from __future__ import annotations

import copy
import dataclasses
from pathlib import Path

import pytest
import yaml

from tools.agent_working_paths import TICKETS
from tools.sessions import roster as roster_mod
from tools.sessions.roster import RosterError, load_authority, load_roster
from tools.sessions.validate import complexity_report, main, validate

REAL_ROOT = Path(__file__).resolve().parents[2]

BASE_ROLES = {
    "version": 1,
    "domains": {
        "d1": {"owns": ["d1/**"], "owns_not": [], "routes": {"d2/**": "d2-implementer"}},
        "d2": {"owns": ["d2/**"], "owns_not": [], "routes": {}},
    },
    "ownership_splits": [],
    "roles": [
        {
            "role": f"{d}-{f}",
            "identity": {"domain": d, "function": f, "session_name": f"{d}-{f}", "legacy_session_name": None, "seat_status": "staffed"},
            "responsibility": {"accepts_dispatch_from": ["user"]},
            "capability": {"may_write": []},
            "placement": {"worktree": d if f == "implementer" else f"{d}-{f}", "max_sessions": 1},
            "handover": f".claude/handover/{d}-{f}.md",
        }
        for d in ("d1", "d2")
        for f in ("designer", "planner", "implementer")
    ],
    "worktrees": {
        "d1": {"writer": "d1-implementer"},
        "d2": {"writer": "d2-implementer"},
        **{f"{d}-{f}": {"writer": f"{d}-{f}"} for d in ("d1", "d2") for f in ("designer", "planner")},
    },
}

BASE_AUTHORITY = {
    "governing_file": True,
    "version": 1,
    "function_defaults": {f: {"forbidden": [], "needs_user": ["merge"]} for f in ("designer", "planner", "implementer")},
    "authority": {},
}


def _write(root: Path, roles: dict, authority: dict) -> None:
    (root / "registries").mkdir(parents=True, exist_ok=True)
    (root / "registries/session_roles.yaml").write_text(yaml.safe_dump(roles, sort_keys=False), encoding="utf-8")
    (root / "registries/session_authority.yaml").write_text(yaml.safe_dump(authority, sort_keys=False), encoding="utf-8")
    for d in ("d1", "d2"):
        (root / d).mkdir(exist_ok=True)
        (root / d / "file.txt").write_text("x", encoding="utf-8")


@pytest.fixture
def fixture_root(tmp_path: Path) -> Path:
    _write(tmp_path, BASE_ROLES, BASE_AUTHORITY)
    return tmp_path


def _mutated(root: Path, mutate, authority=None) -> list:
    roles = copy.deepcopy(BASE_ROLES)
    mutate(roles)
    _write(root, roles, authority if authority is not None else BASE_AUTHORITY)
    return validate(root)


def _role(roles: dict, role_id: str) -> dict:
    return next(r for r in roles["roles"] if r["role"] == role_id)


def _rules(findings) -> set[str]:
    return {f.rule for f in findings}


def test_positive_control_unmodified_fixture_passes(fixture_root):
    assert validate(fixture_root) == []


def test_real_registry_validates():
    assert validate(REAL_ROOT) == []


def test_real_registry_has_sixteen_seats_three_unstaffed():
    # Changed from twelve seats / five unstaffed: on the owner's request of 2026-10-09
    # (TCK-20261009-REGISTER-OTHER-HOST-SEATS) the asset and perf planner/implementer seats were registered and the
    # codebase planner/implementer seats marked staffed; those sessions run on the other host. Asset and perf have
    # no designer seat (their planners take dispatch from the user).
    roster = load_roster(REAL_ROOT)
    assert len(roster.roles) == 16
    assert {r.role for r in roster.roles if r.seat_status == "unstaffed"} == {
        "agent-working-planner", "testing-designer", "codebase-designer",
    }
    assert {(r.domain, r.function) for r in roster.roles} == {
        (d, f) for d in ("rpg", "agent-working", "testing", "codebase") for f in ("designer", "planner", "implementer")
    } | {(d, f) for d in ("asset", "perf") for f in ("planner", "implementer")}


def test_glob_matches_nothing(fixture_root):
    findings = _mutated(fixture_root, lambda r: r["domains"]["d1"]["owns"].append("d1/missing/**"))
    assert "glob-matches-nothing" in _rules(findings)


def test_overlapping_ownership_without_split_and_allowed_with_split(fixture_root):
    findings = _mutated(fixture_root, lambda r: r["domains"]["d2"]["owns"].append("d1/**"))
    assert "overlapping-ownership" in _rules(findings)

    def with_split(r):
        r["domains"]["d2"]["owns"].append("d1/**")
        r["ownership_splits"].append({"paths": ["d1/**"], "domains": ["d1", "d2"], "reason": "test"})

    assert "overlapping-ownership" not in _rules(_mutated(fixture_root, with_split))


def test_missing_handover(fixture_root):
    findings = _mutated(fixture_root, lambda r: _role(r, "d1-designer").update(handover=""))
    assert "missing-handover" in _rules(findings)
    findings = _mutated(fixture_root, lambda r: _role(r, "d1-designer").update(handover="notes/elsewhere.md"))
    assert "missing-handover" in _rules(findings)


def test_unknown_route_target(fixture_root):
    findings = _mutated(fixture_root, lambda r: r["domains"]["d1"]["routes"].update({"x/**": "nobody"}))
    assert "unknown-route-target" in _rules(findings)
    findings = _mutated(fixture_root, lambda r: _role(r, "d1-planner")["responsibility"].update(accepts_dispatch_from=["ghost"]))
    assert "unknown-route-target" in _rules(findings)


def test_duplicate_session_name(fixture_root):
    findings = _mutated(fixture_root, lambda r: _role(r, "d1-planner")["identity"].update(session_name="d1-designer"))
    assert "duplicate-session-name" in _rules(findings)


def test_worktree_with_no_writer(fixture_root):
    findings = _mutated(fixture_root, lambda r: r["worktrees"].update(d1={}))
    assert "worktree-writer" in _rules(findings)


def test_role_in_undeclared_worktree(fixture_root):
    findings = _mutated(fixture_root, lambda r: _role(r, "d1-designer")["placement"].update(worktree="nowhere"))
    assert "worktree-writer" in _rules(findings)


def test_worktree_two_writers_is_unrepresentable_but_a_list_is_rejected(fixture_root):
    # `writer` holds one role id; a list (two writers) must not pass as valid.
    findings = _mutated(fixture_root, lambda r: r["worktrees"].update(d1={"writer": ["d1-implementer", "d1-planner"]}))
    assert findings, "a list of writers must be reported"


def test_a_designer_or_planner_may_be_a_worktrees_writer(fixture_root):
    assert _mutated(fixture_root, lambda r: None) == []  # d1-designer writes d1-designer, no implementer-only rule


def test_worktree_hosting_a_second_role_is_reported(fixture_root):
    findings = _mutated(fixture_root, lambda r: _role(r, "d1-planner")["placement"].update(worktree="d1"))
    assert "worktree-shared" in _rules(findings)


def test_writer_placed_elsewhere_is_reported(fixture_root):
    findings = _mutated(fixture_root, lambda r: r["worktrees"].update(d1={"writer": "d1-planner"}))
    assert "worktree-writer" in _rules(findings)


def test_real_manifest_gives_every_designer_and_planner_its_own_worktree():
    roster = load_roster(REAL_ROOT)
    for r in roster.roles:
        wt = next(w for w in roster.worktrees if w.name == r.worktree)
        assert wt.writer == r.role
        assert (r.worktree == r.role) == (r.function != "implementer")


def test_unstaffed_seat_needs_named_holder(fixture_root):
    def unstaff(r):
        _role(r, "d1-planner")["identity"]["seat_status"] = "unstaffed"

    assert "bad-field" in _rules(_mutated(fixture_root, unstaff))

    def unstaff_with_holder(r):
        _role(r, "d1-planner")["identity"].update(seat_status="unstaffed", interim_holder="d1-designer")

    assert _mutated(fixture_root, unstaff_with_holder) == []


def test_bad_function_and_status(fixture_root):
    findings = _mutated(fixture_root, lambda r: _role(r, "d1-planner")["identity"].update(function="wizard", seat_status="maybe"))
    assert [f.rule for f in findings].count("bad-field") >= 2


def test_stale_ticket_citation_reported(fixture_root):
    def cite(r):
        r["domains"]["d1"]["owns_not"].append("TCK-20200101-NO-SUCH-TICKET")

    findings = _mutated(fixture_root, cite)
    assert "stale-citation" in _rules(findings)
    tickets = fixture_root / TICKETS / "done"
    tickets.mkdir(parents=True)
    (tickets / "TCK-20200101-NO-SUCH-TICKET.md").write_text("x", encoding="utf-8")
    assert "stale-citation" not in _rules(validate(fixture_root))


def test_authority_must_be_governing_and_cover_every_function(fixture_root):
    not_governing = {**BASE_AUTHORITY, "governing_file": False}
    assert "authority-not-governing" in _rules(_mutated(fixture_root, lambda r: None, authority=not_governing))
    missing = copy.deepcopy(BASE_AUTHORITY)
    del missing["function_defaults"]["planner"]
    assert "authority-missing-default" in _rules(_mutated(fixture_root, lambda r: None, authority=missing))
    ghost = copy.deepcopy(BASE_AUTHORITY)
    ghost["authority"] = {"ghost-role": {"grants": []}}
    assert "authority-unknown-role" in _rules(_mutated(fixture_root, lambda r: None, authority=ghost))
    undated = copy.deepcopy(BASE_AUTHORITY)
    undated["authority"] = {"d1-implementer": {"grants": [{"action": ["push"], "scope": "s", "date": "2026-10-04", "quote": "", "source": "u"}]}}
    assert "authority-grant-undated" in _rules(_mutated(fixture_root, lambda r: None, authority=undated))


def test_real_authority_file_is_marked_governing():
    authority = load_authority(REAL_ROOT)
    assert authority.governing_file is True
    header = (REAL_ROOT / "registries/session_authority.yaml").read_text(encoding="utf-8").splitlines()[0]
    assert "GOVERNING FILE" in header
    assert authority.grants_for("agent-working-implementer"), "the dated push grant must be recorded with its quote"
    assert all(g.quote and g.date for _, gs in authority.grants for g in gs)


def test_complexity_report_does_not_change_exit_code(fixture_root, capsys):
    def many_overrides(r):
        _role(r, "d1-designer")["responsibility"].update(owns=["d1/**"], owns_not=[], routes={"d2/**": "d2-implementer"})

    _mutated(fixture_root, many_overrides)
    report = complexity_report(load_roster(fixture_root))
    assert report["d1-designer"]["overrides"] == 3
    assert main(["--root", str(fixture_root)]) == 0
    assert "complexity (report only)" in capsys.readouterr().out


def test_cli_exit_code_is_one_on_finding(fixture_root, capsys):
    _mutated(fixture_root, lambda r: r["worktrees"].update(d1={}))
    assert main(["--root", str(fixture_root)]) == 1
    assert "[worktree-writer]" in capsys.readouterr().out


def test_malformed_file_raises_roster_error_with_path(tmp_path):
    (tmp_path / "registries").mkdir()
    (tmp_path / "registries/session_roles.yaml").write_text("- not a mapping\n", encoding="utf-8")
    with pytest.raises(RosterError, match="session_roles.yaml"):
        load_roster(tmp_path)


def test_loader_returns_typed_records_never_raw_dicts():
    roster = load_roster(REAL_ROOT)
    authority = load_authority(REAL_ROOT)

    def walk(value):
        assert not isinstance(value, (dict, list, set)), f"raw container leaked: {type(value)}"
        if dataclasses.is_dataclass(value):
            assert value.__dataclass_params__.frozen
            for f in dataclasses.fields(value):
                walk(getattr(value, f.name))
        elif isinstance(value, tuple):
            for item in value:
                walk(item)

    walk(roster)
    walk(authority)


def test_loading_and_validating_write_nothing(fixture_root):
    before = {p: p.read_bytes() for p in fixture_root.rglob("*") if p.is_file()}
    load_roster(fixture_root)
    load_authority(fixture_root)
    validate(fixture_root)
    after = {p: p.read_bytes() for p in fixture_root.rglob("*") if p.is_file()}
    assert before == after


def test_loader_module_has_no_write_calls():
    source = Path(roster_mod.__file__).read_text(encoding="utf-8")
    for needle in (".write_text", ".write_bytes", "open(", "unlink", "mkdir", "rename"):
        assert needle not in source, needle


def test_schema_stores_no_liveness_and_does_not_key_on_agent_type():
    # M0 q: liveness is derivable (pid in /proc), so it is not stored. M0 o: agent_type is absent on
    # SessionStart(resume), so resolution cannot depend on it alone: it is not a manifest field.
    text = (REAL_ROOT / "registries/session_roles.yaml").read_text(encoding="utf-8")
    for key in ("pid:", "process_id", "live:", "alive", "state:", "holder_session", "agent_type"):
        assert key not in text, key
    fields = {f.name for f in dataclasses.fields(roster_mod.Role)}
    assert not fields & {"pid", "process_id", "live", "state", "agent_type"}
