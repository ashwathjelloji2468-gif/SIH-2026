import networkx as nx
from typing import List, Dict, Any

class DependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_asset_node(self, asset_id: str, name: str, algorithm: str, asset_type: str):
        self.graph.add_node(asset_id, name=name, algorithm=algorithm, asset_type=asset_type)

    def add_dependency(self, source_asset_id: str, target_asset_id: str, relationship: str = "depends_on"):
        self.graph.add_edge(source_asset_id, target_asset_id, relationship=relationship)

    def compute_centrality(self) -> Dict[str, float]:
        if len(self.graph.nodes) == 0:
            return {}
        try:
            return nx.degree_centrality(self.graph)
        except Exception:
            return {node: 0.0 for node in self.graph.nodes}

    def analyze_impact(self, asset_id: str) -> List[str]:
        if asset_id not in self.graph:
            return []
        descendants = nx.descendants(self.graph, asset_id)
        return list(descendants)
