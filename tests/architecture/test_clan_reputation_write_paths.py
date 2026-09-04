"""
Idea 54/M5 (SOC-268) AC5 guard: this ticket's new/modified clan-reputation
code must never write an individual member's own SocialComponent
.public_reputation -- ClanState.clan_reputation is a structurally distinct
field with its own apply-path branch (apply.py's clan-merge block).

Follows the same inspect.getsource() source-text scan technique as
tests/architecture/test_social_write_paths.py::
test_reputation_seed_write_path_does_not_reference_reputation_update_service.

Ticket: TCK-20260904-CLAN-REPUTATION-ASSOCIATION
"""
from __future__ import annotations

import inspect
import re

import pytest

pytestmark = pytest.mark.architecture

_WRITE_PATTERN = re.compile(r'\bpublic_reputation\s*=')


def test_no_writes_to_member_public_reputation_from_clan_reputation_code():
    from src.engine.pipeline_phases.groups import GroupPhase
    from src.systems.social_systems.clan_lifecycle import ClanLifecycleService
    from src.systems.social_systems.contracts import ContractService
    from src.systems.social_systems.appraisal import SocialAppraisalSystem

    sources = {
        "GroupPhase.resolve": inspect.getsource(GroupPhase.resolve),
        "ClanLifecycleService.find_clan_id_for_entity": inspect.getsource(
            ClanLifecycleService.find_clan_id_for_entity
        ),
        "ContractService.compute_betrayal_clan_reputation_update": inspect.getsource(
            ContractService.compute_betrayal_clan_reputation_update
        ),
        "SocialAppraisalSystem.appraise_contract": inspect.getsource(
            SocialAppraisalSystem.appraise_contract
        ),
    }

    violations = {
        name: matches
        for name, source in sources.items()
        if (matches := _WRITE_PATTERN.findall(source))
    }

    assert not violations, (
        "Found public_reputation= write(s) in clan-reputation code that must "
        "never mutate an individual member's own SocialComponent.public_reputation:\n"
        + "\n".join(f"  {name}: {matches}" for name, matches in violations.items())
    )
