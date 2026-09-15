import os
import re
from typing import List, Dict, Any, Optional, Set, Tuple

from app.scanners.base import BaseScanner, RawFinding, IGNORE_DIRS
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

# Protocol rules: (regex_pattern, protocol_name, version, status, is_weak, purpose, confidence)
PROTOCOL_RULES = [
    # Explicit SSL/TLS Versions
    (r"\b(?i:SSLv2|SSL_v2)\b", "SSLv2", "2.0", "deprecated", True, CryptoPurpose.AUTHENTICATION, 1.0),
    (r"\b(?i:SSLv3|SSL_v3)\b", "SSLv3", "3.0", "deprecated", True, CryptoPurpose.AUTHENTICATION, 1.0),
    (r"\b(?i:TLSv1\.0|TLSv1_0|TLS1\.0|TLS_1_0)\b", "TLSv1.0", "1.0", "deprecated", True, CryptoPurpose.AUTHENTICATION, 1.0),
    (r"\b(?i:TLSv1\.1|TLSv1_1|TLS1\.1|TLS_1_1)\b", "TLSv1.1", "1.1", "deprecated", True, CryptoPurpose.AUTHENTICATION, 1.0),
    (r"\b(?i:TLSv1\.2|TLSv1_2|TLS1\.2|TLS_1_2)\b", "TLSv1.2", "1.2", "active", False, CryptoPurpose.AUTHENTICATION, 1.0),
    (r"\b(?i:TLSv1\.3|TLSv1_3|TLS1\.3|TLS_1_3)\b", "TLSv1.3", "1.3", "recommended", False, CryptoPurpose.AUTHENTICATION, 1.0),

    # TLS Cipher Suites
    (r"\bTLS_AES_128_GCM_SHA256\b", "TLS_AES_128_GCM_SHA256", "TLS1.3", "recommended", False, CryptoPurpose.ENCRYPTION, 1.0),
    (r"\bTLS_AES_256_GCM_SHA384\b", "TLS_AES_256_GCM_SHA384", "TLS1.3", "recommended", False, CryptoPurpose.ENCRYPTION, 1.0),
    (r"\bTLS_CHACHA20_POLY1305_SHA256\b", "TLS_CHACHA20_POLY1305_SHA256", "TLS1.3", "recommended", False, CryptoPurpose.ENCRYPTION, 1.0),
    (r"\bECDHE-RSA-AES128-GCM-SHA256\b", "ECDHE-RSA-AES128-GCM-SHA256", "TLS1.2", "active", True, CryptoPurpose.KEY_ESTABLISHMENT, 1.0),
    (r"\bECDHE-ECDSA-AES128-GCM-SHA256\b", "ECDHE-ECDSA-AES128-GCM-SHA256", "TLS1.2", "active", True, CryptoPurpose.KEY_ESTABLISHMENT, 1.0),
    (r"\bDHE-RSA-AES256-GCM-SHA384\b", "DHE-RSA-AES256-GCM-SHA384", "TLS1.2", "active", True, CryptoPurpose.KEY_ESTABLISHMENT, 1.0),

    # IPsec / IKE
    (r"\b(?i:IKEv1|IKE_v1)\b", "IKEv1", "1.0", "deprecated", True, CryptoPurpose.KEY_ESTABLISHMENT, 0.95),
    (r"\b(?i:IKEv2|IKE_v2)\b", "IKEv2", "2.0", "active", False, CryptoPurpose.KEY_ESTABLISHMENT, 0.95),
    (r"\b(?i:IPsec|IPSEC)\b", "IPsec", None, "active", False, CryptoPurpose.KEY_ESTABLISHMENT, 0.90),

    # SSH Explicit Algorithms & Hybrid/PQC Kex
    (r"\bssh-rsa\b", "SSH-RSA", "2.0", "deprecated", True, CryptoPurpose.SIGNATURE, 1.0),
    (r"\bssh-ed25519\b", "SSH-Ed25519", "2.0", "active", False, CryptoPurpose.SIGNATURE, 1.0),
    (r"\becdsa-sha2-nistp256\b", "SSH-ECDSA-P256", "2.0", "active", True, CryptoPurpose.SIGNATURE, 1.0),
    (r"\becdsa-sha2-nistp384\b", "SSH-ECDSA-P384", "2.0", "active", True, CryptoPurpose.SIGNATURE, 1.0),
    (r"\becdsa-sha2-nistp521\b", "SSH-ECDSA-P521", "2.0", "active", True, CryptoPurpose.SIGNATURE, 1.0),
    (r"\bdiffie-hellman-group14-sha1\b", "SSH-DH-Group14-SHA1", "2.0", "deprecated", True, CryptoPurpose.KEY_ESTABLISHMENT, 1.0),
    (r"\bdiffie-hellman-group14-sha256\b", "SSH-DH-Group14-SHA256", "2.0", "active", True, CryptoPurpose.KEY_ESTABLISHMENT, 1.0),
    (r"\bcurve25519-sha256\b", "SSH-Curve25519-SHA256", "2.0", "active", False, CryptoPurpose.KEY_ESTABLISHMENT, 1.0),
    (r"\bsntrup761x25519-sha512\b", "SSH-SNTRUP761-Hybrid", "2.0", "recommended", False, CryptoPurpose.KEY_ESTABLISHMENT, 1.0),
    (r"\bmlkem768x25519-sha256\b", "SSH-MLKEM768-Hybrid", "2.0", "recommended", False, CryptoPurpose.KEY_ESTABLISHMENT, 1.0),

    # SSH Configurations & Libraries
    (r"\b(HostKey|HostKeyAlgorithms|KexAlgorithms|Ciphers|MACs|PubkeyAcceptedAlgorithms|CASignatureAlgorithms)\b", "SSH_CONFIG", None, "active", False, CryptoPurpose.AUTHENTICATION, 0.95),
    (r"\b(Paramiko|paramiko|JSch|jsch|Apache MINA SSHD|libssh|libssh2|OpenSSH)\b", "SSH_LIBRARY", None, "active", False, CryptoPurpose.AUTHENTICATION, 0.90),

    # Generic TLS/SSL Generic APIs (Version unassigned unless explicit version on line)
    (r"\b(?i:SSLContext|TLSContext|ssl_context|tls_config|SSL_CTX_new|SSL_connect|TLSSocket|ssl_protocol|tls_protocol)\b", "TLS", None, "active", False, CryptoPurpose.AUTHENTICATION, 0.80),
]

