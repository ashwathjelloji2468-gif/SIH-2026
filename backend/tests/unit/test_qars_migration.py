import pytest
from app.qars.migration import evaluate_migration_complexity, collect_migration_complexity_evidence, QARSMigrationComplexity


class MockAsset:
    def __init__(self, evidence_items=None, extra_metadata=None):
        self.id = "mock-asset-mig-1"
        self.evidence_items = evidence_items or []
        self.extra_metadata = extra_metadata or {}


def test_migration_complexity_score_bounded_and_configured():
    asset = MockAsset(extra_metadata={
        "business_criticality_score": 80.0,
        "testing_requirement_level": "HIGH",
        "blast_radius_affected_nodes": 10
    })
    res = evaluate_migration_complexity(asset)
    assert isinstance(res, QARSMigrationComplexity)
    assert res.score is not None
    assert 0.0 <= res.score <= 100.0
    assert res.status in ["CONFIGURED", "PARTIALLY_CONFIGURED"]
    assert "business_criticality_score" in res.contributing_factors
    assert res.calibration_version == "SENTRIQ QARS Prototype Heuristic Migration Calibration v1"


def test_migration_complexity_unconfigured_when_no_evidence():
    asset = MockAsset()
    res = evaluate_migration_complexity(asset)
    assert res.score is not None  # Basic scanner factors (files=1, assets=1) are active
    assert res.status == "PARTIALLY_CONFIGURED"


def test_migration_complexity_no_legacy_placeholders_used():
    asset = MockAsset()
    evidence_data = collect_migration_complexity_evidence(asset)
    factors = evidence_data["factors"]
    # Verify legacy effort_estimator defaults (4.0, 0.5, 75.0) are NOT present
    assert factors.get("base_days_per_asset") is None
    assert factors.get("crypto_agility_score") is None
    assert factors.get("business_criticality_score") is None  # Must come from real context, not 75.0 default
