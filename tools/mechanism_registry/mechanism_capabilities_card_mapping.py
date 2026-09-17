#!/usr/bin/env python3
"""
The capabilities-page card <-> mechanism id mapping (TCK-20260915-ARTIFACT-STATE-CONVERGENCE).

Unlike tools/mechanism_registry/mechanism_atlas_card_mapping.py, there is NO pre-existing citation table to reuse here
-- TCK-20260915-MECHANISM-REGISTRY-FOUNDATION's investigation.md only cited atlas cards. This
mapping was built fresh by reading every one of the 99 capabilities cards' full `desc` text against
the 75 registered mechanisms' real atlas-card descriptions (cross-referenced, not guessed from
title or position -- positional correspondence between the two files does NOT hold in general, see
Judgment Call 1 below for the clearest counter-example).

Every non-obvious call is a numbered Judgment Call below, each citing the specific evidence (a
quoted phrase from the capabilities card and/or the atlas card) that justified it -- mirroring
mechanism_atlas_card_mapping.py's own documentation discipline.

SHAPE DIFFERENCE FROM THE ATLAS MAPPING: every capabilities card carries exactly one `tier` field
(unlike an atlas card, which can carry multiple badges). So no capabilities card was found to need
a SPLIT_CARD_MECHANISMS-style per-badge index -- where the atlas splits one card's two badges into
two mechanisms (e.g. Aging/Succession), capabilities instead already uses two entirely separate
single-tier cards for the same two mechanisms (identity#5 "Aging & Old-Age Death" / identity#6
"Inheritance"). SPLIT_CARD_MECHANISMS and PARTIAL_COVERAGE_CARDS are declared below only for
structural parity with the atlas module's interface; both are empty, and should stay empty unless a
real one-card/multiple-mechanism case is found and documented as its own Judgment Call.

REVERSE OF THE ATLAS SHAPE: multiple capabilities cards legitimately map to the SAME mechanism id
(the atlas mapping's own `all_mechanism_card_badge_positions()` already returns a list per
mechanism id for exactly this reason). E.g. `combat_engagement` is described by both action#2 (the
pre-combat-assessment system itself) and mind#3 (a specific, newly-live facet of it) -- see
Judgment Call 2.

CARDS DELIBERATELY LEFT UNMAPPED -- not a coverage failure, a checked absence. Three shapes, each
confirmed by reading, not assumed:
  (a) Pure future-idea cards with no registered mechanism behind them at all (most of `family`,
      `clans`, half of `legacy`/`cities`/`monsters`/`nations`/`world`) -- these describe *plans*,
      not built systems, and the registry only tracks mechanisms that exist as at least gap/skeleton
      code, not every narrative idea in the corpus.
  (b) Real, built sub-features described in a capabilities card that were never given their own
      registry mechanism id during Foundation's seed, distinct from the nearby mechanism that DOES
      have an id -- see Judgment Calls 1, 3, 4.
  (c) A card that would need to be forced onto a mechanism whose registry `state` contradicts what
      the card's own text says, where mapping it would make the page WORSE (flip an accurate
      description to an inaccurate one) -- see Judgment Calls 5, 6, 7. Per this ticket's own
      standing discipline (verify before trusting, never force a mapping where the evidence doesn't
      support it), these are left unmapped and flagged for a human/peer decision rather than guessed.

JUDGMENT CALLS:

1. `action#6` "Paying for Information" (tier=built, "never actually triggers") is NOT
   `information_trust_deception`. The atlas's own `information_trust_deception` card
   (`entity-cognition#10`) explicitly says it is "distinct from the narrower unflagged Paid
   Information card above" -- confirming a separate, unregistered "Paid Information" atlas card
   exists (one of the 68 idea-level cards, never given a mechanism id). `action#6` matches that
   unregistered card, not `information_trust_deception`. Left unmapped.
   `mind#12` "Asking Specific People for Information" (tier=built, "not yet active") IS
   `information_trust_deception` -- its own text ("A separate, richer system from Paying for
   Information above: ... seek out the right kind of specialist ... guide for directions, a
   blacksmith for a recipe ... trust ... currently switched off") matches
   `information_trust_deception`'s atlas description (InformationSourceKind guide/guild/
   blacksmith/traveler, InformationProviderState, gated) closely enough to map confidently.

2. `combat_engagement` gets two capabilities cards: `action#2` "Sizing Up a Fight Before It Starts"
   (the pre-combat-assessment system itself -- "assessing perceived strength, estimating their own
   chances, and picking a stance", matching the atlas's "opponent perception, self-estimate, and
   posture selection") and `mind#3` "Sizing Up an Opponent Before Fighting" (tier=live, tierLabel
   "Newly live -- September 2026"). `action#2`'s own tier (`built`, "currently switched off") is
   almost certainly STALE prose predating the same live-by-default flip that
   TCK-20260915-MECHANISM-PRIORITY-DERIVATION already found and fixed in the wiring map for this
   exact mechanism ("still said GATED OFF by default the day after Foundation's own work confirmed
   it went live-by-default") -- `mind#3`'s "Newly live" framing is the internally-consistent, more
   recent description. Mapped both; the regenerator will correct `action#2`'s tier from `built` to
   `live` to match the registry, which is expected to be a real fix, not a surprise.

3. `identity#7` "Elder Frailty" and `identity#12` "Practice-Based Combat Experience" are real, built
   sub-features cited WITHIN the `aging_death` and `xp_leveling`/`breakthrough_bonuses` atlas cards
   respectively (`compute_elder_attribute_update()`, "a fourth fragment ... a genuine orphan", and
   `VeterancyService`, "the closest thing to practice-based mastery" -- both explicitly named as
   distinct from the cited mechanism's own main claim), but neither was given its own registry
   mechanism id. Mapping either onto its parent mechanism (`aging_death`=done, `breakthrough_bonuses`
   =done) would force a `live` tier onto cards that explicitly describe non-live sub-features
   ("never applied", "much smaller system"). Left unmapped.

4. `cities#3` "Knowing You're 'Home'" (tier=built, "Confirmed not working correctly") describes a
   real, specific home-detection bug, but no registered mechanism (`city`, `buildings_town_services`)
   cites this specific failure in its own atlas description. Left unmapped rather than guessed onto
   `city`.

5. `nations#5` "Nations Can't Be Founded or Destroyed" (tier=planned, "Confirmed not built")
   describes exactly the gap `country_lifecycle`'s own atlas title already names ("real state
   transitions, but the founding/dissolution edges are unmodeled"). But `country_lifecycle` is
   `partial`/live-by-default under this mapping's own tier function (see `nations#6` below, mapped
   to the SAME mechanism, describing its working half) -- mapping `nations#5` too would force the
   regenerator to flip an accurate "not built" card to an inaccurate "live" one, since one
   mechanism id can only carry one computed tier. Left unmapped; `nations#6` carries the
   `country_lifecycle` mapping instead, since flipping a correct "live/partial" card is safe while
   flipping a correct "not built" card to "live" is not.

6. `world#6` "Gods & Religion" (tier=built, "not yet visible in play") describes a real clan-level
   belief-formation system ("once a specific hero's deeds become famous enough, every clan in the
   world forms its own belief around that legend") that has NO registered mechanism id anywhere in
   the 75 -- and is a substantively different claim from `gods_pantheon_blessings`' own atlas
   description ("No system exists. The only trace ... is a CHURCH building offering a literal
   'BLESSING' string ... one token, not a mechanic"), which this capabilities card's own opening
   sentence agrees with ("no hand-authored pantheon or actual deity ... stays an open question,
   deliberately") before pivoting to describe the different, real belief system. Mapping this card
   to `gods_pantheon_blessings` (`state: gap`) would flip an accurate "built" description of a real
   system to an inaccurate "planned" one. Left unmapped -- flagged as a likely missing registry
   mechanism (a clan-level legend/belief-formation system), a decision for a human/peer, not this
   mapping file.

7. `legacy#5` "A Final Wish That Shapes What Comes Next" and `legacy#7` "The Same Deeds, Read
   Differently Depending on Where You Are" both describe real, built extensions ("now genuinely
   recorded", "real and tracked correctly behind the scenes") of `succession`/`reputation`
   respectively, but with narrower "not yet visible/read back" caveats the parent mechanism's own
   registry entry doesn't carry (`reputation` is plain `done` with no verified block capturing
   this specific "not visible in play yet" nuance -- `succession` was `orphan` when this note was
   first written, later corrected to `done` by TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-
   VERIFICATION, which removes that half of the original contradiction but not the underlying
   "mapping would erase real nuance" concern below). Mapping either risks the regenerator
   erasing real, accurate nuance the tier system can't otherwise represent. Left unmapped, flagged
   for a possible future registry refinement rather than forced through here.

COVERAGE GAPS FOUND (mechanism ids with zero capabilities coverage, confirmed absent by reading the
whole page, not by omission): `conversation` (gap) -- no capabilities card matches its own "merged
future vision" framing, only the narrower, unregistered "Paid Information" idea (Judgment Call 1);
`class_assignment` (partial) -- no capabilities card describes Novice/Warrior/Mage/Rogue class
identity specifically, distinct from the combat-role-derivation card (`derived_stats`) that a
title-only skim could wrongly conflate it with; `gods_pantheon_blessings` (gap) -- see Judgment
Call 6; `cross_episode_social_consequences` (orphan) -- its narrative-event-conversion facet is
folded into `nations#4`'s prose alongside `cross_episode_grief_nemesis`'s own (live) facet, but that
card's single tier field can't carry two different mechanisms' two different states, so only the
live half (`cross_episode_grief_nemesis`) was mapped from that card -- see the docstring note on
`nations#4` mapping to `cross_episode_grief_nemesis` only; `quest_generation_sourcing` (gated) --
grepped the full 99-card corpus for its atlas card's own vocabulary ("hub", "GuildNet",
"quest-worthy leads", "self-directed") and found zero matches; the hub-based quest-sourcing system
has no capabilities-page counterpart at all, not even an unregistered idea card; `social_memory`
(skeleton, "a distinct, 52-line module for tracking witnessed events -- not to be confused with the
Entity-layer Memory system") -- the closest candidate, `nations#4`'s "a nation can hold a grudge as
a whole even after the specific individual responsible is gone", is itself the
`cross_episode_social_consequences` facet already left unmapped above (a `FactionSocialMemory`
persistence claim, not this narrower witnessed-events module), so `social_memory` specifically has
no distinct capabilities-page text of its own either.

A THIRD DEMONSTRATED INSTANCE OF THE CAMP BUG PATTERN, found while building this mapping, not
guessed: `land#1` "Population Ebb & Flow" (`demographic_cohort_cycle`, registry `orphan`) is
currently `tier: planned`, `tierLabel: "Built, but confirmed not working"` -- the exact same
self-contradictory shape (a `planned`-tier card whose own label admits "built") already found and
fixed for `camp` (`monsters#0`) in this same ticket. Mapped; the regenerator will fix both in the
same pass.
"""
from __future__ import annotations

