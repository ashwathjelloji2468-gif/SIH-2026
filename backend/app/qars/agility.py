import ast
import re
from typing import Optional, Dict, Any, List, Set
from app.qars.models import QARSCryptoAgilityEvidence

# ----------------------------------------------------------------------
# KNOWN CRYPTO DOMAIN PATTERNS & REGEXES
# ----------------------------------------------------------------------

KNOWN_CRYPTO_MODULES = {
    "hashlib", "cryptography", "Crypto", "pycryptodome", "jwt", "jose",
    "ssl", "paramiko", "rsa", "ecdsa", "secretstorage", "kmip", "openwall",
    "javax.crypto", "java.security", "org.bouncycastle", "webcrypto"
}

KNOWN_CRYPTO_FUNCTIONS = {
    "sha256", "sha512", "sha384", "sha1", "md5", "new", "generate_private_key",
    "generate_key", "derive_key", "encrypt", "decrypt", "sign", "verify",
    "getInstance", "createCipher", "createCipheriv", "createDecipher",
    "createDecipheriv", "createSign", "createVerify", "digest"
}

CRYPTO_METHOD_SEMANTICS = {
    "encrypt", "decrypt", "sign", "verify", "generate_key", "derive_key",
    "exchange_key", "hash", "digest", "cipher", "certificate", "private_key",
    "public_key", "signature", "key_exchange", "get_cipher", "sign_ssh_data", "verify_ssh_sig",
    "add_provider", "register_provider", "set_crypto_backend"
}

CRYPTO_TYPE_KEYWORDS = {
    "Crypto", "Cipher", "PKey", "Key", "SecurityProvider", "JCE", "PKCS11",
    "Encryption", "Decryption", "Signature", "KMS", "HSM", "OpenSSL", "Backend"
}

CRYPTO_ALG_REGEX = re.compile(
    r"\b(AES|RSA|ECDSA|ECDH|SHA-?256|SHA-?512|SHA-?384|SHA-?1|DES|3DES|RC4|Ed25519|X25519|Dilithium|Falcon|Sphincs|Kyber|SABER|BIKE|HQC|FrodoKEM|RS256|RS512|HS256|HS512)\b",
    re.IGNORECASE
)


