"""
src/domains/campaigns/spec.py
───────────────────────────────────────────────────────────────────────────────
Phase 9 — Campaign Spec loading, parsing, and normalization.
"""

import yaml
from typing import Any, Dict
from src.domains.campaigns.schema import CampaignSpec, ActorDistribution


class CampaignSpecLoader:
    @staticmethod
    def load_from_yaml(yaml_content: str) -> CampaignSpec:
        """Parses a YAML string into a CampaignSpec."""
        data = yaml.safe_load(yaml_content)
        if not data:
            raise ValueError("Empty or invalid campaign YAML specification.")

        # Ensure required fields
        required_fields = ["campaign_id", "seed", "ticks", "world_pack", "actors"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required campaign spec field: {field}")

        actors_data = data["actors"]
        if "count" not in actors_data or "start_region" not in actors_data or "start_level" not in actors_data:
            raise ValueError("Actors config must contain count, start_region, and start_level.")

        # Validate non-scripted constraint
        if "exact_action_path" in data or "scripted_actions" in data:
            raise ValueError("Campaign spec cannot define an exact scripted action sequence.")

        actor_dist = ActorDistribution(
            count=int(actors_data["count"]),
            start_region=str(actors_data["start_region"]),
            start_level=int(actors_data["start_level"]),
            class_distribution=actors_data.get("class_distribution", {}),
            trait_distribution=actors_data.get("trait_distribution", {})
        )

        spec = CampaignSpec(
            campaign_id=str(data["campaign_id"]),
            seed=int(data["seed"]),
            ticks=int(data["ticks"]),
            world_pack=str(data["world_pack"]),
            actors=actor_dist,
            initial_world_pressures=tuple(data.get("initial_world_pressures", [])),
            expected_arc_families=tuple(data.get("expected_arc_families", [])),
            forbidden_behavior=tuple(data.get("forbidden_behavior", [])),
            performance_budget=data.get("performance_budget", {}),
            scorecard_rules=data.get("scorecard_rules", {})
        )

        # Validate expected arc families
        if not spec.expected_arc_families:
            raise ValueError("expected_arc_families cannot be empty in CampaignSpec.")

        # Validate forbidden behavior
        if not spec.forbidden_behavior:
            raise ValueError("forbidden_behavior rules cannot be empty in CampaignSpec.")

        return spec
