from __future__ import annotations
import logging
from typing import Any, Iterator
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily

logger = logging.getLogger(__name__)

class PrometheusMetricsCollector:
    """
    Custom Prometheus collector for V2 RPG Simulation Engine.
    Reads safe snapshots from V2EngineManager to expose telemetry in standard text format.
    """
    def __init__(self, manager: Any) -> None:
        self._manager = manager

    def collect(self) -> Iterator[Any]:
        """Collect and yield metrics in Prometheus family formats."""
        try:
            snapshot = self._manager.get_metrics_snapshot()
        except Exception:
            logger.exception("Failed to retrieve metrics snapshot from engine manager")
            return

        if not snapshot:
            return

        # P0 Metrics
        # 1. sim_current_tick
        current_tick = GaugeMetricFamily("sim_current_tick", "Current simulation tick index")
        current_tick.add_metric([], snapshot.get("tick", 0))
        yield current_tick

        # 2. sim_active_entities
        active_entities = GaugeMetricFamily("sim_active_entities", "Number of currently active/alive entities")
        active_entities.add_metric([], snapshot.get("active_entities", 0))
        yield active_entities

        # 3. sim_ticks_per_second
        tps = GaugeMetricFamily("sim_ticks_per_second", "Measured ticks completed per second")
        tps.add_metric([], snapshot.get("tps", 0.0))
        yield tps

        # 4. sim_tick_compute_ms
        compute_ms = GaugeMetricFamily("sim_tick_compute_ms", "Execution latency of the last tick in milliseconds")
        compute_ms.add_metric([], snapshot.get("tick_compute_ms", 0.0))
        yield compute_ms

        # 5. sim_worker_utilization
        worker_util = GaugeMetricFamily("sim_worker_utilization", "Worker pool utilization ratio")
        worker_util.add_metric([], snapshot.get("worker_utilization", 0.0))
        yield worker_util

        # 6. sim_queue_utilization
        queue_util = GaugeMetricFamily("sim_queue_utilization", "Worker task queue utilization ratio")
        queue_util.add_metric([], snapshot.get("queue_utilization", 0.0))
        yield queue_util

        # 7. sim_memory_rss_bytes
        memory_rss = GaugeMetricFamily("sim_memory_rss_bytes", "Resident Set Size (RSS) memory utilization in bytes")
        memory_rss.add_metric([], snapshot.get("memory_rss_bytes", 0.0))
        yield memory_rss

        # 8. sim_work_debt_total
        work_debt = GaugeMetricFamily("sim_work_debt_total", "Total outstanding work debt")
        work_debt.add_metric([], snapshot.get("work_debt_total", 0))
        yield work_debt

        # 9. sim_governor_mode
        gov_mode = GaugeMetricFamily("sim_governor_mode", "Active governor engine operational mode")
        gov_mode.add_metric([], snapshot.get("governor_mode", 0))
        yield gov_mode

        # 10. sim_gold_circulation_total
        gold_circ = GaugeMetricFamily("sim_gold_circulation_total", "Total gold in circulation across all entity inventories")
        gold_circ.add_metric([], snapshot.get("gold_circulation_total", 0.0))
        yield gold_circ

        # P1 Metrics
        # 11. sim_rejection_count_total
        rejections = GaugeMetricFamily("sim_rejection_count_total", "Total action rejections grouped by reason", labels=["reason"])
        for reason, count in snapshot.get("rejection_counts", {}).items():
            rejections.add_metric([reason], count)
        yield rejections

        # 12. sim_quest_status_count
        quests = GaugeMetricFamily("sim_quest_status_count", "Active quests grouped by current lifecycle status", labels=["status"])
        for status, count in snapshot.get("quest_status_counts", {}).items():
            quests.add_metric([status], count)
        yield quests

        # 13. sim_dropped_work_delta
        dropped = GaugeMetricFamily("sim_dropped_work_delta", "Work items shed in the current tick")
        dropped.add_metric([], snapshot.get("dropped_work_delta", 0))
        yield dropped

        # 14. sim_errors_total
        errors = CounterMetricFamily("sim_errors_total", "Cumulative simulation tick processing exceptions")
        errors.add_metric([], snapshot.get("errors_total", 0))
        yield errors

        # Phase Timings (sim_phase_duration_seconds)
        phase_duration = GaugeMetricFamily("sim_phase_duration_seconds", "Compute duration of engine phases in seconds", labels=["phase"])
        for phase, ms in snapshot.get("phase_costs_ms", {}).items():
            phase_duration.add_metric([phase], ms / 1000.0)
        yield phase_duration

        # 15. sim_hard_law_violations_total
        violations_total = CounterMetricFamily(
            "sim_hard_law_violations_total", 
            "Cumulative count of hard law violations", 
            labels=["law_id", "severity"]
        )
        for law_id, count in snapshot.get("hard_law_violations_cumulative", {}).items():
            violations_total.add_metric([law_id, "ERROR"], count)
        yield violations_total

        # 16. sim_hard_law_last_violation_tick
        last_violation = GaugeMetricFamily(
            "sim_hard_law_last_violation_tick",
            "Tick at which the last hard law violation occurred"
        )
        last_violation.add_metric([], snapshot.get("last_hard_law_violation_tick", -1))
        yield last_violation

        # Grafana Dashboard Alignment metrics
        # 17. sim_world_difficulty_mult
        world_diff = GaugeMetricFamily(
            "sim_world_difficulty_mult",
            "Active world simulation difficulty multiplier coefficient"
        )
        world_diff.add_metric([], snapshot.get("world_difficulty_mult", 1.0))
        yield world_diff

        # 18. sim_faction_population
        faction_pop = GaugeMetricFamily(
            "sim_faction_population",
            "Current entity populations grouped by faction",
            labels=["faction_id"]
        )
        for fid, count in snapshot.get("faction_population", {}).items():
            faction_pop.add_metric([str(fid)], count)
        yield faction_pop

        # 19. sim_entity_level_distribution
        lvl_dist = GaugeMetricFamily(
            "sim_entity_level_distribution",
            "Current entity count distribution grouped by level",
            labels=["level"]
        )
        for lvl, count in snapshot.get("entity_level_distribution", {}).items():
            lvl_dist.add_metric([str(lvl)], count)
        yield lvl_dist

        # 20. sim_items_crafted_total
        items_crafted = CounterMetricFamily(
            "sim_items_crafted_total",
            "Cumulative count of crafted items total"
        )
        items_crafted.add_metric([], snapshot.get("items_crafted_total", 0))
        yield items_crafted

        # 21. sim_shop_transactions_total
        shop_trans = CounterMetricFamily(
            "sim_shop_transactions_total",
            "Cumulative count of shop transactions total"
        )
        shop_trans.add_metric([], snapshot.get("shop_transactions_total", 0))
        yield shop_trans

        # 22. sim_combat_events_total
        combat_total = CounterMetricFamily(
            "sim_combat_events_total",
            "Cumulative count of combat events total"
        )
        combat_total.add_metric([], snapshot.get("combat_events_total", 0))
        yield combat_total

        # 23. sim_skill_events_total
        skill_total = CounterMetricFamily(
            "sim_skill_events_total",
            "Cumulative count of skill events total"
        )
        skill_total.add_metric([], snapshot.get("skill_events_total", 0))
        yield skill_total
