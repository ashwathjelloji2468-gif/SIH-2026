import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import (
    Project, Scan, CryptoAsset, Evidence, RiskAssessment, Recommendation,
    MigrationPlan, MigrationTask
)
from app.models.enums import (
    AssetType, CryptoPurpose, QuantumSafety, RiskLevel, StandardStatus,
    RecommendationCategory, TaskType, TaskStatus, MigrationPriority, ImpactLevel
)
from app.graph.dependency_graph import DependencyGraph
from app.graph.graph_builder import GraphBuilder, build_project_graph
from app.graph.impact import ImpactAnalyzer
from app.migration.planner import MigrationPlanner
from app.repositories.migration_repository import MigrationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.recommendation_repository import RecommendationRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_1_graph_builder_stable_nodes(db_session):
    project = Project(id="proj_1", name="Payment Gateway")
    scan = Scan(id="scan_1", project_id="proj_1", target_path="/app")
    asset = CryptoAsset(
        id="asset_1",
        scan_id="scan_1",
        name="ECDH-KeyEx",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDH",
        location="src/auth/key_exchange.py",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )

    builder = GraphBuilder()
    graph = builder.build_graph(assets=[asset], project=project)

    dict_repr = graph.to_dict()
    node_ids = [n["id"] for n in dict_repr["nodes"]]

    assert "project:proj_1" in node_ids
    assert "component:auth" in node_ids
    assert "file:src/auth/key_exchange.py" in node_ids
    assert "asset:asset_1" in node_ids


