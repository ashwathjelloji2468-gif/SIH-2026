import os
import tempfile
from app.scanners.vendor_scanner import VendorScanner
from app.models.enums import AssetType, CryptoPurpose


def test_vendor_scanner_detects_hsm_and_kms():
    scanner = VendorScanner()
    code = """
import boto3
from azure.keyvault.keys import KeyClient

# Connect to AWS KMS
kms = boto3.client('kms', region_name='us-east-1')

# Initialize SoftHSM PKCS#11 session
C_Initialize()
session = C_OpenSession(slot_id, CKF_RW_SESSION)
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "main.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        findings = scanner.scan(tmpdir)
        vendors = {f.extra_metadata["vendor_name"]: f for f in findings}

        assert "AWS KMS" in vendors
        aws_finding = vendors["AWS KMS"]
        assert aws_finding.asset_type == AssetType.VENDOR_MANAGED
        assert aws_finding.confidence == 0.95
        assert aws_finding.extra_metadata["vendor_category"] == "CLOUD_KMS"

        assert "PKCS#11 HSM Interface" in vendors or "SoftHSM" in vendors
