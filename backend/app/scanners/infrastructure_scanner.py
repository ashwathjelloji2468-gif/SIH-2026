import os
import re
from typing import List, Dict, Any, Optional, Set, Tuple

from app.scanners.base import BaseScanner, RawFinding, IGNORE_DIRS
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

# Supported file extensions for static infrastructure & key discovery
INFRA_EXTENSIONS = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".sh", ".bash", ".yml", ".yaml", ".json", ".conf", ".ini", ".env", ".properties",
    ".toml", ".xml", ".pem", ".key", ".der", ".cer", ".crt", ".pub", ".p12", ".pfx",
    ".jks", ".keystore", ".p8", ".md", ".txt", ".rst", ".doc", "authorized_keys", "known_hosts"
)

# 1. HSM & PKCS#11 Rules
HSM_RULES = [
    # Header includes & C/C++ functions
    (r"(?i)#include\s*[<\"](pkcs11|pkcs11t|pkcs11f)\.h[>\"]", "PKCS11_HSM", "C_HEADER", 1.0),
    (r"\b(CK_FUNCTION_LIST|CK_MECHANISM|CK_SESSION_HANDLE|C_Initialize|C_GetSlotList|C_OpenSession|C_Login|C_Sign|C_DigestInit)\b", "PKCS11_HSM", "PKCS11_C_API", 0.95),
    # Drivers & shared libraries
    (r"(?i)\b(libpkcs11|opensc-pkcs11|p11-kit|softhsm|softhsm2|libsofthsm2\.so|opensc-pkcs11\.so)\b", "PKCS11_HSM", "PKCS11_DRIVER", 0.95),
    # PKCS#11 URI
    (r"(?i)pkcs11:[a-zA-Z0-9_=\-\./?&%]+", "PKCS11_HSM", "PKCS11_URI", 1.0),
    # Language bindings
    (r"(?i)\bsun\.security\.pkcs11\b", "SunPKCS11", "JAVA_PKCS11", 0.95),
    (r"(?i)\b(import\s+pkcs11|from\s+pkcs11\s+import|import\s+PyKCS11|from\s+PyKCS11\s+import)\b", "PyKCS11", "PYTHON_PKCS11", 0.95),
    (r"(?i)\b(require\s*\(\s*['\"]pkcs11['\"]|from\s+['\"]pkcs11js['\"]|graphene-pkcs11)\b", "PKCS11_JS", "NODE_PKCS11", 0.95),
    (r"(?i)\b(PKCS11_MODULE_PATH|engine_id\s*=\s*pkcs11)\b", "OpenSSL_PKCS11", "OPENSSL_ENGINE", 0.95),
]

# 2. TPM Rules
TPM_RULES = [
    (r"(?i)/dev/tpm(rm)?\d+", "TPM2_DEVICE", "LINUX_DEVICE", 1.0),
    (r"\b(tpm2_create|tpm2_load|tpm2_sign|tpm2_encryptdecrypt|tpm2_getrandom|tpm2_takeownership|tpm2_pcrread|tpm2_flushcontext)\b", "TPM2_CLI", "CLI_TOOL", 0.90),
    (r"\b(TSS2_ESYS|TPM2B_\w+|TPM2_\w+|ESYS_CONTEXT|Esys_Initialize|Tss2_Sys_Initialize)\b", "TPM2_TSS2_API", "TSS2_LIB", 0.95),
    (r"(?i)\b(import\s+tpm2_pytss|from\s+tpm2_pytss\s+import)\b", "tpm2-pytss", "PYTHON_TPM", 0.95),
    (r"(?i)github\.com/google/go-tpm", "go-tpm", "GO_TPM", 0.95),
    (r"(?i)\b(tss-esapi|tpm2-tss)\b", "tss-esapi", "RUST_TPM", 0.95),
    (r"(?i)\b(Tpm2|Microsoft\.Tpm|TSS\.Java)\b", "TPM2_LIBRARY", "DOTNET_JAVA_TPM", 0.95),
]

