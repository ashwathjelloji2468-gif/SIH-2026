import re
from typing import List, Dict, Any, Optional
from app.scanners.parsers.tree_sitter_parser import get_java_parser, parse_code_tree, get_node_text
from app.models.enums import CryptoPurpose
from app.core.logging import logger

JAVA_CRYPTO_CLASSES = {
    "javax.crypto.Cipher": ("AES", CryptoPurpose.ENCRYPTION),
    "java.security.MessageDigest": ("SHA-256", CryptoPurpose.HASHING),
    "java.security.Signature": ("RSA", CryptoPurpose.SIGNATURE),
    "java.security.KeyPairGenerator": ("RSA", CryptoPurpose.KEY_ESTABLISHMENT),
    "java.security.KeyFactory": ("RSA", CryptoPurpose.KEY_ESTABLISHMENT),
    "java.security.KeyStore": ("KEYSTORE", CryptoPurpose.KEY_ESTABLISHMENT)
}

def parse_java_file(file_path: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code_str = f.read()
    except Exception as e:
        logger.warning(f"Failed to read Java file '{file_path}': {e}")
        return findings

    parser = get_java_parser()
    if not parser:
        return _fallback_java_regex_parse(code_str)

    root_node = parse_code_tree(parser, code_str)
    if not root_node:
        return _fallback_java_regex_parse(code_str)

    def get_string_val(node) -> Optional[str]:
        if not node:
            return None
        if node.type in ["string_literal", "string"]:
            text = get_node_text(node, code_str)
            return text.strip("'\"")
        for child in node.children:
            val = get_string_val(child)
            if val:
                return val
        return None

    def walk_tree(node):
        # 1. Imports
        if node.type == "import_declaration":
            import_text = get_node_text(node, code_str)
            for cls_path, (alg, purpose) in JAVA_CRYPTO_CLASSES.items():
                if cls_path in import_text:
                    findings.append({
                        "line": node.start_point[0] + 1,
                        "algorithm": alg,
                        "purpose": purpose,
                        "mode": None,
                        "padding": None,
                        "key_size": None,
                        "library": cls_path,
                        "api_call": import_text.strip(";"),
                        "matched_text": import_text,
                        "type": "IMPORT",
                        "description": f"Java Crypto Import: {cls_path}",
                        "confidence": 0.95,
                        "detector": "tree_sitter",
                        "evidence_type": "STRUCTURAL_API_CALL",
                        "parameters": {}
                    })

        # 2. Method Invocations
        elif node.type == "method_invocation":
            method_text = get_node_text(node, code_str)
            if ".getInstance(" in method_text:
                args_node = node.child_by_field_name("arguments")
                arg_str = get_string_val(args_node) if args_node else None

                alg = "UNKNOWN"
                purpose = CryptoPurpose.UNKNOWN
                mode = None
                padding = None
                parameters = {}

                if "Cipher.getInstance" in method_text:
                    purpose = CryptoPurpose.ENCRYPTION
                    if arg_str and arg_str != "UNKNOWN_DYNAMIC":
                        parts = arg_str.split("/")
                        alg = parts[0].upper()
                        if alg == "AES":
                            alg = "AES"
                        elif alg in ["DES", "3DES", "TRIPLEDES"]:
                            alg = "DES"

                        if len(parts) > 1:
                            mode = parts[1].upper()
                            parameters["mode"] = mode
                        if len(parts) > 2:
                            padding = parts[2]
                            parameters["padding"] = padding
                    else:
                        alg = "AES"

                elif "MessageDigest.getInstance" in method_text:
                    purpose = CryptoPurpose.HASHING
                    if arg_str and arg_str != "UNKNOWN_DYNAMIC":
                        alg = arg_str.upper().replace("SHA", "SHA-") if "sha" in arg_str.lower() and "-" not in arg_str else arg_str.upper()
                        if alg == "SHA256":
                            alg = "SHA-256"
                        elif alg == "SHA512":
                            alg = "SHA-512"
                    else:
                        alg = "SHA-256"

                elif "Signature.getInstance" in method_text:
                    purpose = CryptoPurpose.SIGNATURE
                    if arg_str and arg_str != "UNKNOWN_DYNAMIC":
                        if "WITH" in arg_str.upper():
                            hash_part, alg_part = arg_str.upper().split("WITH", 1)
                            alg = alg_part.strip()
                            parameters["hash"] = hash_part.strip()
                        else:
                            alg = arg_str.upper()
                        if alg in ["ECDSA", "EC"]:
                            alg = "ECDSA"
                    else:
                        alg = "RSA"

                elif "KeyPairGenerator.getInstance" in method_text or "KeyFactory.getInstance" in method_text:
                    purpose = CryptoPurpose.KEY_ESTABLISHMENT
                    if arg_str and arg_str != "UNKNOWN_DYNAMIC":
                        alg = arg_str.upper()
                        if alg in ["EC", "ECDSA"]:
                            alg = "ECDSA"
                    else:
                        alg = "RSA"

                if alg != "UNKNOWN":
                    findings.append({
                        "line": node.start_point[0] + 1,
                        "algorithm": alg,
                        "purpose": purpose,
                        "mode": mode,
                        "padding": padding,
                        "key_size": None,
                        "library": "java.security",
                        "api_call": method_text[:80],
                        "matched_text": method_text[:120],
                        "type": "API_CALL",
                        "description": f"Java Tree-sitter detected {method_text[:60]}",
                        "confidence": 0.95 if arg_str and arg_str != "UNKNOWN_DYNAMIC" else 0.75,
                        "evidence_type": "STRUCTURAL_API_CALL",
                        "detector": "tree_sitter",
                        "parameters": parameters
                    })

        for child in node.children:
            walk_tree(child)

    walk_tree(root_node)
    return findings


def _fallback_java_regex_parse(code_str: str) -> List[Dict[str, Any]]:
    findings = []
    lines = code_str.splitlines()
    for idx, line in enumerate(lines, start=1):
        line_str = line.strip()
        if "Cipher.getInstance" in line_str:
            findings.append({
                "line": idx,
                "algorithm": "AES",
                "purpose": CryptoPurpose.ENCRYPTION,
                "mode": None,
                "padding": None,
                "key_size": None,
                "library": "javax.crypto",
                "api_call": "Cipher.getInstance",
                "matched_text": line_str,
                "type": "API_CALL",
                "description": "Java Cipher.getInstance match",
                "confidence": 0.85,
                "detector": "regex_fallback",
                "evidence_type": "OBSERVED",
                "parameters": {}
            })
        elif "MessageDigest.getInstance" in line_str:
            findings.append({
                "line": idx,
                "algorithm": "SHA-256",
                "purpose": CryptoPurpose.HASHING,
                "mode": None,
                "padding": None,
                "key_size": None,
                "library": "java.security",
                "api_call": "MessageDigest.getInstance",
                "matched_text": line_str,
                "type": "API_CALL",
                "description": "Java MessageDigest.getInstance match",
                "confidence": 0.85,
                "detector": "regex_fallback",
                "evidence_type": "OBSERVED",
                "parameters": {}
            })
    return findings
