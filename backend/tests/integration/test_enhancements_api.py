import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.db_models import Scan, CryptoAsset
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety

def test_coverage_and_unknowns_api():
    with TestClient(app) as client:
        # Create project
        proj_res = client.post("/api/v1/projects", json={"name": "Coverage Test Project"})
        proj_id = proj_res.json()["id"]

        # Fetch coverage report
        cov_res = client.get(f"/api/v1/projects/{proj_id}/coverage")
        assert cov_res.status_code == 200
        cov_data = cov_res.json()
        assert "overall_coverage_percentage" in cov_data
        assert "disclaimer" in cov_data
        assert len(cov_data["categories"]) >= 6

        # Fetch unknowns queue
        unk_res = client.get(f"/api/v1/projects/{proj_id}/unknowns")
        assert unk_res.status_code == 200
        assert isinstance(unk_res.json(), list)

def test_knowledge_versions_api():
    with TestClient(app) as client:
        res = client.get("/api/v1/knowledge/versions")
        assert res.status_code == 200
        data = res.json()
        assert data["cbom_schema_version"] == "1.6"

def test_migration_simulation_patterns_api():
    with TestClient(app) as client:
        proj_res = client.post("/api/v1/projects", json={"name": "Sim Project"})
        proj_id = proj_res.json()["id"]

        # Seed scan & asset in database so simulation can operate on target asset
        db = SessionLocal()
        try:
            scan = Scan(
                project_id=proj_id,
                status=ScanStatus.COMPLETED,
                target_path="app/"
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)

            asset = CryptoAsset(
                scan_id=scan.id,
                asset_type=AssetType.ALGORITHM,
                name="ECDSA Test Key",
                algorithm_name="ECDSA-P256",
                purpose=CryptoPurpose.DIGITAL_SIGNATURE,
                quantum_safety=QuantumSafety.QUANTUM_VULNERABLE,
                location="app/crypto.py"
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)
        finally:
            db.close()

        plan_res = client.post(f"/api/v1/projects/{proj_id}/migration/plans", json={"name": "PQC Plan"})
        plan_id = plan_res.json()["id"]

        sim_res = client.post(f"/api/v1/migration/plans/{plan_id}/simulate?pattern=ECDSA_TO_ML_DSA")
        assert sim_res.status_code == 200
        sim_data = sim_res.json()
        assert sim_data["status"] == "SIMULATION_COMPLETED"
        assert "transformation" in sim_data
        assert "sandbox_path" in sim_data
