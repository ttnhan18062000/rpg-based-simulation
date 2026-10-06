"""Generated `.claude/agents/session-<role>.md` files (session-layer M1c)."""

from __future__ import annotations

import dataclasses
import shutil
from pathlib import Path

from tools.sessions import generate_agents as gen
from tools.sessions.roster import load_authority, load_roster
from tools.sessions.validate import validate

ROOT = Path(__file__).resolve().parents[2]


def _copy_inputs(dest: Path) -> Path:
    for rel in ("registries/session_roles.yaml", "registries/session_authority.yaml"):
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, dest / rel)
    shutil.copytree(ROOT / "docs/guidelines/session_roles", dest / "docs/guidelines/session_roles")
    for sub in ("tools", "docs", "src", "tests", "frontend", "agent-working", "registries"):
        (dest / sub).mkdir(exist_ok=True)
    return dest


def test_generation_is_deterministic():
    first, second = gen.generate(ROOT), gen.generate(ROOT)
    assert first == second
    assert {k: v.encode() for k, v in first.items()} == {k: v.encode() for k, v in second.items()}


def test_generates_one_file_per_seat_with_launcher_only_description():
    files = gen.generate(ROOT)
    roster = load_roster(ROOT)
    # 12 seats: the codebase domain (three unstaffed seats) was registered with the owner's approval.
    assert len(files) == len(roster.roles) == 12
    for role in roster.roles:
        content = files[gen.AGENT_DIR / f"session-{role.role}.md"]
        assert f"name: session-{role.role}\n" in content
        assert "Never spawn this as a subagent" in content
        assert f"You are `{role.role}`" in content


def test_committed_files_have_no_drift():
    assert gen.check_generated(ROOT) == []
    assert not [f for f in validate(ROOT) if f.rule == "generated-drift"]


def test_drift_check_fails_on_a_hand_edited_file_and_passes_when_regenerated(tmp_path):
    root = _copy_inputs(tmp_path)
    gen.write_generated(root)
    assert gen.check_generated(root) == []  # positive control: a fresh generation is clean
    target = root / gen.AGENT_DIR / "session-rpg-planner.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nhand edit\n", encoding="utf-8")
    problems = gen.check_generated(root)
    assert len(problems) == 1 and "session-rpg-planner.md" in problems[0]
    assert any(f.rule == "generated-drift" for f in validate(root))
    gen.write_generated(root)
    assert gen.check_generated(root) == []


def test_drift_check_reports_missing_and_stray_files(tmp_path):
    root = _copy_inputs(tmp_path)
    gen.write_generated(root)
    (root / gen.AGENT_DIR / "session-testing-planner.md").unlink()
    (root / gen.AGENT_DIR / "session-ghost.md").write_text("x", encoding="utf-8")
    problems = gen.check_generated(root)
    assert any("session-testing-planner.md" in p and "missing" in p for p in problems)
    assert any("session-ghost.md" in p and "no such seat" in p for p in problems)


def test_unrelated_agent_files_are_ignored_by_the_drift_check(tmp_path):
    root = _copy_inputs(tmp_path)
    gen.write_generated(root)
    (root / gen.AGENT_DIR / "planner.md").write_text("not a session agent", encoding="utf-8")
    assert gen.check_generated(root) == []


def test_tool_allowlist_is_emitted_and_read_only_roles_exclude_write_tools():
    roster = load_roster(ROOT)
    authority = load_authority(ROOT)
    role = dataclasses.replace(roster.role("testing-planner"), tools=("Read", "Glob", "Grep"))
    content = gen.render_agent_file(role, roster, authority, ROOT)
    tools_line = next(line for line in content.splitlines() if line.startswith("tools:"))
    assert tools_line == "tools: Read, Glob, Grep"
    assert not {"Bash", "Edit", "Write"} & set(tools_line.removeprefix("tools: ").split(", "))
    # positive control: a role with no allowlist inherits the session's tools (no `tools:` line)
    inherits = gen.render_agent_file(roster.role("testing-planner"), roster, authority, ROOT)
    assert "\ntools:" not in inherits


def test_every_role_with_an_allowlist_in_the_manifest_is_read_only():
    # M1c AC4: an allowlist in the manifest exists to make a role read-only (plan section 10).
    for role in load_roster(ROOT).roles:
        if role.tools is not None:
            assert not {"Bash", "Edit", "Write"} & set(role.tools), role.role


def test_generation_writes_only_under_the_agents_dir(tmp_path):
    root = _copy_inputs(tmp_path)
    before = {p.relative_to(root) for p in root.rglob("*") if p.is_file()}
    written = gen.write_generated(root)
    after = {p.relative_to(root) for p in root.rglob("*") if p.is_file()}
    assert after - before == set(written)
    assert all(p.parent == gen.AGENT_DIR for p in written)


def test_generated_agent_names_the_main_checkout_handover_location():
    # TCK-20261006-HANDOVER-NOTES-RESOLVE-FROM-MAIN-CHECKOUT: the gitignored notes are not in a seat's worktree
    text = (ROOT / ".claude" / "agents" / "session-agent-working-implementer.md").read_text()
    assert "main-checkout `.claude/handover/agent-working-implementer.md`" in text
