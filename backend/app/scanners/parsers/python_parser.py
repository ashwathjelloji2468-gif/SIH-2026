import ast
from typing import List, Dict, Any

class PythonCryptoVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.findings: List[Dict[str, Any]] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self._check_module(alias.name, node.lineno)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            self._check_module(node.module, node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        # Detect RSA key generation / signing
        if "rsa" in func_name.lower() or "generate_private_key" in func_name.lower():
            self.findings.append({
                "line": node.lineno,
                "algorithm": "RSA",
                "matched_text": f"Call to {func_name}",
                "type": "API_CALL"
            })
        elif "ecdsa" in func_name.lower() or "ec" in func_name.lower():
            self.findings.append({
                "line": node.lineno,
                "algorithm": "ECDSA",
                "matched_text": f"Call to {func_name}",
                "type": "API_CALL"
            })
        elif "aes" in func_name.lower() or "cipher" in func_name.lower():
            self.findings.append({
                "line": node.lineno,
                "algorithm": "AES",
                "matched_text": f"Call to {func_name}",
                "type": "API_CALL"
            })

        self.generic_visit(node)

    def _check_module(self, module_name: str, lineno: int):
        crypto_modules = {
            "cryptography.hazmat.primitives.asymmetric.rsa": "RSA",
            "cryptography.hazmat.primitives.asymmetric.ec": "ECDSA",
            "cryptography.hazmat.primitives.ciphers": "AES",
            "Crypto.Cipher.AES": "AES",
            "Crypto.PublicKey.RSA": "RSA",
            "Crypto.Signature.pkcs1_15": "RSA",
            "hashlib": "HASHING"
        }
        for mod, alg in crypto_modules.items():
            if mod in module_name:
                self.findings.append({
                    "line": lineno,
                    "algorithm": alg,
                    "matched_text": f"import {module_name}",
                    "type": "IMPORT"
                })

def parse_python_file(file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=file_path)
        visitor = PythonCryptoVisitor(file_path)
        visitor.visit(tree)
        return visitor.findings
    except Exception:
        return []
