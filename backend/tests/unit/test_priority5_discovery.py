import os
import tempfile
import pytest
from app.scanners.infrastructure_scanner import InfrastructureScanner
from app.scanners.protocol_scanner import ProtocolScanner
from app.models.enums import AssetType, CryptoPurpose, EvidenceType

def test_hsm_pkcs11_detection():
    scanner = InfrastructureScanner()
    temp_dir = tempfile.mkdtemp()
    
    # 1. C header & API
    c_file = os.path.join(temp_dir, "hsm_client.c")
    with open(c_file, "w") as f:
        f.write('#include <pkcs11.h>\nvoid init() { C_Initialize(NULL); C_OpenSession(1, 0, NULL, NULL, &hSession); }\n')
        
    # 2. Python PyKCS11
    py_file = os.path.join(temp_dir, "hsm_service.py")
    with open(py_file, "w") as f:
        f.write('from PyKCS11 import PyKCS11Lib\npkcs11 = PyKCS11Lib()\npkcs11.load("/usr/lib/softhsm/libsofthsm2.so")\n')

    # 3. PKCS11 URI
    conf_file = os.path.join(temp_dir, "app.conf")
    with open(conf_file, "w") as f:
        f.write('KEY_STORE_URI=pkcs11:token=MyHSMToken;object=MyKey\n')

    findings = scanner.scan(temp_dir)
    algo_names = [f.algorithm_name for f in findings]
    asset_types = [f.asset_type for f in findings]

    assert AssetType.HSM in asset_types
    assert any("PKCS11" in a or "PyKCS11" in a for a in algo_names)
    assert any("hsm_client.c" in f.file_path for f in findings)
    assert any("pkcs11:token=" in f.matched_text for f in findings)

def test_tpm2_detection():
    scanner = InfrastructureScanner()
    temp_dir = tempfile.mkdtemp()
    
    sh_file = os.path.join(temp_dir, "tpm_provision.sh")
    with open(sh_file, "w") as f:
        f.write('#!/bin/bash\n/dev/tpmrm0\ntpm2_create -C primary.ctx -g sha256 -G rsa -u key.pub -r key.priv\ntpm2_sign -c key.ctx -g sha256 -o sig.raw data.bin\n')

    py_file = os.path.join(temp_dir, "tpm_helper.py")
    with open(py_file, "w") as f:
        f.write('from tpm2_pytss import ESAPI\nesys = ESAPI()\n')

    findings = scanner.scan(temp_dir)
    asset_types = [f.asset_type for f in findings]
    algo_names = [f.algorithm_name for f in findings]

    assert AssetType.TPM in asset_types
    assert any("TPM2" in a or "tpm2-pytss" in a for a in algo_names)

def test_cloud_kms_detection():
    scanner = InfrastructureScanner()
    temp_dir = tempfile.mkdtemp()
    
    # AWS KMS
    aws_py = os.path.join(temp_dir, "aws_kms.py")
    with open(aws_py, "w") as f:
        f.write('import boto3\nkms = boto3.client("kms")\nARN = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"\n')

    # Azure Key Vault
    azure_ts = os.path.join(temp_dir, "azure_vault.ts")
    with open(azure_ts, "w") as f:
        f.write('import { KeyClient } from "@azure/keyvault-keys";\nconst url = "https://mycompany.vault.azure.net";\n')

    # GCP KMS
    gcp_py = os.path.join(temp_dir, "gcp_kms.py")
    with open(gcp_py, "w") as f:
        f.write('from google.cloud import kms\nclient = kms.KeyManagementServiceClient()\nkey_name = "projects/my-proj/locations/global/keyRings/my-ring/cryptoKeys/my-key"\n')

    findings = scanner.scan(temp_dir)
    algo_names = [f.algorithm_name for f in findings]
    providers = [f.extra_metadata.get("provider") for f in findings]

    assert "AWS_KMS" in algo_names
    assert "AZURE_KEY_VAULT" in algo_names
    assert "GCP_KMS" in algo_names
    assert "AWS_KMS" in providers
    assert "AZURE_KEY_VAULT" in providers
    assert "GCP_KMS" in providers

def test_kms_documentation_false_positive_confidence():
    scanner = InfrastructureScanner()
    temp_dir = tempfile.mkdtemp()
    
    doc_file = os.path.join(temp_dir, "README.md")
    with open(doc_file, "w") as f:
        f.write('# Infrastructure Setup\nDocumentation note: system can optionally use boto3.client("kms") for envelope encryption.\n')

    findings = scanner.scan(temp_dir)
    doc_findings = [f for f in findings if f.file_path == "README.md"]
    
    assert len(doc_findings) > 0
    # Confidence should be downgraded for documentation files to prevent false positives
    assert doc_findings[0].confidence <= 0.65
    assert doc_findings[0].evidence_type == EvidenceType.INFERRED

def test_pem_private_key_redaction():
    scanner = InfrastructureScanner()
    temp_dir = tempfile.mkdtemp()
    
    pem_file = os.path.join(temp_dir, "server.key")
    raw_private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0Z3V9...\nSECRET_PRIVATE_KEY_MATERIAL_1234567890\n-----END RSA PRIVATE KEY-----\n"
    with open(pem_file, "w") as f:
        f.write(raw_private_key)

    findings = scanner.scan(temp_dir)
    assert len(findings) == 1
    f = findings[0]

    assert f.asset_type == AssetType.KEY_STORE
    assert f.algorithm_name == "RSA-PRIVATE-KEY"
    assert f.extra_metadata.get("is_private_key") is True
    # SECURITY: Verify private key material is NEVER persisted
    assert "SECRET_PRIVATE_KEY_MATERIAL_1234567890" not in f.matched_text
    assert "SECRET_PRIVATE_KEY_MATERIAL_1234567890" not in f.context
    assert "[SAFE_METADATA" in f.matched_text

def test_unknown_key_file_needs_review():
    scanner = InfrastructureScanner()
    temp_dir = tempfile.mkdtemp()
    
    unknown_key = os.path.join(temp_dir, "unknown.pem")
    with open(unknown_key, "w") as f:
        f.write('random binary junk with no pem header\n')

    findings = scanner.scan(temp_dir)
    assert len(findings) == 1
    f = findings[0]

    assert f.algorithm_name == "UNKNOWN_KEY_FILE"
    assert f.extra_metadata.get("is_unknown") is True
    assert f.confidence == 0.50

def test_protocol_scanner_ssh_tls_enhancements():
    scanner = ProtocolScanner()
    temp_dir = tempfile.mkdtemp()
    
    ssh_conf = os.path.join(temp_dir, "sshd_config")
    with open(ssh_conf, "w") as f:
        f.write('KexAlgorithms mlkem768x25519-sha256,curve25519-sha256,diffie-hellman-group14-sha256\nHostKeyAlgorithms ssh-ed25519,ssh-rsa\nCiphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com\n')

    nginx_conf = os.path.join(temp_dir, "nginx.conf")
    with open(nginx_conf, "w") as f:
        f.write('ssl_protocols TLSv1.2 TLSv1.3;\nssl_ciphers TLS_AES_256_GCM_SHA384:ECDHE-RSA-AES128-GCM-SHA256;\n')

    findings = scanner.scan(temp_dir)
    algos = [f.algorithm_name for f in findings]

    assert "SSH-MLKEM768-Hybrid" in algos
    assert "SSH-Ed25519" in algos
    assert "SSH-RSA" in algos
    assert "TLSv1.2" in algos
    assert "TLSv1.3" in algos
    assert "TLS_AES_256_GCM_SHA384" in algos
