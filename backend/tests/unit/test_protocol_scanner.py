import os
import tempfile
from app.scanners.protocol_scanner import ProtocolScanner
from app.models.enums import AssetType, CryptoPurpose


def test_protocol_scanner_detects_protocols():
    scanner = ProtocolScanner()
    content = """
# Server Configuration
ssl_protocol = "TLSv1.0"  # Legacy protocol
secure_protocol = "TLSv1.3"
ssh_host = "SSH-2.0-OpenSSH_8.9"
vpn = "IKEv2"
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "app.conf")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)

        findings = scanner.scan(tmpdir)
        protos = {f.algorithm_name: f for f in findings}

        assert "TLSv1.0-1.0" in protos or "TLSv1.0" in protos
        tlsv1 = protos.get("TLSv1.0-1.0") or protos.get("TLSv1.0")
        assert tlsv1.asset_type == AssetType.PROTOCOL
        assert tlsv1.extra_metadata["is_weak"] is True

        assert "TLSv1.3-1.3" in protos or "TLSv1.3" in protos
        tlsv13 = protos.get("TLSv1.3-1.3") or protos.get("TLSv1.3")
        assert tlsv13.extra_metadata["is_weak"] is False

        assert "IKEv2-2.0" in protos or "IKEv2" in protos
        ikev2 = protos.get("IKEv2-2.0") or protos.get("IKEv2")
        assert ikev2.purpose == CryptoPurpose.KEY_ESTABLISHMENT
