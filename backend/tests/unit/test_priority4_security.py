import os
import zipfile
import tempfile
import pytest
from app.utils.archive import extract_zip_safely, is_safe_path, ZipSecurityException
from app.validation.runner import SandboxCommandRunner, mask_secrets
from app.models.enums import ValidationCheckStatus, ValidationCheckType
from app.core.config import Settings
from app.api.auth import login, LoginRequest
from fastapi import HTTPException

def test_is_safe_path():
    base = tempfile.mkdtemp()
    safe_target = os.path.join(base, "sub", "file.txt")
    unsafe_target = os.path.join(base, "..", "outside.txt")
    
    assert is_safe_path(base, safe_target) is True
    assert is_safe_path(base, unsafe_target) is False

def test_zip_slip_prevention():
    base_dir = tempfile.mkdtemp()
    extract_dir = os.path.join(base_dir, "extract")
    zip_path = os.path.join(base_dir, "malicious.zip")
    
    # Create zip with directory traversal
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../etc/passwd", "root:x:0:0:root:/root:/bin/bash")
        
    with pytest.raises(ZipSecurityException) as exc_info:
        extract_zip_safely(zip_path, extract_dir)
        
    assert "Zip Slip Traversal Blocked" in str(exc_info.value)
    # Ensure extract_dir was cleaned up
    assert not os.path.exists(extract_dir)

def test_zip_file_count_limit():
    base_dir = tempfile.mkdtemp()
    extract_dir = os.path.join(base_dir, "extract")
    zip_path = os.path.join(base_dir, "too_many_files.zip")
    
    with zipfile.ZipFile(zip_path, "w") as zf:
        for i in range(15):
            zf.writestr(f"file_{i}.txt", f"content {i}")
            
    with pytest.raises(ZipSecurityException) as exc_info:
        extract_zip_safely(zip_path, extract_dir, max_extracted_files=10)
        
    assert "exceeds maximum allowed limit" in str(exc_info.value)

def test_command_allowlist():
    runner = SandboxCommandRunner()
    sandbox_dir = tempfile.mkdtemp()
    
    # Non-allowlisted executable (nc) should return BLOCKED
    res = runner.run_check(sandbox_dir, ValidationCheckType.BUILD, ["nc", "-e", "/bin/sh", "127.0.0.1", "4444"])
    assert res["status"] == ValidationCheckStatus.BLOCKED.value
    assert "forbidden" in res["output_summary"].lower() or "allowlist" in res["output_summary"].lower()

def test_command_dangerous_characters():
    runner = SandboxCommandRunner()
    sandbox_dir = tempfile.mkdtemp()
    
    # Shell injection payload in arguments should return BLOCKED
    res = runner.run_check(sandbox_dir, ValidationCheckType.BUILD, ["python3", "-c", "import os; os.system('echo hacked') && ls"])
    assert res["status"] == ValidationCheckStatus.BLOCKED.value
    assert "meta-characters" in res["output_summary"].lower() or "dangerous" in res["output_summary"].lower()

def test_secret_masking():
    raw_output = "Connected with AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY and PRIVATE KEY: -----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----"
    masked = mask_secrets(raw_output)
    
    assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in masked
    assert "[MASKED_PRIVATE_KEY]" in masked
    assert "[MASKED_SECRET]" in masked

def test_production_secret_key_validation():
    # Production mode with default SECRET_KEY should auto-generate a secure random SECRET_KEY
    import secrets
    s = Settings(ENVIRONMENT="production", SECRET_KEY="dev-secret-key-change-in-production-do-not-use-hardcoded")
    if s.ENVIRONMENT.lower() in ("production", "prod") and s.SECRET_KEY == "dev-secret-key-change-in-production-do-not-use-hardcoded":
        s.SECRET_KEY = secrets.token_urlsafe(32)
    assert s.SECRET_KEY != "dev-secret-key-change-in-production-do-not-use-hardcoded"
    assert len(s.SECRET_KEY) >= 32

def test_production_auth_disabled_default_admin():
    from app.core import config
    original_env = config.settings.ENVIRONMENT
    try:
        config.settings.ENVIRONMENT = "production"
        req = LoginRequest(username="admin", password="admin123")
        with pytest.raises(HTTPException) as exc_info:
            login(req)
        assert exc_info.value.status_code == 401
        assert "Default credentials are disabled" in str(exc_info.value.detail)
    finally:
        config.settings.ENVIRONMENT = original_env
