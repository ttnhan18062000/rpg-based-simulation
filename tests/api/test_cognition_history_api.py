from __future__ import annotations
import os
import json
import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from src.api.routes.history import (
    get_entity_snapshots,
    get_entity_diffs,
    get_entity_features,
    get_run_patterns
)

@pytest.fixture
def mock_run_service():
    with patch("src.api.routes.history.run_service") as mock_service:
        yield mock_service


@pytest.mark.anyio
async def test_get_entity_snapshots_success(mock_run_service):
    # Setup mock return value
    mock_run_service.get_entity_snapshots.return_value = {
        "snapshots": [
            {"tick": 10, "entity_id": 1, "objective": "test_obj", "nodes_count": 5}
        ],
        "total": 1,
        "page": 1,
        "page_size": 20
    }

    # Call directly
    res = await get_entity_snapshots(
        run_id="run_123",
        entity_id="1",
        page=1,
        page_size=20,
        full_graph=False
    )

    assert res["total"] == 1
    assert len(res["snapshots"]) == 1
    assert res["snapshots"][0]["entity_id"] == 1
    mock_run_service.get_entity_snapshots.assert_called_once_with(
        run_id="run_123",
        entity_id="1",
        page=1,
        page_size=20,
        full_graph=False
    )


@pytest.mark.anyio
async def test_get_entity_snapshots_path_traversal(mock_run_service):
    # Simulate a value error from query service
    mock_run_service.get_entity_snapshots.side_effect = ValueError("Invalid identifier security warning")

    with pytest.raises(HTTPException) as exc:
        await get_entity_snapshots(run_id="../../etc/passwd", entity_id="1")
    
    assert exc.value.status_code == 400
    assert "Invalid identifier" in exc.value.detail


@pytest.mark.anyio
async def test_get_entity_snapshots_missing_run(mock_run_service):
    mock_run_service.get_entity_snapshots.side_effect = FileNotFoundError("Manifest not found")

    with pytest.raises(HTTPException) as exc:
        await get_entity_snapshots(run_id="missing_run", entity_id="1")
    
    assert exc.value.status_code == 404
    assert "Manifest not found" in exc.value.detail


@pytest.mark.anyio
async def test_get_entity_diffs_success(mock_run_service):
    mock_run_service.get_entity_diffs.return_value = [
        {"tick": 11, "entity_id": 1, "added_edges": []}
    ]

    res = await get_entity_diffs(run_id="run_123", entity_id="1")
    assert len(res) == 1
    assert res[0]["tick"] == 11
    mock_run_service.get_entity_diffs.assert_called_once_with(run_id="run_123", entity_id="1")


@pytest.mark.anyio
async def test_get_entity_features_success(mock_run_service):
    mock_run_service.get_entity_features.return_value = [
        {"tick": 10, "entity_id": 1, "features": {}}
    ]

    res = await get_entity_features(run_id="run_123", entity_id="1")
    assert len(res) == 1
    mock_run_service.get_entity_features.assert_called_once_with(run_id="run_123", entity_id="1")


@pytest.mark.anyio
async def test_get_run_patterns_success(mock_run_service):
    mock_run_service.get_run_patterns.return_value = [
        {"pattern_id": "P01", "severity": "WARNING"}
    ]

    res = await get_run_patterns(run_id="run_123")
    assert len(res) == 1
    assert res[0]["pattern_id"] == "P01"
    mock_run_service.get_run_patterns.assert_called_once_with(run_id="run_123")
