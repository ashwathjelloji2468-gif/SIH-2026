import unittest
from types import SimpleNamespace
from app.context.effective_context import resolve_effective_artifact_context
from app.risk.risk_engine import RiskEngine
from app.risk.mosca import calculate_mosca_analysis
from app.engines.z_engine import ZEngine
from app.risk.scoring import calculate_deterministic_risk_score

class DummyAsset:
    def __init__(self, id="asset_1", algorithm_name="RSA-2048", purpose="SIGNATURE", asset_type="ALGORITHM", location="/src/crypto.py", extra_metadata=None):
        self.id = id
        self.algorithm_name = algorithm_name
        self.purpose = purpose
        self.asset_type = asset_type
        self.location = location
        self.quantum_safety = "VULNERABLE"
        self.extra_metadata = extra_metadata or {}
        self.evidence_items = []
        self.business_criticality_label = "HIGH"

class DummyProject:
    def __init__(self, user_x_years=10, business_context=None, folder_contexts=None):
        self.id = "proj_1"
        self.name = "Test Project"
        self.description = "Test Desc"
        self.repository_url = None
        self.user_x_years = user_x_years
        self.user_domain = None
        self.user_y_scenario = None
        self.folder_contexts = folder_contexts or {}
        self.business_context = {
            "factor_ratings": {
                "dataSensitivity": 4,
                "regulatoryExposure": 5,
                "financialImpact": 5,
                "availabilityImpact": 4,
                "integrityImpact": 4,
                "exposureRating": 4
            }
        } if business_context is None else business_context

