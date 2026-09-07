import networkx as nx
from typing import List, Dict, Any, Optional

class DependencyGraph:
    """
    Normalized Graph Model using NetworkX.
    Represents nodes (Project, Component, SourceFile, CryptoAsset, Evidence, RiskAssessment, Recommendation, MigrationTask, etc.)
    and deterministic edges with provenance metadata.
    """
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node_id: str, node_type: str, label: str, metadata: Optional[Dict[str, Any]] = None):
        self.graph.add_node(
            node_id,
            id=node_id,
            type=node_type,
            label=label,
            metadata=metadata or {}
        )

    def add_asset_node(self, asset_id: str, name: str, algorithm: str, asset_type: str, metadata: Optional[Dict[str, Any]] = None):
        node_metadata = metadata or {}
        node_metadata.update({"algorithm": algorithm, "asset_type": asset_type})
        self.add_node(node_id=asset_id, node_type="CryptoAsset", label=name, metadata=node_metadata)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        provenance: str = "deterministic",
        properties: Optional[Dict[str, Any]] = None
    ):
        if source_id in self.graph and target_id in self.graph:
            self.graph.add_edge(
                source_id,
                target_id,
                relationship=relationship,
                provenance=provenance,
                **(properties or {})
            )

    def add_dependency(self, source_asset_id: str, target_asset_id: str, relationship: str = "depends_on", provenance: str = "deterministic"):
        self.add_edge(source_asset_id, target_asset_id, relationship=relationship, provenance=provenance)

    def compute_centrality(self) -> Dict[str, float]:
        if len(self.graph.nodes) == 0:
            return {}
        try:
            return nx.degree_centrality(self.graph)
        except Exception:
            return {node: 0.0 for node in self.graph.nodes}

    def analyze_impact(self, node_id: str) -> List[str]:
        if node_id not in self.graph:
            return []
        descendants = nx.descendants(self.graph, node_id)
        return list(descendants)

    def to_dict(self) -> Dict[str, Any]:
        centralities = self.compute_centrality()
        nodes = []
        for n, data in self.graph.nodes(data=True):
            node_info = {
                "id": n,
                "type": data.get("type", "Unknown"),
                "label": data.get("label", n),
                "centrality": round(centralities.get(n, 0.0), 4),
                "metadata": data.get("metadata", {})
            }
            nodes.append(node_info)

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edge_info = {
                "source": u,
                "target": v,
                "relationship": data.get("relationship", "relates_to"),
                "provenance": data.get("provenance", "deterministic")
            }
            edges.append(edge_info)

        return {
            "nodes": nodes,
            "edges": edges
        }
