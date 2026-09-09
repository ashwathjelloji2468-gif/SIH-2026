import os
import tempfile
import pytest
from app.scanners.parsers.javascript_parser import parse_javascript_file
from app.models.enums import CryptoPurpose

def create_temp_js(code: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".js")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(code)
    return path

def test_js_create_hash():
    code = """
const crypto = require("crypto");
const hash = crypto.createHash("sha256").update("data").digest("hex");
"""
    path = create_temp_js(code)
    try:
        findings = parse_javascript_file(path)
        hash_call = next((f for f in findings if f["algorithm"] == "SHA-256"), None)
        assert hash_call is not None
        assert hash_call["purpose"] == CryptoPurpose.HASHING
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_js_create_cipheriv():
    code = """
const crypto = require("crypto");
const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
"""
    path = create_temp_js(code)
    try:
        findings = parse_javascript_file(path)
        cipher_call = next((f for f in findings if f["algorithm"] == "AES"), None)
        assert cipher_call is not None
        assert cipher_call["purpose"] == CryptoPurpose.ENCRYPTION
        assert cipher_call["key_size"] == 256
        assert cipher_call["mode"] == "GCM"
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_js_sign_verify():
    code = """
const crypto = require("crypto");
const signature = crypto.sign("sha256", data, privateKey);
const isValid = crypto.verify("sha256", data, publicKey, signature);
"""
    path = create_temp_js(code)
    try:
        findings = parse_javascript_file(path)
        sign_calls = [f for f in findings if f["type"] == "API_CALL"]
        assert len(sign_calls) >= 2
        for c in sign_calls:
            assert c["purpose"] == CryptoPurpose.SIGNATURE
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_js_alias_handling():
    code = """
const c = require("crypto");
const hash = c.createHash("sha256");
"""
    path = create_temp_js(code)
    try:
        findings = parse_javascript_file(path)
        hash_call = next((f for f in findings if f["algorithm"] == "SHA-256"), None)
        assert hash_call is not None
        assert hash_call["purpose"] == CryptoPurpose.HASHING
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_js_dynamic_argument():
    code = """
const crypto = require("crypto");
const algorithm = getAlgorithm();
const hash = crypto.createHash(algorithm);
"""
    path = create_temp_js(code)
    try:
        findings = parse_javascript_file(path)
        hash_call = next((f for f in findings if f["type"] == "API_CALL"), None)
        assert hash_call is not None
        assert hash_call["algorithm"] == "UNKNOWN_DYNAMIC"
        assert hash_call["confidence"] == 0.75
    finally:
        if os.path.exists(path):
            os.remove(path)