from typing import Dict, Tuple

# (section, card_index) -> single mechanism id. Every capabilities card carries exactly one tier
# field, so (unlike the atlas) there is no badge index to track -- position 0 always.
CARD_TO_MECHANISM_ID: Dict[Tuple[str, int], str] = {
    # -- action (9 cards; action#6 "Paying for Information" deliberately unmapped, Judgment Call 1)
    ("action", 0): "combat_resolution",
    ("action", 1): "tactical_decision",
    ("action", 2): "combat_engagement",  # Judgment Call 2 -- stale "built" tier, will be corrected
    ("action", 3): "movement",
    ("action", 4): "action_pacing_readiness",
    ("action", 5): "interaction_channeling",
    ("action", 7): "entity_trade",
    ("action", 8): "team_up",
    # -- identity (15 cards; #4 Elder Frailty, #12 Practice-Based unmapped, Judgment Call 3)
    ("identity", 0): "attributes_biology",
    ("identity", 1): "derived_stats",
    ("identity", 2): "race_archetype",
    ("identity", 3): "personality",
    ("identity", 4): "build_diversity",
    ("identity", 5): "aging_death",
    ("identity", 6): "succession",
    ("identity", 8): "genetics_aptitude",
    ("identity", 9): "evolution",
    ("identity", 10): "skill_unlocks",
    ("identity", 11): "xp_leveling",
    ("identity", 13): "breakthrough_bonuses",
    ("identity", 14): "entity_role",
    # -- modification (2 cards, both mapped)
    ("modification", 0): "trauma",
    ("modification", 1): "status_effects",
    # -- mind (21 cards; #6 Relationships That Fade unmapped -- pure idea, no mechanism)
    ("mind", 0): "self_model",
    ("mind", 1): "declared_cognition_schema",
    ("mind", 2): "perception",
    ("mind", 3): "combat_engagement",  # second card, Judgment Call 2
    ("mind", 4): "emotion",
    ("mind", 5): "affection_relationship_bonds",
    ("mind", 7): "motivation_doctrine",
    ("mind", 8): "commitment_betrayal",
    ("mind", 9): "temporal_pressure",
    ("mind", 10): "goal_hierarchy",
    ("mind", 11): "belief_cycle",
    ("mind", 12): "information_trust_deception",  # Judgment Call 1
    ("mind", 13): "goal_hierarchy",  # second card -- Tier 1 of knowledge_model's own atlas card is
    # attributed to goal_hierarchy by Foundation's own Judgment Call 5, not to knowledge_model
    ("mind", 14): "knowledge_model",
    ("mind", 15): "causal_spatial_memory",  # second card -- Tier 3, same Judgment Call 5 lineage
    ("mind", 16): "causal_spatial_memory",
    ("mind", 17): "adventure_routing",
    ("mind", 18): "strategic_intelligence_core",
    ("mind", 19): "committed_intentions",
    ("mind", 20): "cognition_capacity_fatigue",
    # -- family (4 cards): ALL unmapped -- pure future-idea cards, no registered mechanism exists
    # for birth/marriage/childhood anywhere in the 75.
    # -- parties (3 cards, all mapped)
    ("parties", 0): "party_formation",
    ("parties", 1): "party_formation",  # second card -- lifecycle-management facet
    ("parties", 2): "guilds",
    # -- cities (6 cards; #3 Home-detection, #4 City personality, #5 Death economics unmapped)
    ("cities", 0): "city",
    ("cities", 1): "buildings_town_services",
    ("cities", 2): "building_sabotage",
    # -- land (2 cards, both mapped)
    ("land", 0): "regional_trauma_hazards_sovereignty",
    ("land", 1): "demographic_cohort_cycle",  # a THIRD camp-shaped bug -- see module docstring
    # -- monsters (6 cards; #5 Place-type transitions unmapped -- deferred idea, matches the
    # roadmap's own idea 48 deferral)
    ("monsters", 0): "camp",
    ("monsters", 1): "ruins_mines_battlefields",
    ("monsters", 2): "settlement_capacity_axis",
    ("monsters", 3): "nest",  # nest/lair have NO atlas card at all -- this is their first and only
    ("monsters", 4): "lair",  # non-wiring-map citation, genuinely new coverage found here
    # -- nations (8 cards; #5, #7 unmapped -- Judgment Call 5)
    ("nations", 0): "diplomacy",
    ("nations", 1): "betrayal_siege_war",
    ("nations", 2): "social_contracts",
    ("nations", 3): "reputation",
    ("nations", 4): "cross_episode_grief_nemesis",  # NOT cross_episode_social_consequences --
    # see module docstring coverage-gap note; this card's single tier can't carry both mechanisms'
    # different states
    ("nations", 6): "country_lifecycle",
    # -- clans (2 cards; #1 unmapped -- pure idea layered on top of `clan`)
    ("clans", 0): "clan",
    # -- races (2 cards, both mapped)
    ("races", 0): "race_archetype",  # second card for race_archetype
    ("races", 1): "race_collective_force",
    # -- world (8 cards; #6 Gods & Religion, #7 memory-drift-over-generations unmapped)
    ("world", 0): "campaigns",
    ("world", 1): "chronicle",
    ("world", 2): "opportunity_rumor_seeds",
    ("world", 3): "cultural_drift",
    ("world", 4): "calamities_boss_spawns",
    ("world", 5): "world_generation",
    # -- legacy (8 cards; #1, #3, #4, #5, #6, #7 unmapped -- see Judgment Call 7 and module
    # docstring; lowest-coverage section, each decision evidence-based)
    ("legacy", 0): "reputation",  # second card -- birth-echo facet
    ("legacy", 2): "cross_episode_grief_nemesis",  # second card -- cross-chapter feud/blocker facet
    # -- objects (3 cards, all mapped)
    ("objects", 0): "equipment_scoring",
    ("objects", 1): "inventory_trade_conservation",
    ("objects", 2): "crafting",
}