def test_2_asset_to_evidence_relationship():
    asset = CryptoAsset(
        id="asset_ecdh",
        scan_id="scan_1",
        name="ECDH",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDH",
        location="src/auth.py",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    evidence = Evidence(
        id="ev_1",
        asset_id="asset_ecdh",
        source_file="src/auth.py",
        detector_name="SourceScanner",
        confidence_score=0.95
    )
    asset.evidence_items = [evidence]

    graph = build_project_graph(assets=[asset])
    edges = graph.to_dict()["edges"]

    has_ev_edge = any(
        e["source"] == "asset:asset_ecdh" and e["target"] == "evidence:ev_1" and e["relationship"] == "supported_by"
        for e in edges
    )
    assert has_ev_edge


def test_3_asset_to_risk_relationship():
    asset = CryptoAsset(
        id="asset_rsa",
        scan_id="scan_1",
        name="RSA-2048",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        location="src/crypto.py",
        purpose=CryptoPurpose.SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    risk = RiskAssessment(
        id="risk_rsa",
        asset_id="asset_rsa",
        risk_score=85.0,
        risk_level=RiskLevel.CRITICAL
    )

    graph = build_project_graph(assets=[asset], risks=[risk])
    edges = graph.to_dict()["edges"]

    has_risk_edge = any(
        e["source"] == "asset:asset_rsa" and e["target"] == "risk:risk_rsa" and e["relationship"] == "has_risk"
        for e in edges
    )
    assert has_risk_edge


def test_4_asset_to_recommendation_relationship():
    asset = CryptoAsset(
        id="asset_rsa",
        scan_id="scan_1",
        name="RSA-2048",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        location="src/crypto.py",
        purpose=CryptoPurpose.SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    rec = Recommendation(
        id="rec_rsa",
        asset_id="asset_rsa",
        target_pqc_candidate="ML-DSA",
        recommended_algorithm="ML-DSA (FIPS 204)",
        category=RecommendationCategory.PQC_REPLACEMENT,
        priority="HIGH",
        rationale="Upgrade RSA signature to ML-DSA"
    )

    graph = build_project_graph(assets=[asset], recommendations=[rec])
    edges = graph.to_dict()["edges"]

    has_rec_edge = any(
        e["source"] == "asset:asset_rsa" and e["target"] == "recommendation:rec_rsa" and e["relationship"] == "has_recommendation"
        for e in edges
    )
    assert has_rec_edge


def test_5_source_file_uses_crypto_asset():
    asset = CryptoAsset(
        id="asset_sha",
        scan_id="scan_1",
        name="SHA-256",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="SHA-256",
        location="src/hash/digest.py",
        purpose=CryptoPurpose.HASHING,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    )

    graph = build_project_graph(assets=[asset])
    edges = graph.to_dict()["edges"]

    has_uses_edge = any(
        e["source"] == "file:src/hash/digest.py" and e["target"] == "asset:asset_sha" and e["relationship"] == "uses" and e["provenance"] == "source_scanner"
        for e in edges
    )
    assert has_uses_edge


def test_6_no_fabricated_unrelated_dependencies():
    asset1 = CryptoAsset(
        id="asset_1",
        scan_id="scan_1",
        name="RSA-2048",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        location="src/module_a/service.py",
        purpose=CryptoPurpose.SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    asset2 = CryptoAsset(
        id="asset_2",
        scan_id="scan_1",
        name="AES-256",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        location="src/module_b/db.py",
        purpose=CryptoPurpose.ENCRYPTION,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    )

    graph = build_project_graph(assets=[asset1, asset2])
    edges = graph.to_dict()["edges"]

    # No direct edge should connect asset_1 directly to asset_2
    has_direct = any(
        (e["source"] == "asset:asset_1" and e["target"] == "asset:asset_2") or
        (e["source"] == "asset:asset_2" and e["target"] == "asset:asset_1")
        for e in edges
    )
    assert not has_direct


def test_7_impact_analysis_dependents():
    asset = CryptoAsset(
        id="asset_ecdh",
        scan_id="scan_1",
        name="ECDH",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDH",
        location="src/auth/key_exchange.py",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    analyzer = ImpactAnalyzer()
    impact = analyzer.analyze_asset_impact(asset)

    assert impact["asset_id"] == "asset_ecdh"
    assert "auth" in impact["affected_components"]
    assert "src/auth/key_exchange.py" in impact["affected_files"]
    assert impact["impact_score"] >= 0.0
    assert impact["impact_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def test_8_risk_and_impact_scores_remain_separate():
    asset = CryptoAsset(
        id="asset_rsa",
        scan_id="scan_1",
        name="RSA",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        location="src/simple.py",
        purpose=CryptoPurpose.SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    risk = RiskAssessment(
        id="risk_rsa",
        asset_id="asset_rsa",
        risk_score=95.0,  # High risk
        risk_level=RiskLevel.CRITICAL,
        business_criticality_score=10.0  # Low business criticality
    )
    rec = Recommendation(
        id="rec_rsa",
        asset_id="asset_rsa",
        migration_complexity="LOW"
    )

    analyzer = ImpactAnalyzer()
    impact = analyzer.analyze_asset_impact(asset, risk_assessment=risk, recommendation=rec)

    # Risk score is 95.0, but impact score should be distinct (e.g. ~40-60)
    assert risk.risk_score == 95.0
    assert impact["impact_score"] != risk.risk_score
    assert "factors" in impact


def test_9_ecdh_key_establishment_generates_ml_kem_tasks():
    asset = CryptoAsset(
        id="asset_ecdh",
        scan_id="scan_1",
        name="ECDH-256",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDH",
        location="src/tls/handshake.py",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    rec = Recommendation(
        id="rec_ecdh",
        asset_id="asset_ecdh",
        target_pqc_candidate="ML-KEM",
        recommended_algorithm="ML-KEM (FIPS 203)",
        category=RecommendationCategory.PQC_REPLACEMENT,
        migration_complexity="MEDIUM"
    )

    planner = MigrationPlanner()
    tasks = planner.generate_tasks_for_asset(asset, recommendation=rec)

    task_types = [t["task_type"] for t in tasks]
    assert "DISCOVERY_REVIEW" in task_types
    assert "CRYPTO_API_CHANGE" in task_types
    assert "ALGORITHM_REPLACEMENT" in task_types or "HYBRID_DEPLOYMENT" in task_types
    assert "PERFORMANCE_TESTING" in task_types
    assert "SECURITY_VALIDATION" in task_types


def test_10_rsa_signature_generates_ml_dsa_tasks():
    asset = CryptoAsset(
        id="asset_rsa_sig",
        scan_id="scan_1",
        name="RSA-2048",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        location="src/tokens/jwt.py",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    rec = Recommendation(
        id="rec_rsa_sig",
        asset_id="asset_rsa_sig",
        target_pqc_candidate="ML-DSA",
        recommended_algorithm="ML-DSA (FIPS 204)",
        category=RecommendationCategory.PQC_REPLACEMENT,
        migration_complexity="MEDIUM"
    )

    planner = MigrationPlanner()
    tasks = planner.generate_tasks_for_asset(asset, recommendation=rec)

    task_types = [t["task_type"] for t in tasks]
    assert "DISCOVERY_REVIEW" in task_types
    assert "CRYPTO_API_CHANGE" in task_types
    assert "ALGORITHM_REPLACEMENT" in task_types
    assert "APPLICATION_TESTING" in task_types
    assert "SECURITY_VALIDATION" in task_types


def test_11_aes_does_not_generate_pqc_replacement_task():
    asset = CryptoAsset(
        id="asset_aes",
        scan_id="scan_1",
        name="AES-256-GCM",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        location="src/storage/enc.py",
        purpose=CryptoPurpose.ENCRYPTION,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    )
    rec = Recommendation(
        id="rec_aes",
        asset_id="asset_aes",
        target_pqc_candidate="RETAIN_EXISTING",
        recommended_algorithm="RETAIN_EXISTING",
        category=RecommendationCategory.RETAIN_SYMMETRIC_CRYPTO,
        migration_complexity="LOW"
    )

    planner = MigrationPlanner()
    tasks = planner.generate_tasks_for_asset(asset, recommendation=rec)

    task_types = [t["task_type"] for t in tasks]
    assert "ALGORITHM_REPLACEMENT" not in task_types
    assert "HYBRID_DEPLOYMENT" not in task_types
    assert "DISCOVERY_REVIEW" in task_types
    assert "SECURITY_VALIDATION" in task_types


def test_12_unknown_purpose_produces_human_review():
    asset = CryptoAsset(
        id="asset_custom",
        scan_id="scan_1",
        name="CUSTOM_CIPHER",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="CUSTOM_CIPHER",
        location="src/legacy/cipher.py",
        purpose=CryptoPurpose.UNKNOWN,
        quantum_safety=QuantumSafety.UNKNOWN
    )
    rec = Recommendation(
        id="rec_custom",
        asset_id="asset_custom",
        target_pqc_candidate="MANUAL_REVIEW_REQUIRED",
        recommended_algorithm="MANUAL_REVIEW_REQUIRED",
        category=RecommendationCategory.MANUAL_REVIEW,
        migration_complexity="HIGH"
    )

    planner = MigrationPlanner()
    tasks = planner.generate_tasks_for_asset(asset, recommendation=rec)

    task_types = [t["task_type"] for t in tasks]
    assert "HUMAN_REVIEW" in task_types
    blockers = [b for t in tasks for b in t["blockers"]]
    assert any("HUMAN_REVIEW" in b for b in blockers)


def test_13_complex_cases_create_appropriate_blockers():
    asset = CryptoAsset(
        id="asset_binary",
        scan_id="scan_1",
        name="Native HSM Binary",
        asset_type=AssetType.BINARY,
        algorithm_name="HSM-RSA",
        location="bin/hsm_driver.so",
        purpose=CryptoPurpose.SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    rec = Recommendation(
        id="rec_hsm",
        asset_id="asset_binary",
        migration_complexity="HIGH"
    )

    planner = MigrationPlanner()
    tasks = planner.generate_tasks_for_asset(asset, recommendation=rec)

    task_types = [t["task_type"] for t in tasks]
    assert "HUMAN_REVIEW" in task_types
    blockers = [b for t in tasks for b in t["blockers"]]
    assert any("VENDOR_REVIEW" in b or "HUMAN_REVIEW" in b for b in blockers)


def test_14_migration_task_dependency_ordering():
    asset = CryptoAsset(
        id="asset_ecdh",
        scan_id="scan_1",
        name="ECDH",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDH",
        location="src/net/tls.py",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )

    planner = MigrationPlanner()
    tasks = planner.generate_tasks_for_asset(asset)

    # Task 1 has no dependencies
    assert tasks[0]["dependencies"] == []
    # Task 2 depends on Task 1 ID
    assert tasks[1]["dependencies"] == [tasks[0]["id"]]
    # Task 3 depends on Task 2 ID
    assert tasks[2]["dependencies"] == [tasks[1]["id"]]


def test_15_tasks_not_automatically_marked_completed():
    asset = CryptoAsset(
        id="asset_rsa",
        scan_id="scan_1",
        name="RSA",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        location="src/sign.py",
        purpose=CryptoPurpose.SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )

    planner = MigrationPlanner()
    tasks = planner.generate_tasks_for_asset(asset)

    statuses = [t["status"] for t in tasks]
    assert "COMPLETED" not in statuses
    assert tasks[0]["status"] in ["READY", "NOT_STARTED", "BLOCKED"]


def test_16_migration_plans_persist_in_sqlite(db_session):
    project = Project(id="proj_sqlite", name="Test SQLite Project")
    scan = Scan(id="scan_sqlite", project_id="proj_sqlite", target_path="/app")
    asset = CryptoAsset(
        id="asset_sqlite",
        scan_id="scan_sqlite",
        name="ECDH-256",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="ECDH",
        location="src/auth.py",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add_all([project, scan, asset])
    db_session.commit()

    planner = MigrationPlanner()
    plan = planner.create_plan_for_project(
        db=db_session,
        project_id="proj_sqlite",
        plan_name="SQLite Test Migration Plan",
        assets=[asset]
    )

    assert plan.id is not None
    assert plan.project_id == "proj_sqlite"
    assert len(plan.tasks) > 0

    repo = MigrationRepository(db_session)
    fetched_plan = repo.get_plan(plan.id)
    assert fetched_plan is not None
    assert fetched_plan.name == "SQLite Test Migration Plan"
    assert len(fetched_plan.tasks) == len(plan.tasks)


def test_17_api_endpoints_return_persisted_data(db_session):
    project = Project(id="proj_api", name="API Test Project")
    scan = Scan(id="scan_api", project_id="proj_api", target_path="/app")
    asset = CryptoAsset(
        id="asset_api",
        scan_id="scan_api",
        name="RSA-2048",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="RSA",
        location="src/jwt.py",
        purpose=CryptoPurpose.DIGITAL_SIGNATURE,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    db_session.add_all([project, scan, asset])
    db_session.commit()

    planner = MigrationPlanner()
    plan = planner.create_plan_for_project(
        db=db_session,
        project_id="proj_api",
        plan_name="API Plan",
        assets=[asset]
    )

    repo = MigrationRepository(db_session)
    plans = repo.get_plans_by_project("proj_api")
    assert len(plans) == 1
    assert plans[0].id == plan.id
    assert plans[0].name == "API Plan"


def test_18_prompt4_recommendation_engine_regression():
    from app.recommend.engine import RecommendationEngine
    engine = RecommendationEngine()
    rec = engine.generate_recommendation(
        algorithm_name="ECDH",
        purpose=CryptoPurpose.KEY_ESTABLISHMENT,
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert rec["recommended_algorithm"] == "ML-KEM (FIPS 203)"
    assert rec["category"] == RecommendationCategory.PQC_REPLACEMENT


def test_19_prompt3_risk_engine_regression():
    from app.risk.risk_engine import RiskEngine
    engine = RiskEngine()
    risk = engine.evaluate_asset_risk(
        algorithm_name="RSA",
        quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
    )
    assert risk["risk_score"] >= 70.0
    assert risk["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value, "HIGH", "CRITICAL"]


def test_20_prompt1_2_asset_repository_regression(db_session):
    scan = Scan(id="scan_p1", project_id="proj_p1", target_path="/app")
    db_session.add(scan)
    db_session.commit()

    repo = AssetRepository(db_session)
    asset = repo.create(
        scan_id="scan_p1",
        name="AES-256",
        asset_type=AssetType.ALGORITHM,
        algorithm_name="AES-256",
        location="src/crypto.py",
        purpose=CryptoPurpose.ENCRYPTION,
        quantum_safety=QuantumSafety.QUANTUM_RESISTANT_WITH_REDUCED_SECURITY_MARGIN
    )

    assert asset.id is not None
    fetched = repo.get(asset.id)
    assert fetched.algorithm_name == "AES-256"
