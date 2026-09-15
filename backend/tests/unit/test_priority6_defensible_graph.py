import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.db_models import Base, Scan, CryptoAsset, CryptoNode, CryptoEdge, Project
from app.graph.blast_radius_engine import BlastRadiusEngine
from app.validation.runner import mask_secrets

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    project = Project(id="p1", name="Test Project", repository_url="https://github.com/test/repo")
    session.add(project)
    session.commit()

    yield session
    session.close()

def test_secret_masking_in_edge_evidence():
    raw_text = "Private key -----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEA...\n-----END RSA PRIVATE KEY----- exposed in auth.py"
    masked = mask_secrets(raw_text)
    assert "[MASKED_PRIVATE_KEY]" in masked
    assert "BEGIN RSA PRIVATE KEY" not in masked

def test_defensible_graph_edge_evidence_generation(db_session):
    scan = Scan(id="scan-p6-1", project_id="p1", target_path="/test/repo", status="COMPLETED")
    db_session.add(scan)
    db_session.commit()

    asset1 = CryptoAsset(
        id="asset-1",
        scan_id="scan-p6-1",
        name="RSA-2048 Auth Key",
        algorithm_name="RSA",
        key_size=2048,
        asset_type="ALGORITHM",
        quantum_safety="QUANTUM_VULNERABLE",
        location="backend/app/auth/jwt.py",
        extra_metadata={"fingerprint": "fp_shared_12345", "detector_name": "ASTScanner"}
    )
    asset2 = CryptoAsset(
        id="asset-2",
        scan_id="scan-p6-1",
        name="RSA-2048 Signer Key",
        algorithm_name="RSA",
        key_size=2048,
        asset_type="ALGORITHM",
        quantum_safety="QUANTUM_VULNERABLE",
        location="backend/app/services/signer.py",
        extra_metadata={"fingerprint": "fp_shared_12345", "detector_name": "ASTScanner"}
    )
    db_session.add_all([asset1, asset2])
    db_session.commit()

    engine = BlastRadiusEngine()
    graph_res = engine.build_graph_for_scan("scan-p6-1", db_session)

    nodes = graph_res["nodes"]
    edges = graph_res["edges"]

    assert len(nodes) >= 4
    assert len(edges) >= 3

    # Check DIRECT_USAGE edge evidence
    uses_edges = [e for e in edges if e.relation_type == "uses"]
    assert len(uses_edges) >= 2
    for e in uses_edges:
        assert e.evidence_type in ["DIRECT_USAGE", "SOURCE_CONFIG_REFERENCE"]
        assert e.confidence > 0.8
        assert e.evidence_text != ""

    # Check CBOM_RELATIONSHIP edge evidence (shares_key via fingerprint)
    shares_key_edges = [e for e in edges if e.relation_type == "shares_key"]
    assert len(shares_key_edges) >= 2
    for e in shares_key_edges:
        assert e.evidence_type == "CBOM_RELATIONSHIP"
        assert e.confidence == 1.0
        assert "shares key fingerprint" in e.evidence_text

def test_cross_scan_edge_rejection(db_session):
    scan1 = Scan(id="scan-1", project_id="p1", target_path="/test/repo1", status="COMPLETED")
    scan2 = Scan(id="scan-2", project_id="p1", target_path="/test/repo2", status="COMPLETED")
    db_session.add_all([scan1, scan2])
    db_session.commit()

    node1 = CryptoNode(id="node-s1", scan_id="scan-1", name="Node Scan 1", artefact_type="ALGORITHM")
    node2 = CryptoNode(id="node-s2", scan_id="scan-2", name="Node Scan 2", artefact_type="ALGORITHM")
    db_session.add_all([node1, node2])
    db_session.commit()

    # Attempt to create edge across scans
    engine = BlastRadiusEngine()
    edge_cross = CryptoEdge(
        id="cross-e",
        scan_id="scan-1",
        source_node_id="node-s1",
        target_node_id="node-s2",
        relation_type="depends_on"
    )
    db_session.add(edge_cross)
    db_session.commit()

    # Blast radius calculation must ignore cross-scan edge
    res = engine.calculate_blast_radius("node-s1", "scan-1", db_session)
    affected_ids = [an["node_id"] for an in res["affected_nodes"]]
    assert "node-s2" not in affected_ids

