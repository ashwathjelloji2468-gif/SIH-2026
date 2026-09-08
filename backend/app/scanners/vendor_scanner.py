import os
import re
from typing import List, Dict, Any, Optional, Set, Tuple

from app.scanners.base import BaseScanner, RawFinding
from app.models.enums import AssetType, CryptoPurpose, EvidenceType


# Vendor rules: (regex_pattern, vendor_name, vendor_category, default_algo_name, service_type, purpose)
VENDOR_PATTERNS = [
    # Hardware Security Modules (HSM) & PKCS#11
    (r"\b(?i:pkcs11|pkcs#11|libpkcs11|C_Initialize|C_OpenSession|CKF_RW_SESSION)\b", "PKCS#11 HSM Interface", "HSM", "PKCS11-HSM-API", "Hardware Security Module API", CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:SoftHSM|softhsm2|softhsm2\.conf)\b", "SoftHSM", "HSM", "SOFTHSM-PKCS11", "Software HSM Emulator", CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:AWSCloudHSM|CloudHSM|cloudhsmv2|aws-cloudhsm)\b", "AWS CloudHSM", "CLOUD_HSM", "AWS-CLOUD-HSM", "Dedicated Cloud HSM Managed Service", CryptoPurpose.KEY_ESTABLISHMENT),
    (r"\b(?i:AzureManagedHSM|azure-keyvault-keys|KeyVaultClient)\b", "Azure Managed HSM", "CLOUD_HSM", "AZURE-MANAGED-HSM", "Cloud HSM Managed Service", CryptoPurpose.KEY_ESTABLISHMENT),
    (r"\b(?i:nCipher|Thales|Utimaco|SafeNet|LunaHSM|Luna_HSM|Entrust_HSM)\b", "Enterprise Hardware Security Module", "HSM", "HARDWARE-HSM-MODULE", "Dedicated Enterprise HSM Hardware", CryptoPurpose.KEY_ESTABLISHMENT),
    (r"\b(?i:YubiHSM|YubiKey|yubico)\b", "Yubico HSM / Security Key", "HARDWARE_TOKEN", "YUBIKEY-SECURITY-MODULE", "Hardware Security Token & HSM", CryptoPurpose.AUTHENTICATION),
    (r"\b(?i:TPM2_0|TPM20|tpm2_create|tpm2-tools|/dev/tpmrm0|/dev/tpm0)\b", "Trusted Platform Module (TPM)", "TPM", "TPM-2.0-HARDWARE", "Hardware Trusted Platform Module", CryptoPurpose.AUTHENTICATION),

    # Cloud Key Management Services (KMS) & Secrets Managers
    (r"\b(?i:boto3\.client\(['\"]kms|aws_kms|aws-sdk/client-kms|arn:aws:kms:[a-z0-9-]+:[0-9]+:key/|AWS_KMS_KEY_ID)\b", "AWS KMS", "CLOUD_KMS", "AWS-KMS-SERVICE", "AWS Key Management Service", CryptoPurpose.ENCRYPTION),
    (r"\b(?i:kmsclient|kms\.v1|cloud\.google\.com/go/kms|@google-cloud/kms|google_kms_crypto_key)\b", "GCP Cloud KMS", "CLOUD_KMS", "GCP-CLOUD-KMS", "Google Cloud Key Management Service", CryptoPurpose.ENCRYPTION),
    (r"\b(?i:azure\.keyvault\.keys|azure_key_vault|KeyVaultSecret|vault\.azure\.net)\b", "Azure Key Vault", "CLOUD_KMS", "AZURE-KEY-VAULT", "Azure Key Vault KMS", CryptoPurpose.ENCRYPTION),
    (r"\b(?i:hashicorp/vault|vaultclient|api/v1/secret|VAULT_ADDR|vault_token)\b", "HashiCorp Vault", "SECRETS_MANAGER", "HASHICORP-VAULT", "Enterprise Secrets & Encryption Manager", CryptoPurpose.ENCRYPTION),
]

SUPPORTED_EXTENSIONS = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
    ".rb", ".php", ".c", ".cpp", ".h", ".cs", ".yml", ".yaml",
    ".json", ".conf", ".ini", ".env", ".properties", ".toml",
    ".tf", ".hcl", ".sh"
)


class VendorScanner(BaseScanner):
    """Scan source code, infrastructure templates, and configuration files for references to

    Hardware Security Modules (HSM, PKCS#11, TPM) and Cloud KMS Services (AWS KMS, Azure Key Vault, GCP KMS, HashiCorp Vault).
    """

    def scan(self, target_path: str) -> List[RawFinding]:
        findings: List[RawFinding] = []
        seen: Set[Tuple[str, int, str]] = set()

        if not os.path.isdir(target_path):
            return findings

        # Compile rules
        compiled_rules = [
            (re.compile(pattern), vendor_name, vendor_category, algo_name, service_type, purpose)
            for pattern, vendor_name, vendor_category, algo_name, service_type, purpose in VENDOR_PATTERNS
        ]

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

                    for regex, vendor_name, vendor_category, algo_name, service_type, purpose in compiled_rules:
                        match = regex.search(line_str)
                        if match:
                            matched_text = match.group(0)
                            key = (rel_path, line_idx, vendor_name)
                            if key in seen:
                                continue
                            seen.add(key)

                            extra_metadata: Dict[str, Any] = {
                                "vendor_name": vendor_name,
                                "vendor_category": vendor_category,
                                "service_type": service_type,
                                "is_vendor_managed": True,
                                "is_weak": False,
                                "business_criticality_label": "CRITICAL",
                                "data_lifetime_years": 20.0,
                                "lifetime_label": "PERMANENT",
                                "matched_text": matched_text,
                                "file_path": rel_path,
                                "line_number": line_idx,
                            }

                            context = f"Vendor-managed {vendor_category} reference '{vendor_name}' detected in '{rel_path}:{line_idx}'"

                            findings.append(RawFinding(
                                detector_name="VendorScanner",
                                target_path=target_path,
                                file_path=rel_path,
                                line_number=line_idx,
                                asset_type=AssetType.VENDOR_MANAGED,
                                algorithm_name=algo_name,
                                purpose=purpose,
                                matched_text=matched_text,
                                context=context,
                                confidence=0.95,
                                evidence_type=EvidenceType.OBSERVED,
                                extra_metadata=extra_metadata,
                            ))

        return findings
