"""
src/domains/campaigns/reports.py
───────────────────────────────────────────────────────────────────────────────
Phase 9 — Campaign Report Generator.
"""

import json
from typing import Dict, Any
from src.domains.campaigns.schema import CampaignResult


class CampaignReportGenerator:
    def generate_markdown_summary(self, result: CampaignResult) -> str:
        """Generates a detailed, reader-friendly markdown report of the campaign."""
        score = result.semantic_scorecard

        md = f"""# Campaign Semantic Evaluation: {result.campaign_id}

## 1. Overview
- **Campaign ID**: {result.campaign_id}
- **Total Ticks**: {result.performance_summary.get("campaign_ticks", 0)}
- **Entity Population**: {result.performance_summary.get("entity_count", 0)}
- **Overall Verdict**: **{score.verdict.upper()}**

## 2. Semantic Scorecard
- **Self Model Usage**: `{score.self_model_usage}`
- **Route Decision Quality**: `{score.route_decision_quality}`
- **Combat Learning**: `{score.combat_learning}`
- **Information Learning**: `{score.information_learning}`
- **Reward Conversion**: `{score.reward_conversion}`
- **Cooperation Usage**: `{score.cooperation_usage}`
- **World Feedback Usage**: `{score.world_feedback_usage}`
- **Reputation Inheritance Check**: `{score.reputation_inheritance_check}`
- **Nemesis Transfer Check**: `{score.nemesis_transfer_check}`
- **Behavior Change Proofs Detected**: {score.behavior_change_proofs}
- **Route Diversity Score**: {score.route_diversity_score:.2f}
- **Stagnant Entity Ratio**: {score.stagnant_entity_ratio:.2%}
- **Forbidden Behaviors Triggered**: {score.forbidden_behavior_count}

## 3. Entity Arc Highlights
"""
        for report in result.entity_arc_reports[:5]:
            md += f"""### Entity #{report.entity_id}
- **Arc Families**: {", ".join(report.arc_types)}
- **Behavior Change Proofs**: {len(report.behavior_change_proofs)}
- **Major Events**: {len(report.major_events)}
- **Evidence IDs**: {", ".join(report.evidence_event_ids[:3])}...
"""

        md += "\n## 4. World Arcs\n"
        for war in result.world_arc_reports:
            md += f"- **Region `{war.region}`**: {war.details.get('explanation', 'No detailed notes')}\n"

        md += "\n## 5. Route Diversity Distribution\n"
        for arc, count in result.route_diversity.route_family_distribution.items():
            md += f"- `{arc}`: {count} entities\n"

        if result.forbidden_behaviors:
            md += "\n## 6. Forbidden Behaviors Detected\n"
            for fb in result.forbidden_behaviors[:5]:
                md += f"- **{fb.rule_violated}** on Entity #{fb.entity_id} at tick {fb.tick}: {fb.explanation}\n"
        else:
            md += "\n## 6. Forbidden Behaviors Detected\n- None\n"

        md += f"""
## 7. Performance Budget Summary
- **Average Tick Latency**: {result.performance_summary.get("avg_tick_ms", 0.0):.2f} ms
- **95th Percentile Latency**: {result.performance_summary.get("p95_tick_ms", 0.0):.2f} ms
- **Arc Classification Time**: {result.performance_summary.get("arc_classification_ms", 0.0):.2f} ms
- **Scorecard Generation Time**: {result.performance_summary.get("scorecard_generation_ms", 0.0):.2f} ms
"""
        return md

    def write_reports(self, result: CampaignResult, output_dir: str) -> Dict[str, str]:
        """Writes markdown and JSON scorecard files to output directory."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        md_content = self.generate_markdown_summary(result)
        md_path = os.path.join(output_dir, "campaign_summary.md")
        with open(md_path, "w") as f:
            f.write(md_content)

        # Build JSON scorecard dictionary
        scorecard_dict = {
            "campaign_id": result.campaign_id,
            "verdict": result.semantic_scorecard.verdict,
            "scorecard": {
                "self_model_usage": result.semantic_scorecard.self_model_usage,
                "route_decision_quality": result.semantic_scorecard.route_decision_quality,
                "combat_learning": result.semantic_scorecard.combat_learning,
                "information_learning": result.semantic_scorecard.information_learning,
                "reward_conversion": result.semantic_scorecard.reward_conversion,
                "cooperation_usage": result.semantic_scorecard.cooperation_usage,
                "world_feedback_usage": result.semantic_scorecard.world_feedback_usage,
                "reputation_inheritance_check": result.semantic_scorecard.reputation_inheritance_check,
                "nemesis_transfer_check": result.semantic_scorecard.nemesis_transfer_check,
                "behavior_change_proofs": result.semantic_scorecard.behavior_change_proofs,
                "route_diversity_score": result.semantic_scorecard.route_diversity_score,
                "stagnant_entity_ratio": result.semantic_scorecard.stagnant_entity_ratio,
                "forbidden_behavior_count": result.semantic_scorecard.forbidden_behavior_count
            },
            "performance": result.performance_summary
        }
        json_path = os.path.join(output_dir, "campaign_scorecard.json")
        with open(json_path, "w") as f:
            json.dump(scorecard_dict, f, indent=2)

        return {
            "markdown": md_path,
            "json": json_path
        }
