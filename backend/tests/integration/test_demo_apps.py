import os
import pytest
from app.scanners.source_scanner import SourceScanner
from app.scanners.certificate_scanner import CertificateScanner
from app.discovery.deduplication import deduplicate_findings

TEST_APPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../test_apps"))

def test_scan_demo_bank():
    target = os.path.join(TEST_APPS_DIR, "demo-bank")
    assert os.path.exists(target), f"Path {target} does not exist"
    
    scanner = SourceScanner()
    findings = deduplicate_findings(scanner.scan(target))
    
    algorithms = [f.algorithm_name for f in findings]
    assert "RSA" in algorithms
    assert "ECDH" in algorithms
    assert "AES" in algorithms

def test_scan_demo_government():
    target = os.path.join(TEST_APPS_DIR, "demo-government")
    assert os.path.exists(target)
    
    scanner = SourceScanner()
    findings = deduplicate_findings(scanner.scan(target))
    
    algorithms = [f.algorithm_name for f in findings]
    assert "ECDSA" in algorithms
    assert "SHA-256" in algorithms

def test_scan_demo_healthcare():
    target = os.path.join(TEST_APPS_DIR, "demo-healthcare")
    assert os.path.exists(target)
    
    scanner = SourceScanner()
    findings = deduplicate_findings(scanner.scan(target))
    
    algorithms = [f.algorithm_name for f in findings]
    assert "AES" in algorithms
    assert "MD5" in algorithms
    assert "DES" in algorithms
