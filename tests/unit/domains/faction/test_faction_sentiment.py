"""Unit tests for FactionSentimentService (TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION).

Faction-to-faction sentiment derived from real entity interaction, mirroring SocialBond at
faction scope. Full design: docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md §3.2.
"""


def _entity(entity_id, faction_id, pos=(0.0, 0.0)):
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(*pos)
        .identity(role=EntityRole.HERO, faction=Faction.NEUTRAL, properties={"faction_id": faction_id})
        .combat(hp=100, max_hp=100, alive=True)
        .build()
    )


def test_derive_from_bond_updates_emits_symmetric_faction_updates_for_cross_faction_hostility():
    """A real combat-shaped SocialBondUpdate between two different-faction entities derives a
    scaled, symmetric FactionUpdate pair (both factions record the interaction toward each
    other), with pairwise_tension_delta (scoped to that specific rival only, NOT the ambient
    tension_delta) raised by the hostile swing."""
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate, EntityUpdate, SocialUpdate, SocialBondUpdate
    from src.domains.faction.sentiment import FactionSentimentService

    attacker = _entity(1, "hero_guild")
    victim = _entity(2, "orc_clan")

    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={1: attacker, 2: victim},
        factions={"hero_guild": __import__("src.core.state", fromlist=["FactionState"]).FactionState(faction_id="hero_guild"),
                  "orc_clan": __import__("src.core.state", fromlist=["FactionState"]).FactionState(faction_id="orc_clan")},
    )

    # victim's own bond toward attacker degrades on a hit -- real combat.py shape.
    update = StateUpdate(entity_updates={
        2: EntityUpdate(entity_id=2, social=SocialUpdate(bond_updates=[
            SocialBondUpdate(target_id=1, sentiment_delta=-0.1, familiarity_delta=0.05),
        ])),
    })

    faction_updates = FactionSentimentService.derive_from_bond_updates(state, update)

    assert len(faction_updates) == 2
    by_id = {fu.faction_id: fu for fu in faction_updates}
    assert set(by_id) == {"hero_guild", "orc_clan"}

    expected_sentiment = -0.1 * FactionSentimentService.FACTION_SCALE_FACTOR
    expected_familiarity = 0.05 * FactionSentimentService.FACTION_SCALE_FACTOR

    hg_upd = by_id["hero_guild"]
    assert hg_upd.faction_sentiment_delta == {"orc_clan": expected_sentiment}
    assert hg_upd.faction_familiarity_delta == {"orc_clan": expected_familiarity}
    assert hg_upd.tension_delta == 0.0  # ambient tension_delta must NOT be touched by a real rival's fight
    assert hg_upd.pairwise_tension_delta == {"orc_clan": -expected_sentiment}  # hostile swing raises tension, scoped to this rival only

    oc_upd = by_id["orc_clan"]
    assert oc_upd.faction_sentiment_delta == {"hero_guild": expected_sentiment}
    assert oc_upd.tension_delta == 0.0
    assert oc_upd.pairwise_tension_delta == {"hero_guild": -expected_sentiment}


def test_derive_from_bond_updates_ignores_same_faction_interaction():
    """Two entities of the SAME faction interacting must not produce any faction update --
    nothing to derive at faction scope."""
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate, EntityUpdate, SocialUpdate, SocialBondUpdate
    from src.domains.faction.sentiment import FactionSentimentService

    e1 = _entity(1, "hero_guild")
    e2 = _entity(2, "hero_guild")
    state = AuthoritativeState(tick=100, seed=42, entities={1: e1, 2: e2})

    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, social=SocialUpdate(bond_updates=[
            SocialBondUpdate(target_id=2, sentiment_delta=-0.1, familiarity_delta=0.05),
        ])),
    })

    assert FactionSentimentService.derive_from_bond_updates(state, update) == []


