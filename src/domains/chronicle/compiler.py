"""
src/domains/chronicle/compiler.py
────────────────────────────────────────────────────────────────────────────────
ChronicleCompiler — top-level entry point that chains the full Chronicle pipeline:
  load NarrativeLedger → score/group → render markdown → render json → write files.

Implemented by E51D (TCK-20260619-E51D-RENDERER).
Requires all of E51A (scorer), E51B (grouper), E51C (namer), E51D (renderer).
Gates E51E (REST API).

Design constraints:
  - Stateless coordinator: no durable state, no engine imports.
  - compile() is the sole public entry point.
  - Returns (markdown_str, json_dict) for testability without disk I/O.
  - File writes use utf-8 encoding. Parent output_dir must exist.
  - Monitoring failure must never raise — file writes are best-effort.
"""
from __future__ import annotations

import json
import os

from src.domains.campaigns.state import CampaignState
from src.domains.chronicle.grouper import ChronicleGrouper, ChronicleHierarchy
from src.domains.chronicle.renderer import ChronicleRenderer


class ChronicleCompiler:
    """Top-level orchestrator for the Chronicle generation pipeline.

    Usage::

        compiler = ChronicleCompiler()
        md, data = compiler.compile(campaign_state, output_dir="/tmp/chronicle")
        # → writes Chronicle.md and chronicle.json to /tmp/chronicle/
        # → returns the text and dict for inspection / testing
    """

    def compile(
        self,
        campaign_state: CampaignState,
        output_dir: str,
        entity_names: dict[int, str] | None = None,
    ) -> tuple[str, dict]:
        """Run the full chronicle pipeline and write output files.

        Pipeline:
          1. Load entries from campaign_state.narrative_ledger.
          2. Group via ChronicleGrouper (filters unworthy events internally).
          3. Render to Markdown string via ChronicleRenderer.render_markdown().
          4. Render to JSON dict via ChronicleRenderer.render_json().
          5. Write Chronicle.md and chronicle.json to output_dir.

        Args:
            campaign_state: The CampaignState whose narrative_ledger to compile.
            output_dir: Directory path where Chronicle.md and chronicle.json are
                        written. Directory must already exist.
            entity_names: Optional mapping of int entity id → display name.
                          Passed through to ChronicleNamer for milestone titles.

        Returns:
            Tuple of (markdown_str, json_dict) — the rendered outputs. Files are
            written as a side effect.

        Raises:
            OSError: If output_dir is not writable.
        """
        names = entity_names or {}
        campaign_id = campaign_state.campaign_id

        # Step 1 + 2: load + group
        grouper = ChronicleGrouper()
        hierarchy: ChronicleHierarchy = grouper.group(
            list(campaign_state.narrative_ledger)
        )

        # Step 3: render markdown
        md_str = ChronicleRenderer.render_markdown(hierarchy, campaign_id, names)

        # Step 4: render json
        json_dict = ChronicleRenderer.render_json(hierarchy, campaign_id, names)

        # Step 5: write files
        self._write_markdown(output_dir, md_str)
        self._write_json(output_dir, json_dict)

        return md_str, json_dict

    # ── private file I/O ───────────────────────────────────────────────────────

    @staticmethod
    def _write_markdown(output_dir: str, content: str) -> None:
        path = os.path.join(output_dir, "Chronicle.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def _write_json(output_dir: str, data: dict) -> None:
        path = os.path.join(output_dir, "chronicle.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
