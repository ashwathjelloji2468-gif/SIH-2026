from app.models.enums import CryptoPurpose

def classify_purpose(algorithm_name: str, matched_text: str) -> CryptoPurpose:
    text_lower = matched_text.lower()
    alg_upper = algorithm_name.upper()

    if "sign" in text_lower or "verify" in text_lower:
        return CryptoPurpose.SIGNATURE
    elif "encrypt" in text_lower or "cipher" in text_lower or alg_upper == "AES":
        return CryptoPurpose.ENCRYPTION
    elif "hash" in text_lower or alg_upper in ["SHA-256", "MD5"]:
        return CryptoPurpose.HASHING
    elif "dh" in text_lower or "ecdh" in text_lower or "key" in text_lower:
        return CryptoPurpose.KEY_ESTABLISHMENT
    elif alg_upper in ["RSA", "ECDSA"]:
        return CryptoPurpose.SIGNATURE

    return CryptoPurpose.UNKNOWN
