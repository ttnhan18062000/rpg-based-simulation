"""Session owner lookup (session-layer M3a): path in, seat out, from the manifest only."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from tools.sessions import route as route_mod
from tools.sessions.roster import Domain, OwnershipSplit, Role, Roster, RosterError, load_roster
from tools.sessions.route import OWNED, SPLIT, UNOWNED, main, route

REAL_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def real_roster() -> Roster:
    return load_roster(REAL_ROOT)


def _role(role: str, domain: str, function: str) -> Role:
    return Role(role, domain, function, role, None, "staffed", None, (), (), (), ("user",), (), None, domain, 1, f".claude/handover/{role}.md", ())


def _fixture_roster() -> Roster:
    domains = (
        Domain("a", ("src/**", "src/core/**", "docs/*.md"), ("src/core/secret.py",), (("web/**", "b-planner"),)),
        Domain("b", ("src/core/deep/**", "web/**"), (), ()),
    )
    roles = tuple(_role(f"{d}-{f}", d, f) for d in ("a", "b") for f in ("designer", "planner", "implementer"))
    return Roster(domains=domains, splits=(OwnershipSplit(("shared/**",), ("a", "b"), "both"),), roles=roles, worktrees=())


@pytest.mark.parametrize(
    ("path", "status", "domains", "seats"),
    [
        ("registries/mechanisms.yaml", OWNED, ("rpg",), ("rpg-planner",)),
        ("tools/mechanism_registry/generate_mechanism_registry_view.py", OWNED, ("agent-working",), ("agent-working-planner",)),
        ("tests/architecture/test_x.py", SPLIT, ("rpg", "testing"), ("rpg-planner", "testing-planner")),
        ("tools/sessions/route.py", OWNED, ("agent-working",), ("agent-working-planner",)),
        ("src/core/registries.py", OWNED, ("rpg",), ("rpg-planner",)),
        ("totally/unowned/file.txt", UNOWNED, (), ()),
    ],
)
def test_real_manifest_cases(real_roster: Roster, path: str, status: str, domains: tuple[str, ...], seats: tuple[str, ...]) -> None:
    result = route(path, real_roster)
    assert (result.status, result.domains, result.seats) == (status, domains, seats)


def test_split_carries_reason(real_roster: Roster) -> None:
    assert "architecture" in route("tests/architecture/x.py", real_roster).reason


def test_src_from_agent_working_side_routes_to_rpg_planner(real_roster: Roster) -> None:
    result = route("src/ai/goals/x.py", real_roster, from_domain="agent-working")
    assert result.seats == ("rpg-planner",)
    assert result.domains == ("rpg",)


def test_from_domain_does_not_override_its_own_paths(real_roster: Roster) -> None:
    assert route("tools/sessions/x.py", real_roster, from_domain="agent-working").seats == ("agent-working-planner",)


def test_unknown_from_domain_is_an_error(real_roster: Roster) -> None:
    with pytest.raises(RosterError, match="unknown domain"):
        route("src/x.py", real_roster, from_domain="nope")


def test_longest_glob_wins_across_domains() -> None:
    roster = _fixture_roster()
    assert route("src/core/deep/x.py", roster).domains == ("b",)  # b's glob is longer than a's src/core/**
    assert route("src/core/other.py", roster).domains == ("a",)


def test_owns_not_excludes_the_domain() -> None:
    result = route("src/core/secret.py", _fixture_roster())
    assert result.status == UNOWNED  # a excludes it, b does not claim it


def test_split_returns_both_domains() -> None:
    result = route("shared/x.txt", _fixture_roster())
    assert (result.status, result.domains, result.seats) == (SPLIT, ("a", "b"), ("a-planner", "b-planner"))


def test_single_star_stays_in_one_segment() -> None:
    roster = _fixture_roster()
    assert route("docs/readme.md", roster).domains == ("a",)
    assert route("docs/sub/readme.md", roster).status == UNOWNED


def test_domain_route_applies_only_when_not_owned() -> None:
    roster = _fixture_roster()
    assert route("web/x.js", roster, from_domain="a").seats == ("b-planner",)


def test_output_names_a_seat_never_liveness(real_roster: Roster, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["src/x.py", "--root", str(REAL_ROOT)]) == 0
    out = capsys.readouterr().out
    assert "seat: rpg-planner" in out
    assert "not computed here" in out


def test_route_module_imports_nothing_that_lists_sessions() -> None:
    tree = ast.parse(Path(route_mod.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert not {m for m in imported if m.startswith(("tools.sessions.state", "tools.sessions.launch", "subprocess", "socket"))}


def _snapshot(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for sub in ("registries", "tools/sessions")
        for p in sorted((root / sub).rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def test_route_is_read_only() -> None:
    before = _snapshot(REAL_ROOT)
    route("src/x.py", load_roster(REAL_ROOT))
    main(["tools/sessions/route.py", "--from", "rpg", "--root", str(REAL_ROOT)])
    assert _snapshot(REAL_ROOT) == before
