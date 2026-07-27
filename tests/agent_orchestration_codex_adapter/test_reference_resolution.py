"""One-directional reference-resolution test for generated Codex skill packages.

For every generated `.agents/skills/<id>/SKILL.md` body, extracts same-skill relative file
references (markdown-link syntax and `@filename` mentions) and asserts each one resolves to a
real file inside that skill's generated package. Deliberately one-directional: it does NOT
assert the converse ("every shipped companion_assets file is referenced by name in the body") —
falsified by real data for `api-design-principles` (4 of 5 companion files unreferenced) and
`brainstorming` (5 of 7, the whole `scripts/` dir, unreferenced). See investigation.md §5.

Detection is scoped to avoid two known non-companion-asset false-positive sources:
- `backend-testing/SKILL.md` has two pre-existing dead cross-skill markdown links
  (`../api-design/SKILL.md`, `../authentication/SKILL.md`) — excluded via the `../`-traversal
  filter, since this ticket must not touch `.claude/skills/` (read-only source).
- `@example.com` / `@pytest.fixture` / `@pytest.mark.*` / `@domain.co.uk` mentions in
  `backend-testing`, `python-performance-optimization`, `python-testing-patterns` — excluded via
  the companion-file extension allowlist, since none of these end in `.md/.py/.js/.cjs/.sh/.html`.

Both regexes are additionally run only outside fenced code blocks, so decorator/example noise
inside code samples cannot match either.
"""
from __future__ import annotations

import re
from pathlib import Path

from tools.agent_orchestration_codex_adapter.generator import render_codex_guidance
from tools.agent_orchestration.loader import load_contract

ROOT = Path(__file__).parent.parent.parent

_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_AT_MENTION_RE = re.compile(r"@([\w./-]+\.(?:md|py|js|cjs|sh|html))\b")


def _extract_references(body: str) -> list[str]:
    stripped = _FENCE_RE.sub("", body)
    candidates = _MARKDOWN_LINK_RE.findall(stripped) + _AT_MENTION_RE.findall(stripped)
    return [
        ref for ref in candidates
        if not ref.startswith(("http://", "https://", "#")) and "../" not in ref
    ]


def test_reference_resolution_all_sixteen_skills(tmp_path):
    render_codex_guidance(ROOT, tmp_path, allow_outside_contract=True)

    failures = []
    for skill in load_contract(ROOT).skills["skills"]:
        skill_dir = tmp_path / ".agents" / "skills" / skill["id"]
        body = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        for ref in _extract_references(body):
            if not (skill_dir / ref).is_file():
                failures.append(f"{skill['id']}: unresolved reference {ref!r}")

    assert not failures, "\n".join(failures)