# 3. AWS KMS Rules
AWS_KMS_RULES = [
    (r"(?i)@aws-sdk/client-kms", "AWS_KMS", "JS_SDK", 0.95),
    (r"\b(KMSClient|EncryptCommand|DecryptCommand|SignCommand|VerifyCommand|GenerateDataKeyCommand)\b", "AWS_KMS", "JS_KMS_COMMAND", 0.95),
    (r"(?i)boto3\.(client|resource)\(\s*['\"]kms['\"]\s*\)", "AWS_KMS", "BOTO3_KMS", 0.95),
    (r"(?i)\bkms_client\.(encrypt|decrypt|sign|verify|generate_data_key)\b", "AWS_KMS", "PYTHON_KMS_CALL", 0.95),
    (r"(?i)software\.amazon\.awssdk\.services\.kms\.KmsClient", "AWS_KMS", "JAVA_V2_KMS", 0.95),
    (r"(?i)com\.amazonaws\.services\.kms\.AWSKMSClient", "AWS_KMS", "JAVA_V1_KMS", 0.95),
    (r"(?i)aws/aws-sdk-go(-v2)?/service/kms", "AWS_KMS", "GO_KMS", 0.95),
    (r"\bAWS_KMS_KEY_ID\b", "AWS_KMS", "ENV_CONFIG", 0.90),
    (r"arn:aws[a-z-]*:kms:[a-z0-9-]+:\d{12}:key/[a-f0-9-]+", "AWS_KMS", "KMS_ARN", 1.0),
]

# 4. Azure Key Vault Rules
AZURE_KV_RULES = [
    (r"(?i)@azure/keyvault-(keys|secrets)", "AZURE_KEY_VAULT", "JS_KEYVAULT_SDK", 0.95),
    (r"(?i)\b(KeyClient|CryptographyClient)\b", "AZURE_KEY_VAULT", "AZURE_KEY_CLIENT", 0.90),
    (r"(?i)azure\.keyvault", "AZURE_KEY_VAULT", "PYTHON_KEYVAULT_SDK", 0.95),
    (r"(?i)\b(SecretClient|DefaultAzureCredential)\b", "AZURE_KEY_VAULT", "AZURE_CRED_CLIENT", 0.90),
    (r"(?i)com\.azure\.security\.keyvault", "AZURE_KEY_VAULT", "JAVA_KEYVAULT_SDK", 0.95),
    (r"(?i)Azure\.Security\.KeyVault", "AZURE_KEY_VAULT", "DOTNET_KEYVAULT_SDK", 0.95),
    (r"https://[a-zA-Z0-9-]+\.vault\.azure\.net", "AZURE_KEY_VAULT", "VAULT_URL", 1.0),
    (r"\bAZURE_KEY_VAULT_URL\b", "AZURE_KEY_VAULT", "ENV_CONFIG", 0.90),
]

# 5. GCP KMS Rules
GCP_KMS_RULES = [
    (r"(?i)@google-cloud/kms", "GCP_KMS", "JS_GCP_KMS_SDK", 0.95),
    (r"(?i)google\.cloud\.kms", "GCP_KMS", "PYTHON_GCP_KMS_SDK", 0.95),
    (r"(?i)\bKeyManagementServiceClient\b", "GCP_KMS", "GCP_KMS_CLIENT", 0.95),
    (r"(?i)com\.google\.cloud\.kms\.v1", "GCP_KMS", "JAVA_GCP_KMS_SDK", 0.95),
    (r"(?i)cloud\.google\.com/go/kms", "GCP_KMS", "GO_GCP_KMS_SDK", 0.95),
    (r"projects/[^/]+/locations/[^/]+/keyRings/[^/]+/cryptoKeys/[^/]+", "GCP_KMS", "GCP_RESOURCE_NAME", 1.0),
]

# PEM Headers mapping to Key Types
PEM_HEADERS = [
    ("-----BEGIN RSA PRIVATE KEY-----", "RSA-PRIVATE-KEY", True),
    ("-----BEGIN EC PRIVATE KEY-----", "EC-PRIVATE-KEY", True),
    ("-----BEGIN PRIVATE KEY-----", "PKCS8-PRIVATE-KEY", True),
    ("-----BEGIN ENCRYPTED PRIVATE KEY-----", "ENCRYPTED-PKCS8-PRIVATE-KEY", True),
    ("-----BEGIN OPENSSH PRIVATE KEY-----", "OPENSSH-PRIVATE-KEY", True),
    ("-----BEGIN DSA PRIVATE KEY-----", "DSA-PRIVATE-KEY", True),
    ("-----BEGIN PUBLIC KEY-----", "PUBLIC-KEY", False),
    ("-----BEGIN RSA PUBLIC KEY-----", "RSA-PUBLIC-KEY", False),
]

