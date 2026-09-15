import pytest
from app.cbom.comparator import CBOMComparator

def sample_cbom(components):
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "components": components
    }

def create_component(name="RSA-2048", bom_ref="ref-1", asset_type="ALGORITHM", alg="RSA", key_size="2048", primitive="ENCRYPTION", qs_level=0, location="main.py", line=10):
    return {
        "type": "cryptographic",
        "name": name,
        "bom-ref": bom_ref,
        "cryptoProperties": {
            "assetType": asset_type,
            "algorithmProperties": {
                "primitive": primitive,
                "parameterSetIdentifier": str(key_size),
                "cryptoFunctions": [primitive]
            },
            "classicalSecurityLevel": 112,
            "nistQuantumSecurityLevel": qs_level
        },
        "evidence": {
            "occurrences": [
                {
                    "location": location,
                    "line": line
                }
            ]
        }
    }

def test_cbom_comparator_identical_cboms():
    comp1 = create_component("RSA-2048", "ref-1", "ALGORITHM", "RSA", "2048", "ENCRYPTION", 0, "main.py", 10)
    before = sample_cbom([comp1])
    after = sample_cbom([comp1])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "NO_CHANGE"
    assert res["before_component_count"] == 1
    assert res["after_component_count"] == 1
    assert res["changed_count"] == 0
    assert res["unchanged_count"] == 1

def test_cbom_comparator_added_component():
    comp1 = create_component("RSA-2048", "ref-1", "ALGORITHM", "RSA", "2048", "ENCRYPTION", 0, "main.py", 10)
    comp2 = create_component("AES-256", "ref-2", "ALGORITHM", "AES", "256", "ENCRYPTION", 1, "util.py", 20)
    before = sample_cbom([comp1])
    after = sample_cbom([comp1, comp2])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "CHANGED"
    assert res["added_count"] == 1
    assert res["added"][0]["name"] == "AES-256"

def test_cbom_comparator_removed_component():
    comp1 = create_component("RSA-2048", "ref-1", "ALGORITHM", "RSA", "2048", "ENCRYPTION", 0, "main.py", 10)
    before = sample_cbom([comp1])
    after = sample_cbom([])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "CHANGED"
    assert res["removed_count"] == 1
    assert res["removed"][0]["name"] == "RSA-2048"

def test_cbom_comparator_algorithm_changed():
    comp_before = create_component("RSA-2048", "ref-1", "ALGORITHM", "RSA", "2048", "ENCRYPTION", 0, "main.py", 10)
    comp_after = create_component("ML-KEM-768", "ref-1", "ALGORITHM", "ML-KEM", "768", "ENCRYPTION", 1, "main.py", 10)

    before = sample_cbom([comp_before])
    after = sample_cbom([comp_after])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "CHANGED"
    assert res["changed_count"] == 1
    ch = res["changed"][0]
    assert ch["before_properties"]["algorithm"] == "RSA"
    assert ch["after_properties"]["algorithm"] == "ML-KEM"
    assert ch["before_properties"]["quantum_safety"] == "QUANTUM_VULNERABLE"
    assert ch["after_properties"]["quantum_safety"] == "QUANTUM_SAFE"

def test_cbom_comparator_key_size_changed():
    comp_before = create_component("RSA-1024", "ref-1", "ALGORITHM", "RSA", "1024", "ENCRYPTION", 0, "main.py", 10)
    comp_after = create_component("RSA-4096", "ref-1", "ALGORITHM", "RSA", "4096", "ENCRYPTION", 0, "main.py", 10)

    before = sample_cbom([comp_before])
    after = sample_cbom([comp_after])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "CHANGED"
    assert res["changed_count"] == 1
    ch = res["changed"][0]
    assert "key_size" in ch["changes"]

def test_cbom_comparator_quantum_status_changed():
    comp_before = create_component("AES-128", "ref-1", "ALGORITHM", "AES", "128", "ENCRYPTION", 0, "main.py", 10)
    comp_after = create_component("AES-256", "ref-1", "ALGORITHM", "AES", "256", "ENCRYPTION", 1, "main.py", 10)

    before = sample_cbom([comp_before])
    after = sample_cbom([comp_after])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "CHANGED"
    assert res["changed_count"] == 1
    ch = res["changed"][0]
    assert ch["changes"]["quantum_safety"]["before"] == "QUANTUM_VULNERABLE"
    assert ch["changes"]["quantum_safety"]["after"] == "QUANTUM_SAFE"

def test_cbom_comparator_multiple_changes():
    comp1 = create_component("RSA-2048", "ref-1", "ALGORITHM", "RSA", "2048", "ENCRYPTION", 0, "main.py", 10)
    comp2 = create_component("SHA-1", "ref-2", "ALGORITHM", "SHA", "1", "HASHING", 0, "hash.py", 5)

    comp1_migrated = create_component("ML-KEM-768", "ref-1", "ALGORITHM", "ML-KEM", "768", "ENCRYPTION", 1, "main.py", 10)
    comp3_new = create_component("ML-DSA-65", "ref-3", "ALGORITHM", "ML-DSA", "65", "SIGNATURE", 1, "sign.py", 15)

    before = sample_cbom([comp1, comp2])
    after = sample_cbom([comp1_migrated, comp3_new])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "CHANGED"
    assert res["changed_count"] == 1
    assert res["removed_count"] == 1
    assert res["added_count"] == 1

def test_cbom_comparator_all_unchanged():
    c1 = create_component("RSA-2048", "ref-1")
    c2 = create_component("AES-256", "ref-2")

    before = sample_cbom([c1, c2])
    after = sample_cbom([c1, c2])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "NO_CHANGE"
    assert res["unchanged_count"] == 2

def test_cbom_comparator_invalid_cbom():
    comparator = CBOMComparator()
    res = comparator.compare(None, {})
    assert res["status"] == "INVALID_CBOM"

    res2 = comparator.compare({"invalid": True}, sample_cbom([]))
    assert res2["status"] == "INVALID_CBOM"

def test_cbom_comparator_missing_cbom():
    comparator = CBOMComparator()
    res = comparator.compare(sample_cbom([]), None)
    assert res["status"] == "INVALID_CBOM"

def test_cbom_comparator_stable_identity_fallback():
    # Without matching bom-ref, fallback to (location, line)
    comp_before = create_component("RSA-2048", "ref-old", "ALGORITHM", "RSA", "2048", "ENCRYPTION", 0, "src/auth.py", 42)
    comp_after = create_component("ML-KEM-768", "ref-new", "ALGORITHM", "ML-KEM", "768", "ENCRYPTION", 1, "src/auth.py", 42)

    before = sample_cbom([comp_before])
    after = sample_cbom([comp_after])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "CHANGED"
    assert res["changed_count"] == 1
    assert res["changed"][0]["location"] == "src/auth.py:42"

def test_cbom_comparator_unrelated_replacement():
    # Completely different location and identity -> REMOVED + ADDED
    comp_before = create_component("RSA-2048", "ref-1", "ALGORITHM", "RSA", "2048", "ENCRYPTION", 0, "old_file.py", 10)
    comp_after = create_component("ML-KEM-768", "ref-2", "ALGORITHM", "ML-KEM", "768", "ENCRYPTION", 1, "new_file.py", 99)

    before = sample_cbom([comp_before])
    after = sample_cbom([comp_after])

    comparator = CBOMComparator()
    res = comparator.compare(before, after)

    assert res["status"] == "CHANGED"
    assert res["removed_count"] == 1
    assert res["added_count"] == 1
    assert res["changed_count"] == 0
