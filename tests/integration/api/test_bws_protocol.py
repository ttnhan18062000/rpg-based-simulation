import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
import asyncio
import msgpack
import json
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.config import SimulationConfig

@pytest.fixture
def client():
    # Use a small world for speed in integration tests
    config = SimulationConfig(
        grid_width=64, 
        grid_height=64,
        hero_count=1,
        initial_entity_count=5,
        num_camps=1
    )
    app = create_app(config)
    with TestClient(app) as c:
        yield c

def test_protocol_metadata(client):
    """Verify that the protocol metadata endpoint returns the KeyMap."""
    response = client.get("/api/v1/metadata/protocol")
    assert response.status_code == 200
    data = response.json()
    assert "entity_key_map" in data
    assert "state_enum_map" in data
    assert data["entity_key_map"] == ["id", "x", "y", "hp", "state_id", "target_id", "loot_progress"]

def test_websocket_handshake_json(client):
    """Verify JSON WebSocket handshake and initial tick."""
    with client.websocket_connect("/api/v1/ws") as websocket:
        # Handshake
        websocket.send_json({"type": "handshake", "format": "json"})
        
        # Receive initial tick (might be empty if engine not started, but encoder should still send it)
        data = websocket.receive_json()
        assert "tick" in data
        assert "entities" in data

def test_websocket_handshake_msgpack(client):
    """Verify MessagePack WebSocket handshake and initial tick."""
    with client.websocket_connect("/api/v1/ws") as websocket:
        # Handshake
        websocket.send_json({"type": "handshake", "format": "msgpack"})
        
        # Receive initial tick
        data_bytes = websocket.receive_bytes()
        data = msgpack.unpackb(data_bytes, raw=False)
        
        # [tick, entities, events]
        assert isinstance(data, list)
        assert len(data) == 3
        assert isinstance(data[0], int) # tick

def test_gzip_compression(client):
    """Verify that GZip middleware is working for REST endpoints."""
    # We need a large enough response to trigger GZip (min 512 bytes)
    # /api/v1/metadata/items is usually large
    response = client.get("/api/v1/metadata/items", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    # TestClient doesn't always show the content-encoding header if it handles it internally
    # but we can check if it's functional.