OPENSSH_PUBLIC_KEY_PREFIXES = [
    ("ssh-rsa", "SSH-RSA-PUBLIC-KEY"),
    ("ssh-ed25519", "SSH-ED25519-PUBLIC-KEY"),
    ("ecdsa-sha2-nistp256", "ECDSA-P256-PUBLIC-KEY"),
    ("ecdsa-sha2-nistp384", "ECDSA-P384-PUBLIC-KEY"),
    ("ecdsa-sha2-nistp521", "ECDSA-P521-PUBLIC-KEY"),
]

class InfrastructureScanner(BaseScanner):
    """
    Priority 5 Discovery Scanner: Static Infrastructure & Key Management Discovery.
    Detects HSM / PKCS#11, TPM, Cloud KMS (AWS/Azure/GCP), and Key Stores / PEM Files.
    
    CRITICAL SECURITY GUARANTEES:
    1. Static discovery ONLY – zero network connections, zero credential requests.
    2. Private key material is NEVER stored. All key matches are sanitized to safe metadata summaries.
    """

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        seen: Set[Tuple[str, int, str]] = set()

        if not os.path.exists(target_path):
            return findings

        files_to_scan = []
        if os.path.isfile(target_path):
            files_to_scan.append((target_path, os.path.basename(target_path)))
        else:
            for root, dirs, files in os.walk(target_path):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
                for file in files:
                    if file.lower().endswith(INFRA_EXTENSIONS) or file in ("authorized_keys", "known_hosts"):
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, target_path)
                        files_to_scan.append((full_p, rel_p))

        # Compile pattern sets
        hsm_compiled = [(re.compile(p), name, detail, conf) for p, name, detail, conf in HSM_RULES]
        tpm_compiled = [(re.compile(p), name, detail, conf) for p, name, detail, conf in TPM_RULES]
        aws_compiled = [(re.compile(p), name, detail, conf) for p, name, detail, conf in AWS_KMS_RULES]
        azure_compiled = [(re.compile(p), name, detail, conf) for p, name, detail, conf in AZURE_KV_RULES]
        gcp_compiled = [(re.compile(p), name, detail, conf) for p, name, detail, conf in GCP_KMS_RULES]

        for full_path, rel_path in files_to_scan:
            try:
                # 1. File extension structure analysis (Keys / Stores / Certs)
                ext = os.path.splitext(full_path)[1].lower()
                is_key_ext = ext in (".key", ".pem", ".der", ".cer", ".crt", ".pub", ".p12", ".pfx", ".jks", ".keystore", ".p8") or os.path.basename(full_path) in ("authorized_keys", "known_hosts")

                if is_key_ext:
                    key_findings = self._scan_key_file(full_path, rel_path, target_path)
                    for kf in key_findings:
                        key = (rel_path, kf.line_number or 1, kf.algorithm_name)
                        if key not in seen:
                            seen.add(key)
                            findings.append(kf)

                # Skip non-text files for line-by-line scanning
                if ext in (".der", ".p12", ".pfx", ".jks", ".keystore"):
                    continue

                if os.path.getsize(full_path) > 2 * 1024 * 1024:
                    continue

                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

            except Exception:
                continue

            is_doc_file = rel_path.lower().endswith((".md", ".txt", ".rst", ".doc")) or "doc" in rel_path.lower()

            for line_idx, line in enumerate(lines, start=1):
                line_str = line.strip()
                if not line_str:
                    continue

                is_comment = line_str.startswith(("#", "//", "/*", "*", "<!--"))

                # Helper matcher
                def check_rules(rule_list, asset_type, default_service):
                    for regex, algo_name, detail, base_conf in rule_list:
                        match = regex.search(line_str)
                        if match:
                            matched = match.group(0)
                            key = (rel_path, line_idx, algo_name)
                            if key in seen:
                                continue

                            # Adjust confidence for comments/documentation to avoid false positives
                            conf = base_conf
                            ev_type = EvidenceType.OBSERVED
                            if is_doc_file or is_comment:
                                conf = max(0.50, round(base_conf - 0.35, 2))
                                ev_type = EvidenceType.INFERRED

                            seen.add(key)

                            context_msg = f"Static {default_service} reference detected in '{rel_path}:{line_idx}'"
                            if is_doc_file or is_comment:
                                context_msg += " (Documentation/Comment Reference)"

                            extra = {
                                "provider": algo_name,
                                "integration_type": detail,
                                "service": default_service,
                                "matched_line": matched[:200],
                                "is_comment_or_doc": is_comment or is_doc_file
                            }

                            findings.append(RawFinding(
                                detector_name=f"{default_service.replace(' ', '')}Detector",
                                target_path=target_path,
                                file_path=rel_path,
                                line_number=line_idx,
                                asset_type=asset_type,
                                algorithm_name=algo_name,
                                purpose=CryptoPurpose.KEY_ESTABLISHMENT,
                                matched_text=matched[:200],
                                context=context_msg,
                                confidence=conf,
                                evidence_type=ev_type,
                                extra_metadata=extra
                            ))

                check_rules(hsm_compiled, AssetType.HSM, "PKCS11 HSM")
                check_rules(tpm_compiled, AssetType.TPM, "TPM2 Infrastructure")
                check_rules(aws_compiled, AssetType.CLOUD_KMS, "AWS KMS")
                check_rules(azure_compiled, AssetType.CLOUD_KMS, "Azure Key Vault")
                check_rules(gcp_compiled, AssetType.CLOUD_KMS, "GCP Cloud KMS")

        return findings

    def _scan_key_file(self, full_path: str, rel_path: str, target_path: str) -> List[RawFinding]:
        """
        Inspect key file content and structure cleanly.
        GUARANTEE: NEVER return raw private key material!
        """
        findings: List[RawFinding] = []
        try:
            with open(full_path, "rb") as f:
                content = f.read(50000)
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            return findings

        # 1. Check for PEM headers
        found_pem = False
        for header, key_type, is_private in PEM_HEADERS:
            if header in text:
                found_pem = True
                end_header = header.replace("BEGIN", "END")
                safe_matched = f"[SAFE_METADATA_PEM_KEY: {header} ... {end_header} (Key content omitted for security)]"
                
                purpose = CryptoPurpose.SIGNATURE if "RSA" in key_type or "DSA" in key_type or "EC" in key_type else CryptoPurpose.KEY_ESTABLISHMENT
                
                extra = {
                    "key_type": key_type,
                    "is_private_key": is_private,
                    "is_encrypted": "ENCRYPTED" in header or "Proc-Type: 4,ENCRYPTED" in text,
                    "header_detected": header,
                    "content_redacted": True
                }

                context_str = f"PEM Key File '{rel_path}' contains {key_type}"
                if is_private:
                    context_str += " (Private Key — Material Redacted)"

                findings.append(RawFinding(
                    detector_name="PEMKeyStructureDetector",
                    target_path=target_path,
                    file_path=rel_path,
                    line_number=1,
                    asset_type=AssetType.KEY_STORE,
                    algorithm_name=key_type,
                    purpose=purpose,
                    matched_text=safe_matched,
                    context=context_str,
                    confidence=1.0,
                    evidence_type=EvidenceType.OBSERVED,
                    extra_metadata=extra
                ))

        if found_pem:
            return findings

        # 2. Check for OpenSSH Public Keys
        for prefix, key_type in OPENSSH_PUBLIC_KEY_PREFIXES:
            if prefix in text:
                safe_matched = f"[SAFE_METADATA: {prefix} (OpenSSH Public Key)]"
                findings.append(RawFinding(
                    detector_name="OpenSSHKeyDetector",
                    target_path=target_path,
                    file_path=rel_path,
                    line_number=1,
                    asset_type=AssetType.KEY_STORE,
                    algorithm_name=key_type,
                    purpose=CryptoPurpose.AUTHENTICATION,
                    matched_text=safe_matched,
                    context=f"OpenSSH Public Key file '{rel_path}' ({prefix})",
                    confidence=1.0,
                    evidence_type=EvidenceType.OBSERVED,
                    extra_metadata={"key_type": key_type, "prefix": prefix}
                ))
                return findings

        # 3. Handle key file extension with unclassified/unknown structure
        ext = os.path.splitext(full_path)[1].lower()
        if ext in (".pem", ".key", ".der", ".p12", ".pfx", ".jks", ".keystore"):
            safe_matched = f"[KEY_FILE_EXTENSION: {ext}]"
            findings.append(RawFinding(
                detector_name="UnclassifiedKeyFileDetector",
                target_path=target_path,
                file_path=rel_path,
                line_number=1,
                asset_type=AssetType.KEY_STORE,
                algorithm_name="UNKNOWN_KEY_FILE",
                purpose=CryptoPurpose.UNKNOWN,
                matched_text=safe_matched,
                context=f"Key file extension '{ext}' detected without recognizable PEM structure header.",
                confidence=0.50,
                evidence_type=EvidenceType.UNKNOWN,
                extra_metadata={
                    "is_unknown": True,
                    "unknown_reason": f"File extension '{ext}' detected without recognizable PEM structure header.",
                    "extension": ext
                }
            ))

        return findings
