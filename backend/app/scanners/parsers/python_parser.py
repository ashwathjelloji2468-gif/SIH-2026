import ast
from typing import List, Dict, Any, Optional
from app.models.enums import CryptoPurpose, EvidenceType, AssetType
from app.core.logging import logger

KNOWN_CRYPTO_MODULES = {
    "cryptography.hazmat.primitives.asymmetric.rsa": ("RSA", CryptoPurpose.SIGNATURE),
    "cryptography.hazmat.primitives.asymmetric.ec": ("ECDSA", CryptoPurpose.SIGNATURE),
    "cryptography.hazmat.primitives.asymmetric.dsa": ("DSA", CryptoPurpose.SIGNATURE),
    "cryptography.hazmat.primitives.asymmetric.ed25519": ("Ed25519", CryptoPurpose.SIGNATURE),
    "cryptography.hazmat.primitives.asymmetric.x25519": ("X25519", CryptoPurpose.KEY_ESTABLISHMENT),
    "cryptography.hazmat.primitives.ciphers": ("AES", CryptoPurpose.ENCRYPTION),
    "Crypto.Cipher.AES": ("AES", CryptoPurpose.ENCRYPTION),
    "Crypto.Cipher.DES": ("DES", CryptoPurpose.ENCRYPTION),
    "Crypto.Cipher.ARC4": ("RC4", CryptoPurpose.ENCRYPTION),
    "Crypto.PublicKey.RSA": ("RSA", CryptoPurpose.KEY_ESTABLISHMENT),
    "Crypto.PublicKey.ECC": ("ECDSA", CryptoPurpose.KEY_ESTABLISHMENT),
    "Crypto.Signature.pkcs1_15": ("RSA", CryptoPurpose.SIGNATURE),
    "Crypto.Signature.pss": ("RSA", CryptoPurpose.SIGNATURE),
    "Crypto.Signature.dss": ("ECDSA", CryptoPurpose.SIGNATURE),
    "hashlib": ("HASHING", CryptoPurpose.HASHING),
}


class PythonCryptoVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings: List[Dict[str, Any]] = []
        # Mapping from local alias/variable to fully qualified module or algorithm info
        self.imports: Dict[str, str] = {}
        # Track variable assignments e.g. private_key = rsa.generate_private_key(...)
        self.var_types: Dict[str, Dict[str, Any]] = {}

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            local_name = alias.asname or alias.name
            self.imports[local_name] = alias.name
            self._check_module(alias.name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod_prefix = node.module or ""
        for alias in node.names:
            full_name = f"{mod_prefix}.{alias.name}" if mod_prefix else alias.name
            local_name = alias.asname or alias.name
            self.imports[local_name] = full_name
            self._check_module(full_name, node.lineno)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        self.generic_visit(node)

        # Track variable assignments if value is a Call returning a crypto object
        if isinstance(node.value, ast.Call):
            call_name = self._resolve_call_name(node.value.func)
            info = self._analyze_call(node.value, call_name)
            if info:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.var_types[target.id] = info

    def visit_Call(self, node: ast.Call):
        call_name = self._resolve_call_name(node.func)
        info = self._analyze_call(node, call_name)

        if info:
            self.findings.append({
                "line": node.lineno,
                "algorithm": info["algorithm"],
                "purpose": info["purpose"],
                "api_call": call_name,
                "resolved_library": info.get("resolved_library", "unknown"),
                "matched_text": f"Call to {call_name}",
                "type": "API_CALL",
                "key_size": info.get("key_size"),
                "parameters": info.get("parameters", {}),
                "confidence": 0.95,
                "evidence_type": "OBSERVED"
            })

        self.generic_visit(node)

    def _resolve_call_name(self, node: ast.AST) -> str:
        """Recursively resolves call target AST node to a string representation."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val_str = self._resolve_call_name(node.value)
            return f"{val_str}.{node.attr}" if val_str else node.attr
        elif isinstance(node, ast.Call):
            return self._resolve_call_name(node.func)
        return ""

    def _analyze_call(self, node: ast.Call, call_name: str) -> Optional[Dict[str, Any]]:
        if not call_name:
            return None

        parts = call_name.split(".")
        base_obj = parts[0]
        method_name = parts[-1]

        resolved_prefix = self.imports.get(base_obj, base_obj)
        resolved_full_call = f"{resolved_prefix}.{'.'.join(parts[1:])}" if len(parts) > 1 else resolved_prefix

        # Check if base object is a tracked variable (e.g. private_key.sign)
        var_info = self.var_types.get(base_obj)

        # 1. RSA calls: rsa.generate_private_key or private_key.sign
        if "rsa" in resolved_full_call.lower() or "generate_private_key" in method_name:
            key_size = self._extract_key_size(node)
            return {
                "algorithm": "RSA",
                "purpose": CryptoPurpose.KEY_ESTABLISHMENT if "generate" in method_name else CryptoPurpose.SIGNATURE,
                "resolved_library": self._infer_library(resolved_full_call),
                "key_size": key_size,
                "parameters": {"key_size": key_size} if key_size else {}
            }

        # 2. Hashlib calls: hashlib.sha256, h.sha256, hashlib.new('sha256'), digest(), hexdigest()
        if "hashlib" in resolved_full_call or base_obj == "hashlib" or resolved_prefix == "hashlib":
            alg_name = "SHA-256"
            if len(parts) > 1:
                sub = parts[1].lower()
                if "sha512" in sub:
                    alg_name = "SHA-512"
                elif "sha384" in sub:
                    alg_name = "SHA-384"
                elif "sha1" in sub:
                    alg_name = "SHA-1"
                elif "md5" in sub:
                    alg_name = "MD5"
                elif sub == "new":
                    first_arg = self._extract_string_arg(node, 0)
                    if first_arg:
                        alg_name = first_arg.upper()

            return {
                "algorithm": alg_name,
                "purpose": CryptoPurpose.HASHING,
                "resolved_library": "hashlib",
                "key_size": None,
                "parameters": {"algorithm": alg_name}
            }

        # 3. Method calls on tracked crypto variables or general method semantics
        if method_name in ["sign", "verify", "encrypt", "decrypt", "digest", "hexdigest"]:
            alg_name = var_info["algorithm"] if var_info else "UNKNOWN"
            if alg_name == "UNKNOWN":
                if "rsa" in base_obj.lower():
                    alg_name = "RSA"
                elif "ec" in base_obj.lower() or "ecdsa" in base_obj.lower():
                    alg_name = "ECDSA"
                elif "aes" in base_obj.lower() or "cipher" in base_obj.lower():
                    alg_name = "AES"
                elif method_name in ["digest", "hexdigest"]:
                    alg_name = "SHA-256"

            purpose = CryptoPurpose.SIGNATURE
            if method_name in ["encrypt", "decrypt"]:
                purpose = CryptoPurpose.ENCRYPTION
            elif method_name in ["digest", "hexdigest"]:
                purpose = CryptoPurpose.HASHING

            mode = self._extract_cipher_mode(node)
            params = {}
            if mode:
                params["mode"] = mode

            return {
                "algorithm": alg_name,
                "purpose": purpose,
                "resolved_library": self._infer_library(resolved_full_call),
                "key_size": var_info.get("key_size") if var_info else None,
                "parameters": params
            }

        # 4. AES / Symmetric Cipher calls
        if "aes" in resolved_full_call.lower() or "cipher" in resolved_full_call.lower():
            mode = self._extract_cipher_mode(node)
            key_size = self._extract_key_size(node)
            params = {}
            if mode:
                params["mode"] = mode
            if key_size:
                params["key_size"] = key_size

            return {
                "algorithm": "AES",
                "purpose": CryptoPurpose.ENCRYPTION,
                "resolved_library": self._infer_library(resolved_full_call),
                "key_size": key_size,
                "parameters": params
            }

        # 5. ECDSA / EC calls
        if "ecdsa" in resolved_full_call.lower() or "ec." in resolved_full_call.lower():
            return {
                "algorithm": "ECDSA",
                "purpose": CryptoPurpose.SIGNATURE,
                "resolved_library": self._infer_library(resolved_full_call),
                "key_size": None,
                "parameters": {}
            }

        return None

    def _extract_key_size(self, node: ast.Call) -> Optional[int]:
        # Check keyword arguments first
        for kw in node.keywords:
            if kw.arg in ["key_size", "bits", "size"]:
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int):
                    return kw.value.value
                elif isinstance(kw.value, ast.Num):
                    return kw.value.n

        # Check positional arguments for key sizes
        for arg in node.args:
            val = None
            if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                val = arg.value
            elif isinstance(arg, ast.Num):
                val = arg.n

            if val and val in [128, 192, 256, 512, 1024, 2048, 3072, 4096, 8192]:
                return val

        return None

    def _extract_cipher_mode(self, node: ast.Call) -> Optional[str]:
        for kw in node.keywords:
            if kw.arg in ["mode", "cipher_mode"]:
                val_str = self._resolve_call_name(kw.value)
                for m in ["CBC", "GCM", "CTR", "ECB", "CFB", "OFB"]:
                    if m in val_str.upper():
                        return m

        for arg in node.args:
            val_str = self._resolve_call_name(arg)
            for m in ["CBC", "GCM", "CTR", "ECB", "CFB", "OFB"]:
                if m in val_str.upper():
                    return m

        return None

    def _extract_string_arg(self, node: ast.Call, index: int = 0) -> Optional[str]:
        if len(node.args) > index:
            arg = node.args[index]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
        return None

    def _infer_library(self, call_str: str) -> str:
        if "cryptography" in call_str:
            return "cryptography"
        elif "Crypto" in call_str or "PyCryptodome" in call_str:
            return "PyCryptodome"
        elif "hashlib" in call_str:
            return "hashlib"
        elif "ssl" in call_str:
            return "ssl"
        return "python-crypto"

    def _check_module(self, module_name: str, lineno: int):
        for mod, (alg, purpose) in KNOWN_CRYPTO_MODULES.items():
            if mod in module_name:
                self.findings.append({
                    "line": lineno,
                    "algorithm": alg if alg != "HASHING" else "SHA-256",
                    "purpose": purpose,
                    "api_call": module_name,
                    "resolved_library": self._infer_library(module_name),
                    "matched_text": f"import {module_name}",
                    "type": "IMPORT",
                    "key_size": None,
                    "parameters": {},
                    "confidence": 0.95,
                    "evidence_type": "OBSERVED"
                })


def parse_python_file(file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=file_path)
        visitor = PythonCryptoVisitor(file_path)
        visitor.visit(tree)
        return visitor.findings
    except SyntaxError as se:
        logger.warning(f"Python parser syntax error in '{file_path}' at line {se.lineno}: {se.msg}")
        return []
    except (UnicodeDecodeError, OSError) as ioe:
        logger.warning(f"Python parser file reading error in '{file_path}': {ioe}")
        return []
    except Exception as e:
        logger.error(f"Python parser unexpected error processing '{file_path}': {e}", exc_info=True)
        return []