# No one-card/multiple-mechanism split was found in the capabilities page (every card has exactly
# one tier field) -- kept for interface parity with mechanism_atlas_card_mapping.py, and to make a
# future real split (if one is ever found) visible as a deliberate addition rather than a silent
# structural change.
SPLIT_CARD_MECHANISMS: Dict[Tuple[str, int], list] = {}

# No partial-coverage card (one card, several sub-systems, only some registered) was found either --
# same interface-parity reasoning as SPLIT_CARD_MECHANISMS above.
PARTIAL_COVERAGE_CARDS: Dict[Tuple[str, int], Dict[int, str]] = {}


def all_mechanism_card_badge_positions() -> Dict[str, list]:
    """mechanism_id -> [(section, card_index, badge_index), ...]. badge_index is always 0 here
    (capabilities cards have one tier field, never a badge list) -- kept as a 3-tuple for interface
    parity with mechanism_atlas_card_mapping.py's own function of the same name, so a caller can
    treat both mapping modules identically."""
    result: Dict[str, list] = {}
    for (section, idx), mech_id in CARD_TO_MECHANISM_ID.items():
        result.setdefault(mech_id, []).append((section, idx, 0))
    for (section, idx), mech_ids in SPLIT_CARD_MECHANISMS.items():
        for badge_idx, mech_id in enumerate(mech_ids):
            result.setdefault(mech_id, []).append((section, idx, badge_idx))
    for (section, idx), badge_map in PARTIAL_COVERAGE_CARDS.items():
        for badge_idx, mech_id in badge_map.items():
            result.setdefault(mech_id, []).append((section, idx, badge_idx))
    return result
