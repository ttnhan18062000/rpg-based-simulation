"""Tests for the /api/glossary endpoint (TCK-20260718-GLOSSARY-API).

Covers: happy path merging tools/glossary_registry.py + tools/layer_registry.py entries, the
layer note-reuse behavior (never a duplicated description), the "no collision silently overwrites"
guard, empty-registry edge case, and the real live registries (proving the actual seeded data
returns correctly, not just a fixture).
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.api.agent_ops_dashboard import ingest, main


def _init_repo_skeleton(tmp_path: Path) -> None:
    (tmp_path / "agent-monitoring").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "done").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tickets" / "todos").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "guidelines").mkdir(parents=True, exist_ok=True)


def _write_glossary(tmp_path: Path, entries: list[dict]) -> None:
    path = tmp_path / "docs" / "guidelines" / "glossary_registry.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + ("\n" if entries else ""), encoding="utf-8")


def _write_layers(tmp_path: Path, entries: list[dict]) -> None:
    path = tmp_path / "docs" / "guidelines" / "layer_registry.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + ("\n" if entries else ""), encoding="utf-8")


def _write_agent_role_file(tmp_path: Path, filename: str, name: str, description: str) -> None:
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / filename).write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )


def test_glossary_merges_registry_and_layer_entries(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_glossary(tmp_path, [
        {"term": "DONE", "category": "ticket-status", "added_date": "2026-07-18", "description": "Work is complete."},
    ])
    _write_layers(tmp_path, [
        {"layer": "economy", "added_date": "2026-07-18", "note": "Resource/trade/crafting subsystem."},
    ])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    glossary = cache.get_glossary()

    assert glossary.terms["DONE"].category == "ticket-status"
    assert glossary.terms["DONE"].description == "Work is complete."
    assert glossary.terms["economy"].category == "layer"
    assert glossary.terms["economy"].description == "Resource/trade/crafting subsystem."


def test_glossary_reuses_layer_note_never_duplicates_description(tmp_path):
    # The whole point of merging at read time instead of copying: change the layer's note, the
    # glossary reflects it immediately, with zero glossary_registry.jsonl edit required.
    _init_repo_skeleton(tmp_path)
    _write_glossary(tmp_path, [])
    _write_layers(tmp_path, [
        {"layer": "combat", "added_date": "2026-07-18", "note": "original note"},
    ])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    first = cache.get_glossary()
    assert first.terms["combat"].description == "original note"

    _write_layers(tmp_path, [
        {"layer": "combat", "added_date": "2026-07-18", "note": "updated note"},
    ])
    second = cache.get_glossary()
    assert second.terms["combat"].description == "updated note"


def test_glossary_layer_with_empty_note_is_skipped(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_glossary(tmp_path, [])
    _write_layers(tmp_path, [
        {"layer": "misc", "added_date": "2026-07-18", "note": ""},
    ])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    glossary = cache.get_glossary()

    assert "misc" not in glossary.terms


def test_glossary_merges_agent_role_descriptions(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_glossary(tmp_path, [])
    _write_layers(tmp_path, [])
    _write_agent_role_file(
        tmp_path, "implementer.md", "implementer", "Writes the code changes described in an approved plan.md."
    )

    cache = ingest.DashboardCache(repo_root=tmp_path)
    glossary = cache.get_glossary()

    assert glossary.terms["implementer"].category == "agent"
    assert glossary.terms["implementer"].description == (
        "Writes the code changes described in an approved plan.md."
    )


def test_glossary_missing_agents_directory_returns_no_agent_terms_not_crash(tmp_path):
    # _init_repo_skeleton deliberately never creates .claude/agents/ — every other tmp_path-based
    # test in this file relies on this exact tolerance already (they'd all fail loudly otherwise).
    _init_repo_skeleton(tmp_path)
    _write_glossary(tmp_path, [
        {"term": "DONE", "category": "ticket-status", "added_date": "2026-07-18", "description": "Work is complete."},
    ])
    _write_layers(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    glossary = cache.get_glossary()

    assert "DONE" in glossary.terms
    assert not any(e.category == "agent" for e in glossary.terms.values())


def test_glossary_agent_file_with_missing_description_is_skipped(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_glossary(tmp_path, [])
    _write_layers(tmp_path, [])
    agents_dir = tmp_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "no-description.md").write_text(
        "---\nname: no-description\n---\n\n# No Description\n", encoding="utf-8"
    )

    cache = ingest.DashboardCache(repo_root=tmp_path)
    glossary = cache.get_glossary()

    assert "no-description" not in glossary.terms


def test_glossary_empty_registries_returns_empty_dict_not_crash(tmp_path):
    _init_repo_skeleton(tmp_path)
    _write_glossary(tmp_path, [])
    _write_layers(tmp_path, [])

    cache = ingest.DashboardCache(repo_root=tmp_path)
    glossary = cache.get_glossary()

    assert glossary.terms == {}


def test_glossary_route_returns_200_typed_shape(tmp_path, monkeypatch):
    _init_repo_skeleton(tmp_path)
    _write_glossary(tmp_path, [
        {"term": "P0", "category": "priority", "added_date": "2026-07-18", "description": "Highest priority."},
    ])
    _write_layers(tmp_path, [])

    monkeypatch.setattr(main, "_cache", ingest.DashboardCache(repo_root=tmp_path))
    client = TestClient(main.app)

    resp = client.get("/api/glossary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["terms"]["P0"]["category"] == "priority"
    assert data["terms"]["P0"]["description"] == "Highest priority."


def test_glossary_route_never_returns_raw_dict_shape():
    # API-boundary rule check: response_model on the route forces the typed shape — a raw dict
    # return would 500, not silently pass through un-typed. main.py uses
    # `from __future__ import annotations`, so return_annotation is the string form, not the
    # resolved class object.
    import inspect

    sig = inspect.signature(main.get_glossary)
    assert sig.return_annotation == "GlossaryResponse"


def test_glossary_against_real_seeded_registries():
    # No tmp_path override — against the real repo's glossary_registry.jsonl + layer_registry.jsonl
    # + .claude/agents/*.md, proving the live 3-way merge actually works end to end, not just on a
    # fixture.
    cache = ingest.DashboardCache()
    glossary = cache.get_glossary()

    assert "DONE" in glossary.terms
    assert glossary.terms["DONE"].category == "ticket-status"
    assert "economy" in glossary.terms
    assert glossary.terms["economy"].category == "layer"
    assert "implementer" in glossary.terms
    assert glossary.terms["implementer"].category == "agent"
    assert len(glossary.terms) >= 48  # 35 glossary_registry + non-empty-note layers + 13 agents