def test_derive_from_bond_updates_ignores_zero_delta_updates():
    """A bond_update with both deltas at 0.0 (e.g. a role-only or tick-only update) must not
    produce a faction update."""
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate, EntityUpdate, SocialUpdate, SocialBondUpdate
    from src.domains.faction.sentiment import FactionSentimentService

    e1 = _entity(1, "hero_guild")
    e2 = _entity(2, "orc_clan")
    state = AuthoritativeState(tick=100, seed=42, entities={1: e1, 2: e2})

    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, social=SocialUpdate(bond_updates=[
            SocialBondUpdate(target_id=2, sentiment_delta=0.0, familiarity_delta=0.0, last_interaction_tick_set=100),
        ])),
    })

    assert FactionSentimentService.derive_from_bond_updates(state, update) == []


def test_apply_path_clamps_sentiment_and_stamps_last_interaction_tick():
    """The real apply-path (src/engine/apply.py) clamps sentiment to [-1,1] and stamps
    last_interaction_tick on a real interaction delta."""
    from dataclasses import replace
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    state = AuthoritativeState(
        tick=250,
        seed=42,
        factions={
            "hero_guild": FactionState(faction_id="hero_guild"),
            "orc_clan": FactionState(faction_id="orc_clan"),
        },
    )
    update = StateUpdate(faction_updates=[
        FactionUpdate(faction_id="hero_guild", faction_sentiment_delta={"orc_clan": -0.95}),
    ])

    new_state = ApplyPath.apply_generation(state, update)
    sent = new_state.factions["hero_guild"].faction_sentiments["orc_clan"]
    assert sent.sentiment == -0.95
    assert sent.last_interaction_tick == 250

    # A second, large negative delta must clamp at -1.0, not overshoot.
    update2 = StateUpdate(faction_updates=[
        FactionUpdate(faction_id="hero_guild", faction_sentiment_delta={"orc_clan": -0.5}),
    ])
    new_state2 = ApplyPath.apply_generation(new_state, update2)
    sent2 = new_state2.factions["hero_guild"].faction_sentiments["orc_clan"]
    assert sent2.sentiment == -1.0


def test_apply_path_scopes_pairwise_tension_to_named_rival_only():
    """A pairwise_tension_delta targeting one rival must NOT affect a faction's tension with any
    other faction (TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION regression: this used to
    be a single ambient scalar shared across every pair, so a fight with one rival read as
    tension with every other faction the fighter had never met)."""
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    state = AuthoritativeState(
        tick=100,
        seed=42,
        factions={
            "bandit_company": FactionState(faction_id="bandit_company"),
            "wild_beast_pack": FactionState(faction_id="wild_beast_pack"),
            "merchant_league": FactionState(faction_id="merchant_league"),
        },
    )
    update = StateUpdate(faction_updates=[
        FactionUpdate(faction_id="bandit_company", pairwise_tension_delta={"wild_beast_pack": 0.9}),
    ])
    new_state = ApplyPath.apply_generation(state, update)
    bc = new_state.factions["bandit_company"]
    assert bc.pairwise_tension.get("wild_beast_pack") == 0.9
    assert bc.pairwise_tension.get("merchant_league", 0.0) == 0.0  # untouched -- never fought this one
    assert bc.tension_level == 0.0  # ambient scalar untouched by a pairwise delta


def test_compute_transitions_does_not_cascade_hostility_to_uninvolved_factions():
    """A pair that crosses the HOSTILE threshold via pairwise_tension must not make either
    faction TENSE/HOSTILE toward a third faction it has zero pairwise_tension with -- the exact
    cascade confirmed live in a real run before this fix (one HOSTILE pair spread to blanket
    HOSTILE across an entire 15-faction world in one tick)."""
    from src.core.state import FactionState
    from src.domains.faction.diplomatic_state_machine import compute_transitions

    factions = {
        "bandit_company": FactionState(faction_id="bandit_company", pairwise_tension={"wild_beast_pack": 0.95}),
        "wild_beast_pack": FactionState(faction_id="wild_beast_pack", pairwise_tension={"bandit_company": 0.95}),
        "merchant_league": FactionState(faction_id="merchant_league"),  # never interacted with bandit_company
    }
    updates = compute_transitions(factions)
    touched_pairs = {
        (u.faction_id, target) for u in updates for target in u.diplomatic_relations_set
    }
    assert ("bandit_company", "wild_beast_pack") in touched_pairs
    assert ("wild_beast_pack", "bandit_company") in touched_pairs
    assert ("bandit_company", "merchant_league") not in touched_pairs
    assert ("merchant_league", "bandit_company") not in touched_pairs


