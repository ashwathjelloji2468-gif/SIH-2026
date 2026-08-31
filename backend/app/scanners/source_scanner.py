import os
import re
from typing import List
from app.scanners.base import BaseScanner, RawFinding
from app.scanners.parsers.python_parser import parse_python_file
from app.scanners.parsers.javascript_parser import parse_javascript_file
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

KNOWN_PATTERNS = [
    (r"(?i)\bRSA\b", "RSA", CryptoPurpose.SIGNATURE, AssetType.ALGORITHM),
    (r"(?i)\bECDSA\b", "ECDSA", CryptoPurpose.SIGNATURE, AssetType.ALGORITHM),
    (r"(?i)\bECDH\b", "ECDH", CryptoPurpose.KEY_ESTABLISHMENT, AssetType.ALGORITHM),
    (r"(?i)\bAES(-128|-192|-256)?\b", "AES", CryptoPurpose.ENCRYPTION, AssetType.ALGORITHM),
    (r"(?i)\bSHA-?256\b", "SHA-256", CryptoPurpose.HASHING, AssetType.ALGORITHM),
    (r"(?i)\bSHA-?512\b", "SHA-512", CryptoPurpose.HASHING, AssetType.ALGORITHM),
    (r"(?i)\bMD5\b", "MD5", CryptoPurpose.HASHING, AssetType.ALGORITHM),
    (r"(?i)\bDES\b", "DES", CryptoPurpose.ENCRYPTION, AssetType.ALGORITHM),
    (r"-----BEGIN (RPC|RSA|EC|PRIVATE) KEY-----", "RSA", CryptoPurpose.KEY_ESTABLISHMENT, AssetType.CERTIFICATE),
]

UNKNOWN_PATTERNS = [
    (r"(?i)\b(cipher|crypto|encrypt|decrypt|private_key|public_key|sign_data)\b", "UNKNOWN_ALGORITHM", CryptoPurpose.UNKNOWN, AssetType.ALGORITHM)
]

class SourceScanner(BaseScanner):
    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []

        if not os.path.exists(target_path):
            return findings

        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith((".py", ".js", ".jsx", ".ts", ".tsx", ".pem", ".key", ".crt", ".json", ".yaml", ".yml")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, target_path)

                    # 1. Run AST parser on Python files
                    if file.endswith(".py"):
                        ast_results = parse_python_file(full_path)
                        for item in ast_results:
                            alg = item["algorithm"]
                            purpose = CryptoPurpose.SIGNATURE if alg in ["RSA", "ECDSA"] else (CryptoPurpose.ENCRYPTION if alg == "AES" else CryptoPurpose.HASHING)
                            findings.append(RawFinding(
                                detector_name="PythonASTDetector",
                                target_path=target_path,
                                file_path=rel_path,
                                line_number=item["line"],
                                asset_type=AssetType.API_CALL,
                                algorithm_name=alg if alg != "HASHING" else "SHA-256",
                                purpose=purpose,
                                matched_text=item["matched_text"],
                                context=f"Python AST detected {item['matched_text']} at line {item['line']}",
                                confidence=0.95,
                                evidence_type=EvidenceType.OBSERVED
                            ))

                    # 2. Run JS/TS parser on JavaScript and TypeScript files
                    elif file.endswith((".js", ".jsx", ".ts", ".tsx")):
                        js_results = parse_javascript_file(full_path)
                        for item in js_results:
                            alg = item["algorithm"]
                            purpose_str = item["purpose"]
                            purpose = CryptoPurpose[purpose_str] if purpose_str in CryptoPurpose.__members__ else CryptoPurpose.UNKNOWN
                            asset_type = AssetType.DEPENDENCY if item["type"] == "IMPORT" else AssetType.API_CALL

                            findings.append(RawFinding(
                                detector_name="JavaScriptParser",
                                target_path=target_path,
                                file_path=rel_path,
                                line_number=item["line"],
                                asset_type=asset_type,
                                algorithm_name=alg,
                                purpose=purpose,
                                matched_text=item["matched_text"],
                                context=f"{item['description']} at line {item['line']}",
                                confidence=0.95,
                                evidence_type=EvidenceType.OBSERVED
                            ))

                    # 3. Run Regex scanner for known & unknown patterns
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                        for idx, line in enumerate(lines, start=1):
                            matched_known = False
                            for pattern, alg, purpose, asset_type in KNOWN_PATTERNS:
                                if re.search(pattern, line):
                                    matched_known = True
                                    findings.append(RawFinding(
                                        detector_name="RegexScanner",
                                        target_path=target_path,
                                        file_path=rel_path,
                                        line_number=idx,
                                        asset_type=asset_type,
                                        algorithm_name=alg,
                                        purpose=purpose,
                                        matched_text=line.strip(),
                                        context=f"Regex match '{pattern}' at line {idx}",
                                        confidence=0.85,
                                        evidence_type=EvidenceType.OBSERVED
                                    ))

                            if not matched_known:
                                for pattern, alg, purpose, asset_type in UNKNOWN_PATTERNS:
                                    if re.search(pattern, line):
                                        findings.append(RawFinding(
                                            detector_name="RegexUnknownDetector",
                                            target_path=target_path,
                                            file_path=rel_path,
                                            line_number=idx,
                                            asset_type=asset_type,
                                            algorithm_name="UNKNOWN_ALGORITHM",
                                            purpose=CryptoPurpose.UNKNOWN,
                                            matched_text=line.strip(),
                                            context=f"Potential cryptographic operation detected but algorithm could not be conclusively identified at line {idx}",
                                            confidence=0.50,
                                            evidence_type=EvidenceType.INFERRED,
                                            extra_metadata={"is_unknown": True, "unknown_reason": "Potential cryptographic keyword detected without explicit algorithm identifier."}
                                        ))
                    except Exception:
                        continue

        return findings
