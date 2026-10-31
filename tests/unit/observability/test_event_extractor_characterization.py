"""Characterization tests for EventExtractor.extract (TCK-20261028-EVENT-EXTRACTOR-CHARACTERIZATION-TESTS).

These pin what ``extract`` emits today, so that moving its code (TCK-20261028-EVENT-EXTRACTOR-SPLIT-BY-DOMAIN) can be shown to change nothing.
They are not a statement that the pinned behavior is right.

What is pinned, per config (default flags, each of the 4 ``ENABLE_PUSH_EVENT_SHAPERS*`` rollback flags off alone, all four off under LIGHT
and under NORMAL): for every ``extract`` call, the number of events and a SHA-256 prefix over the ordered canonical lines. A canonical line is one event
as sorted-key JSON with ``timestamp``, ``created_at`` and ``event_id`` left out (wall clock / random). Emission order is part of the digest.

Two sources of calls:
- the corpus: every ``extract`` call made by the existing ``test_event_extractor_*.py`` unit tests, recorded by a pytest plugin
  (extractor_characterization/recorder_plugin.py) that evaluates each call under every config and leaves the test's own call unchanged;
- two seeded real-Kernel runs under ``audit_mode`` (extractor_characterization/kernel_scenario.py).

Hash seed: set-listing events used to follow the process hash seed; the emit-order fix (#790) sorts them. Recordings still pin seed 0 and
the ``*_under_a_second_hash_seed`` tests prove a second seed gives the same rows as the pinned seed-0 fixtures.

Modes: ``OFF`` returns ``[]``. LIGHT and LONG_RUN are treated alike and any other mode differently, in the four mode checks inside the
rollback branches; ``all_off_light`` vs ``all_off_normal`` pin both sides.

Fixtures: tests/fixtures/event_extractor_characterization/*.jsonl. Pinned rows must match exactly; a new unit test adds rows without a failure.
To see which events moved, record full lines at both commits with ``EXTRACTOR_RECORD_FULL=<path>`` (see recorder_plugin.py) and diff them.

Regenerating (only for an intentional change of extract()'s output, agreed with rpg-planner first):
    python -m tests.unit.observability.extractor_characterization.corpus
"""
from __future__ import annotations

import pytest

from src.observability.config import ObservabilityMode
from src.observability.divergence_episode import DivergenceEpisodes
from src.observability.event_extractor import EventExtractor
from tests.unit.observability import test_event_extractor_cognition as cognition
from tests.unit.observability import test_event_extractor_progression as progression
from tests.unit.observability.extractor_characterization import corpus
from tests.unit.observability.extractor_characterization.recorder_plugin import (
    _STATE_NAMES,
    CONFIGS,
    FLAGS,
)


def test_off_mode_emits_nothing():
    assert EventExtractor.extract(object(), object(), None, ObservabilityMode.OFF) == []


def test_config_matrix_covers_every_rollback_flag_and_both_mode_sides():
    names = set(CONFIGS)
    assert {f"off_{flag}" for flag in FLAGS} <= names
    assert {"as_built", "default_flags", "all_off_light", "all_off_normal"} <= names
    assert len(FLAGS) == 4


def test_reset_run_state_clears_all_eight_collections_and_divergence_episodes():
    try:
        EventExtractor._seen_routing_families[1] = {"f"}
        EventExtractor._last_xp_tick[1] = 5
        EventExtractor._emitted_plateau.add(1)
        EventExtractor._emitted_stale_leads[1] = {"lead"}
        EventExtractor._emitted_social_memory.add((1, 2))
        EventExtractor._emitted_contract_milestones.add("c:25%")
        EventExtractor._last_capability_growth_tick[1] = 7
        EventExtractor._emitted_capability_stalled.add(1)
        DivergenceEpisodes._diverged.add(1)
        assert len(_STATE_NAMES) == 8
        EventExtractor.reset_run_state()
        for name in _STATE_NAMES:
            assert not getattr(EventExtractor, name), name
        assert not DivergenceEpisodes._diverged
    finally:
        EventExtractor.reset_run_state()


def test_unit_corpus_matches_pinned_fixture():
    expected = corpus.load_rows(corpus.CORPUS_FIXTURE)
    assert expected, "unit corpus fixture is empty"
    problems = corpus.differences(expected, corpus.run_corpus())
    assert not problems, f"{len(problems)} pinned extract() outputs moved; first: {problems[:5]}"


