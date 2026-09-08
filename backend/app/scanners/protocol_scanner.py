import os
import re
from typing import List, Dict, Any, Optional, Set, Tuple

from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType


# Protocol rules: (regex_pattern, protocol_name, version, status, is_weak, purpose)
PROTOCOL_RULES = [
    # SSL/TLS Specific Versions
    (r"\b(?i:SSLv2|SSL_v2)\b", "SSLv2", "2.0", "deprecated", True, CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:SSLv3|SSL_v3)\b", "SSLv3", "3.0", "deprecated", True, CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:TLSv1\.0|TLSv1_0|TLS1\.0|TLS_1_0)\b", "TLSv1.0", "1.0", "deprecated", True, CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:TLSv1\.1|TLSv1_1|TLS1\.1|TLS_1_1)\b", "TLSv1.1", "1.1", "deprecated", True, CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:TLSv1\.2|TLSv1_2|TLS1\.2|TLS_1_2)\b", "TLSv1.2", "1.2", "active", False, CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:TLSv1\.3|TLSv1_3|TLS1\.3|TLS_1_3)\b", "TLSv1.3", "1.3", "recommended", False, CryptoPurpose.AUTHENTICATION),

    # IPsec / IKE
    (r"\b(?i:IKEv1|IKE_v1)\b", "IKEv1", "1.0", "deprecated", True, CryptoPurpose.KEY_ESTABLISHMENT),
    (r"\b(?i:IKEv2|IKE_v2)\b", "IKEv2", "2.0", "active", False, CryptoPurpose.KEY_ESTABLISHMENT),
    (r"\b(?i:IPsec|IPSEC)\b", "IPsec", None, "active", False, CryptoPurpose.KEY_ESTABLISHMENT),

    # SSH & DTLS & QUIC
    (r"\b(?i:SSH-2\.0|SSH2|sshd_config|libssh2|OpenSSH)\b", "SSH", "2.0", "active", False, CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:DTLSv1\.2|DTLS1\.2|DTLS1\.0)\b", "DTLS", "1.2", "active", False, CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:QUIC|HTTP/3)\b", "QUIC", "1.0", "active", False, CryptoPurpose.AUTHENTICATION),

    # Secure Application Protocols
    (r"\b(?i:SMTPS|LDAPS|FTPS|IMAPS|POP3S)\b", "SECURE-APP-PROTOCOL", None, "active", False, CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:ssl_context|tls_config|SSLContext|TLSContext|ssl_protocol|tls_protocol)\b", "TLS", None, "active", False, CryptoPurpose.AUTHENTICATION),
]

SUPPORTED_EXTENSIONS = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
    ".rb", ".php", ".c", ".cpp", ".h", ".cs", ".yml", ".yaml",
    ".json", ".conf", ".ini", ".env", ".properties", ".toml", ".xml"
)


class ProtocolScanner(BaseScanner):
    """Scan source code and configuration files for cryptographic protocol implementations and configurations."""

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        seen: Set[Tuple[str, int, str]] = set()

        if not os.path.isdir(target_path):
            return findings

        # Compile patterns
        compiled_rules = [(re.compile(pattern), name, ver, status, is_weak, purpose)
                          for pattern, name, ver, status, is_weak, purpose in PROTOCOL_RULES]

        for root, _, files in os.walk(target_path):
            for file in files:
                if not file.lower().endswith(SUPPORTED_EXTENSIONS):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, target_path)

                # Skip large files (> 2MB)
                try:
                    if os.path.getsize(full_path) > 2 * 1024 * 1024:
                        continue
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    continue

                for line_idx, line in enumerate(lines, start=1):
                    line_str = line.strip()
                    if not line_str or line_str.startswith(("#", "//", "/*", "*", "<!--")):
                        continue

                    for regex, proto_name, ver, status, is_weak, purpose in compiled_rules:
                        match = regex.search(line_str)
                        if match:
                            matched_text = match.group(0)
                            key = (rel_path, line_idx, proto_name)
                            if key in seen:
                                continue
                            seen.add(key)

                            weak_reasons = []
                            if is_weak:
                                weak_reasons.append(f"Deprecated/insecure protocol version ({proto_name})")

                            algo_name = f"{proto_name}-{ver}" if ver else proto_name

                            extra_metadata: Dict[str, Any] = {
                                "protocol_name": proto_name,
                                "version": ver,
                                "status": status,
                                "is_weak": is_weak,
                                "weak_reasons": weak_reasons,
                                "matched_text": matched_text,
                                "file_path": rel_path,
                                "line_number": line_idx,
                            }

                            context = f"Cryptographic Protocol '{algo_name}' ({status}) detected in '{rel_path}:{line_idx}'"

                            findings.append(RawFinding(
                                detector_name="ProtocolScanner",
                                target_path=target_path,
                                file_path=rel_path,
                                line_number=line_idx,
                                asset_type=AssetType.PROTOCOL,
                                algorithm_name=algo_name,
                                purpose=purpose,
                                matched_text=matched_text,
                                context=context,
                                confidence=0.9 if ver else 0.8,
                                evidence_type=EvidenceType.OBSERVED,
                                extra_metadata=extra_metadata,
                            ))

        return findings
