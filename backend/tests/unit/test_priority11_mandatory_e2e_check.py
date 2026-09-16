import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.db_models import Project, Scan, CryptoAsset
from app.models.enums import ScanStatus, AssetType, CryptoPurpose, QuantumSafety

def test_mandatory_e2e_consistency_check():
    """
    Mandatory Final End-to-End Consistency Check:
    Verifies the 18-step project context -> RiskEngine -> DB -> GET /risk API -> Summary pipeline.
    """
    db = SessionLocal()
    try:
        # Create Project, Scan, and RSA Asset
        project = Project(
            name="E2E Consistency Test Gateway",
            description="Testing E2E XYZ risk consistency",
            user_x_years=5,
            user_y_scenario="FAST"
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        scan = Scan(
            project_id=project.id,
            status=ScanStatus.COMPLETED,
            target_path="/app/crypto"
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        rsa_asset = CryptoAsset(
            scan_id=scan.id,
            name="RSA Authentication Key Pair",
            asset_type=AssetType.ALGORITHM,
            algorithm_name="RSA-2048",
            key_size=2048,
            purpose=CryptoPurpose.DIGITAL_SIGNATURE,
            location="auth_service.py",
            quantum_safety=QuantumSafety.QUANTUM_VULNERABLE
        )
        db.add(rsa_asset)
        db.commit()
        db.refresh(rsa_asset)

        with TestClient(app) as client:
            # Step 1: Set project: user_x_years = 5, user_y_scenario = FAST
            patch_res = client.patch(f"/api/v1/projects/{project.id}", json={
                "user_x_years": 5,
                "user_y_scenario": "FAST"
            })
            assert patch_res.status_code == 200
            proj_data = patch_res.json()
            assert proj_data["user_x_years"] == 5
            assert proj_data["user_y_scenario"] == "FAST"

            # Step 2 & 3: Run project risk assessment & capture response for RSA asset
            assess_res = client.post(f"/api/v1/projects/{project.id}/risk/assess", json={
                "user_x_years": 5,
                "user_y_scenario": "FAST"
            })
            assert assess_res.status_code == 200
            assess_list = assess_res.json()
            assert len(assess_list) >= 1
            rsa_assess = next(a for a in assess_list if a["asset_id"] == rsa_asset.id)

            # Step 4: Verify canonical values in response: x.value = 5, y.value = 5, z from ZEngine
            x1 = rsa_assess["x"]["value"]
            y1 = rsa_assess["y"]["value"]
            z1_target = rsa_assess["z"]["z_target_year"]
            z1_horizon = rsa_assess["z_planning_horizon_years"]
            m1 = rsa_assess["mosca_score"]

            assert x1 == 5.0, f"Expected X=5, got {x1}"
            assert y1 == 5.0, f"Expected Y=5 for FAST, got {y1}"
            assert z1_target is not None, "Expected valid Z target year from ZEngine"
            assert z1_horizon is not None, "Expected valid Z planning horizon years"
            assert m1 is not None, "Expected valid mosca score M"

            # Step 5 & 6: Fetch same asset through GET risk endpoint & verify values are IDENTICAL
            get_asset_res = client.get(f"/api/v1/assets/{rsa_asset.id}/risk")
            assert get_asset_res.status_code == 200
            rsa_get = get_asset_res.json()

            assert rsa_get["x"]["value"] == x1, f"GET x value mismatch: {rsa_get['x']['value']} vs {x1}"
            assert rsa_get["y"]["value"] == y1, f"GET y value mismatch: {rsa_get['y']['value']} vs {y1}"
            assert rsa_get["z"]["z_target_year"] == z1_target, f"GET z target year mismatch"
            assert rsa_get["z_planning_horizon_years"] == z1_horizon, f"GET z horizon mismatch"
            assert rsa_get["mosca_score"] == m1, f"GET mosca score mismatch"

            # Step 7 & 8: Fetch project risk summary & verify corresponding Mosca values are IDENTICAL
            summary_res = client.get(f"/api/v1/projects/{project.id}/risk/summary")
            assert summary_res.status_code == 200
            summary_data = summary_res.json()

            # Verify priority_list item for RSA asset has identical values
            pitem = next(p for p in summary_data["priority_list"] if p["asset_id"] == rsa_asset.id)
            assert pitem["x"]["value"] == x1
            assert pitem["y"]["value"] == y1
            assert pitem["z"]["z_target_year"] == z1_target
            assert pitem["mosca_score"] == m1

            # Step 9 & 10: Verify same values returned for UI drawers/modals
            assert rsa_get["mosca"]["x_years"] == x1
            assert rsa_get["mosca"]["y_years"] == y1
            assert rsa_get["mosca"]["quantum_threat_horizon"] == z1_target

            # Step 11: Change project context: user_x_years = 15, user_y_scenario = COMPLEX
            patch_res2 = client.patch(f"/api/v1/projects/{project.id}", json={
                "user_x_years": 15,
                "user_y_scenario": "COMPLEX"
            })
            assert patch_res2.status_code == 200

            # Step 12: Re-run assessment
            assess_res2 = client.post(f"/api/v1/projects/{project.id}/risk/assess", json={
                "user_x_years": 15,
                "user_y_scenario": "COMPLEX"
            })
            assert assess_res2.status_code == 200
            assess_list2 = assess_res2.json()
            rsa_assess2 = next(a for a in assess_list2 if a["asset_id"] == rsa_asset.id)

            # Step 13: Verify X and Y changed to X = 15, Y = 15 (COMPLEX scenario = 15)
            x2 = rsa_assess2["x"]["value"]
            y2 = rsa_assess2["y"]["value"]
            z2_target = rsa_assess2["z"]["z_target_year"]
            m2 = rsa_assess2["mosca_score"]

            assert x2 == 15.0, f"Expected X=15, got {x2}"
            assert y2 == 15.0, f"Expected Y=15 for COMPLEX, got {y2}"

            # Step 14: Verify Z did NOT change merely because X/Y changed
            assert z2_target == z1_target, f"Z target year changed unexpectedly: {z2_target} vs {z1_target}"

            # Step 15: Verify M changed according to X + Y - Z logic
            assert m2 != m1, "Mosca score should change when X and Y increase from 5 to 15"

            # Step 16: Verify no stale cached response is returned on GET endpoint
            get_asset_res2 = client.get(f"/api/v1/assets/{rsa_asset.id}/risk")
            assert get_asset_res2.status_code == 200
            rsa_get2 = get_asset_res2.json()
            assert rsa_get2["x"]["value"] == 15.0
            assert rsa_get2["y"]["value"] == 15.0
            assert rsa_get2["mosca_score"] == m2

            # Step 17 & 18: Confirm context propagation and backend consistency
            assert rsa_get2["mosca"]["x_years"] == 15.0
            assert rsa_get2["mosca"]["y_years"] == 15.0
            assert rsa_get2["mosca"]["quantum_threat_horizon"] == z2_target

    finally:
        db.close()
