import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.db_models import Project, Scan, CryptoAsset
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety

def test_inventory_canonical_xyz_context():
    """
    Mandatory Inventory Canonical XYZ Context Test:
    Verifies /inventory endpoint returns project-aware canonical X, Y, and Z fields
    without mutating underlying CryptoAsset properties.
    """
    db = SessionLocal()
    try:
        project = Project(
            name="Inventory XYZ Test Project",
            description="Testing project-aware inventory XYZ context",
            user_x_years=5,
            user_y_scenario="FAST"
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        scan = Scan(
            project_id=project.id,
            status=ScanStatus.COMPLETED,
            target_path="/app/src"
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        rsa_asset = CryptoAsset(
            scan_id=scan.id,
            name="RSA Authentication Key",
            asset_type=AssetType.ALGORITHM,
            algorithm_name="RSA-2048",
            key_size=2048,
            purpose=CryptoPurpose.DIGITAL_SIGNATURE,
            location="auth.py",
            quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
        )
        aes_asset = CryptoAsset(
            scan_id=scan.id,
            name="AES Encryption Cipher",
            asset_type=AssetType.ALGORITHM,
            algorithm_name="AES-256-GCM",
            key_size=256,
            purpose=CryptoPurpose.ENCRYPTION,
            location="cipher.py",
            quantum_safety=QuantumSafety.QUANTUM_SAFE
        )
        db.add_all([rsa_asset, aes_asset])
        db.commit()
        db.refresh(rsa_asset)
        db.refresh(aes_asset)

        with TestClient(app) as client:
            # CASE 1: user_x_years = 5, user_y_scenario = FAST
            inv_res1 = client.get(f"/api/v1/projects/{project.id}/inventory")
            assert inv_res1.status_code == 200
            inv_list1 = inv_res1.json()
            assert len(inv_list1) == 2

            rsa_inv1 = next(item for item in inv_list1 if item["id"] == rsa_asset.id)
            aes_inv1 = next(item for item in inv_list1 if item["id"] == aes_asset.id)

            # Verify every row X = 5, Y = 5
            assert rsa_inv1["effective_x_years"] == 5.0
            assert rsa_inv1["effective_y_years"] == 5.0
            assert rsa_inv1["effective_y_scenario"] == "FAST"

            assert aes_inv1["effective_x_years"] == 5.0
            assert aes_inv1["effective_y_years"] == 5.0
            assert aes_inv1["effective_y_scenario"] == "FAST"

            # Z comes from ZEngine and is component-specific
            z_rsa_1 = rsa_inv1["effective_z_target_year"]
            z_aes_1 = aes_inv1["effective_z_target_year"]
            assert z_rsa_1 is not None, "RSA Z target year should come from ZEngine"

            # Raw CryptoAsset classification defaults preserved and NOT overwritten
            assert rsa_inv1["data_lifetime_years"] == 10.0
            assert rsa_inv1["migration_time_years"] == 3.0
            assert rsa_inv1["quantum_threat_horizon"] == 2033

            # CASE 2: user_x_years = 15, user_y_scenario = COMPLEX
            patch_res = client.patch(f"/api/v1/projects/{project.id}", json={
                "user_x_years": 15,
                "user_y_scenario": "COMPLEX"
            })
            assert patch_res.status_code == 200

            inv_res2 = client.get(f"/api/v1/projects/{project.id}/inventory")
            assert inv_res2.status_code == 200
            inv_list2 = inv_res2.json()

            rsa_inv2 = next(item for item in inv_list2 if item["id"] == rsa_asset.id)
            aes_inv2 = next(item for item in inv_list2 if item["id"] == aes_asset.id)

            # Verify X = 15, Y = 15
            assert rsa_inv2["effective_x_years"] == 15.0
            assert rsa_inv2["effective_y_years"] == 15.0
            assert rsa_inv2["effective_y_scenario"] == "COMPLEX"

            assert aes_inv2["effective_x_years"] == 15.0
            assert aes_inv2["effective_y_years"] == 15.0
            assert aes_inv2["effective_y_scenario"] == "COMPLEX"

            # Verify Z for each component remains component-specific and did NOT change merely because X/Y changed
            assert rsa_inv2["effective_z_target_year"] == z_rsa_1
            assert aes_inv2["effective_z_target_year"] == z_aes_1

    finally:
        db.close()
