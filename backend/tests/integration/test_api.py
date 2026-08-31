import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"

def test_project_crud():
    with TestClient(app) as client:
        # Create project
        create_res = client.post("/api/v1/projects", json={
            "name": "Test Payment Gateway",
            "description": "Integration test project"
        })
        assert create_res.status_code == 201
        proj = create_res.json()
        proj_id = proj["id"]
        assert proj["name"] == "Test Payment Gateway"

        # Get project
        get_res = client.get(f"/api/v1/projects/{proj_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == proj_id

        # List projects
        list_res = client.get("/api/v1/projects")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1
