"""Adapter for converting CognitionGraph to Cytoscape.js format. [MILESTONE 6]

This module provides utilities to transform the canonical cognition graph 
into the element structure required by the Cytoscape.js visualization library.
"""

from __future__ import annotations
from typing import Any
from src.core.models.cognition_graph import CognitionGraph

class CytoscapeAdapter:
    """Transformation logic for Cytoscape.js JSON format."""

    @staticmethod
    def to_cytoscape_json(graph: CognitionGraph) -> dict[str, Any]:
        """Convert a CognitionGraph to Cytoscape.js elements JSON."""
        
        nodes = []
        for node in graph.nodes:
            # Flatten attributes into data for cytoscape
            data = {
                "id": node.node_id,
                "label": node.label,
                "kind": node.kind,
            }
            # Append any attributes directly to data
            data.update(node.attributes)
            
            nodes.append({"data": data})

        edges = []
        for edge in graph.edges:
            data = {
                "id": edge.edge_id,
                "source": edge.source_id,
                "target": edge.target_id,
                "kind": edge.kind,
                "label": edge.label or edge.kind
            }
            # Append any attributes
            data.update(edge.attributes)
            
            edges.append({"data": data})

        return {
            "elements": {
                "nodes": nodes,
                "edges": edges
            },
            "metadata": {
                "entity_id": graph.entity_id,
                "tick": graph.tick,
                "version": graph.version,
                "exported_at_tick": graph.exported_at_tick
            }
        }