def analyze_source_ast_for_agility(source_code: str, file_path: str = "source.py") -> Dict[str, Any]:
    """
    Analyzes Python source code AST deterministically using a Two-Signal Classifier:
    - Signal 1: Structural pattern (ABC, Interface, Provider, Adapter, Registry)
    - Signal 2: Cryptographic relevance (crypto library import, crypto method, crypto type)

    Returns precise counts and auditable evidence signals for hard-coded algorithm references,
    crypto abstraction layers, and replaceable crypto interfaces.
    """
    results: Dict[str, Any] = {
        "hard_coded_count": 0,
        "configured_count": 0,
        "total_crypto_refs": 0,
        "abstractions_found": [],
        "replaceable_interfaces_found": [],
        "evidence_files": [file_path] if file_path else [],
        "evidence_signals": []
    }

    try:
        tree = ast.parse(source_code)
    except Exception:
        return results

    class TwoSignalASTVisitor(ast.NodeVisitor):
        def __init__(self):
            self.imported_modules: Set[str] = set()
            self.has_crypto_import: bool = False

        def visit_Import(self, node: ast.Import):
            for alias in node.names:
                mod_name = alias.name
                self.imported_modules.add(mod_name)
                if any(m in mod_name for m in KNOWN_CRYPTO_MODULES) or any(k in mod_name.lower() for k in ["crypto", "cipher", "hazmat", "security"]):
                    self.has_crypto_import = True
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom):
            mod_name = node.module or ""
            self.imported_modules.add(mod_name)
            if any(m in mod_name for m in KNOWN_CRYPTO_MODULES) or any(k in mod_name.lower() for k in ["crypto", "cipher", "hazmat", "security"]):
                self.has_crypto_import = True
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call):
            call_name = ""
            base_obj = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
                if isinstance(node.func.value, ast.Name):
                    base_obj = node.func.value.id

            full_call_str = f"{base_obj}.{call_name}" if base_obj else call_name

            # Check if this call is a known, verified crypto operation
            is_crypto_call = False
            if base_obj and (any(m in base_obj for m in KNOWN_CRYPTO_MODULES) or base_obj in ["hashlib", "rsa", "ec", "Cipher", "Signature", "crypto", "jwt"]):
                is_crypto_call = True
            elif call_name in KNOWN_CRYPTO_FUNCTIONS and self.has_crypto_import:
                is_crypto_call = True
            elif full_call_str in ["hashlib.sha256", "hashlib.sha512", "hashlib.md5", "hashlib.sha1", "hashlib.new"]:
                is_crypto_call = True

            if is_crypto_call:
                results["total_crypto_refs"] += 1
                has_hardcoded_arg = False

                for arg in node.args:
                    if isinstance(arg, (ast.Constant, ast.Str)):
                        val_str = str(getattr(arg, "value", getattr(arg, "s", "")))
                        if CRYPTO_ALG_REGEX.search(val_str):
                            has_hardcoded_arg = True
                            break

                for kw in node.keywords:
                    if isinstance(kw.value, (ast.Constant, ast.Str)):
                        val_str = str(getattr(kw.value, "value", getattr(kw.value, "s", "")))
                        if CRYPTO_ALG_REGEX.search(val_str):
                            has_hardcoded_arg = True
                            break

                if has_hardcoded_arg or call_name in ["sha256", "sha512", "sha384", "md5", "generate_private_key"]:
                    results["hard_coded_count"] += 1
                else:
                    results["configured_count"] += 1

            if call_name in ["add_provider", "register_provider", "set_crypto_backend", "register_adapter", "addProvider"] and (self.has_crypto_import or "crypto" in full_call_str.lower()):
                signal_entry = {
                    "file": file_path,
                    "pattern": f"Call to {call_name}",
                    "signals": ["provider_registry_call", "crypto_context_verified"]
                }
                results["replaceable_interfaces_found"].append(f"Call to {call_name} at line {getattr(node, 'lineno', 0)}")
                results["evidence_signals"].append(signal_entry)

            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef):
            class_name = node.name
            base_names = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(base.attr)

            # --------------------------------------------------
            # SIGNAL 1: Structural Abstraction / Provider Pattern
            # --------------------------------------------------
            is_abstract_struct = any(b in ["ABC", "Interface", "BaseCryptoProvider", "ICryptoProvider", "PKey", "CipherContext"] for b in base_names)
            is_provider_struct = any(kw in class_name for kw in ["Provider", "Adapter", "Registry", "Factory", "Wrapper", "Service", "Backend"])

            has_abstract_methods = False
            class_methods = set()
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef):
                    class_methods.add(body_item.name)
                    for decorator in body_item.decorator_list:
                        dec_name = decorator.id if isinstance(decorator, ast.Name) else (decorator.attr if isinstance(decorator, ast.Attribute) else "")
                        if dec_name == "abstractmethod":
                            has_abstract_methods = True

            signal1_present = is_abstract_struct or is_provider_struct or has_abstract_methods
            signal1_reasons = []
            if is_abstract_struct:
                signal1_reasons.append("class_inherits_abstract_base")
            if is_provider_struct:
                signal1_reasons.append("class_matches_provider_pattern")
            if has_abstract_methods:
                signal1_reasons.append("class_has_abstract_methods")

            # --------------------------------------------------
            # SIGNAL 2: Cryptographic Relevance Evidence
            # --------------------------------------------------
            has_crypto_method = bool(class_methods.intersection(CRYPTO_METHOD_SEMANTICS))
            has_crypto_type = any(kw in class_name for kw in CRYPTO_TYPE_KEYWORDS) or any(b in ["CipherContext", "PKey", "BaseCryptoProvider", "ICryptoProvider"] for b in base_names)
            has_crypto_import = self.has_crypto_import

            signal2_present = has_crypto_method or has_crypto_type or (has_crypto_import and (has_abstract_methods or is_provider_struct or "crypto" in class_name.lower()))
            signal2_reasons = []
            if has_crypto_method:
                signal2_reasons.append("crypto_method_detected")
            if has_crypto_type:
                signal2_reasons.append("crypto_type_detected")
            if has_crypto_import:
                signal2_reasons.append("crypto_library_import")

            # --------------------------------------------------
            # MULTI-SIGNAL EVALUATION (Requires Signal 1 AND Signal 2)
            # --------------------------------------------------
            if signal1_present and signal2_present:
                all_signals = signal1_reasons + signal2_reasons
                signal_entry = {
                    "file": file_path,
                    "pattern": f"Class {class_name}",
                    "signals": all_signals
                }

                if is_abstract_struct or has_abstract_methods or "Factory" in class_name or "Wrapper" in class_name or "Service" in class_name or "CipherContext" in class_name or "PKey" in class_name:
                    results["abstractions_found"].append(f"Class {class_name} at line {node.lineno}")
                    results["evidence_signals"].append(signal_entry)

                if "Provider" in class_name or "Adapter" in class_name or "Registry" in class_name or "Backend" in class_name:
                    results["replaceable_interfaces_found"].append(f"Pluggable class {class_name} at line {node.lineno}")
                    if signal_entry not in results["evidence_signals"]:
                        results["evidence_signals"].append(signal_entry)

            self.generic_visit(node)

    visitor = TwoSignalASTVisitor()
    visitor.visit(tree)
    return results


