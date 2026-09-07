import time
from fastapi.testclient import TestClient
from app.main import app

def test_projects_endpoint_returns_real_projects():
    with TestClient(app) as client:
        res = client.get("/api/v1/projects")
        assert res.status_code == 200
        projects = res.json()
        assert isinstance(projects, list)
        
        # Verify that fake project proj-demo-cryptography-01 is NOT returned by backend
        project_ids = [p["id"] for p in projects]
        assert "proj-demo-cryptography-01" not in project_ids

def test_risk_summary_performance_and_unassessed_reporting():
    with TestClient(app) as client:
        # Get real projects
        proj_res = client.get("/api/v1/projects")
        assert proj_res.status_code == 200
        projects = proj_res.json()
        if not projects:
            return

        target_project = next((p for p in projects if "cryptography" in p["name"].lower()), projects[0])
        proj_id = target_project["id"]

        start_time = time.time()
        risk_res = client.get(f"/api/v1/projects/{proj_id}/risk/summary")
        elapsed = time.time() - start_time

        assert risk_res.status_code == 200
        summary = risk_res.json()

        # Risk summary must respond in less than 2 seconds (not 20+ seconds)
        assert elapsed < 2.0, f"Risk summary took too long: {elapsed:.2f}s"

        # Verify truthful counts
        assert "total_assets" in summary
        assert "assessed_assets" in summary
        assert "unassessed_assets" in summary
        assert summary["unassessed_assets"] == summary["total_assets"] - summary["assessed_assets"]
