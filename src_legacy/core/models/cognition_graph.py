"""Canonical models for the Entity Cognition Graph. [MILESTONE 6]

This module defines the structural schema for exporting an entity's 
internal cognitive state as a deterministic graph.
"""

from __future__ import annotations
from typing import Any
from pydantic import Field, ConfigDict
from src_legacy.core.models.base import SimulationModel

class GraphNode(SimulationModel):
    """A node in the cognition graph representing a cognitive concept."""
    model_config = ConfigDict(extra='forbid')
    
    node_id: str
    kind: str # 'entity', 'directive', 'project', 'objective', 'concern', 'blocker', 'lead', 'contract'
    label: str
    attributes: dict[str, Any] = Field(default_factory=dict)

class GraphEdge(SimulationModel):
    """An edge representing a relationship between cognitive concepts."""
    model_config = ConfigDict(extra='forbid')
    
    edge_id: str
    source_id: str
    target_id: str
    kind: str # 'owns', 'pursuing', 'blocked_by', 'interrupted_by', 'informed_by'
    label: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)

class CognitionGraph(SimulationModel):
    """A deterministic export of an entity's strategic mind."""
    model_config = ConfigDict(extra='forbid')
    
    entity_id: int
    tick: int
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    
    # Metadata for the export
    version: str = "1.0.0"
    exported_at_tick: int = 0

def rebuild_graph_models():
    """Resolve forward references."""
    GraphNode.model_rebuild()
    GraphEdge.model_rebuild()
    CognitionGraph.model_rebuild()

rebuild_graph_models()
