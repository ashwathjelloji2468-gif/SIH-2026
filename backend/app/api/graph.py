from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.graph.graph_builder import build_project_graph

router = APIRouter(tags=["Graph & Impact"])

@router.get("/projects/{project_id}/graph")
def get_project_graph(project_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    assets = asset_repo.get_by_project(project_id)
    graph = build_project_graph(assets)
    centralities = graph.compute_centrality()
    
    nodes = [{"id": n, **graph.graph.nodes[n], "centrality": centralities.get(n, 0.0)} for n in graph.graph.nodes]
    edges = [{"source": u, "target": v, **data} for u, v, data in graph.graph.edges(data=True)]

    return {"project_id": project_id, "nodes": nodes, "edges": edges}

@router.get("/assets/{asset_id}/impact")
def get_asset_impact(asset_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    assets = asset_repo.get_by_project(asset.scan.project_id) if asset.scan else [asset]
    graph = build_project_graph(assets)
    impacted_nodes = graph.analyze_impact(asset_id)

    return {
        "asset_id": asset_id,
        "affected_components_count": len(impacted_nodes),
        "impacted_asset_ids": impacted_nodes
    }

@router.post("/assets/{asset_id}/impact/simulate")
def simulate_asset_impact(asset_id: str, db: Session = Depends(get_db)):
    return get_asset_impact(asset_id, db)