def test_decay_stale_sentiments_only_fires_at_interval_and_past_staleness():
    """decay_stale_sentiments() only acts on the DECAY_INTERVAL cadence, and only for pairs
    whose last_interaction_tick is older than DECAY_STALENESS_THRESHOLD."""
    from src.core.state import AuthoritativeState, FactionState, FactionSentiment
    from src.domains.faction.sentiment import FactionSentimentService

    interval = FactionSentimentService.DECAY_INTERVAL
    staleness = FactionSentimentService.DECAY_STALENESS_THRESHOLD

    # Not on the decay cadence -- must be a no-op regardless of staleness.
    state_off_cadence = AuthoritativeState(
        tick=interval + 1,
        seed=42,
        factions={"hero_guild": FactionState(
            faction_id="hero_guild",
            faction_sentiments={"orc_clan": FactionSentiment(target_faction_id="orc_clan", sentiment=-0.5, last_interaction_tick=0)},
        )},
    )
    assert FactionSentimentService.decay_stale_sentiments(state_off_cadence) == []

    # On cadence, but recently interacted (not stale) -- must be a no-op.
    state_fresh = AuthoritativeState(
        tick=interval,
        seed=42,
        factions={"hero_guild": FactionState(
            faction_id="hero_guild",
            faction_sentiments={"orc_clan": FactionSentiment(target_faction_id="orc_clan", sentiment=-0.5, last_interaction_tick=interval - 1)},
        )},
    )
    assert FactionSentimentService.decay_stale_sentiments(state_fresh) == []

    # On cadence AND stale -- must decay toward 0.0 via the absolute decay_set path, not delta.
    stale_tick = interval + staleness + interval
    state_stale = AuthoritativeState(
        tick=stale_tick,
        seed=42,
        factions={"hero_guild": FactionState(
            faction_id="hero_guild",
            faction_sentiments={"orc_clan": FactionSentiment(target_faction_id="orc_clan", sentiment=-0.5, last_interaction_tick=0)},
        )},
    )
    updates = FactionSentimentService.decay_stale_sentiments(state_stale)
    assert len(updates) == 1
    assert updates[0].faction_id == "hero_guild"
    assert updates[0].faction_sentiment_delta == {}
    expected = -0.5 * FactionSentimentService.DECAY_FACTOR
    assert updates[0].faction_sentiment_decay_set == {"orc_clan": expected}


def test_decay_apply_path_does_not_reset_last_interaction_tick():
    """Applying a decay update must NOT bump last_interaction_tick -- decay itself is not a
    real interaction, or the staleness clock it's checking would never re-fire for that pair."""
    from src.core.state import AuthoritativeState, FactionState, FactionSentiment
    from src.core.updates import StateUpdate, FactionUpdate
    from src.engine.apply import ApplyPath

    state = AuthoritativeState(
        tick=5000,
        seed=42,
        factions={"hero_guild": FactionState(
            faction_id="hero_guild",
            faction_sentiments={"orc_clan": FactionSentiment(target_faction_id="orc_clan", sentiment=-0.5, last_interaction_tick=10)},
        )},
    )
    update = StateUpdate(faction_updates=[
        FactionUpdate(faction_id="hero_guild", faction_sentiment_decay_set={"orc_clan": -0.45}),
    ])
    new_state = ApplyPath.apply_generation(state, update)
    sent = new_state.factions["hero_guild"].faction_sentiments["orc_clan"]
    assert sent.sentiment == -0.45
    assert sent.last_interaction_tick == 10  # unchanged by decay
