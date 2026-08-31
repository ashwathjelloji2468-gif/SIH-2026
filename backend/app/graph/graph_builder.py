from typing import List
from app.models.db_models import CryptoAsset
from app.graph.dependency_graph import DependencyGraph

def build_project_graph(assets: List[CryptoAsset]) -> DependencyGraph:
    dep_graph = DependencyGraph()
    
    for asset in assets:
        dep_graph.add_asset_node(
            asset_id=asset.id,
            name=asset.name,
            algorithm=asset.algorithm_name,
            asset_type=asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type)
        )

    # Link assets in the same file or module
    location_map = {}
    for asset in assets:
        location_map.setdefault(asset.location, []).append(asset.id)

    for loc, asset_ids in location_map.items():
        for i in range(len(asset_ids) - 1):
            dep_graph.add_dependency(asset_ids[i], asset_ids[i+1], relationship="co_located_with")

    return dep_graph
