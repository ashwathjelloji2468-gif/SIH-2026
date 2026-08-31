import re
from typing import List, Dict, Any

JS_CRYPTO_PATTERNS = [
    # Node.js crypto module & APIs
    (r"crypto\.generateKeyPair(?:Sync)?\(\s*['\"]rsa['\"]", "RSA", "SIGNATURE", "Node.js crypto RSA key pair generation"),
    (r"crypto\.generateKeyPair(?:Sync)?\(\s*['\"]ec['\"]", "ECDSA", "SIGNATURE", "Node.js crypto EC key pair generation"),
    (r"crypto\.createCipheriv\(\s*['\"]aes-(128|192|256)-(gcm|cbc|ctr)['\"]", "AES", "ENCRYPTION", "Node.js AES cipher creation"),
    (r"crypto\.createCipheriv\(\s*['\"]des-", "DES", "ENCRYPTION", "Node.js legacy DES cipher creation"),
    (r"crypto\.createHash\(\s*['\"]sha256['\"]", "SHA-256", "HASHING", "Node.js SHA-256 hash creation"),
    (r"crypto\.createHash\(\s*['\"]sha512['\"]", "SHA-512", "HASHING", "Node.js SHA-512 hash creation"),
    (r"crypto\.createHash\(\s*['\"]md5['\"]", "MD5", "HASHING", "Node.js MD5 hash creation"),
    (r"crypto\.createHmac\(\s*['\"]sha256['\"]", "SHA-256", "MAC", "Node.js HMAC-SHA256 creation"),

    # Web Crypto API
    (r"crypto\.subtle\.generateKey\([^)]*['\"]RSA-", "RSA", "KEY_ESTABLISHMENT", "Web Crypto API RSA key generation"),
    (r"crypto\.subtle\.generateKey\([^)]*['\"]ECDSA['\"]", "ECDSA", "SIGNATURE", "Web Crypto API ECDSA key generation"),
    (r"crypto\.subtle\.encrypt\([^)]*['\"]AES-", "AES", "ENCRYPTION", "Web Crypto API AES encryption"),

    # Popular Libraries (CryptoJS, forge, jose, jsonwebtoken, tweetnacl)
    (r"CryptoJS\.AES\.encrypt", "AES", "ENCRYPTION", "CryptoJS AES encryption call"),
    (r"CryptoJS\.SHA256", "SHA-256", "HASHING", "CryptoJS SHA-256 call"),
    (r"CryptoJS\.MD5", "MD5", "HASHING", "CryptoJS legacy MD5 call"),
    (r"forge\.pki\.rsa\.generateKeyPair", "RSA", "SIGNATURE", "node-forge RSA key generation"),
    (r"jwt\.sign", "RSA", "SIGNATURE", "jsonwebtoken JWT signing"),
    (r"jose\.SignJWT", "RSA", "SIGNATURE", "jose JWT signature creation"),
    (r"nacl\.sign", "ECDSA", "SIGNATURE", "tweetnacl signature creation")
]

JS_IMPORT_PATTERNS = [
    (r"(?:const|let|var|import)\s+.*?\s*=?\s*require\(['\"](?:crypto|crypto-js|node-forge|jose|jsonwebtoken|tweetnacl)['\"]\)", "CryptoLibrary", "UNKNOWN", "JavaScript Crypto Library Import"),
    (r"import\s+.*?\s+from\s+['\"](?:crypto|crypto-js|node-forge|jose|jsonwebtoken|tweetnacl)['\"]", "CryptoLibrary", "UNKNOWN", "ES Module Crypto Library Import")
]

def parse_javascript_file(file_path: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        for idx, line in enumerate(lines, start=1):
            line_str = line.strip()

            # Check API calls & crypto constructs
            for pattern, alg, purpose, desc in JS_CRYPTO_PATTERNS:
                if re.search(pattern, line_str):
                    findings.append({
                        "line": idx,
                        "algorithm": alg,
                        "purpose": purpose,
                        "matched_text": line_str,
                        "type": "API_CALL",
                        "description": desc
                    })

            # Check Imports
            for pattern, alg, purpose, desc in JS_IMPORT_PATTERNS:
                if re.search(pattern, line_str):
                    findings.append({
                        "line": idx,
                        "algorithm": alg,
                        "purpose": purpose,
                        "matched_text": line_str,
                        "type": "IMPORT",
                        "description": desc
                    })

    except Exception:
        pass

    return findings
