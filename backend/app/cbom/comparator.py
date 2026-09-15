import copy
from typing import Dict, Any, List, Optional, Tuple
from app.cbom.validator import CBOMValidator

class CBOMComparator:
    """
    Deterministic Before/After CBOM Comparison Engine for SENTRIQ (Priority 2 Task #8).
    Compares baseline CBOM against post-migration CBOM without modifying either source CBOM.
    
    Component Identity Strategy:
    1. Primary identity match: exact CycloneDX `bom-ref` (if present and non-generic).
    2. Fallback identity match: `(location, line_number)` - representing the physical source code location of the cryptographic asset.
    3. Secondary fallback: `(location, asset_type)` - for assets in the same file with matching type.
    4. Tertiary fallback: `(name, asset_type)` - matching asset name and classification.
    
    Change Classification:
    - ADDED: Components present in AFTER CBOM but not matched to BEFORE CBOM.
    - REMOVED: Components present in BEFORE CBOM but not matched to AFTER CBOM.
    - CHANGED: Matched components where algorithm, key_size, purpose/primitive, or quantum_safety status changed.
    - UNCHANGED: Matched components where all cryptographic properties remain identical.
    """

    def __init__(self):
        self.validator = CBOMValidator()

    def compare(self, before_cbom: Optional[Dict[str, Any]], after_cbom: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        # 1. Input Validation
        if not before_cbom or not isinstance(before_cbom, dict):
            return self._build_error_response("INVALID_CBOM", "BEFORE CBOM is missing or not a valid CycloneDX document.")
        
        if not after_cbom or not isinstance(after_cbom, dict):
            return self._build_error_response("INVALID_CBOM", "AFTER CBOM is missing or not a valid CycloneDX document.")

        if not self.validator.validate(before_cbom):
            return self._build_error_response("INVALID_CBOM", "BEFORE CBOM failed CycloneDX 1.6 validation rules.")

        if not self.validator.validate(after_cbom):
            return self._build_error_response("INVALID_CBOM", "AFTER CBOM failed CycloneDX 1.6 validation rules.")

        before_components = before_cbom.get("components", [])
        after_components = after_cbom.get("components", [])

        # 2. Extract Parsed Component Metadata
        before_parsed = [self._parse_component(c, idx) for idx, c in enumerate(before_components)]
        after_parsed = [self._parse_component(c, idx) for idx, c in enumerate(after_components)]

        # 3. Match Components deterministically
        matched_pairs, unmatched_before, unmatched_after = self._match_components(before_parsed, after_parsed)

        added: List[Dict[str, Any]] = []
        removed: List[Dict[str, Any]] = []
        changed: List[Dict[str, Any]] = []
        unchanged: List[Dict[str, Any]] = []
        summary: List[str] = []

        # Process Matched Components
        for b_comp, a_comp in matched_pairs:
            diffs = self._detect_property_changes(b_comp, a_comp)
            comp_info = {
                "bom_ref": a_comp["bom_ref"] or b_comp["bom_ref"],
                "name": a_comp["name"] or b_comp["name"],
                "asset_type": a_comp["asset_type"] or b_comp["asset_type"],
                "location": a_comp["location"] if a_comp["location"] != "Evidence unavailable" else b_comp["location"],
                "before_properties": {
                    "algorithm": b_comp["algorithm"],
                    "key_size": b_comp["key_size"],
                    "purpose": b_comp["purpose"],
                    "quantum_safety": b_comp["quantum_safety"],
                    "security_level": b_comp["security_level"]
                },
                "after_properties": {
                    "algorithm": a_comp["algorithm"],
                    "key_size": a_comp["key_size"],
                    "purpose": a_comp["purpose"],
                    "quantum_safety": a_comp["quantum_safety"],
                    "security_level": a_comp["security_level"]
                },
                "evidence": a_comp["evidence_summary"] if a_comp["evidence_summary"] != "Evidence unavailable" else b_comp["evidence_summary"],
                "changes": diffs
            }

            if diffs:
                changed.append(comp_info)
                alg_change = f"{b_comp['algorithm']} → {a_comp['algorithm']}" if b_comp['algorithm'] != a_comp['algorithm'] else b_comp['algorithm']
                qs_change = f" ({b_comp['quantum_safety']} → {a_comp['quantum_safety']})" if b_comp['quantum_safety'] != a_comp['quantum_safety'] else ""
                summary.append(f"CHANGED: '{b_comp['name']}' at {comp_info['location']}: {alg_change}{qs_change}")
            else:
                unchanged.append(comp_info)

        # Process Removed Components
        for b_comp in unmatched_before:
            removed_info = {
                "bom_ref": b_comp["bom_ref"],
                "name": b_comp["name"],
                "asset_type": b_comp["asset_type"],
                "location": b_comp["location"],
                "before_properties": {
                    "algorithm": b_comp["algorithm"],
                    "key_size": b_comp["key_size"],
                    "purpose": b_comp["purpose"],
                    "quantum_safety": b_comp["quantum_safety"],
                    "security_level": b_comp["security_level"]
                },
                "after_properties": None,
                "evidence": b_comp["evidence_summary"]
            }
            removed.append(removed_info)
            summary.append(f"REMOVED: '{b_comp['name']}' ({b_comp['algorithm']}) at {b_comp['location']}")

        # Process Added Components
        for a_comp in unmatched_after:
            added_info = {
                "bom_ref": a_comp["bom_ref"],
                "name": a_comp["name"],
                "asset_type": a_comp["asset_type"],
                "location": a_comp["location"],
                "before_properties": None,
                "after_properties": {
                    "algorithm": a_comp["algorithm"],
                    "key_size": a_comp["key_size"],
                    "purpose": a_comp["purpose"],
                    "quantum_safety": a_comp["quantum_safety"],
                    "security_level": a_comp["security_level"]
                },
                "evidence": a_comp["evidence_summary"]
            }
            added.append(added_info)
            summary.append(f"ADDED: '{a_comp['name']}' ({a_comp['algorithm']}) at {a_comp['location']}")

        status = "CHANGED" if (added or removed or changed) else "NO_CHANGE"
        if not summary:
            summary.append("No cryptographic asset or CBOM component changes detected between BEFORE and AFTER states.")

        return {
            "status": status,
            "before_component_count": len(before_components),
            "after_component_count": len(after_components),
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
            "unchanged_count": len(unchanged),
            "added": added,
            "removed": removed,
            "changed": changed,
            "unchanged": unchanged,
            "summary": summary
        }

    def _parse_component(self, comp: Dict[str, Any], idx: int) -> Dict[str, Any]:
        bom_ref = comp.get("bom-ref") or f"ref-{idx}"
        name = comp.get("name") or "Unknown Asset"
        comp_type = comp.get("type") or "cryptographic"
        
        crypto_props = comp.get("cryptoProperties", {})
        asset_type = crypto_props.get("assetType") or comp_type
        
        alg_props = crypto_props.get("algorithmProperties", {})
        primitive = alg_props.get("primitive") or "UNKNOWN"
        param_id = alg_props.get("parameterSetIdentifier") or "default"
        
        # Extract algorithm name cleanly
        if "-" in name:
            parts = name.split("-")
            if parts[-1].isdigit():
                alg_name = "-".join(parts[:-1])
            else:
                alg_name = name
        else:
            alg_name = name
        
        nist_qs = crypto_props.get("nistQuantumSecurityLevel")
        quantum_safety = "QUANTUM_SAFE" if nist_qs == 1 else ("QUANTUM_VULNERABLE" if nist_qs == 0 else "UNKNOWN")

        # Extract evidence & location
        ev_occs = comp.get("evidence", {}).get("occurrences", [])
        loc_str = "Evidence unavailable"
        line_num = None
        if ev_occs and isinstance(ev_occs, list) and len(ev_occs) > 0:
            occ0 = ev_occs[0]
            loc_path = occ0.get("location")
            line_num = occ0.get("line")
            if loc_path:
                loc_str = f"{loc_path}:{line_num}" if line_num else loc_path

        sec_level = crypto_props.get("classicalSecurityLevel") or param_id

        return {
            "raw": comp,
            "idx": idx,
            "bom_ref": bom_ref,
            "name": name,
            "asset_type": asset_type,
            "algorithm": alg_name,
            "key_size": param_id,
            "purpose": primitive,
            "quantum_safety": quantum_safety,
            "security_level": sec_level,
            "location": loc_str,
            "line_number": line_num,
            "evidence_summary": loc_str
        }

    def _match_components(
        self,
        before_list: List[Dict[str, Any]],
        after_list: List[Dict[str, Any]]
    ) -> Tuple[List[Tuple[Dict[str, Any], Dict[str, Any]]], List[Dict[str, Any]], List[Dict[str, Any]]]:

        matched: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        used_before = set()
        used_after = set()

        # Rule 1: Match by exact bom-ref (if custom/stable)
        for b in before_list:
            if b["idx"] in used_before:
                continue
            for a in after_list:
                if a["idx"] in used_after:
                    continue
                if b["bom_ref"] and b["bom_ref"] == a["bom_ref"]:
                    matched.append((b, a))
                    used_before.add(b["idx"])
                    used_after.add(a["idx"])
                    break

        # Rule 2: Match by exact (location, line_number) if location available
        for b in before_list:
            if b["idx"] in used_before:
                continue
            if b["location"] == "Evidence unavailable":
                continue
            for a in after_list:
                if a["idx"] in used_after:
                    continue
                if a["location"] != "Evidence unavailable" and b["location"] == a["location"]:
                    matched.append((b, a))
                    used_before.add(b["idx"])
                    used_after.add(a["idx"])
                    break

        # Rule 3: Match by (location_file_base, asset_type)
        for b in before_list:
            if b["idx"] in used_before:
                continue
            b_file = b["location"].split(":")[0] if b["location"] != "Evidence unavailable" else ""
            if not b_file:
                continue
            for a in after_list:
                if a["idx"] in used_after:
                    continue
                a_file = a["location"].split(":")[0] if a["location"] != "Evidence unavailable" else ""
                if a_file and b_file == a_file and b["asset_type"] == a["asset_type"]:
                    matched.append((b, a))
                    used_before.add(b["idx"])
                    used_after.add(a["idx"])
                    break

        # Rule 4: Match by (name, asset_type)
        for b in before_list:
            if b["idx"] in used_before:
                continue
            for a in after_list:
                if a["idx"] in used_after:
                    continue
                if b["name"] == a["name"] and b["asset_type"] == a["asset_type"]:
                    matched.append((b, a))
                    used_before.add(b["idx"])
                    used_after.add(a["idx"])
                    break

        unmatched_before = [b for b in before_list if b["idx"] not in used_before]
        unmatched_after = [a for a in after_list if a["idx"] not in used_after]

        return matched, unmatched_before, unmatched_after

    def _detect_property_changes(self, b_comp: Dict[str, Any], a_comp: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        diffs = {}

        fields_to_check = [
            ("algorithm", "Algorithm"),
            ("key_size", "Key Size / Parameter Set"),
            ("purpose", "Crypto Purpose / Primitive"),
            ("quantum_safety", "Quantum Safety Status"),
            ("security_level", "Classical Security Level")
        ]

        for key, label in fields_to_check:
            b_val = b_comp.get(key)
            a_val = a_comp.get(key)
            if b_val != a_val:
                diffs[key] = {
                    "label": label,
                    "before": b_val,
                    "after": a_val
                }

        return diffs

    def _build_error_response(self, status: str, error_msg: str) -> Dict[str, Any]:
        return {
            "status": status,
            "before_component_count": 0,
            "after_component_count": 0,
            "added_count": 0,
            "removed_count": 0,
            "changed_count": 0,
            "unchanged_count": 0,
            "added": [],
            "removed": [],
            "changed": [],
            "unchanged": [],
            "summary": [f"CBOM Comparison Error: {error_msg}"]
        }
