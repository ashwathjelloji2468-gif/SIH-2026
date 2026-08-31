import os
import pytest
from app.scanners.source_scanner import SourceScanner
from app.discovery.deduplication import deduplicate_findings

TEST_APPS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../test_apps"))

def test_javascript_and_typescript_scanner():
    target = os.path.join(TEST_APPS_DIR, "demo-js")
    assert os.path.exists(target)

    scanner = SourceScanner()
    raw_findings = scanner.scan(target)
    findings = deduplicate_findings(raw_findings)

    algorithms = set(f.algorithm_name for f in findings)
    detectors = set(f.detector_name for f in findings)

    assert "JavaScriptParser" in detectors
    assert "RSA" in algorithms
    assert "AES" in algorithms
    assert "SHA-256" in algorithms
    assert "MD5" in algorithms

def test_mixed_python_and_js_project_scan():
    # Scan parent directory containing both python and js demo apps
    scanner = SourceScanner()
    raw_findings = scanner.scan(TEST_APPS_DIR)
    findings = deduplicate_findings(raw_findings)

    file_extensions = set(os.path.splitext(f.file_path)[1] for f in findings)
    assert ".py" in file_extensions
    assert ".js" in file_extensions or ".ts" in file_extensions
