import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import Project, Scan, CryptoAsset, CryptoNode, CryptoEdge, BlastRadiusResult
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety
from app.graph.blast_radius_engine import BlastRadiusEngine

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_blast_radius_graph_construction_and_inference(db_session):
    # 1. Create Project and Scan
    project = Project(id="p1", name="Test Project")
    scan = Scan(id="s1", project_id="p1", status=ScanStatus.COMPLETED, target_path="/tmp/test")
    db_session.add_all([project, scan])
    db_session.commit()

    # 2. Add Assets with shared fingerprint and cross references
    a1 = CryptoAsset(
        id="a1",
        scan_id="s1",
        name="RSA-2048 Auth Key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        key_size=2048,
        purpose=CryptoPurpose.SIGNATURE,
        location="auth_service/jwt_signer.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        extra_metadata={"fingerprint": "fp_12345_abc", "references": ["gateway/proxy.py"]}
    )

    a2 = CryptoAsset(
        id="a2",
        scan_id="s1",
        name="RSA-2048 Verification Key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        key_size=2048,
        purpose=CryptoPurpose.SIGNATURE,
        location="gateway/proxy.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        extra_metadata={"fingerprint": "fp_12345_abc"}
    )

    a3 = CryptoAsset(
        id="a3",
        scan_id="s1",
        name="AES-256 Storage Cipher",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES",
        key_size=256,
        purpose=CryptoPurpose.ENCRYPTION,
        location="storage/db_vault.py",
        quantum_safety=QuantumSafety.QUANTUM_SAFE,
        extra_metadata={}
    )

    db_session.add_all([a1, a2, a3])
    db_session.commit()

    # 3. Execute BlastRadiusEngine build
    engine = BlastRadiusEngine()
    graph_res = engine.build_graph_for_scan("s1", db_session)

    assert len(graph_res["nodes"]) >= 3
    assert len(graph_res["edges"]) >= 3

    # Verify 'shares_key' edge inferred between a1 and a2
    shares_key_edges = db_session.query(CryptoEdge).filter(
        CryptoEdge.scan_id == "s1",
        CryptoEdge.relation_type == "shares_key"
    ).all()
    assert len(shares_key_edges) >= 2

def test_blast_radius_calculation_and_scoring(db_session):
    project = Project(id="p2", name="Bank Project")
    scan = Scan(id="s2", project_id="p2", status=ScanStatus.COMPLETED, target_path="/tmp/bank")
    db_session.add_all([project, scan])
    db_session.commit()

    a1 = CryptoAsset(
        id="asset_root",
        scan_id="s2",
        name="RSA-4096 Master Cert",
        asset_type=AssetType.CERTIFICATE,
        algorithm_name="RSA",
        key_size=4096,
        purpose=CryptoPurpose.AUTHENTICATION,
        location="certs/master_cert.pem",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        extra_metadata={"cert_serial": "9988776655"}
    )

    a2 = CryptoAsset(
        id="asset_dep",
        scan_id="s2",
        name="RSA-4096 Service Cert",
        asset_type=AssetType.CERTIFICATE,
        algorithm_name="RSA",
        key_size=4096,
        purpose=CryptoPurpose.AUTHENTICATION,
        location="payment/client_cert.pem",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
        extra_metadata={"cert_serial": "9988776655"}
    )

    db_session.add_all([a1, a2])
    db_session.commit()

    engine = BlastRadiusEngine()
    engine.build_graph_for_scan("s2", db_session)

    root_node = db_session.query(CryptoNode).filter(CryptoNode.asset_id == "asset_root").first()
    assert root_node is not None

    br_result = engine.calculate_blast_radius(root_node.id, "s2", db_session, max_hops=3)

    assert br_result["root_node_id"] == root_node.id
    assert br_result["radius_score"] > 0.0
    assert br_result["affected_nodes_count"] >= 1
    assert "SYSTEM_PKI_KEYS" in br_result["data_classes"] or "AUTHENTICATION_CREDENTIALS" in br_result["data_classes"]

def test_top_blast_radius_summary(db_session):
    project = Project(id="p3", name="Gov Project")
    scan = Scan(id="s3", project_id="p3", status=ScanStatus.COMPLETED, target_path="/tmp/gov")
    db_session.add_all([project, scan])
    db_session.commit()

    a1 = CryptoAsset(
        id="asset_gov",
        scan_id="s3",
        name="ECDSA P-256 Identity Key",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDSA",
        key_size=256,
        purpose=CryptoPurpose.SIGNATURE,
        location="gov/identity.py",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add(a1)
    db_session.commit()

    engine = BlastRadiusEngine()
    summary = engine.get_top_blast_radii_for_project("p3", db_session)

    assert summary["project_id"] == "p3"
    assert len(summary["top_blast_radii"]) >= 1
