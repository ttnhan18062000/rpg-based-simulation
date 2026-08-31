"""
tests/unit/domains/cooperation/test_role_1_magic_number_disclosure.py
───────────────────────────────────────────────────────────────────────────────
TCK-20260824-OCCUPATION-CHANGE-TRIGGER, plan.md Step 9 (optional, recommended by test_plan.md
test 10) — locks in the CURRENT, disclosed (not fixed) behavior of PartnerCandidateProvider's
`cand.identity.role == 1` check: EntityRole(1) is SHOPKEEPER (src/core/enums.py:8), not a
distinct "Hireling"/"Guild Merchant" role, but providers.py still charges the hireling gold cost
to any same-faction SHOPKEEPER candidate. This is now a TODO-flagged, live-reachable bug (role_set
is runtime-reachable as of this ticket), not a latent one -- if this test's assertion ever
needs to change, that's a deliberate fix to the magic number, not an accidental regression.
"""
from src.core.enums import EntityRole
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.domains.cooperation.evaluators import HelpNeed
from src.domains.cooperation.providers import CandidateBudget, PartnerCandidateProvider


def test_shopkeeper_candidate_is_still_charged_hireling_cost_disclosed_not_fixed():
    req = V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build()
    shopkeeper = (
        V2EntityBuilder(2)
        .kind("NPC")
        .location(1.0, 1.0)
        .identity(role=EntityRole.SHOPKEEPER)
        .lifecycle(active=True)
        .build()
    )
    assert shopkeeper.identity.faction == req.identity.faction

    state = AuthoritativeState(entities={1: req, 2: shopkeeper}, tick=1, seed=123)
    help_need = HelpNeed("combat_support_needed", 0.8, "Test need")
    budget = CandidateBudget(max_candidates=5, spatial_radius=15.0)

    candidates = PartnerCandidateProvider.get_candidates(req, state, (help_need,), budget)

    assert len(candidates) == 1
    assert candidates[0].entity_id == 2
    assert candidates[0].cost_gold == 20
