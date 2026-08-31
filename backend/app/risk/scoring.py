from app.models.enums import QuantumSafety

def get_quantum_vulnerability_score(algorithm_name: str, quantum_safety: QuantumSafety) -> float:
    alg_upper = algorithm_name.upper()
    if quantum_safety == QuantumSafety.QUANTUM_VULNERABLE:
        if alg_upper in ["RSA", "ECDSA", "ECDH"]:
            return 100.0
        elif alg_upper in ["MD5", "DES"]:
            return 100.0  # Broken classically + quantum
        return 80.0
    elif quantum_safety == QuantumSafety.QUANTUM_SAFE:
        return 0.0
    return 50.0
