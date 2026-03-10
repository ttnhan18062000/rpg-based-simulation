"""Tests for the /api/v1/stream Server-Sent Events endpoint."""

import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.dependencies import get_engine_manager
from src.config import SimulationConfig

import asyncio

import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis using an in-memory queue so testcontainers isn't required locally."""
    stream_data = []
    stream_event = threading.Event()

    async def mock_xread(streams, count=None, block=None):
        last_id = streams.get("sim:stream")
        start_idx = 0
        if last_id != "$" and last_id is not None:
             try:
                 start_idx = int(str(last_id).split('-')[0]) + 1
             except ValueError:
                 pass
        
        # We must use asyncio.to_thread or brief async sleeps so we don't block the event loop
        # waiting on a threading.Event
        if start_idx >= len(stream_data) and block:
            deadline = asyncio.get_running_loop().time() + (block / 1000.0)
            while start_idx >= len(stream_data) and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.01)
                
        if start_idx < len(stream_data):
            messages = []
            limit = count if count else len(stream_data)
            for i in range(start_idx, min(start_idx + limit, len(stream_data))):
                messages.append((f"{i}-0", stream_data[i]))
            
            return [["sim:stream", messages]]
        return []

    def mock_xadd(name, fields):
        stream_data.append(fields)
        stream_event.set()

    with patch("src.api.redis_client.get_async_redis") as mock_async, \
         patch("src.api.redis_client.get_sync_redis") as mock_sync:
        
        async_r = AsyncMock()
        async_r.xread.side_effect = mock_xread
        
        sync_r = MagicMock()
        sync_r.xadd.side_effect = mock_xadd
        
        mock_async.return_value = async_r
        mock_sync.return_value = sync_r
        
        yield async_r, sync_r

@pytest.fixture
def test_app(load_registries):
    """Create a FastAPI app instance with a fast tick rate for testing."""
    config = SimulationConfig(
        world_seed=42,
        grid_width=32,
        grid_height=32,
        town_radius=2,
        num_camps=1,
        initial_entity_count=2,
    )
    app = create_app(config)
    return app

def test_stream_delta_updates(test_app):
    """Test that the /stream endpoint returns SSE delta payloads."""
    # We must use the app's lifespan to initialize the EngineManager
    with TestClient(test_app) as client:
        # Start the stream request
        with client.stream("GET", "/api/v1/stream") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # Read the first event (full snapshot)
            lines = []
            for line in response.iter_lines():
                if line:
                    lines.append(line)
                if not line and lines: # Empty line marks end of event
                    break
                    
            assert len(lines) > 0
            assert lines[0].startswith("data: ")
            
            data = json.loads(lines[0][6:])
            assert "tick" in data
            assert "changed" in data
            assert "removed" in data
            assert "events" in data
            
            # Since this is the initial snapshot, 'changed' should contain all living entities
            assert len(data["changed"]) > 0
            
            # Trigger a manual tick to generate a delta
            manager = test_app.dependency_overrides.get(get_engine_manager, get_engine_manager)()
            manager.step()
            
            # Read the next event (delta)
            lines = []
            for line in response.iter_lines():
                if line:
                    lines.append(line)
                if not line and lines:
                    break
                    
            if lines:
                data = json.loads(lines[0][6:])
                assert "tick" in data
                assert "changed" in data
                # Delta should only contain entities that changed (moved, etc.)
                # If they didn't do anything, it might be empty or heartbeat
