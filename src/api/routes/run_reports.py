"""Compiled run reports: the markdown executive summary of a recorded run."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, Response

from src.api.admission_control import require_admission
from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.observability.reporting.history_query import sanitize_id

router = APIRouter(dependencies=[Depends(require_admission)])


@router.get("/api/v1/observability/history/runs/{run_id}/report")
async def get_run_report(run_id: str):  # noqa: ANN201  # a return annotation would change the pinned OpenAPI document
    """Helper endpoint to dynamically retrieve compile run report markdown."""
    try:
        run_id = sanitize_id(run_id)
        repo = RunArtifactRepository()
        report_path = repo.resolve_path(run_id, "report_md")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                return Response(content=f.read(), media_type="text/markdown")
        else:
            return Response(
                content="# Executive Summary Run Report\n\nNo compiled markdown report found for this run.",
                media_type="text/markdown",
            )
    except Exception as e:  # noqa: BLE001  # any failure to load the report is rendered into the markdown body, not raised
        return Response(content=f"# Error\n\nFailed to load run report: {e}", media_type="text/markdown")
