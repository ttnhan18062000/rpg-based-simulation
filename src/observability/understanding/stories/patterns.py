"""
Story patterns — five emergent narrative detectors.

These detect interesting non-bug events. They do NOT affect the health
score. Their purpose is to surface simulation stories for designers.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, List

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.stories.models import StoryCandidate, StoryPattern


class UnexpectedSurvivor(StoryPattern):
    """
    Entity survives far longer than peers in high-mortality conditions.
    Requires combat_kill events with target entity tracking.
    """
    pattern_id = "UnexpectedSurvivor"

    def detect(self, ctx: AnalysisContext) -> List[StoryCandidate]:
        kill_events = ctx.events_by_type("combat_kill")
        if len(kill_events) < 10:
            return []

        killed_ids: set = set()
        for ev in kill_events:
            target = ev.payload.get("target_id") or ev.payload.get("victim_id")
            if target is not None:
                killed_ids.add(target)

        alive_entities_with_combat = set()
        for ev in kill_events:
            eid = ev.entity_id
            if eid is not None and eid not in killed_ids:
                alive_entities_with_combat.add(eid)

        if not alive_entities_with_combat:
            return []

        # Pick top 3 survivors by kill participation
        kill_counts: Dict[int, int] = defaultdict(int)
        for ev in kill_events:
            eid = ev.entity_id
            if eid in alive_entities_with_combat:
                kill_counts[eid] += 1

        survivors = sorted(alive_entities_with_combat, key=lambda e: kill_counts[e], reverse=True)[:3]
        if not survivors:
            return []

        return [StoryCandidate(
            story_type=self.pattern_id,
            title=f"Unexpected Survivor{'s' if len(survivors) > 1 else ''} — {survivors}",
            summary=(
                f"{len(survivors)} entities survived despite high combat mortality "
                f"({len(killed_ids)} total kills). Entity IDs: {survivors}."
            ),
            entities=survivors,
            tick_range=(
                min(ev.tick for ev in kill_events),
                max(ev.tick for ev in kill_events)
            ),
            supporting_events=[f"{len(kill_events)} combat_kill events"],
            interestingness_score=min(0.4 + len(survivors) * 0.1 + kill_counts.get(survivors[0], 0) * 0.01, 1.0),
        )]


class ResourceCrisis(StoryPattern):
    """
    Economy activity drops to zero for a sustained window — a resource crisis.
    """
    pattern_id = "ResourceCrisis"

    CRISIS_TICK_THRESHOLD = 80

    def detect(self, ctx: AnalysisContext) -> List[StoryCandidate]:
        economy_events = ctx.events_by_category("economy")
        if not economy_events:
            return []

        sorted_events = sorted(economy_events, key=lambda e: e.tick)
        max_gap = 0
        gap_start = gap_end = 0
        prev_tick = sorted_events[0].tick

        for ev in sorted_events[1:]:
            gap = ev.tick - prev_tick
            if gap > max_gap:
                max_gap = gap
                gap_start = prev_tick
                gap_end = ev.tick
            prev_tick = ev.tick

        if max_gap < self.CRISIS_TICK_THRESHOLD:
            return []

        score = min(0.3 + (max_gap - self.CRISIS_TICK_THRESHOLD) / 200.0, 0.9)

        return [StoryCandidate(
            story_type=self.pattern_id,
            title=f"Resource Crisis — {max_gap}-Tick Economy Freeze",
            summary=(
                f"The simulation economy halted for {max_gap} consecutive ticks "
                f"(ticks {gap_start}–{gap_end}), suggesting a resource supply chain collapse."
            ),
            tick_range=(gap_start, gap_end),
            supporting_events=[
                f"Economy freeze window: ticks {gap_start}–{gap_end}",
                f"Total economy events: {len(economy_events)}",
            ],
            interestingness_score=score,
        )]


class QuestHero(StoryPattern):
    """
    A single entity completes an unusually high number of quests.
    """
    pattern_id = "QuestHero"

    HERO_QUEST_MINIMUM = 3

    def detect(self, ctx: AnalysisContext) -> List[StoryCandidate]:
        quest_events = ctx.events_by_category("quest")
        completions: Dict[int, int] = defaultdict(int)

        for ev in quest_events:
            status = ev.payload.get("status")
            if status == "completed" and ev.entity_id is not None:
                completions[ev.entity_id] += 1

        if not completions:
            return []

        max_completions = max(completions.values())
        if max_completions < self.HERO_QUEST_MINIMUM:
            return []

        avg_completions = sum(completions.values()) / len(completions)
        hero = max(completions, key=completions.get)

        if completions[hero] <= avg_completions * 1.5:
            return []  # Not remarkable enough

        score = min(0.3 + (max_completions - avg_completions) / max(avg_completions, 1) * 0.15, 0.95)

        return [StoryCandidate(
            story_type=self.pattern_id,
            title=f"Quest Hero — Entity {hero}",
            summary=(
                f"Entity {hero} completed {max_completions} quests, "
                f"far exceeding the average ({avg_completions:.1f}). "
                "This agent may have found an unusually effective strategy."
            ),
            entities=[hero],
            supporting_events=[f"Entity {hero} quest completions: {max_completions}"],
            interestingness_score=score,
        )]


class FactionComeback(StoryPattern):
    """
    A faction that was losing (low kill share early) ends up with high kill share.
    Requires combat_kill events with faction data.
    """
    pattern_id = "FactionComeback"

    def detect(self, ctx: AnalysisContext) -> List[StoryCandidate]:
        kill_events = ctx.events_by_type("combat_kill")
        if len(kill_events) < 20:
            return []

        mid = len(kill_events) // 2
        early_kills: dict = defaultdict(int)
        late_kills: dict = defaultdict(int)

        for ev in kill_events[:mid]:
            f = ev.payload.get("killer_faction") or ev.payload.get("faction")
            if f:
                early_kills[f] += 1

        for ev in kill_events[mid:]:
            f = ev.payload.get("killer_faction") or ev.payload.get("faction")
            if f:
                late_kills[f] += 1

        if not early_kills or not late_kills:
            return []

        early_total = max(sum(early_kills.values()), 1)
        late_total = max(sum(late_kills.values()), 1)

        stories = []
        for faction, early_count in early_kills.items():
            early_share = early_count / early_total
            late_share = late_kills.get(faction, 0) / late_total
            # Comeback: was losing (<30%) in early game, won in late (>50%)
            if early_share < 0.30 and late_share > 0.50:
                score = min(0.4 + (late_share - early_share), 0.95)
                stories.append(StoryCandidate(
                    story_type=self.pattern_id,
                    title=f"Faction Comeback — {faction}",
                    summary=(
                        f"Faction '{faction}' reversed from {early_share:.0%} early kill share "
                        f"to {late_share:.0%} in the second half of the run."
                    ),
                    factions=[faction],
                    tick_range=(kill_events[0].tick, kill_events[-1].tick),
                    supporting_events=[
                        f"Early share: {early_share:.0%}, Late share: {late_share:.0%}",
                    ],
                    interestingness_score=score,
                ))
        return stories


class RegionPowerShift(StoryPattern):
    """
    Detects a region that had high activity early but went quiet, or vice versa.
    Requires events with region_id in payload.
    """
    pattern_id = "RegionPowerShift"

    def detect(self, ctx: AnalysisContext) -> List[StoryCandidate]:
        all_events = ctx.events
        region_events: dict = defaultdict(list)
        for ev in all_events:
            region = ev.payload.get("region_id")
            if region:
                region_events[region].append(ev.tick)

        if not region_events or len(region_events) < 2:
            return []

        final_tick = ctx.final_tick()
        if final_tick == 0:
            return []

        mid = final_tick // 2
        stories = []

        for region, ticks in region_events.items():
            early_count = sum(1 for t in ticks if t <= mid)
            late_count = sum(1 for t in ticks if t > mid)
            total = early_count + late_count
            if total < 10:
                continue

            early_share = early_count / total
            late_share = late_count / total

            # Significant shift: ≥70% in one half
            if early_share >= 0.70 and late_share <= 0.30:
                stories.append(StoryCandidate(
                    story_type=self.pattern_id,
                    title=f"Region '{region}' Abandoned Late-Game",
                    summary=(
                        f"Region '{region}' accounted for {early_share:.0%} of its events in the first half, "
                        "then activity collapsed in the second half."
                    ),
                    regions=[region],
                    tick_range=(min(ticks), max(ticks)),
                    supporting_events=[f"Total events in region: {total}"],
                    interestingness_score=min(0.3 + (early_share - late_share) * 0.5, 0.85),
                ))
            elif late_share >= 0.70 and early_share <= 0.30:
                stories.append(StoryCandidate(
                    story_type=self.pattern_id,
                    title=f"Region '{region}' Emerged Late-Game",
                    summary=(
                        f"Region '{region}' was quiet early ({early_share:.0%} of events), "
                        "then became the dominant activity zone in the second half."
                    ),
                    regions=[region],
                    tick_range=(min(ticks), max(ticks)),
                    supporting_events=[f"Total events in region: {total}"],
                    interestingness_score=min(0.3 + (late_share - early_share) * 0.5, 0.85),
                ))

        return stories


ALL_STORY_PATTERNS = [
    UnexpectedSurvivor(),
    ResourceCrisis(),
    QuestHero(),
    FactionComeback(),
    RegionPowerShift(),
]