SUPPORTED_EXTENSIONS = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
    ".rb", ".php", ".c", ".cpp", ".h", ".cs", ".yml", ".yaml",
    ".json", ".conf", ".ini", ".env", ".properties", ".toml", ".xml",
    "sshd_config", "ssh_config", "nginx.conf", "haproxy.cfg", "httpd.conf", "openssl.cnf"
)


class ProtocolScanner(BaseScanner):
    """Scan source code and configuration files for cryptographic protocol implementations and configurations."""

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        seen: Set[Tuple[str, int, str]] = set()

        if not os.path.exists(target_path):
            return findings

        compiled_rules = [
            (re.compile(pattern), name, ver, status, is_weak, purpose, conf)
            for pattern, name, ver, status, is_weak, purpose, conf in PROTOCOL_RULES
        ]

        files_to_scan = []
        if os.path.isfile(target_path):
            files_to_scan.append((target_path, os.path.basename(target_path)))
        else:
            for root, dirs, files in os.walk(target_path):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
                for file in files:
                    if file.lower().endswith(SUPPORTED_EXTENSIONS) or file in ("sshd_config", "ssh_config", "nginx.conf", "haproxy.cfg", "httpd.conf", "openssl.cnf"):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, target_path)
                        files_to_scan.append((full_path, rel_path))

        for full_path, rel_path in files_to_scan:
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

                for regex, proto_name, ver, status, is_weak, purpose, base_conf in compiled_rules:
                    match = regex.search(line_str)
                    if match:
                        matched_text = match.group(0)
                        key = (rel_path, line_idx, proto_name)
                        if key in seen:
                            continue
                        seen.add(key)

                        weak_reasons = []
                        if is_weak:
                            weak_reasons.append(f"Deprecated/insecure or vulnerable protocol/algorithm ({proto_name})")

                        if not ver or proto_name.startswith(("TLS", "SSL", "SSH", "ECDHE", "DHE", "IKE", "SMTPS", "LDAPS", "FTPS")):
                            algo_name = proto_name
                        else:
                            algo_name = f"{proto_name}-{ver}"

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
                            confidence=base_conf,
                            evidence_type=EvidenceType.OBSERVED,
                            extra_metadata=extra_metadata,
                        ))

        return findings
