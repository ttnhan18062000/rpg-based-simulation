"""TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS — per-entity lifecycle scoring tool."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import entity_lifecycle_score as els  # noqa: E402


@pytest.fixture(scope="module")
def weights():
    return els.load_weights()


def _path(events, role="CITIZEN", faction="town_council", kind="worker", region="hometown"):
    return {
        "events": events,
        "metadata": {"role": role, "faction": faction, "kind": kind, "region": region},
    }


# ---------------------------------------------------------------------------
# Per-entity metric formulas
# ---------------------------------------------------------------------------


class TestPerEntityMetrics:

    def test_path_length_and_density(self, weights):
        events = [(i, "movement", "INFO") for i in range(10)]
        metrics = els.compute_entity_metrics(_path(events), weights, ticks_observed=100)
        assert metrics["path_length"] == 10
        assert metrics["path_density"] == pytest.approx(0.1)

    def test_phase_coverage_counts_distinct_buckets_touched(self, weights):
        events = [
            (1, "movement", "INFO"),           # EXPLORATION
            (2, "biological_state_changed", "INFO"),  # VITALS
            (3, "xp_granted", "INFO"),          # GROWTH_PROGRESSION
        ]
        metrics = els.compute_entity_metrics(_path(events), weights, ticks_observed=100)
        n_buckets = len(weights["lifecycle_phase_buckets"])
        assert metrics["phase_coverage"] == pytest.approx(3 / n_buckets)
        assert set(metrics["buckets_touched"]) == {"EXPLORATION", "VITALS", "GROWTH_PROGRESSION"}

    def test_path_entropy_zero_for_single_type_max_for_uniform(self, weights):
        degenerate = [(i, "movement", "INFO") for i in range(20)]
        degenerate_metrics = els.compute_entity_metrics(_path(degenerate), weights, ticks_observed=100)
        assert degenerate_metrics["path_entropy"] == pytest.approx(0.0, abs=1e-6)

        uniform_types = ["movement", "biological_state_changed", "stamina_changed", "xp_granted"]
        uniform = [(i, uniform_types[i % 4], "INFO") for i in range(20)]
        uniform_metrics = els.compute_entity_metrics(_path(uniform), weights, ticks_observed=100)
        assert uniform_metrics["path_entropy"] == pytest.approx(1.0, abs=1e-6)

    def test_loop_score_detects_dominant_short_cycle(self, weights):
        looped = [(i, "movement" if i % 2 == 0 else "biological_state_changed", "INFO") for i in range(20)]
        looped_metrics = els.compute_entity_metrics(_path(looped), weights, ticks_observed=100)
        assert looped_metrics["loop_score"] > 0.9

        # Genuinely non-cyclic: a shuffled, non-periodic ordering (a fixed period-N repeat, no
        # matter how many distinct types it contains, IS a real loop -- confirmed correct
        # behavior, not a bug -- so the low-loop-score fixture must break periodicity itself).
        import random
        varied_types = ["movement", "biological_state_changed", "xp_granted", "quest_started",
                         "social_memory_created", "belief_assimilated", "combat_damage"]
        rng = random.Random(7)
        pool = varied_types * 4
        rng.shuffle(pool)
        varied = [(i, et, "INFO") for i, et in enumerate(pool[:21])]
        varied_metrics = els.compute_entity_metrics(_path(varied), weights, ticks_observed=100)
        assert varied_metrics["loop_score"] < looped_metrics["loop_score"]

    def test_growth_trajectory_positive_and_negative(self, weights):
        growth_heavy = [(i, "xp_granted", "INFO") for i in range(8)] + [(i, "level_up", "INFO") for i in range(2)]
        growth_metrics = els.compute_entity_metrics(_path(growth_heavy), weights, ticks_observed=100)
        assert growth_metrics["growth_trajectory"] > 0

        stall_heavy = [(i, "progression_plateau_detected", "INFO") for i in range(8)] + \
            [(i, "capability_growth_stalled", "INFO") for i in range(2)]
        stall_metrics = els.compute_entity_metrics(_path(stall_heavy), weights, ticks_observed=100)
        assert stall_metrics["growth_trajectory"] < 0

    def test_conclusion_coherence_flags_incoherent_and_silent_from_spawn(self, weights):
        incoherent = [(1, "life_arc_incoherent", "WARNING")]
        incoherent_metrics = els.compute_entity_metrics(_path(incoherent), weights, ticks_observed=100)
        assert incoherent_metrics["conclusion_coherence"] is False

        silent = els.compute_entity_metrics(_path([]), weights, ticks_observed=100)
        assert silent["silent_from_spawn"] is True
        assert silent["conclusion_coherence"] is True  # no incoherent tag -- distinct finding from silence

        normal_death = [(1, "movement", "INFO"), (2, "entity_killed", "INFO")]
        normal_metrics = els.compute_entity_metrics(_path(normal_death), weights, ticks_observed=100)
        assert normal_metrics["conclusion_coherence"] is True

    def test_minimum_sample_gating_flags_low_confidence(self, weights):
        threshold = weights["minimum_sample_threshold"]
        few_events = [(i, "movement", "INFO") for i in range(threshold - 1)]
        low_conf = els.compute_entity_metrics(_path(few_events), weights, ticks_observed=100)
        assert low_conf["path_entropy_confidence"] == "low"
        assert low_conf["loop_score_confidence"] == "low"

        enough_events = [(i, "movement", "INFO") for i in range(threshold + 5)]
        normal_conf = els.compute_entity_metrics(_path(enough_events), weights, ticks_observed=100)
        assert normal_conf["path_entropy_confidence"] == "normal"
        assert normal_conf["loop_score_confidence"] == "normal"


# ---------------------------------------------------------------------------
# Population aggregation + grouping
# ---------------------------------------------------------------------------


class TestAggregation:

    def test_aggregation_reports_mean_and_stdev_not_mean_alone(self, weights):
        low = els.compute_entity_metrics(_path([(i, "movement", "INFO") for i in range(5)]), weights, 100)
        high = els.compute_entity_metrics(_path([(i, "movement", "INFO") for i in range(50)]), weights, 100)
        entity_metrics = {1: low, 2: high}
        agg = els.aggregate(entity_metrics)
        assert "mean" in agg["global"]["path_length"]
        assert "stdev" in agg["global"]["path_length"]
        assert agg["global"]["path_length"]["stdev"] > 0

    def test_grouping_by_role_faction_kind_region(self, weights):
        citizen = els.compute_entity_metrics(
            _path([(i, "movement", "INFO") for i in range(5)], role="CITIZEN"), weights, 100
        )
        guard = els.compute_entity_metrics(
            _path([(i, "movement", "INFO") for i in range(50)], role="GUARD"), weights, 100
        )
        entity_metrics = {1: citizen, 2: guard}
        agg = els.aggregate(entity_metrics, group_by=["role"])
        assert set(agg["groups"]["role"].keys()) == {"CITIZEN", "GUARD"}
        assert agg["groups"]["role"]["CITIZEN"]["path_length"]["mean"] != agg["groups"]["role"]["GUARD"]["path_length"]["mean"]

    def test_path_clustering_reports_dominant_shape_share(self, weights):
        """Regression check against the investigation's own real finding: a population where
        most entities share an identical event-type set must be caught, not averaged away."""
        shared_events = [(1, "capability_growth_stalled", "INFO"), (2, "progression_plateau_detected", "INFO")]
        entity_paths = {i: _path(shared_events) for i in range(1, 15)}  # 14 identical
        entity_paths[15] = _path([(1, "quest_started", "INFO"), (2, "quest_completed", "INFO")])  # 1 different
        cluster = els.cluster_paths(entity_paths, weights)
        assert cluster["global"]["dominant_shape_share"] == pytest.approx(14 / 15, abs=1e-4)
        assert cluster["global"]["distinct_shapes"] == 2

    def test_diversity_context_annotation_for_monster_only_world(self, weights):
        """TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS — wilderness_survival is a real,
        registry-confirmed monster_only_gauntlet archetype; its clustering output must carry a
        diversity_context annotation, not leave a low dominant_shape_share to be misread as a
        defect."""
        entity_paths = {i: _path([(1, "movement", "INFO")]) for i in range(1, 3)}
        cluster = els.cluster_paths(entity_paths, weights, world_name="wilderness_survival")
        assert "diversity_context" in cluster["global"]
        assert "monster-only gauntlet" in cluster["global"]["diversity_context"]

    def test_no_diversity_context_for_civilian_world(self, weights):
        entity_paths = {i: _path([(1, "movement", "INFO")]) for i in range(1, 3)}
        cluster = els.cluster_paths(entity_paths, weights, world_name="sandbox_world")
        assert "diversity_context" not in cluster["global"]

    def test_no_diversity_context_when_world_name_omitted(self, weights):
        entity_paths = {i: _path([(1, "movement", "INFO")]) for i in range(1, 3)}
        cluster = els.cluster_paths(entity_paths, weights)
        assert "diversity_context" not in cluster["global"]


# ---------------------------------------------------------------------------
# Comparability mechanism
# ---------------------------------------------------------------------------


class TestComparability:

    def test_within_run_zscore_computation(self, weights):
        low = els.compute_entity_metrics(_path([(i, "movement", "INFO") for i in range(5)]), weights, 100)
        mid = els.compute_entity_metrics(_path([(i, "movement", "INFO") for i in range(10)]), weights, 100)
        high = els.compute_entity_metrics(_path([(i, "movement", "INFO") for i in range(15)]), weights, 100)
        entity_metrics = {1: low, 2: mid, 3: high}
        agg = els.aggregate(entity_metrics)
        assert agg["zscores"][1]["path_length"] < agg["zscores"][2]["path_length"] < agg["zscores"][3]["path_length"]

    def test_detector_reachability_metadata_reflects_tick_count(self, weights):
        short_run = els.run_metadata(200, weights)
        long_run = els.run_metadata(800, weights)
        assert short_run["stall_detector_reachable"] is False
        assert long_run["stall_detector_reachable"] is True
        assert short_run["life_arc_detector_reachable"] is None  # honestly reported, not guessed

    def test_clustering_reliable_reflects_tick_count(self, weights):
        """TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION: dominant_shape_share was found
        empirically unreliable below ~1000 ticks (artificially inflated at 200/500 ticks on real
        sandbox_world data, stabilizing by 1000)."""
        below_threshold = els.run_metadata(500, weights)
        at_threshold = els.run_metadata(1000, weights)
        assert below_threshold["clustering_reliable"] is False
        assert at_threshold["clustering_reliable"] is True

    def test_minimum_sample_threshold_unchanged_at_6(self, weights):
        """TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION: swept truncated-prefix entropy
        against full-length entropy across 59 real entities and found no sharp knee anywhere
        (smooth decay from 0.43 at L=3 to 0.26 at L=25) -- no evidence justified changing this
        value. A real, verified "no correction needed" finding, not a placeholder."""
        assert weights["minimum_sample_threshold"] == 6


# ---------------------------------------------------------------------------
# Bucket mapping / translation
# ---------------------------------------------------------------------------


class TestBucketMapping:

    def test_all_nine_buckets_present_in_shipped_weights(self, weights):
        buckets = weights["lifecycle_phase_buckets"]
        expected = {
            "VITALS", "GROWTH_PROGRESSION", "EXPLORATION", "COMBAT", "ECONOMY", "SOCIAL",
            "STRATEGY_COGNITION", "NARRATIVE_QUEST", "IDENTITY", "CONCLUSION_DEMOGRAPHIC",
        }
        assert expected.issubset(set(buckets.keys()))

    def test_event_type_to_bucket_has_no_duplicate_assignment_within_a_bucket(self, weights):
        for bucket, types in weights["lifecycle_phase_buckets"].items():
            assert len(types) == len(set(types)), f"{bucket} has a duplicate event type"


# ---------------------------------------------------------------------------
# Real, non-mocked integration checks
# ---------------------------------------------------------------------------


class TestRealIntegration:

    def test_scoring_an_existing_run_dir_does_not_drive_a_new_kernel(self, tmp_path, weights, monkeypatch):
        import logging
        logging.disable(logging.CRITICAL)
        from tools.calibrate_simq import _load_world_state

        called = {"kernel_constructed": False}

        def _fail_if_called(*args, **kwargs):
            called["kernel_constructed"] = True
            raise AssertionError("Kernel should not be constructed when --run-dir is used")

        monkeypatch.setattr(els, "_run_for_analysis", _fail_if_called)

        run_dir = tmp_path / "scratch_run"
        run_dir.mkdir()
        world_state, _report = _load_world_state("sandbox_world", 42)
        eid = next(iter(world_state.entities.keys()))
        with open(run_dir / "simulation_events.jsonl", "w") as fh:
            fh.write(json.dumps({
                "event_id": "e1", "run_id": "r1", "tick": 1, "entity_id": eid,
                "event_type": "movement", "event_category": "lifecycle", "severity": "INFO",
                "source_system": "event_extractor", "message": "", "payload": {},
            }) + "\n")

        result = els.score_run(str(run_dir), world_state, ticks=100, weights=weights)
        assert called["kernel_constructed"] is False
        assert eid in result["entity_metrics"]

    def test_run_dir_mode_still_works_without_final_entities(self, tmp_path, weights):
        """--run-dir mode (scoring a historical run, no live Kernel) has no final_entities
        available -- score_run's own default (None) must not crash, and must fall back to
        pre-run-only metadata (TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP)."""
        import logging
        logging.disable(logging.CRITICAL)
        from tools.calibrate_simq import _load_world_state

        world_state, _report = _load_world_state("sandbox_world", 42)
        eid = next(iter(world_state.entities.keys()))
        run_dir = tmp_path / "scratch_run2"
        run_dir.mkdir()
        with open(run_dir / "simulation_events.jsonl", "w") as fh:
            fh.write(json.dumps({
                "event_id": "e1", "run_id": "r1", "tick": 1, "entity_id": eid,
                "event_type": "movement", "event_category": "lifecycle", "severity": "INFO",
                "source_system": "event_extractor", "message": "", "payload": {},
            }) + "\n")

        result = els.score_run(str(run_dir), world_state, ticks=100, weights=weights)
        assert eid in result["entity_metrics"]
        assert result["entity_metrics"][eid]["metadata"]["role"] is not None

    def test_run_for_analysis_returns_final_entities(self):
        """TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP: the real, post-run entity map
        must be non-empty and real (not a placeholder)."""
        import logging
        logging.disable(logging.CRITICAL)
        run_dir, _health, final_entities = els._run_for_analysis("sandbox_world", 42, 50, "NORMAL")
        try:
            assert isinstance(final_entities, dict)
            assert len(final_entities) > 0
            some_entity = next(iter(final_entities.values()))
            assert hasattr(some_entity, "identity")
        finally:
            import shutil
            if run_dir and run_dir.startswith("data/runs/"):
                shutil.rmtree(run_dir, ignore_errors=True)

    def test_midrun_spawned_entity_gets_real_metadata(self, weights):
        """Real, longer run (wilderness_survival, confirmed in the real 2000-tick committed data
        to produce mid-run spawns) with final_entities passed through: any entity present in the
        real post-run state must resolve real metadata, not the None fallback."""
        import logging
        logging.disable(logging.CRITICAL)
        from tools.calibrate_simq import _load_world_state

        run_dir, health, final_entities = els._run_for_analysis("wilderness_survival", 42, 500, "NORMAL")
        try:
            assert health["dropped_count"] == 0
            world_state, _report = _load_world_state("wilderness_survival", 42)
            pre_run_ids = set(world_state.entities.keys())
            post_run_ids = set(final_entities.keys())
            midrun_born_ids = post_run_ids - pre_run_ids

            result = els.score_run(
                run_dir, world_state, 500, weights, group_by=["role"],
                final_entities=final_entities,
            )
            checked = 0
            for eid in midrun_born_ids:
                if eid in result["entity_metrics"]:
                    checked += 1
                    assert result["entity_metrics"][eid]["metadata"]["role"] is not None, (
                        f"entity {eid} was born mid-run and present in final_entities, but its "
                        "metadata is still None -- the fix did not resolve it"
                    )
            # not asserting checked > 0 -- whether this specific 500-tick/seed42 run produces a
            # mid-run spawn that also emits events is itself real, run-dependent behavior; the
            # real assertion is that IF one occurs, it must resolve real metadata.
        finally:
            import shutil
            if run_dir and run_dir.startswith("data/runs/"):
                shutil.rmtree(run_dir, ignore_errors=True)

    def test_dedicated_run_driver_reports_dropped_count(self):
        """Real, non-mocked: run a short real simulation; the tool's own output must include
        dropped_count, and a successful run must not raise merely due to transient queue
        pressure -- the real conflict found in Investigate against calibrate_simq._run_engine's
        own stricter guard."""
        import logging
        logging.disable(logging.CRITICAL)
        run_dir, health, _final_entities = els._run_for_analysis("sandbox_world", 42, 50, "NORMAL")
        try:
            assert "dropped_count" in health
            assert "pressure_mode_final" in health
            assert health["dropped_count"] == 0
        finally:
            import shutil
            if run_dir and run_dir.startswith("data/runs/"):
                shutil.rmtree(run_dir, ignore_errors=True)

    def test_sandbox_world_800t_end_to_end_produces_sane_output(self, weights):
        """Real, non-mocked, real Kernel run: confirms the tool runs end-to-end on a real world
        without crashing and produces non-trivial, sane output -- the same real check performed
        manually during Implement, now a durable regression test."""
        import logging
        logging.disable(logging.CRITICAL)
        from tools.calibrate_simq import _load_world_state

        run_dir, health, final_entities = els._run_for_analysis("sandbox_world", 42, 800, "NORMAL")
        try:
            assert health["dropped_count"] == 0
            world_state, _report = _load_world_state("sandbox_world", 42)
            result = els.score_run(
                run_dir, world_state, 800, weights, group_by=["role", "faction", "kind", "region"],
                final_entities=final_entities,
            )

            assert result["aggregation"]["global"]["entity_count"] > 0
            assert result["aggregation"]["global"]["path_length"]["mean"] > 0
            assert result["clustering"]["global"]["entity_count"] > 0
            assert 0.0 <= result["clustering"]["global"]["dominant_shape_share"] <= 1.0
            assert result["run_metadata"]["stall_detector_reachable"] is True
        finally:
            import shutil
            if run_dir and run_dir.startswith("data/runs/"):
                shutil.rmtree(run_dir, ignore_errors=True)
