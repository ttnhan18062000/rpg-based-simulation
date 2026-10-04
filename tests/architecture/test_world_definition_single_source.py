"""Architecture guards for the one-`world_id`-one-definition law.

`docs/architecture/world_repository_layout.md` §1 makes `data/worlds/<world_id>/` the sole
authoritative definition of a `world_id`, and `resolved/world.resolved.yaml` a generated
projection that must equal a fresh resolve. Neither half is enforceable by
`WorldValidator`: whether a *second* definition of the same `world_id` exists elsewhere in the
repository is unknowable to a validator handed one spec, and the projection check compares two
on-disk artifacts. They are repository-layout laws, enforced here.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from src.worldassembly.resolve_io import load_composition_spec, resolve_composition
from src.worldbuilding.repository import WorldRepository

# The walk is bounded to the repository's content roots and never reaches `docs/`: at least a
# dozen files under `docs/` mention `worldcomposition` in prose, including the ADR itself, so an
# unbounded text-shaped walk reports them as offenders.
DATA_ROOTS = ("data", "content")
WORLDS_ROOT = Path("data/worlds")


def _is_composition(data: object) -> bool:
    return isinstance(data, dict) and "worldcomposition" in str(data.get("schema_version", ""))


def _composition_files() -> list[tuple[Path, dict]]:
    """Every file under the content roots whose PARSED `schema_version` is a composition schema."""
    found: list[tuple[Path, dict]] = []
    for root in DATA_ROOTS:
        base = Path(root)
        if not base.is_dir():
            continue
        candidates = sorted(list(base.rglob("*.yaml")) + list(base.rglob("*.yml")))
        for path in candidates:
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if _is_composition(data):
                found.append((path, data))
    return found


def _authoritative_path_for(path: Path) -> bool:
    return path.name == "world.yaml" and path.parent.parent == WORLDS_ROOT


def test_world_id_resolves_to_exactly_one_definition():
    offenders = [str(path) for path, _ in _composition_files() if not _authoritative_path_for(path)]
    assert not offenders, (
        "World composition definitions found outside data/worlds/<world_id>/world.yaml — "
        "data/worlds/<world_id>/ is the sole authoritative definition of a world_id "
        "(docs/architecture/world_repository_layout.md §1):\n  " + "\n  ".join(offenders)
    )


def test_no_source_outside_data_worlds_defines_a_known_world_id():
    known = set(WorldRepository(WORLDS_ROOT).list_worlds())
    assert known, "No worlds indexed under data/worlds/ — the guard would be vacuous."

    offenders = []
    for path, data in _composition_files():
        if _authoritative_path_for(path):
            continue
        world_id = data.get("world_id")
        if world_id in known:
            offenders.append(f"{world_id} redefined at {path}")
    assert not offenders, (
        "These world_ids already have an authoritative definition under data/worlds/ and are "
        "defined a second time elsewhere:\n  " + "\n  ".join(offenders)
    )


def test_committed_resolved_projection_equals_a_fresh_resolve():
    """The committed projection must equal what the resolver produces from today's inputs.

    Full equality against a fresh resolve is the check. `content_fingerprint` is computed from
    the resolver's *inputs*, so it detects a stale snapshot but cannot detect a hand-edited
    `world.resolved.yaml` whose recorded fingerprint still matches — and "never hand-edited" is
    half the law being enforced.
    """
    repo = WorldRepository(WORLDS_ROOT)
    world_ids = repo.list_worlds()
    assert world_ids, "No worlds indexed under data/worlds/ — the guard would be vacuous."

    checked = 0
    failures = []
    for world_id in world_ids:
        source = WORLDS_ROOT / world_id / "world.yaml"
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
        if not _is_composition(raw):
            continue
        checked += 1

        committed = WORLDS_ROOT / world_id / "resolved" / "world.resolved.yaml"
        if not committed.is_file():
            failures.append(f"{world_id}: no committed resolved/world.resolved.yaml")
            continue

        _, fresh_yaml = resolve_composition(load_composition_spec(source))
        if committed.read_text(encoding="utf-8") != fresh_yaml:
            failures.append(
                f"{world_id}: committed resolved/world.resolved.yaml differs from a fresh resolve"
            )

    assert checked, "No worldcomposition.v1 worlds found — the guard would be vacuous."
    assert not failures, (
        "A committed projection that differs from a fresh resolve is a defect "
        "(docs/architecture/world_repository_layout.md §1):\n  " + "\n  ".join(failures)
    )
