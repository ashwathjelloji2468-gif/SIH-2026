from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.graph.graph_builder import build_project_graph, GraphBuilder
from app.graph.impact import ImpactAnalyzer
from app.graph.blast_radius_engine import BlastRadiusEngine
from app.models.db_models import CryptoNode, CryptoEdge, Scan
from app.models.schemas import (
    CryptoNodeResponse, CryptoEdgeResponse, ScanGraphResponse,
    BlastRadiusResponse, TopBlastRadiusSummaryResponse
)

router = APIRouter(tags=["Graph & Blast Radius"])

@router.get("/scans/{scan_id}/graph", response_model=ScanGraphResponse)
def get_scan_graph(scan_id: str, db: Session = Depends(get_db)):
    """
    Returns full cryptographic dependency graph (CryptoNodes + CryptoEdges) for a scan.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")

    nodes = db.query(CryptoNode).filter(CryptoNode.scan_id == scan_id).all()
    edges = db.query(CryptoEdge).filter(CryptoEdge.scan_id == scan_id).all()

    if not nodes:
        # Build graph on-demand if not present
        engine = BlastRadiusEngine()
        res = engine.build_graph_for_scan(scan_id, db)
        nodes = res["nodes"]
        edges = res["edges"]

    # Calculate single points of failure (nodes with 2+ outgoing/incoming connections or high risk)
    spof = []
    for n in nodes:
        degree = db.query(CryptoEdge).filter(
            (CryptoEdge.source_node_id == n.id) | (CryptoEdge.target_node_id == n.id)
        ).count()
        if degree >= 2 or str(n.quantum_risk).upper() in ["CRITICAL", "HIGH", "QUANTUM_VULNERABLE"]:
            spof.append({
                "node_id": n.id,
                "name": n.name,
                "artefact_type": n.artefact_type,
                "degree": degree,
                "quantum_risk": n.quantum_risk
            })

    return {
        "scan_id": scan_id,
        "nodes": [CryptoNodeResponse.model_validate(n) for n in nodes],
        "edges": [CryptoEdgeResponse.model_validate(e) for e in edges],
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "single_points_of_failure": spof
    }

@router.post("/scans/{scan_id}/build-graph", response_model=ScanGraphResponse)
def build_scan_graph(scan_id: str, db: Session = Depends(get_db)):
    """
    Triggers graph construction & edge inference for a scan.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")

    engine = BlastRadiusEngine()
    res = engine.build_graph_for_scan(scan_id, db)

    nodes = res["nodes"]
    edges = res["edges"]

    return {
        "scan_id": scan_id,
        "nodes": [CryptoNodeResponse.model_validate(n) for n in nodes],
        "edges": [CryptoEdgeResponse.model_validate(e) for e in edges],
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "single_points_of_failure": []
    }

@router.get("/nodes/{node_id}/blast-radius", response_model=BlastRadiusResponse)
def get_node_blast_radius(
    node_id: str,
    scan_id: Optional[str] = Query(None),
    max_hops: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Calculates blast radius for a given node using directional BFS traversal.
    """
    # Resolve node first to get its authoritative scan_id
    node = db.query(CryptoNode).filter(
        (CryptoNode.id == node_id) | (CryptoNode.asset_id == node_id)
    ).first()

    if node:
        scan_id = node.scan_id
    elif scan_id:
        # Check if passed scan_id is actually a project_id or scan_id
        scan_obj = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan_obj:
            latest = db.query(Scan).filter(Scan.project_id == scan_id, Scan.status == "COMPLETED").order_by(Scan.created_at.desc()).first()
            if latest:
                scan_id = latest.id

    if not scan_id:
        latest_scan = db.query(Scan).filter(Scan.status == "COMPLETED").order_by(Scan.created_at.desc()).first()
        if latest_scan:
            scan_id = latest_scan.id
        else:
            raise HTTPException(status_code=404, detail="Scan ID required or no completed scan found.")

    engine = BlastRadiusEngine()
    result = engine.calculate_blast_radius(node_id, scan_id, db, max_hops=max_hops)
    return result

@router.get("/projects/{project_id}/blast-radius/top", response_model=TopBlastRadiusSummaryResponse)
def get_project_top_blast_radius(project_id: str, db: Session = Depends(get_db)):
    """
    Returns top 10 largest blast radii, shared key alerts, and single points of failure for a project.
    """
    engine = BlastRadiusEngine()
    return engine.get_top_blast_radii_for_project(project_id, db)

@router.get("/scans/{scan_id}/graph/download")
def download_scan_graph_json(scan_id: str, db: Session = Depends(get_db)):
    """
    Exports machine-readable dependency-graph.json for audit and governance.
    """
    graph_data = get_scan_graph(scan_id, db)
    return JSONResponse(
        content=graph_data if isinstance(graph_data, dict) else graph_data.model_dump(),
        headers={"Content-Disposition": f'attachment; filename="dependency-graph-{scan_id}.json"'}
    )

# Legacy / Compatibility Routes
@router.get("/graph")
def get_overall_graph(project_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    if project_id:
        assets = asset_repo.get_by_project(project_id)
    else:
        from app.models.db_models import CryptoAsset
        assets = db.query(CryptoAsset).all()

    risk_repo = RiskRepository(db)
    rec_repo = RecommendationRepository(db)
    risks = [risk_repo.get_latest_for_asset(a.id) for a in assets if risk_repo.get_latest_for_asset(a.id)]
    recs = [rec_repo.get_latest_for_asset(a.id) for a in assets if rec_repo.get_latest_for_asset(a.id)]

    graph = build_project_graph(assets=assets, risks=risks, recommendations=recs)
    return graph.to_dict()

@router.get("/graph/impact/{asset_id}")
def get_graph_impact_analysis(asset_id: str, db: Session = Depends(get_db)):
    asset_repo = AssetRepository(db)
    asset = asset_repo.get(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Crypto asset '{asset_id}' not found")

    risk_repo = RiskRepository(db)
    rec_repo = RecommendationRepository(db)

    ra = risk_repo.get_latest_for_asset(asset_id)
    rec = rec_repo.get_latest_for_asset(asset_id)
    all_assets = asset_repo.get_by_project(asset.scan.project_id) if asset.scan else [asset]

    analyzer = ImpactAnalyzer()
    return analyzer.analyze_asset_impact(asset, all_assets, ra, rec)

@router.get("/projects/{project_id}/graph")
def get_project_graph(project_id: str, db: Session = Depends(get_db)):
    return get_overall_graph(project_id=project_id, db=db)

@router.get("/assets/{asset_id}/impact")
def get_asset_impact(asset_id: str, db: Session = Depends(get_db)):
    return get_graph_impact_analysis(asset_id, db)