def test_emit_once_events_are_pinned_across_ticks_in_the_corpus():
    # The emit-once events (plateau, stale lead, social memory, capability stalled) are pinned by the multi-call
    # tests that already exercise them; the contract-milestone dedupe happens inside one call, so its digest pins it: after the call that emits, the calls with the same trigger must stay at 0 events, and the digest of that call is in the fixture.
    rows = corpus.load_rows(corpus.CORPUS_FIXTURE)
    by_test: dict[str, list[dict]] = {}
    for row in rows:
        by_test.setdefault(row["test"], []).append(row)
    names = (
        "test_event_extractor_progression.py::TestProgressionPlateauDetected::test_fires_only_once_per_entity_per_run",
        "test_event_extractor_progression.py::TestCapabilityGrowthStalled::test_fires_only_once_per_entity_per_run",
        "test_event_extractor_information2.py::TestBeliefStale::test_fires_only_once_per_lead_per_run",
        "test_event_extractor_social_memory.py::test_once_per_run_no_duplicate",
    )
    for suffix in names:
        calls = [r for t, rs in by_test.items() if t.endswith(suffix) for r in rs]
        assert len(calls) >= 2, f"{suffix} must make 2+ extract calls, saw {len(calls)}"
        counts = [r["results"]["as_built"][0] for r in sorted(calls, key=lambda r: r["call"])]
        first = next((i for i, n in enumerate(counts) if n), None)
        assert first is not None, f"{suffix}: never emitted, got {counts}"
        assert counts[-1] == 0 and not any(counts[first + 1:]), f"{suffix}: expected an emission, then silence, got {counts}"


@pytest.mark.parametrize("world,seed,ticks", corpus.KERNEL_SCENARIOS, ids=[s[0] for s in corpus.KERNEL_SCENARIOS])
def test_kernel_scenario_matches_pinned_fixture(world, seed, ticks):
    expected = [r for r in corpus.load_rows(corpus.KERNEL_FIXTURE) if r["test"] == f"{world}:{seed}"]
    assert len(expected) == ticks, f"fixture holds {len(expected)} ticks for {world}, expected {ticks}"
    problems = corpus.differences(expected, corpus.run_kernel_scenario(world, seed, ticks))
    assert not problems, f"{len(problems)} pinned extract() outputs moved; first: {problems[:5]}"


def test_corpus_recording_is_identical_under_a_second_hash_seed():
    """Emit order no longer follows the process hash seed (emit-order fix), so a recording at another seed must equal the one pinned at seed 0, row for row."""
    assert corpus.run_corpus(corpus.ALT_HASH_SEED) == corpus.load_rows(corpus.CORPUS_FIXTURE)


@pytest.mark.parametrize("world,seed,ticks", corpus.KERNEL_SCENARIOS, ids=[s[0] for s in corpus.KERNEL_SCENARIOS])
def test_kernel_recording_is_identical_under_a_second_hash_seed(world, seed, ticks):
    expected = [r for r in corpus.load_rows(corpus.KERNEL_FIXTURE) if r["test"] == f"{world}:{seed}"]
    assert corpus.run_kernel_scenario(world, seed, ticks, corpus.ALT_HASH_SEED) == expected


# -- emitting blocks that neither the unit corpus nor the kernel scenarios reach (found by the coverage run in this ticket's test_plan.md) --

@pytest.fixture
def clean_run_state():
    EventExtractor.reset_run_state()
    yield
    EventExtractor.reset_run_state()


def test_paid_info_changed_goal_fires_when_an_information_purchase_switches_the_project(clean_run_state):
    prior, current = cognition._entity(), cognition._entity()
    prior.strategic.current_project_id = "project_a"
    current.strategic.current_project_id = "project_b"
    update = cognition._update_with_intent_results(1, [cognition._intent_result("INFORMATION_PURCHASE", source_id="prov_42")])
    events = EventExtractor.extract(cognition._state({1: prior}), cognition._state({1: current}), update, ObservabilityMode.NORMAL)
    changed = [e for e in events if e.event_type == "paid_info_changed_goal"]
    assert len(changed) == 1
    assert (changed[0].event_category, changed[0].entity_id, changed[0].payload) == ("strategy", 1, {"source_id": "prov_42"})
    assert [e.event_type for e in events].count("paid_info_transaction") == 1


def test_progression_plateau_skill_silence_fires_at_level_five_with_no_skills(clean_run_state):
    EventExtractor._last_xp_tick[1] = 58  # 2 ticks since XP moved: under the xp_rate_zero threshold, so the skill_silence branch is next
    prior = progression._entity(identity=progression._identity(evolution_points=100, evolution_level=5))
    current = progression._entity(identity=progression._identity(evolution_points=100, evolution_level=5))
    events = EventExtractor.extract(
        progression._state({1: prior}, tick=60), progression._state({1: current}, tick=60), progression._update(1), ObservabilityMode.NORMAL,
    )
    plateau = [e for e in events if e.event_type == "progression_plateau_detected"]
    assert len(plateau) == 1
    assert plateau[0].payload == {"type": "skill_silence", "level": 5}
    assert 1 in EventExtractor._emitted_plateau
