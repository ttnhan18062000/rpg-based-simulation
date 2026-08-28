import dataclasses

from src.core.worker_protocol import WorkerPacket


def test_worker_packet_has_no_dead_town_center_field():
    """WorkerPacket.town_center was confirmed dead duplicate state (zero real consumers,
    written every tick for every dispatched work item) and removed
    (TCK-20260824-TOWN-CENTER-POINTER-FIX). Guards against it silently reappearing without a
    real consumer."""
    field_names = {f.name for f in dataclasses.fields(WorkerPacket)}
    assert "town_center" not in field_names
