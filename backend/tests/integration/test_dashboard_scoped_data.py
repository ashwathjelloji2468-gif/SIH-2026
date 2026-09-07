from fastapi.testclient import TestClient
from app.main import app

def test_validation_summary_project_scoping():
    with TestClient(app) as client:
        # Get project list
        proj_res = client.get("/api/v1/projects")
        assert proj_res.status_code == 200
        projects = proj_res.json()
        assert len(projects) > 0

        target_proj = projects[0]["id"]
        
        val_res = client.get(f"/api/v1/validation/summary?project_id={target_proj}")
        assert val_res.status_code == 200
        val_data = val_res.json()
        
        assert "total_validations" in val_data
        assert "passed" in val_data
        assert "failed" in val_data
        assert "error" in val_data
        assert "in_progress" in val_data

def test_migration_simulations_project_scoping():
    with TestClient(app) as client:
        proj_res = client.get("/api/v1/projects")
        assert proj_res.status_code == 200
        projects = proj_res.json()
        target_proj = projects[0]["id"]

        sim_res = client.get(f"/api/v1/migration/simulations?project_id={target_proj}")
        assert sim_res.status_code == 200
        sims = sim_res.json()
        assert isinstance(sims, list)
