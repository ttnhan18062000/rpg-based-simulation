"""
Architecture guard: SocialComponent.public_reputation and regional_reputation may only be
written by RelationshipService.process_update() (SOC-217, the sole authoritative writer for
SocialComponent). TCK-20260904-REPUTATION-LOCALITY-SCOPE fixed a pre-existing bypass in
SocialMemoryImporter.apply() (src/domains/campaigns/social_memory.py), which previously
called dc_replace(entity.social, ..., public_reputation=...) directly. This guard prevents
that bypass -- or an equivalent one for the new regional_reputation field -- from being
reintroduced anywhere in src/.

Scan strategy:
  - Look for the keyword-argument write patterns `public_reputation=` and
    `regional_reputation=` anywhere under src/.
  - ALLOWED_FILES may contain them (the authoritative writer itself, the dataclass field
    declaration, and initial-construction seeding via V2EntityBuilder).
  - Any other file containing either pattern is a second write path and fails the test.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import FrozenSet

import pytest

pytestmark = pytest.mark.architecture

_SRC_ROOT = Path("src")

_WRITE_PATTERN = re.compile(r'\b(public_reputation|regional_reputation)\s*=')

# Files permitted to contain `public_reputation=` / `regional_reputation=`:
#   - relationships.py: the one authoritative writer (RelationshipService.process_update())
#   - social.py: the SocialComponent dataclass field declarations themselves, not a write
#   - builder.py: V2EntityBuilder's initial-construction seeding (pre-tick, not a live
#     mutation) -- the same accepted exception pattern as place_attachment's builder kwarg
#   - quests.py: writes RelationshipModel.public_reputation (entity.cognition.relationships,
#     the PublicReputationProfile dict) -- a structurally distinct field that only shares a
#     name with SocialComponent.public_reputation; confirmed unrelated and explicitly out of
#     scope for this guard (see ticket TCK-20260904-REPUTATION-LOCALITY-SCOPE's Out of Scope)
#   - fingerprint.py: `regional_reputation=` appears inside a fingerprint f-string label
#     (StateFingerprinter.get_fingerprint()'s determinism string), not a write
ALLOWED_FILES: FrozenSet[str] = frozenset({
    "src/systems/social_systems/relationships.py",
    "src/core/models/social.py",
    "src/core/builder.py",
    "src/engine/quests.py",
    "src/replay/fingerprint.py",
})


def _iter_src_py_files():
    return sorted(_SRC_ROOT.rglob("*.py"))


def test_public_reputation_and_regional_reputation_write_paths_are_allowlisted():
    violations = []

    for path in _iter_src_py_files():
        rel_path = path.as_posix()
        if rel_path in ALLOWED_FILES:
            continue

        text = path.read_text(encoding="utf-8")
        matches = _WRITE_PATTERN.findall(text)
        if matches:
            violations.append((rel_path, sorted(set(matches))))

    assert not violations, (
        "Found direct public_reputation=/regional_reputation= write(s) outside the "
        "authoritative RelationshipService.process_update() path (and its allowlisted "
        "construction-time exceptions):\n"
        + "\n".join(f"  {path}: {fields}" for path, fields in violations)
    )


def test_relationships_py_is_the_authoritative_writer():
    text = Path("src/systems/social_systems/relationships.py").read_text(encoding="utf-8")
    assert "public_reputation=" in text
    assert "regional_reputation=" in text


def test_reputation_seed_write_path_does_not_reference_reputation_update_service():
    """TCK-20260904-INHERITED-REPUTATION-SEED (AC5): the new birth-seed write path
    (V2EntityBuilder.birth_record() and ReputationService.combine_public_reputation())
    must never import or call ReputationUpdateService/PublicReputationProfile -- a
    structurally separate, unrelated reputation representation this ticket must not touch."""
    import inspect
    from src.core.builder import V2EntityBuilder
    from src.systems.social_systems.reputation import ReputationService

    birth_record_source = inspect.getsource(V2EntityBuilder.birth_record)
    combine_source = inspect.getsource(ReputationService.combine_public_reputation)

    for source in (birth_record_source, combine_source):
        assert "ReputationUpdateService" not in source
        assert "PublicReputationProfile" not in source
