import os
import re
from typing import List
from app.scanners.base import BaseScanner, RawFinding
from app.scanners.parsers.python_parser import parse_python_file
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

REGEX_PATTERNS = [
    (r"(?i)\bRSA\b", "RSA", CryptoPurpose.SIGNATURE, AssetType.ALGORITHM),
    (r"(?i)\bECDSA\b", "ECDSA", CryptoPurpose.SIGNATURE, AssetType.ALGORITHM),
    (r"(?i)\bECDH\b", "ECDH", CryptoPurpose.KEY_ESTABLISHMENT, AssetType.ALGORITHM),
    (r"(?i)\bAES(-128|-192|-256)?\b", "AES", CryptoPurpose.ENCRYPTION, AssetType.ALGORITHM),
    (r"(?i)\bSHA-?256\b", "SHA-256", CryptoPurpose.HASHING, AssetType.ALGORITHM),
    (r"(?i)\bMD5\b", "MD5", CryptoPurpose.HASHING, AssetType.ALGORITHM),
    (r"(?i)\bDES\b", "DES", CryptoPurpose.ENCRYPTION, AssetType.ALGORITHM),
    (r"-----BEGIN (RPC|RSA|EC|PRIVATE) KEY-----", "RSA", CryptoPurpose.KEY_ESTABLISHMENT, AssetType.CERTIFICATE),
]

class SourceScanner(BaseScanner):
    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []

        if not os.path.exists(target_path):
            return findings

        for root, _, files in os.walk(target_path):
            for file in files:
                if file.endswith((".py", ".pem", ".key", ".crt", ".json", ".yaml", ".yml")):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, target_path)

                    # Run AST parser on Python files
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
                                context=f"AST detected {item['matched_text']} at line {item['line']}",
                                confidence=0.95,
                                evidence_type=EvidenceType.OBSERVED
                            ))

                    # Run Regex scanner
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            lines = f.readlines()
                        for idx, line in enumerate(lines, start=1):
                            for pattern, alg, purpose, asset_type in REGEX_PATTERNS:
                                if re.search(pattern, line):
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
                    except Exception:
                        continue

        return findings
