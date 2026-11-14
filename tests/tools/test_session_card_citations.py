"""Decision citations on session role cards (TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tools.sessions import generate_agents
from tools.sessions.card_citation_check import Finding, find_findings
from tools.sessions.card_citation_check import main as check_main
from tools.sessions.decisions import (
    DECISIONS_REL_PATH,
    TEMPLATE_DIR,
    card_text,
    covers,
    load_decisions,
    names_used,
    parse_cites,
    target_problem,
    unlisted_references,
)
from tools.validate_frontmatter import validate_file

ROOT = Path(__file__).resolve().parents[2]
VOCAB = load_decisions(ROOT)
CARD_SOURCES = sorted(p for kind in ("domains", "functions") for p in (ROOT / TEMPLATE_DIR / kind).glob("*.md"))


# ---- the real tree (blocking) -------------------------------------------------------------------------------

@pytest.mark.parametrize("path", CARD_SOURCES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_card_names_are_listed_under_cites_and_resolve(path):
    source = path.read_text(encoding="utf-8")
    cites = parse_cites(source)
    assert cites is not None, f"{path.name}: no `## Cites` section (use `- none` when the card names no decision)"
    used = names_used(card_text(source), VOCAB)
    assert used == set(cites), f"{path.name}: Card names {sorted(used)} but Cites lists {sorted(cites)}"
    for name, target in cites.items():
        assert name in VOCAB, f"{path.name}: `{name}` is not in {DECISIONS_REL_PATH}"
        assert target == VOCAB[name].target, f"{path.name}: {name} -> {target}, vocabulary says {VOCAB[name].target}"
    assert unlisted_references(card_text(source), VOCAB) == [], f"{path.name}: unlisted decision reference"


def test_every_vocabulary_target_exists_with_its_heading():
    problems = {d.name: target_problem(d.target, ROOT) for d in VOCAB.values()}
    assert {k: v for k, v in problems.items() if v} == {}


def test_real_tree_has_no_citation_findings():
    # AC4: measured once at the backfill; kept report-only elsewhere, so this only pins today's state
    assert find_findings(ROOT) == []


def test_validate_frontmatter_accepts_an_amends_key(tmp_path):
    doc = tmp_path / "docs" / "architecture" / "x.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("---\nstatus: active\nlayer: architecture\nauthority: P1\naudience: agent\namends: [docs/a.md#b]\n---\n# x\n")
    assert validate_file(doc) == []


# ---- unlisted references: negative control -------------------------------------------------------------------

def test_card_naming_an_unlisted_path_or_adr_token_is_flagged():
    assert unlisted_references("Follow docs/architecture/new_thing.md and made_up_adr.", VOCAB) == [
        "docs/architecture/new_thing.md",
        "made_up_adr",
    ]
    assert unlisted_references("Follow docs/architecture/distributed_workers_adr.md.", VOCAB) == []


def test_covers_rule():
    assert covers("a.md#x", "a.md#x")
    assert covers("a.md#x", "a.md")
    assert covers("a.md", "a.md#y")
    assert not covers("a.md#x", "a.md#y")
    assert not covers("a.md#x", "b.md#x")


# ---- the check on a miniature repo ----------------------------------------------------------------------------

def _doc(root: Path, rel: str, status: str = "active", amends: str | None = None, headings: str = "") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = f"---\nstatus: {status}\nlayer: architecture\nauthority: P1\naudience: agent\n"
    fm += (f"amends: {amends}\n" if amends is not None else "") + "---\n\n# T\n" + headings
    path.write_text(fm, encoding="utf-8")


def _repo(tmp_path: Path, cites: str, amends: str | None = "[docs/architecture/base.md#rule]", status: str = "active") -> Path:
    root = tmp_path / "repo"
    (root / "registries").mkdir(parents=True)
    for name in ("session_roles.yaml", "session_authority.yaml"):
        shutil.copy(ROOT / "registries" / name, root / "registries" / name)
    (root / DECISIONS_REL_PATH).write_text(
        "decisions:\n"
        "  base: {path: docs/architecture/base.md#rule}\n"
        "  newer: {path: docs/architecture/newer.md}\n",
        encoding="utf-8",
    )
    _doc(root, "docs/architecture/base.md", headings="\n## Rule\n")
    _doc(root, "docs/architecture/newer.md", status=status, amends=amends)
    card = root / TEMPLATE_DIR / "domains" / "platform.md"
    card.parent.mkdir(parents=True)
    card.write_text(f"# d\n\n## Card\nbase newer\n\n## Cites\n\n{cites}\n", encoding="utf-8")
    return root


def test_positive_amended_cite_without_the_amender_is_a_finding_with_seat_ids(tmp_path):
    root = _repo(tmp_path, "- base -> docs/architecture/base.md#rule")
    findings = find_findings(root)
    assert len(findings) == 1
    f = findings[0]
    assert (f.cited, f.amended_by, f.kind) == ("base", "docs/architecture/newer.md", "amended")
    assert "platform-planner" in f.seats and "platform-implementer" in f.seats
    assert "platform-planner" in f.render()


def test_negative_nothing_amended_gives_no_finding(tmp_path):
    root = _repo(tmp_path, "- base -> docs/architecture/base.md#rule", amends=None)
    assert find_findings(root) == []


def test_both_cited_gives_no_finding(tmp_path):
    root = _repo(tmp_path, "- base -> docs/architecture/base.md#rule\n- newer -> docs/architecture/newer.md")
    assert find_findings(root) == []


def test_amender_that_is_superseded_or_historical_is_ignored(tmp_path):
    for status in ("superseded", "historical"):
        root = _repo(tmp_path / status, "- base -> docs/architecture/base.md#rule", status=status)
        assert find_findings(root) == []


def test_different_section_of_the_same_doc_is_not_covered(tmp_path):
    root = _repo(tmp_path, "- base -> docs/architecture/base.md#rule", amends="[docs/architecture/base.md#other]")
    assert find_findings(root) == []


def test_amender_missing_from_the_vocabulary_is_reported_as_such(tmp_path):
    root = _repo(tmp_path, "- base -> docs/architecture/base.md#rule")
    _doc(root, "docs/architecture/stray.md", amends="[docs/architecture/base.md]")
    kinds = {f.amended_by: f.kind for f in find_findings(root)}
    assert kinds["docs/architecture/stray.md"] == "unlisted-amender"


def test_malformed_amends_is_reported_not_raised(tmp_path):
    root = _repo(tmp_path, "- base -> docs/architecture/base.md#rule", amends="just-a-string")
    kinds = [f.kind for f in find_findings(root)]
    assert kinds == ["malformed"]


def test_cli_is_report_only_and_prints_findings(tmp_path, capsys):
    root = _repo(tmp_path, "- base -> docs/architecture/base.md#rule")
    assert check_main(["--root", str(root)]) == 0
    out = capsys.readouterr().out
    assert "CITATION" in out and "1 citation finding(s)" in out


def test_long_seat_lists_are_cut_in_the_advisory_but_not_in_the_cli():
    f = Finding("c", "x", "d", tuple(f"s{i}" for i in range(7)))
    assert "(+3 more)" in f.render(4) and "s6" not in f.render(4)
    assert "s6" in f.render() and "more" not in f.render()


def test_generate_check_prints_the_advisory_only_with_findings(capsys, monkeypatch):
    monkeypatch.setattr(generate_agents, "check_generated", lambda root: [])
    monkeypatch.setattr(generate_agents, "find_findings", lambda root: [])
    assert generate_agents.main(["--check"]) == 0
    assert "ADVISORY" not in capsys.readouterr().out

    monkeypatch.setattr(generate_agents, "find_findings", lambda root: [Finding("c.md", "x", "d.md", ("a-planner",))])
    assert generate_agents.main(["--check"]) == 0  # exit code unchanged
    assert "ADVISORY card citation: c.md cites x, amended by d.md" in capsys.readouterr().out


# ---- docs state the rule --------------------------------------------------------------------------------------

def test_docs_state_the_delivery_rule_and_the_reset_step():
    delivery = (ROOT / "docs/guides/delivery_process.md").read_text(encoding="utf-8")
    assert "Decisions named on role cards" in delivery and "lists the role cards it affects in its body" in delivery
    reset = (ROOT / "docs/guides/agent_session_reset_boundaries.md").read_text(encoding="utf-8")
    assert "After a card-changing merge" in reset and "relaunches or clears the seats" in reset
    plan = (ROOT / "docs/plans/agent_infrastructure/session_layer_working_process.md").read_text(encoding="utf-8")
    assert "Decisions named on role cards" in plan