def test_legacy_edge_default_evidence_fallback(db_session):
    scan = Scan(id="scan-legacy", project_id="p1", target_path="/test/repo", status="COMPLETED")
    db_session.add(scan)
    db_session.commit()

    node_a = CryptoNode(id="node-leg-a", scan_id="scan-legacy", name="Legacy A", artefact_type="FILE")
    node_b = CryptoNode(id="node-leg-b", scan_id="scan-legacy", name="Legacy B", artefact_type="ALGORITHM")
    db_session.add_all([node_a, node_b])
    db_session.commit()

    # Create edge without extra_metadata
    legacy_edge = CryptoEdge(
        id="edge-legacy",
        scan_id="scan-legacy",
        source_node_id="node-leg-a",
        target_node_id="node-leg-b",
        relation_type="uses",
        extra_metadata=None
    )
    db_session.add(legacy_edge)
    db_session.commit()

    # Verify property fallbacks
    assert legacy_edge.evidence_type == "UNKNOWN"
    assert legacy_edge.evidence_text == "Legacy relationship; no stored evidence available."
    assert legacy_edge.confidence == 0.50

def test_blast_radius_breakdown_metrics(db_session):
    scan = Scan(id="scan-br-1", project_id="p1", target_path="/test/repo", status="COMPLETED")
    db_session.add(scan)
    db_session.commit()

    root = CryptoNode(id="root-node", scan_id="scan-br-1", name="RSA Root", artefact_type="ALGORITHM", quantum_risk="CRITICAL", mosca_x=10.0, business_criticality=90.0)
    direct1 = CryptoNode(id="direct-1", scan_id="scan-br-1", name="Auth File", artefact_type="FILE", location="backend/auth.py", quantum_risk="LOW")
    direct2 = CryptoNode(id="direct-2", scan_id="scan-br-1", name="Signer File", artefact_type="FILE", location="backend/signer.py", quantum_risk="LOW")
    indirect1 = CryptoNode(id="indirect-1", scan_id="scan-br-1", name="Web Service", artefact_type="COMPONENT", location="web/app.py", quantum_risk="HIGH")
    
    db_session.add_all([root, direct1, direct2, indirect1])
    db_session.commit()

    e1 = CryptoEdge(id="e1", scan_id="scan-br-1", source_node_id="root-node", target_node_id="direct-1", relation_type="uses", extra_metadata={"evidence_type": "DIRECT_USAGE", "evidence_text": "Root used in auth.py"})
    e2 = CryptoEdge(id="e2", scan_id="scan-br-1", source_node_id="root-node", target_node_id="direct-2", relation_type="uses", extra_metadata={"evidence_type": "DIRECT_USAGE", "evidence_text": "Root used in signer.py"})
    e3 = CryptoEdge(id="e3", scan_id="scan-br-1", source_node_id="direct-1", target_node_id="indirect-1", relation_type="depends_on", extra_metadata={"evidence_type": "SOURCE_CONFIG_REFERENCE", "evidence_text": "auth.py imported in web/app.py"})

    db_session.add_all([e1, e2, e3])
    db_session.commit()

    engine = BlastRadiusEngine()
    result = engine.calculate_blast_radius("root-node", "scan-br-1", db_session)

    # Validate root node excluded from affected nodes count
    assert result["affected_nodes_count"] == 3
    assert result["direct_dependents"] == 2
    assert result["indirect_dependents"] == 1
    assert result["edges_traversed"] == 3

    # Validate calculation breakdown
    calc = result["calculation"]
    assert calc is not None
    assert calc["traversal_stats"]["affected_nodes_count"] == 3
    assert calc["traversal_stats"]["direct_dependents"] == 2
    assert calc["traversal_stats"]["indirect_dependents"] == 1
    assert len(result["traversed_edges_evidence"]) == 3
