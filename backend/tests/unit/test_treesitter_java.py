import os
import tempfile
import pytest
from app.scanners.parsers.java_parser import parse_java_file
from app.models.enums import CryptoPurpose

def create_temp_java(code: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".java")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(code)
    return path

def test_java_cipher_transformation():
    code = """
import javax.crypto.Cipher;

public class TestCipher {
    public void encrypt() throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
    }
}
"""
    path = create_temp_java(code)
    try:
        findings = parse_java_file(path)
        cipher_call = next((f for f in findings if f["type"] == "API_CALL" and f["algorithm"] == "AES"), None)
        assert cipher_call is not None
        assert cipher_call["purpose"] == CryptoPurpose.ENCRYPTION
        assert cipher_call["mode"] == "GCM"
        assert cipher_call["padding"] == "NoPadding"
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_java_message_digest():
    code = """
import java.security.MessageDigest;

public class TestDigest {
    public void hash() throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
    }
}
"""
    path = create_temp_java(code)
    try:
        findings = parse_java_file(path)
        hash_call = next((f for f in findings if f["type"] == "API_CALL" and f["algorithm"] == "SHA-256"), None)
        assert hash_call is not None
        assert hash_call["purpose"] == CryptoPurpose.HASHING
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_java_signature():
    code = """
import java.security.Signature;

public class TestSignature {
    public void sign() throws Exception {
        Signature sig = Signature.getInstance("SHA256withRSA");
    }
}
"""
    path = create_temp_java(code)
    try:
        findings = parse_java_file(path)
        sig_call = next((f for f in findings if f["type"] == "API_CALL" and f["algorithm"] == "RSA"), None)
        assert sig_call is not None
        assert sig_call["purpose"] == CryptoPurpose.SIGNATURE
        assert sig_call["parameters"].get("hash") == "SHA256"
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_java_key_pair_generator():
    code = """
import java.security.KeyPairGenerator;

public class TestKeyPair {
    public void gen() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
    }
}
"""
    path = create_temp_java(code)
    try:
        findings = parse_java_file(path)
        kpg_call = next((f for f in findings if f["type"] == "API_CALL" and f["algorithm"] == "RSA"), None)
        assert kpg_call is not None
        assert kpg_call["purpose"] == CryptoPurpose.KEY_ESTABLISHMENT
    finally:
        if os.path.exists(path):
            os.remove(path)
