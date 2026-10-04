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


ADR_PATH = Path("docs/architecture/world_repository_layout.md")
BIBLE_06_PATH = Path("docs/mechanics/06_worldbuilding_foundation.md")
CONTENT_AUTHORING_PATH = Path("docs/guides/content_authoring.md")
AUTHORITY_SENTENCE = "is the sole authoritative definition of a `world_id`"
AUTHORITY_INVARIANT = "The world the engine loads is the one its authored definition resolves to"
ADR_CITATION = "docs/architecture/world_repository_layout.md"
RETIRED_AUTHORING_PATH = "data/content/world_compositions"


def test_authoritative_world_location_stated_once():
    adr = ADR_PATH.read_text(encoding="utf-8")
    assert AUTHORITY_SENTENCE in adr, (
        f"{ADR_PATH} must carry the one normative authority sentence; it is the only place the "
        "authoritative location is stated."
    )

    bible = BIBLE_06_PATH.read_text(encoding="utf-8")
    assert "data/worlds/<world_id>" not in bible, (
        f"{BIBLE_06_PATH} must not restate the authoritative path — it states the invariant and "
        "cites the ADR for the location."
    )
    assert ADR_CITATION in bible, f"{BIBLE_06_PATH} must cite the ADR for the location."

    authoring = CONTENT_AUTHORING_PATH.read_text(encoding="utf-8")
    assert ADR_CITATION in authoring, (
        f"{CONTENT_AUTHORING_PATH} teaches the authoring path and must link the ADR rather than "
        "restating the rule."
    )

    offenders = [
        str(path)
        for path in sorted(Path("docs/guides").rglob("*.md"))
        if RETIRED_AUTHORING_PATH in path.read_text(encoding="utf-8")
    ]
    assert not offenders, (
        "These authoring guides still present the retired catalog directory as an authoring "
        "target:\n  " + "\n  ".join(offenders)
    )


def test_bible_06_does_not_present_the_invariant_as_a_compile_gate():
    """The invariant is enforced by an architecture guard, not by the compiler.

    Promoting it into §7's severity-gate ladder would document a gate nothing aborts on — the
    exact parity break the Authoritative Mechanics Rule forbids. A later editor tidying it into
    the neighbouring ladder must trip a test, not merely contradict a plan.
    """
    lines = BIBLE_06_PATH.read_text(encoding="utf-8").splitlines()
    invariant_idx = [i for i, line in enumerate(lines) if AUTHORITY_INVARIANT in line]
    assert len(invariant_idx) == 1, (
        f"Expected the one-definition invariant stated exactly once in {BIBLE_06_PATH}; "
        f"found {len(invariant_idx)} occurrences."
    )
    idx = invariant_idx[0]

    section_starts = [i for i, line in enumerate(lines) if line.startswith("## ")]
    enclosing = max(i for i in section_starts if i < idx)
    assert "Integrity Validation Laws & Severity Gates" not in lines[enclosing], (
        "The one-definition invariant must not sit inside §7's gate ladder — it is a sibling "
        "repository-layout law, not a build-time severity gate."
    )

    section_end = min([i for i in section_starts if i > enclosing], default=len(lines))
    block = "\n".join(lines[enclosing:section_end])
    assert "WORLD-" not in block, (
        "The one-definition invariant must not carry a WORLD-* rule id — it is not a "
        "WorldValidationRule."
    )
    for severity_word in ("ERROR", "WARNING", "Level 2"):
        assert severity_word not in block, (
            f"The one-definition invariant's block must not assign a severity ({severity_word!r}); "
            "nothing aborts compilation on it."
        )
