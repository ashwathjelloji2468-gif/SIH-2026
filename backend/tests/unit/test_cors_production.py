import pytest
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware
from app.main import app

client = TestClient(app)

PROD_ORIGIN = "https://frontend-phi-seven-18.vercel.app"

def test_1_production_origin_allowed():
    cors_middlewares = [m for m in app.user_middleware if m.cls == CORSMiddleware]
    assert len(cors_middlewares) == 1
    kwargs = cors_middlewares[0].kwargs
    assert PROD_ORIGIN in kwargs["allow_origins"]

def test_2_wildcard_not_used_with_credentials():
    cors_middlewares = [m for m in app.user_middleware if m.cls == CORSMiddleware]
    kwargs = cors_middlewares[0].kwargs
    assert "*" not in kwargs["allow_origins"]
    assert kwargs["allow_credentials"] is True

def test_3_only_one_cors_middleware_registered():
    cors_middlewares = [m for m in app.user_middleware if m.cls == CORSMiddleware]
    assert len(cors_middlewares) == 1

def test_4_get_projects_returns_production_cors_header():
    headers = {"Origin": PROD_ORIGIN}
    response = client.get("/api/v1/projects", headers=headers)
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_5_get_z_context_returns_production_cors_header():
    headers = {"Origin": PROD_ORIGIN}
    response = client.get("/api/v1/projects/proj-123/z/context?quantum_horizon=10", headers=headers)
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_6_get_blast_radius_top_returns_production_cors_header():
    headers = {"Origin": PROD_ORIGIN}
    response = client.get("/api/v1/projects/proj-123/blast-radius/top", headers=headers)
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_7_options_preflight_returns_correct_cors_headers():
    headers = {
        "Origin": PROD_ORIGIN,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization, content-type"
    }
    response = client.options("/api/v1/projects", headers=headers)
    assert response.status_code in [200, 204]
    assert response.headers.get("access-control-allow-origin") == PROD_ORIGIN
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "GET" in (response.headers.get("access-control-allow-methods") or "")

def test_8_broad_origin_regex_not_used():
    cors_middlewares = [m for m in app.user_middleware if m.cls == CORSMiddleware]
    kwargs = cors_middlewares[0].kwargs
    assert kwargs.get("allow_origin_regex") is None
