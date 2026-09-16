import pytest
from app.engines.z_engine import ZEngine, CURRENT_YEAR
from app.engines.mosca_engine import MoscaEngine
from app.engines.x_engine import XEngine
from app.engines.y_engine import YEngine

def test_artefact_scoped_z_regression():
    """
    Dedicated regression test suite enforcing artefact-scoped Z_i contract:
    - Shared project X and Y across all components.
    - Component-specific Z_i evaluated independently per component.
    - M_i = X + Y - Z_i for numeric Z_i components.
    - Null numeric Z_i for non-deadline components (AES-256, SHA-256, ML-KEM).
    - Shor-vulnerable artifacts do not blindly receive 10.0 simply because global T_Q is 10.
    - z_score (relative exposure score) remains separate from z_value (years remaining).
    """
    z_engine = ZEngine(default_horizon=10)
    mosca_engine = MoscaEngine()

    # Shared project parameters
    project_x = 7
    project_y_scenario = "FAST" # Y = 5 years

    artifacts = [
        {"id": "art-rsa-1024", "algorithm_name": "RSA-1024", "primitive": "RSA", "key_size": 1024, "purpose": "ENCRYPTION"},
        {"id": "art-rsa-2048", "algorithm_name": "RSA-2048", "primitive": "RSA", "key_size": 2048, "purpose": "SIGNATURE"},
        {"id": "art-rsa-4096", "algorithm_name": "RSA-4096", "primitive": "RSA", "key_size": 4096, "purpose": "SIGNATURE"},
        {"id": "art-ecdsa-p256", "algorithm_name": "ECDSA-P256", "primitive": "ECDSA", "key_size": 256, "purpose": "SIGNATURE"},
        {"id": "art-ecdsa-p384", "algorithm_name": "ECDSA-P384", "primitive": "ECDSA", "key_size": 384, "purpose": "SIGNATURE"},
        {"id": "art-ecdh-p256", "algorithm_name": "ECDH-P256", "primitive": "ECDH", "key_size": 256, "purpose": "ECDH"},
        {"id": "art-[#3des]", "algorithm_name": "3DES", "primitive": "3DES", "purpose": "ENCRYPTION"},
        {"id": "art-aes-256", "algorithm_name": "AES-256-GCM", "primitive": "AES", "key_size": 256, "purpose": "ENCRYPTION"},
        {"id": "art-sha-256", "algorithm_name": "SHA-256", "primitive": "SHA", "output_size": 256, "purpose": "HASHING"},
        {"id": "art-ml-kem", "algorithm_name": "ML-KEM-768", "primitive": "ML-KEM", "purpose": "KEY_EXCHANGE"},
    ]

    results = {}
    for art in artifacts:
        eval_res = mosca_engine.evaluate_component_mosca(
            component=art,
            user_x_years=project_x,
            user_y_scenario=project_y_scenario
        )
        results[art["id"]] = eval_res

    # Assertion 1 & 2: X is identical for every artifact and matches project X (7 years)
    for art_id, res in results.items():
        assert res["x"]["value"] == 7.0, f"X value mismatch for {art_id}"

    # Assertion 3 & 4: Y is identical for every artifact and matches project Y (5 years for FAST)
    for art_id, res in results.items():
        assert res["y"]["value"] == 5.0, f"Y value mismatch for {art_id}"

    # Assertion 5 & 6: Z_i is calculated independently and Shor-vulnerable components do not all get 10.0
    rsa_1024_z = results["art-rsa-1024"]["z"]["z_value"]
    rsa_2048_z = results["art-rsa-2048"]["z"]["z_value"]
    rsa_4096_z = results["art-rsa-4096"]["z"]["z_value"]
    ecdsa_p384_z = results["art-ecdsa-p384"]["z"]["z_value"]
    ecdh_p256_z = results["art-ecdh-p256"]["z"]["z_value"]

    assert rsa_1024_z != rsa_2048_z, "RSA-1024 and RSA-2048 should have different Z_i values"
    assert rsa_2048_z != rsa_4096_z, "RSA-2048 and RSA-4096 should have different Z_i values"
    assert ecdsa_p384_z != rsa_2048_z, "ECDSA-P384 and RSA-2048 should have different Z_i values"
    assert ecdh_p256_z < rsa_2048_z, "ECDH-P256 (key exchange) should have lower Z_i (tighter deadline) than RSA-2048 signature"

    # Assertion 7: z_score (relative risk score) remains distinct from z_value (years remaining)
    for art_id, res in results.items():
        z_dict = res["z"]
        if z_dict["z_value"] is not None:
            assert z_dict["z_score"] != z_dict["z_value"], f"z_score must be distinct from z_value for {art_id}"

    # Assertion 8: Non-deadline artifacts (AES-256, SHA-256, ML-KEM) retain null numeric Z semantics
    for art_id in ["art-aes-256", "art-sha-256", "art-ml-kem"]:
        z_dict = results[art_id]["z"]
        assert z_dict["z_value"] is None, f"{art_id} must have null z_value"
        assert z_dict["z_planning_horizon_years"] is None, f"{art_id} must have null z_planning_horizon_years"
        assert z_dict["z_target_year"] is None, f"{art_id} must have null z_target_year"

    # Assertion 9: Numeric target year equals CURRENT_YEAR + int(round(z_value))
    for art_id, res in results.items():
        z_dict = res["z"]
        if z_dict["z_value"] is not None:
            expected_target = CURRENT_YEAR + int(round(z_dict["z_value"]))
            assert z_dict["z_target_year"] == expected_target, f"Target year mismatch for {art_id}"

    # Assertion 10: Mosca equals exactly X + Y - Z_i whenever Z_i is numeric
    for art_id, res in results.items():
        z_val = res["z"]["z_value"]
        if z_val is not None:
            expected_m = 7.0 + 5.0 - z_val
            assert abs(res["mosca_score"] - expected_m) < 1e-5, f"M_i calculation mismatch for {art_id}"

    # Assertion 11: Changing project X changes X and M_i but does NOT change artifact Z_i
    res_x12 = mosca_engine.evaluate_component_mosca(
        component=artifacts[1], # RSA-2048
        user_x_years=12,
        user_y_scenario="FAST"
    )
    assert res_x12["x"]["value"] == 12.0
    assert res_x12["z"]["z_value"] == rsa_2048_z
    assert abs(res_x12["mosca_score"] - (12.0 + 5.0 - rsa_2048_z)) < 1e-5

    # Assertion 12: Changing project Y changes Y and M_i but does NOT change artifact Z_i
    res_y_complex = mosca_engine.evaluate_component_mosca(
        component=artifacts[1], # RSA-2048
        user_x_years=7,
        user_y_scenario="COMPLEX" # Y = 15
    )
    assert res_y_complex["y"]["value"] == 15.0
    assert res_y_complex["z"]["z_value"] == rsa_2048_z
    assert abs(res_y_complex["mosca_score"] - (7.0 + 15.0 - rsa_2048_z)) < 1e-5

    # Assertion 13: Changing an artifact-specific Z input (e.g. key_size 1024 -> 4096) changes only Z and M_i for that artifact
    art_mod = dict(artifacts[1])
    art_mod["key_size"] = 4096
    res_mod = mosca_engine.evaluate_component_mosca(component=art_mod, user_x_years=7, user_y_scenario="FAST")
    assert res_mod["z"]["z_value"] == rsa_4096_z
    assert res_mod["z"]["z_value"] != rsa_2048_z

    # Assertion 14: No old 2033/2036 fallback is used as canonical Z for non-deadline components
    for art_id in ["art-aes-256", "art-sha-256", "art-ml-kem"]:
        assert results[art_id]["z"]["z_target_year"] is None
        assert results[art_id]["z"]["z_value"] is None
