import re
from typing import List, Dict, Any, Optional
from app.scanners.parsers.tree_sitter_parser import get_js_parser, parse_code_tree, get_node_text
from app.models.enums import CryptoPurpose
from app.core.logging import logger

def parse_javascript_file(file_path: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code_str = f.read()
    except Exception as e:
        logger.warning(f"Failed to read JavaScript file '{file_path}': {e}")
        return findings

    parser = get_js_parser()
    if not parser:
        return _fallback_regex_parse(code_str)

    root_node = parse_code_tree(parser, code_str)
    if not root_node:
        return _fallback_regex_parse(code_str)

    aliases: Dict[str, str] = {}  # local_var -> module_name

    def get_string_val(node) -> Optional[str]:
        if not node:
            return None
        if node.type in ["string", "string_fragment"]:
            text = get_node_text(node, code_str)
            return text.strip("'\"`")
        for child in node.children:
            val = get_string_val(child)
            if val:
                return val
        return None

    def walk_tree(node):
        nonlocal aliases

        # 1. Track Imports & Requires
        if node.type == "variable_declarator":
            name_node = node.child_by_field_name("name")
            value_node = node.child_by_field_name("value")
            if name_node and value_node and value_node.type == "call_expression":
                func_node = value_node.child_by_field_name("function")
                if func_node and get_node_text(func_node, code_str) == "require":
                    args_node = value_node.child_by_field_name("arguments")
                    if args_node:
                        mod_name = get_string_val(args_node)
                        var_name = get_node_text(name_node, code_str)
                        if mod_name and var_name:
                            aliases[var_name] = mod_name
                            if any(lib in mod_name for lib in ["crypto", "crypto-js", "node-forge", "jose", "jsonwebtoken"]):
                                findings.append({
                                    "line": node.start_point[0] + 1,
                                    "algorithm": "CryptoLibrary",
                                    "purpose": CryptoPurpose.UNKNOWN,
                                    "mode": None,
                                    "padding": None,
                                    "key_size": None,
                                    "library": mod_name,
                                    "api_call": f"require('{mod_name}')",
                                    "matched_text": get_node_text(node, code_str),
                                    "type": "IMPORT",
                                    "description": "JavaScript Crypto Library Import",
                                    "confidence": 0.95,
                                    "detector": "tree_sitter",
                                    "evidence_type": "STRUCTURAL_API_CALL",
                                    "parameters": {}
                                })

        elif node.type == "import_statement":
            import_str = get_node_text(node, code_str)
            mod_match = re.search(r"from\s+['\"]([^'\"]+)['\"]", import_str)
            if mod_match:
                mod_name = mod_match.group(1)
                if any(lib in mod_name for lib in ["crypto", "crypto-js", "node-forge", "jose", "jsonwebtoken"]):
                    id_match = re.search(r"import\s+(\w+)\s+from", import_str)
                    if id_match:
                        aliases[id_match.group(1)] = mod_name
                    star_match = re.search(r"import\s+\*\s+as\s+(\w+)", import_str)
                    if star_match:
                        aliases[star_match.group(1)] = mod_name

                    findings.append({
                        "line": node.start_point[0] + 1,
                        "algorithm": "CryptoLibrary",
                        "purpose": CryptoPurpose.UNKNOWN,
                        "mode": None,
                        "padding": None,
                        "key_size": None,
                        "library": mod_name,
                        "api_call": f"import '{mod_name}'",
                        "matched_text": import_str,
                        "type": "IMPORT",
                        "description": "ES Module Crypto Library Import",
                        "confidence": 0.95,
                        "detector": "tree_sitter",
                        "evidence_type": "STRUCTURAL_API_CALL",
                        "parameters": {}
                    })

        # 2. Track Cryptographic API Calls
        elif node.type == "call_expression":
            func_node = node.child_by_field_name("function")
            args_node = node.child_by_field_name("arguments")
            if func_node:
                func_text = get_node_text(func_node, code_str)
                parts = func_text.split(".")
                base_obj = parts[0]
                method_name = parts[-1]

                is_crypto_obj = (
                    base_obj in aliases or
                    base_obj.lower() in ["crypto", "cryptojs", "subtle", "forge", "jwt", "jose", "nacl"] or
                    "crypto" in func_text.lower()
                )

                if is_crypto_obj or method_name in ["createHash", "createCipheriv", "createDecipheriv", "generateKeyPair", "generateKeyPairSync", "sign", "verify"]:
                    alg = "UNKNOWN"
                    purpose = CryptoPurpose.UNKNOWN
                    key_size = None
                    mode = None
                    parameters = {}

                    first_arg_str = None
                    if args_node and len(args_node.children) > 1:
                        for arg_child in args_node.children:
                            if arg_child.type in ["string", "string_fragment"]:
                                first_arg_str = get_string_val(arg_child)
                                break
                            elif arg_child.type == "identifier":
                                first_arg_str = "UNKNOWN_DYNAMIC"

                    if method_name == "createHash":
                        purpose = CryptoPurpose.HASHING
                        if first_arg_str and first_arg_str != "UNKNOWN_DYNAMIC":
                            alg = first_arg_str.upper().replace("SHA", "SHA-") if "sha" in first_arg_str.lower() and "-" not in first_arg_str else first_arg_str.upper()
                            if alg == "SHA256":
                                alg = "SHA-256"
                            elif alg == "SHA512":
                                alg = "SHA-512"
                        else:
                            alg = "UNKNOWN_DYNAMIC" if first_arg_str == "UNKNOWN_DYNAMIC" else "SHA-256"

                    elif method_name in ["createCipher", "createCipheriv", "createDecipher", "createDecipheriv"]:
                        purpose = CryptoPurpose.ENCRYPTION
                        if first_arg_str and first_arg_str != "UNKNOWN_DYNAMIC":
                            alg = "AES"
                            if "aes" in first_arg_str.lower():
                                m = re.search(r"aes-(\d+)-(\w+)", first_arg_str.lower())
                                if m:
                                    key_size = int(m.group(1))
                                    mode = m.group(2).upper()
                                    parameters["key_size"] = key_size
                                    parameters["mode"] = mode
                            elif "des" in first_arg_str.lower():
                                alg = "DES"
                        else:
                            alg = "AES"

                    elif method_name in ["generateKeyPair", "generateKeyPairSync", "generateKey"]:
                        purpose = CryptoPurpose.KEY_ESTABLISHMENT
                        if first_arg_str and first_arg_str != "UNKNOWN_DYNAMIC":
                            if "rsa" in first_arg_str.lower():
                                alg = "RSA"
                            elif "ec" in first_arg_str.lower():
                                alg = "ECDSA"
                            else:
                                alg = first_arg_str.upper()
                        else:
                            alg = "RSA"

                    elif method_name in ["sign", "verify"]:
                        purpose = CryptoPurpose.SIGNATURE
                        if "rsa" in func_text.lower():
                            alg = "RSA"
                        elif "ec" in func_text.lower() or "nacl" in func_text.lower():
                            alg = "ECDSA"
                        elif first_arg_str and "rsa" in first_arg_str.lower():
                            alg = "RSA"
                        elif first_arg_str and "ec" in first_arg_str.lower():
                            alg = "ECDSA"
                        else:
                            alg = "RSA"

                    elif "CryptoJS.AES" in func_text or "encrypt" in method_name:
                        purpose = CryptoPurpose.ENCRYPTION
                        alg = "AES"

                    elif "CryptoJS.SHA256" in func_text:
                        purpose = CryptoPurpose.HASHING
                        alg = "SHA-256"

                    elif "CryptoJS.MD5" in func_text:
                        purpose = CryptoPurpose.HASHING
                        alg = "MD5"

                    if alg != "UNKNOWN":
                        findings.append({
                            "line": node.start_point[0] + 1,
                            "algorithm": alg,
                            "purpose": purpose,
                            "mode": mode,
                            "padding": None,
                            "key_size": key_size,
                            "library": aliases.get(base_obj, base_obj),
                            "api_call": func_text,
                            "matched_text": get_node_text(node, code_str)[:120],
                            "type": "API_CALL",
                            "description": f"Tree-sitter detected {func_text}",
                            "confidence": 0.95 if alg != "UNKNOWN_DYNAMIC" else 0.75,
                            "evidence_type": "STRUCTURAL_API_CALL",
                            "detector": "tree_sitter",
                            "parameters": parameters
                        })

        for child in node.children:
            walk_tree(child)

    walk_tree(root_node)
    return findings


def _fallback_regex_parse(code_str: str) -> List[Dict[str, Any]]:
    from app.scanners.parsers.javascript_parser import JS_CRYPTO_PATTERNS, JS_IMPORT_PATTERNS
    findings = []
    lines = code_str.splitlines()
    for idx, line in enumerate(lines, start=1):
        line_str = line.strip()
        for pattern, alg, purpose, desc in JS_CRYPTO_PATTERNS:
            if re.search(pattern, line_str):
                findings.append({
                    "line": idx,
                    "algorithm": alg,
                    "purpose": purpose,
                    "mode": None,
                    "padding": None,
                    "key_size": None,
                    "library": "crypto",
                    "api_call": pattern,
                    "matched_text": line_str,
                    "type": "API_CALL",
                    "description": desc,
                    "confidence": 0.85,
                    "detector": "regex_fallback",
                    "evidence_type": "OBSERVED",
                    "parameters": {}
                })
        for pattern, alg, purpose, desc in JS_IMPORT_PATTERNS:
            if re.search(pattern, line_str):
                findings.append({
                    "line": idx,
                    "algorithm": alg,
                    "purpose": purpose,
                    "mode": None,
                    "padding": None,
                    "key_size": None,
                    "library": "crypto",
                    "api_call": pattern,
                    "matched_text": line_str,
                    "type": "IMPORT",
                    "description": desc,
                    "confidence": 0.85,
                    "detector": "regex_fallback",
                    "evidence_type": "OBSERVED",
                    "parameters": {}
                })
    return findings
