import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_real_projects_inventory_api():
    with TestClient(app) as client:
        # Fetch projects list
        proj_res = client.get("/api/v1/projects")
        assert proj_res.status_code == 200
        projects = proj_res.json()
        
        target_names = ["pyca/cryptography", "paramiko/paramiko"]
        real_projects = [p for p in projects if p["name"] in target_names]
        assert len(real_projects) == 2, f"Expected 2 real projects in DB, found {len(real_projects)}"

        for proj in real_projects:
            proj_id = proj["id"]
            proj_name = proj["name"]

            # Query inventory endpoint
            inv_res = client.get(f"/api/v1/projects/{proj_id}/inventory")
            assert inv_res.status_code == 200
            assets = inv_res.json()
            assert len(assets) > 100, f"Project {proj_name} must return hundreds of real assets from DB"

            # Query coverage endpoint
            cov_res = client.get(f"/api/v1/projects/{proj_id}/coverage")
            assert cov_res.status_code == 200
            cov_data = cov_res.json()
            assert cov_data["total_assets_discovered"] == len(assets)

            # Query risk summary endpoint
            risk_res = client.get(f"/api/v1/projects/{proj_id}/risk/summary")
            assert risk_res.status_code == 200
            assert risk_res.json()["total_assets"] == len(assets)