class TestEffectiveArtifactContext(unittest.TestCase):

    def test_1_no_overrides_inherits_defaults(self):
        asset = DummyAsset()
        project = DummyProject(user_x_years=10)
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["x_years"], 10.0)
        self.assertEqual(ctx["data_sensitivity"], 4)
        self.assertEqual(ctx["sources"]["x_years"], "USER_OVERRIDE")
        self.assertEqual(ctx["sources"]["data_sensitivity"], "APPLICATION_DEFAULT")

    def test_2_x_override_works(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"x_years": 25}})
        project = DummyProject(user_x_years=10)
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["x_years"], 25.0)
        self.assertEqual(ctx["sources"]["x_years"], "ARTIFACT_EVIDENCE")

    def test_3_data_sensitivity_override_works(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"data_sensitivity": 5}})
        project = DummyProject()
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["data_sensitivity"], 5)
        self.assertEqual(ctx["sources"]["data_sensitivity"], "ARTIFACT_EVIDENCE")

    def test_4_business_criticality_override_works(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"business_criticality": "CRITICAL"}})
        project = DummyProject()
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["business_criticality"], "CRITICAL")
        self.assertEqual(ctx["sources"]["business_criticality"], "ARTIFACT_EVIDENCE")

    def test_5_regulatory_impact_override_works(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"regulatory_impact": 2}})
        project = DummyProject()
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["regulatory_impact"], 2)
        self.assertEqual(ctx["sources"]["regulatory_impact"], "ARTIFACT_EVIDENCE")

    def test_6_financial_impact_override_works(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"financial_impact": 1}})
        project = DummyProject()
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["financial_impact"], 1)
        self.assertEqual(ctx["sources"]["financial_impact"], "ARTIFACT_EVIDENCE")

    def test_7_operational_impact_override_works(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"operational_impact": 5}})
        project = DummyProject()
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["operational_impact"], 5)
        self.assertEqual(ctx["sources"]["operational_impact"], "ARTIFACT_EVIDENCE")

    def test_8_exposure_override_works(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"exposure": "INTERNAL"}})
        project = DummyProject()
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["exposure"], "INTERNAL")
        self.assertEqual(ctx["sources"]["exposure"], "ARTIFACT_EVIDENCE")

    def test_9_fields_resolve_independently(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"x_years": 15, "exposure": "INTERNAL"}})
        project = DummyProject(user_x_years=10)
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["x_years"], 15.0)
        self.assertEqual(ctx["exposure"], "INTERNAL")
        self.assertEqual(ctx["data_sensitivity"], 4)
        self.assertEqual(ctx["sources"]["x_years"], "ARTIFACT_EVIDENCE")
        self.assertEqual(ctx["sources"]["exposure"], "ARTIFACT_EVIDENCE")
        self.assertEqual(ctx["sources"]["data_sensitivity"], "APPLICATION_DEFAULT")

    def test_10_existing_user_override_remains_authoritative(self):
        asset = DummyAsset()
        project = DummyProject(user_x_years=12)
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["x_years"], 12.0)
        self.assertEqual(ctx["sources"]["x_years"], "USER_OVERRIDE")

    def test_11_folder_x_context_remains_functional(self):
        asset = DummyAsset(location="src/secure/crypto.py")
        project = DummyProject(user_x_years=None, folder_contexts={"src/secure/crypto.py": {"user_x_years": 18}})
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["x_years"], 18.0)
        self.assertEqual(ctx["sources"]["x_years"], "USER_OVERRIDE")

    def test_12_invalid_override_is_not_treated_as_artifact_evidence(self):
        asset = DummyAsset(extra_metadata={"context_overrides": {"x_years": -5, "exposure": "INVALID_EXP"}})
        project = DummyProject(user_x_years=10)
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["x_years"], 10.0)
        self.assertEqual(ctx["sources"]["x_years"], "USER_OVERRIDE")
        self.assertEqual(ctx["exposure"], "EXTERNAL_FACING")
        self.assertEqual(ctx["sources"]["exposure"], "APPLICATION_DEFAULT")

    def test_13_missing_business_context_uses_defaults(self):
        asset = DummyAsset()
        project = DummyProject(business_context={})
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(ctx["data_sensitivity"], 5)
        self.assertEqual(ctx["regulatory_impact"], 5)

    def test_14_unrelated_extra_metadata_survives(self):
        asset = DummyAsset(extra_metadata={"custom_tag": "prod_1", "context_overrides": {"x_years": 8}})
        project = DummyProject()
        ctx = resolve_effective_artifact_context(asset, project)
        self.assertEqual(asset.extra_metadata["custom_tag"], "prod_1")
        self.assertEqual(asset.extra_metadata["effective_context"], ctx)

    def test_15_16_17_risk_service_effective_values(self):
        asset_a = DummyAsset(id="a", extra_metadata={"context_overrides": {"x_years": 20}})
        asset_b = DummyAsset(id="b", extra_metadata={"context_overrides": {"x_years": 5}})
        project = DummyProject(user_x_years=10)

        ctx_a = resolve_effective_artifact_context(asset_a, project)
        ctx_b = resolve_effective_artifact_context(asset_b, project)

        self.assertEqual(ctx_a["x_years"], 20.0)
        self.assertEqual(ctx_b["x_years"], 5.0)

        engine = RiskEngine()
        res_a = engine.evaluate_asset_risk(
            algorithm_name=asset_a.algorithm_name,
            quantum_safety="VULNERABLE",
            purpose="SIGNATURE",
            asset_type="ALGORITHM",
            data_lifetime_years=ctx_a["x_years"]
        )
        res_b = engine.evaluate_asset_risk(
            algorithm_name=asset_b.algorithm_name,
            quantum_safety="VULNERABLE",
            purpose="SIGNATURE",
            asset_type="ALGORITHM",
            data_lifetime_years=ctx_b["x_years"]
        )
        self.assertEqual(res_a["factors"]["x_years"], 20.0)
        self.assertEqual(res_b["factors"]["x_years"], 5.0)

    def test_18_mosca_receives_effective_artifact_x(self):
        mosca_a = calculate_mosca_analysis(data_lifetime_years=20.0, migration_time_years=10.0, quantum_threat_horizon_year=2036)
        mosca_b = calculate_mosca_analysis(data_lifetime_years=10.0, migration_time_years=10.0, quantum_threat_horizon_year=2036)
        self.assertEqual(mosca_a["urgency_gap_years"], 20.0)
        self.assertEqual(mosca_b["urgency_gap_years"], 10.0)

    def test_19_z_i_remains_unchanged(self):
        comp = {
            "id": "c1",
            "algorithm_name": "RSA-2048",
            "primitive": "RSA-2048",
            "purpose": "SIGNATURE",
            "asset_type": "ALGORITHM",
            "location": "/src/main.py",
            "key_size": 2048
        }
        z_res = ZEngine().evaluate_component(comp)
        self.assertEqual(z_res["z_value"], 10.0)

    def test_20_risk_weights_formula_unchanged(self):
        score = calculate_deterministic_risk_score(
            quantum_exposure=100.0,
            data_sensitivity=100.0,
            business_criticality=100.0,
            migration_complexity=100.0,
            lifetime_exposure=100.0
        )
        self.assertEqual(score, 100.0)
        partial = calculate_deterministic_risk_score(
            quantum_exposure=100.0,
            data_sensitivity=0.0,
            business_criticality=0.0,
            migration_complexity=0.0,
            lifetime_exposure=0.0
        )
        self.assertEqual(partial, 30.0)

    def test_mandatory_integration_test(self):
        project = DummyProject(
            user_x_years=10,
            business_context={
                "factor_ratings": {
                    "dataSensitivity": 4,
                    "regulatoryExposure": 5,
                    "financialImpact": 5,
                    "availabilityImpact": 4,
                    "integrityImpact": 4,
                    "exposureRating": 4
                }
            }
        )

        asset_a = DummyAsset(id="A", extra_metadata={"context_overrides": {"x_years": 20, "exposure": "INTERNAL"}})
        asset_b = DummyAsset(id="B")

        ctx_a = resolve_effective_artifact_context(asset_a, project)
        ctx_b = resolve_effective_artifact_context(asset_b, project)

        self.assertEqual(ctx_a["x_years"], 20.0)
        self.assertEqual(ctx_a["exposure"], "INTERNAL")
        self.assertEqual(ctx_a["data_sensitivity"], 4)

        self.assertEqual(ctx_b["x_years"], 10.0)
        self.assertEqual(ctx_b["exposure"], "EXTERNAL_FACING")
        self.assertEqual(ctx_b["data_sensitivity"], 4)

        engine = RiskEngine()
        risk_a = engine.evaluate_asset_risk(
            algorithm_name="RSA-2048", quantum_safety="VULNERABLE", purpose="SIGNATURE", asset_type="ALGORITHM",
            data_lifetime_years=ctx_a["x_years"]
        )
        risk_b = engine.evaluate_asset_risk(
            algorithm_name="RSA-2048", quantum_safety="VULNERABLE", purpose="SIGNATURE", asset_type="ALGORITHM",
            data_lifetime_years=ctx_b["x_years"]
        )
        self.assertEqual(risk_a["factors"]["x_years"], 20.0)
        self.assertEqual(risk_b["factors"]["x_years"], 10.0)

        mosca_a = calculate_mosca_analysis(data_lifetime_years=ctx_a["x_years"])
        mosca_b = calculate_mosca_analysis(data_lifetime_years=ctx_b["x_years"])

        self.assertEqual(mosca_a["urgency_gap_years"], 20.0)
        self.assertEqual(mosca_b["urgency_gap_years"], 10.0)

        comp = {"id": "1", "algorithm_name": "RSA-2048", "primitive": "RSA-2048", "purpose": "SIGNATURE", "asset_type": "ALGORITHM", "location": "a.py", "key_size": 2048}
        self.assertEqual(ZEngine().evaluate_component(comp)["z_value"], 10.0)

if __name__ == "__main__":
    unittest.main()
