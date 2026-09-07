from fastapi.testclient import TestClient
from app.main import app

def test_multiproject_inventory_isolation():
    with TestClient(app) as client:
        # Fetch project list
        proj_res = client.get("/api/v1/projects")
        assert proj_res.status_code == 200
        projects = proj_res.json()
        assert len(projects) > 0

        # Map project names to expected minimum asset counts
        expected_counts = {
            "pyca/cryptography": 600,
            "paramiko/paramiko": 400,
            "demo-bank": 20,
            "demo-healthcare": 10,
            "demo-government": 10
        }

        for proj_name, min_expected in expected_counts.items():
            matched = next((p for p in projects if p["name"] == proj_name), None)
            assert matched is not None, f"Project {proj_name} missing from DB"
            
            proj_id = matched["id"]
            inv_res = client.get(f"/api/v1/projects/{proj_id}/inventory")
            assert inv_res.status_code == 200
            assets = inv_res.json()
            assert len(assets) >= min_expected, f"Project {proj_name} ({proj_id}) expected at least {min_expected} assets, got {len(assets)}"

            # Verify coverage returns correct total count
            cov_res = client.get(f"/api/v1/projects/{proj_id}/coverage")
            assert cov_res.status_code == 200
            cov_data = cov_res.json()
            assert cov_data["total_assets_discovered"] == len(assets)