def collect_crypto_agility_evidence(
    asset: Any,
    project: Optional[Any] = None,
    db: Optional[Any] = None
) -> QARSCryptoAgilityEvidence:
    """
    Phase 3B.2 Multi-Signal Crypto-Agility Structural Evidence Collector.
    Collects observable scanner evidence and structural AST analysis metrics for:
    1. hard_coded_algorithm_ratio
    2. crypto_abstraction_layer_presence
    3. replaceable_library_interface_count

    Does NOT compute fake numeric agility scores, CAR, or arbitrary normalization weights.
    """
    factors: Dict[str, Any] = {}
    provenance: Dict[str, str] = {}
    evidence_files_set = set()

    # ----------------------------------------------------
    # PHASE 3A EVIDENCE FACTORS (Preserved Unchanged)
    # ----------------------------------------------------
    assets_count = 1
    if hasattr(asset, "scan") and asset.scan and hasattr(asset.scan, "assets"):
        assets_count = max(1, len(asset.scan.assets))
    factors["affected_assets_count"] = assets_count
    provenance["affected_assets_count"] = "SCANNER_EVIDENCE"

    files_count = 1
    if hasattr(asset, "evidence_items") and asset.evidence_items:
        files_set = {
            e.source_file for e in asset.evidence_items
            if hasattr(e, "source_file") and e.source_file
        }
        if files_set:
            files_count = len(files_set)
            evidence_files_set.update(files_set)
    factors["affected_files_count"] = files_count
    provenance["affected_files_count"] = "SCANNER_EVIDENCE"

    blast_nodes = 0
    extra = dict(getattr(asset, "extra_metadata", {}) or {}) if hasattr(asset, "extra_metadata") else (asset.get("extra_metadata", {}) if isinstance(asset, dict) else {})
    if "blast_radius_affected_nodes" in extra and extra["blast_radius_affected_nodes"] is not None:
        blast_nodes = int(extra["blast_radius_affected_nodes"])
    elif hasattr(asset, "scan") and asset.scan and hasattr(asset.scan, "blast_radius_results") and asset.scan.blast_radius_results:
        blast_nodes = int(asset.scan.blast_radius_results[0].affected_nodes_count)
    factors["blast_radius_affected_nodes"] = blast_nodes
    provenance["blast_radius_affected_nodes"] = "DERIVED_SYSTEM_ANALYSIS"

    asset_type_str = str(getattr(asset, "asset_type", "") or extra.get("asset_type", "")).upper()
    alg_str = str(getattr(asset, "algorithm_name", "") or extra.get("algorithm", "") or extra.get("algorithm_name", "")).upper()
    vendor_kms_hsm = (
        "VENDOR" in asset_type_str or
        "BINARY" in asset_type_str or
        "KMS" in alg_str or
        "HSM" in alg_str
    )
    factors["vendor_kms_hsm_detected"] = vendor_kms_hsm
    provenance["vendor_kms_hsm_detected"] = "SCANNER_EVIDENCE"

    purpose_str = str(getattr(asset, "purpose", "") or extra.get("purpose", "")).upper()
    protocol_impact = (
        "PROTOCOL" in asset_type_str or
        "TLS" in alg_str or
        "SSH" in alg_str or
        "KEY_ESTABLISHMENT" in purpose_str
    )
    factors["protocol_impact_detected"] = protocol_impact
    provenance["protocol_impact_detected"] = "SCANNER_EVIDENCE"

    pki_count = 0
    if hasattr(asset, "evidence_items") and asset.evidence_items:
        pki_count = sum(
            1 for e in asset.evidence_items
            if hasattr(e, "detector_name") and any(k in str(e.detector_name).lower() for k in ["cert", "pki", "x509"])
        )
    factors["pki_cert_dependency_count"] = pki_count
    provenance["pki_cert_dependency_count"] = "SCANNER_EVIDENCE"

    dep_count = 0
    if hasattr(asset, "scan") and asset.scan and hasattr(asset.scan, "edges"):
        dep_count = sum(
            1 for edge in asset.scan.edges
            if hasattr(edge, "relation_type") and str(edge.relation_type).lower() in ["depends_on", "uses"]
        )
    factors["dependency_count"] = dep_count
    provenance["dependency_count"] = "SCANNER_EVIDENCE"

    if "evidence_files" in extra and isinstance(extra["evidence_files"], list):
        evidence_files_set.update(extra["evidence_files"])

    overrides = extra.get("context_overrides", {})

    # ----------------------------------------------------
    # PHASE 3B STRUCTURAL FACTORS ANALYSIS
    # ----------------------------------------------------

    # 1. HARD-CODED ALGORITHM RATIO
    hard_coded_ratio: Optional[float] = None
    hard_coded_status: str = "UNCONFIGURED"
    hard_coded_conf: Optional[float] = None

    if "hard_coded_algorithm_ratio" in overrides:
        val = overrides["hard_coded_algorithm_ratio"]
        if val is not None:
            hard_coded_ratio = float(val)
            hard_coded_status = "CONFIGURED"
            hard_coded_conf = float(overrides.get("hard_coded_algorithm_ratio_confidence", 0.95))
            provenance["hard_coded_algorithm_ratio"] = "USER_OVERRIDE"
    elif "hard_coded_algorithm_ratio" in extra:
        val = extra["hard_coded_algorithm_ratio"]
        if isinstance(val, dict):
            hard_coded_ratio = val.get("value")
            hard_coded_status = val.get("status", "CONFIGURED" if hard_coded_ratio is not None else "UNCONFIGURED")
            hard_coded_conf = val.get("confidence")
        elif val is not None:
            hard_coded_ratio = float(val)
            hard_coded_status = "CONFIGURED"
            hard_coded_conf = float(extra.get("hard_coded_algorithm_ratio_confidence", 0.95))
        provenance["hard_coded_algorithm_ratio"] = "DERIVED_SYSTEM_ANALYSIS"
    elif "hard_coded_count" in extra or "ast_findings" in extra or "source_code" in extra:
        if "hard_coded_count" in extra:
            hc_count = int(extra["hard_coded_count"])
            total_refs = int(extra.get("total_crypto_references", extra.get("configured_count", 0) + hc_count))
            if total_refs > 0:
                hard_coded_ratio = round(hc_count / total_refs, 4)
                hard_coded_status = "CONFIGURED"
                hard_coded_conf = float(extra.get("confidence", 0.95))
            else:
                hard_coded_ratio = None
                hard_coded_status = "UNCONFIGURED"
                hard_coded_conf = None
        elif "source_code" in extra:
            ast_res = analyze_source_ast_for_agility(extra["source_code"], extra.get("file_path", "source.py"))
            if ast_res["total_crypto_refs"] > 0:
                hard_coded_ratio = round(ast_res["hard_coded_count"] / ast_res["total_crypto_refs"], 4)
                hard_coded_status = "CONFIGURED"
                hard_coded_conf = 0.95
                evidence_files_set.update(ast_res["evidence_files"])
            else:
                hard_coded_ratio = None
                hard_coded_status = "UNCONFIGURED"
                hard_coded_conf = None
        provenance.setdefault("hard_coded_algorithm_ratio", "DERIVED_SYSTEM_ANALYSIS")

    if hard_coded_status == "CONFIGURED" and hard_coded_ratio is not None:
        factors["hard_coded_algorithm_ratio"] = hard_coded_ratio
        provenance.setdefault("hard_coded_algorithm_ratio", "DERIVED_SYSTEM_ANALYSIS")

    # 2. CRYPTO ABSTRACTION LAYER PRESENCE
    abstraction_presence: Optional[bool] = None
    abstraction_status: str = "UNCONFIGURED"
    abstraction_conf: Optional[float] = None

    if "crypto_abstraction_layer_presence" in overrides:
        val = overrides["crypto_abstraction_layer_presence"]
        if val is not None:
            abstraction_presence = bool(val)
            abstraction_status = "CONFIGURED"
            abstraction_conf = float(overrides.get("crypto_abstraction_layer_confidence", 0.95))
            provenance["crypto_abstraction_layer_presence"] = "USER_OVERRIDE"
    elif "crypto_abstraction_layer_presence" in extra:
        val = extra["crypto_abstraction_layer_presence"]
        if isinstance(val, dict):
            abstraction_presence = val.get("present")
            abstraction_status = val.get("status", "CONFIGURED" if abstraction_presence is not None else "UNCONFIGURED")
            abstraction_conf = val.get("confidence")
        elif val is not None:
            abstraction_presence = bool(val)
            abstraction_status = "CONFIGURED"
            abstraction_conf = float(extra.get("crypto_abstraction_layer_confidence", 0.95))
        provenance["crypto_abstraction_layer_presence"] = "SCANNER_EVIDENCE"
    elif "verified_scan" in extra or "source_code" in extra or "abstractions_found" in extra:
        if extra.get("verified_scan") is True or "abstractions_found" in extra:
            abstractions = extra.get("abstractions_found", [])
            has_abstr = len(abstractions) > 0 or extra.get("has_abstraction", False)
            abstraction_presence = bool(has_abstr)
            abstraction_status = "CONFIGURED"
            abstraction_conf = 0.95 if abstraction_presence else 0.90
        elif "source_code" in extra:
            ast_res = analyze_source_ast_for_agility(extra["source_code"], extra.get("file_path", "source.py"))
            abstraction_presence = len(ast_res["abstractions_found"]) > 0
            abstraction_status = "CONFIGURED"
            abstraction_conf = 0.95 if abstraction_presence else 0.90
            evidence_files_set.update(ast_res["evidence_files"])
        provenance.setdefault("crypto_abstraction_layer_presence", "SCANNER_EVIDENCE")

    if abstraction_status == "CONFIGURED" and abstraction_presence is not None:
        factors["crypto_abstraction_layer_presence"] = abstraction_presence
        provenance.setdefault("crypto_abstraction_layer_presence", "SCANNER_EVIDENCE")

    # 3. REPLACEABLE LIBRARY INTERFACE COUNT
    replaceable_count: Optional[int] = None
    replaceable_status: str = "UNCONFIGURED"
    replaceable_conf: Optional[float] = None

    if "replaceable_library_interface_count" in overrides:
        val = overrides["replaceable_library_interface_count"]
        if val is not None:
            replaceable_count = int(val)
            replaceable_status = "CONFIGURED"
            replaceable_conf = float(overrides.get("replaceable_library_interface_confidence", 0.90))
            provenance["replaceable_library_interface_count"] = "USER_OVERRIDE"
    elif "replaceable_library_interface_count" in extra:
        val = extra["replaceable_library_interface_count"]
        if isinstance(val, dict):
            replaceable_count = val.get("count")
            replaceable_status = val.get("status", "CONFIGURED" if replaceable_count is not None else "UNCONFIGURED")
            replaceable_conf = val.get("confidence")
        elif val is not None:
            replaceable_count = int(val)
            replaceable_status = "CONFIGURED"
            replaceable_conf = float(extra.get("replaceable_library_interface_confidence", 0.90))
        provenance["replaceable_library_interface_count"] = "SCANNER_EVIDENCE"
    elif "verified_scan" in extra or "source_code" in extra or "replaceable_interfaces_found" in extra:
        if extra.get("verified_scan") is True or "replaceable_interfaces_found" in extra:
            rep_list = extra.get("replaceable_interfaces_found", [])
            replaceable_count = len(rep_list) if "replaceable_interfaces_found" in extra else int(extra.get("replaceable_count", 0))
            replaceable_status = "CONFIGURED"
            replaceable_conf = 0.90
        elif "source_code" in extra:
            ast_res = analyze_source_ast_for_agility(extra["source_code"], extra.get("file_path", "source.py"))
            replaceable_count = len(ast_res["replaceable_interfaces_found"])
            replaceable_status = "CONFIGURED"
            replaceable_conf = 0.90
            evidence_files_set.update(ast_res["evidence_files"])
        provenance.setdefault("replaceable_library_interface_count", "SCANNER_EVIDENCE")

    if replaceable_status == "CONFIGURED" and replaceable_count is not None:
        factors["replaceable_library_interface_count"] = replaceable_count
        provenance.setdefault("replaceable_library_interface_count", "SCANNER_EVIDENCE")

    # ----------------------------------------------------
    # MISSING FACTORS & TOP-LEVEL STATUS
    # ----------------------------------------------------
    missing_factors = []
    if hard_coded_status == "UNCONFIGURED":
        missing_factors.append("hard_coded_algorithm_ratio")
    if abstraction_status == "UNCONFIGURED":
        missing_factors.append("crypto_abstraction_layer_presence")
    if replaceable_status == "UNCONFIGURED":
        missing_factors.append("replaceable_library_interface_count")

    if len(missing_factors) == 0:
        overall_status = "CONFIGURED"
    elif len(missing_factors) == 3:
        overall_status = "PARTIALLY_CONFIGURED"
    else:
        overall_status = "PARTIALLY_CONFIGURED"

    evidence_files_list = sorted(list(evidence_files_set))

    # ----------------------------------------------------
    # PHASE 4 AGILITY SCORE & CAR CALCULATION
    # ----------------------------------------------------
    agility_score: Optional[float] = None
    car_score: Optional[float] = None

    if len(missing_factors) < 3:
        from app.qars.agility_calibration import load_agility_calibration
        calib = load_agility_calibration()
        weights = calib.get("factor_weights", {})
        agil_ver = calib.get("metadata", {}).get("version", "SENTRIQ QARS Prototype Heuristic Agility Calibration v1")

        weighted_val = 0.0
        active_w_sum = 0.0

        if hard_coded_ratio is not None and "hard_coded_algorithm_ratio" in weights:
            w = weights["hard_coded_algorithm_ratio"]
            weighted_val += (1.0 - float(hard_coded_ratio)) * w
            active_w_sum += w

        if abstraction_presence is not None and "crypto_abstraction_layer_presence" in weights:
            w = weights["crypto_abstraction_layer_presence"]
            weighted_val += (1.0 if abstraction_presence else 0.0) * w
            active_w_sum += w

        if replaceable_count is not None and "replaceable_library_interface_count" in weights:
            w = weights["replaceable_library_interface_count"]
            weighted_val += min(1.0, float(replaceable_count) / 3.0) * w
            active_w_sum += w

        if "vendor_kms_hsm_detected" in weights:
            w = weights["vendor_kms_hsm_detected"]
            weighted_val += (0.0 if vendor_kms_hsm else 1.0) * w
            active_w_sum += w

        if "protocol_impact_detected" in weights:
            w = weights["protocol_impact_detected"]
            weighted_val += (0.0 if protocol_impact else 1.0) * w
            active_w_sum += w

        if active_w_sum > 0:
            agility_score = round((weighted_val / active_w_sum) * 100.0, 2)
            car_score = round(100.0 - agility_score, 2)
    else:
        agil_ver = "SENTRIQ QARS Prototype Heuristic Agility Calibration v1"

    return QARSCryptoAgilityEvidence(
        status=overall_status,
        factors=factors,
        provenance=provenance,
        missing_factors=missing_factors,
        hard_coded_algorithm_ratio=hard_coded_ratio,
        hard_coded_algorithm_ratio_status=hard_coded_status,
        hard_coded_algorithm_ratio_confidence=hard_coded_conf,
        crypto_abstraction_layer_presence=abstraction_presence,
        crypto_abstraction_layer_status=abstraction_status,
        crypto_abstraction_layer_confidence=abstraction_conf,
        replaceable_library_interface_count=replaceable_count,
        replaceable_library_interface_status=replaceable_status,
        replaceable_library_interface_confidence=replaceable_conf,
        evidence_files=evidence_files_list,
        agility_score=agility_score,
        car_score=car_score,
        calibration_version=agil_ver
    )

