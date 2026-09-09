import os
import tempfile
import pytest
from app.scanners.parsers.python_parser import parse_python_file, PythonCryptoVisitor
from app.models.enums import CryptoPurpose

def create_temp_py(code: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(code)
    return path

def test_rsa_imports():
    code = """
import cryptography.hazmat.primitives.asymmetric.rsa
from Crypto.PublicKey import RSA
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        imports = [f for f in findings if f["type"] == "IMPORT"]
        assert len(imports) >= 2
        algs = [f["algorithm"] for f in imports]
        assert "RSA" in algs
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_import_aliases():
    code = """
import cryptography.hazmat.primitives.asymmetric.rsa as rsa_mod
import Crypto.Cipher.AES as my_aes
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        assert len(findings) >= 2
        algs = [f["algorithm"] for f in findings]
        assert "RSA" in algs
        assert "AES" in algs
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_hashlib_aliases():
    code = """
import hashlib as h
h.sha256(b"hello").hexdigest()
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        h_calls = [f for f in findings if f["algorithm"] == "SHA-256"]
        assert len(h_calls) >= 1
        assert h_calls[0]["purpose"] == CryptoPurpose.HASHING
        assert h_calls[0]["resolved_library"] == "hashlib"
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_rsa_key_generation():
    code = """
from cryptography.hazmat.primitives.asymmetric import rsa
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        gen_call = next((f for f in findings if "generate_private_key" in f["api_call"]), None)
        assert gen_call is not None
        assert gen_call["algorithm"] == "RSA"
        assert gen_call["key_size"] == 2048
        assert gen_call["parameters"].get("key_size") == 2048
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_sign_operation():
    code = """
from cryptography.hazmat.primitives.asymmetric import rsa
private_key = rsa.generate_private_key(65537, 4096)
signature = private_key.sign(data, padding, algorithm)
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        sign_call = next((f for f in findings if f["api_call"] == "private_key.sign"), None)
        assert sign_call is not None
        assert sign_call["algorithm"] == "RSA"
        assert sign_call["purpose"] == CryptoPurpose.SIGNATURE
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_verify_operation():
    code = """
verifier.verify(signature, data)
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        verify_call = next((f for f in findings if f["api_call"] == "verifier.verify"), None)
        assert verify_call is not None
        assert verify_call["purpose"] == CryptoPurpose.SIGNATURE
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_aes_encryption():
    code = """
from Crypto.Cipher import AES
cipher = AES.new(key, AES.MODE_CBC)
ciphertext = cipher.encrypt(plaintext)
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        aes_calls = [f for f in findings if f["algorithm"] == "AES"]
        assert len(aes_calls) >= 1
        cipher_new = next((f for f in aes_calls if "AES.new" in f["api_call"]), None)
        assert cipher_new is not None
        assert cipher_new["parameters"].get("mode") == "CBC"
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_sha256_hashing():
    code = """
import hashlib
digest = hashlib.sha256(b"secret").digest()
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        hash_call = next((f for f in findings if f["algorithm"] == "SHA-256"), None)
        assert hash_call is not None
        assert hash_call["purpose"] == CryptoPurpose.HASHING
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_syntax_error_handling():
    code = """
def broken_function(:
    rsa.generate_private_key(
"""
    path = create_temp_py(code)
    try:
        findings = parse_python_file(path)
        assert findings == []
    finally:
        if os.path.exists(path):
            os.remove(path)
