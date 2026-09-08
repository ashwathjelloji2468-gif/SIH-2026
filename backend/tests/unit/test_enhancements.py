import pytest
from app.core.versioning import get_system_versions
from app.discovery.coverage import CoverageEngine
from app.migration.effort_estimator import estimate_migration_effort
from app.migration.sandbox import SandboxEnvironment, SandboxConfig, DEMO_PATTERNS
from app.models.enums import TestingRequirement

def test_versioning_system():
    versions = get_system_versions()
    assert versions["cbom_schema_version"] == "1.6"
    assert "crypto_knowledge_base_version" in versions
    assert "scanner_rule_version" in versions

def test_deepened_migration_effort_estimator():
    res = estimate_migration_effort(
        affected_assets_count=10,
        affected_apps_count=2,
        vendor_dependency_count=2,
        pki_cert_dependency_count=1,
        crypto_agility_score=0.4,
        testing_requirement_level=TestingRequirement.REGULATED,
        business_criticality_score=90.0,
        engineering_capacity_developers=3
    )
    assert res["person_days"] > 0
    assert res["person_months"] > 0
    assert res["calendar_months"] > 0
    assert "assumptions" in res
    assert res["assumptions"]["testing_requirement_level"] == "REGULATED"
    assert res["assumptions"]["vendor_dependency_count"] == 2

def test_sandbox_isolation_and_demo_patterns():
    config = SandboxConfig(allow_network_access=False, requires_human_approval=True)
    sandbox = SandboxEnvironment(plan_id="test-plan-1", config=config)
    sandbox_dir = sandbox.prepare_sandbox("/tmp/non_existent_path")

    # Test RSA_TO_ML_DSA pattern
    res1 = sandbox.apply_transformation_pattern("RSA_TO_ML_DSA")
    assert res1["pattern_applied"] == "RSA_TO_ML_DSA"
    assert res1["isolation"]["network_access"] == "BLOCKED"
    assert res1["isolation"]["human_approval_required_for_production"] is True

    # Test ECDSA_TO_ML_DSA pattern
    res2 = sandbox.apply_transformation_pattern("ECDSA_TO_ML_DSA")
    assert res2["pattern_applied"] == "ECDSA_TO_ML_DSA"

    sandbox.cleanup()

def test_coverage_engine_semantics():
    from app.models.db_models import CryptoAsset
    from app.models.enums import AssetType, ReviewStatus

    # Create mock assets mimicking pyca/cryptography: 636 total, 153 unknown/pending review
    assets = []
    # 483 deterministic algorithm assets
    for i in range(483):
        assets.append(CryptoAsset(id=f"a-{i}", asset_type=AssetType.ALGORITHM, is_unknown=False, review_status=ReviewStatus.RESOLVED))
    # 153 unknown/pending review assets
    for i in range(153):
        assets.append(CryptoAsset(id=f"u-{i}", asset_type=AssetType.ALGORITHM, is_unknown=True, review_status=ReviewStatus.PENDING_REVIEW))

    engine = CoverageEngine()
    report = engine.calculate_project_coverage("test-proj", assets)

    assert report["total_assets_discovered"] == 636
    assert report["unknown_needs_review_count"] == 153
    # 483 / 636 = 75.9%
    assert report["overall_coverage_percentage"] == 75.9
    assert len(report["categories"]) == 6
    cat_names = [c["category_name"] for c in report["categories"]]
    assert "Vendor-Managed Systems" in cat_names
    assert "Binary-only Applications" in cat_names
