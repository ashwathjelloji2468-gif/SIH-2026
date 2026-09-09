import collections
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from app.models.db_models import Scan, CryptoAsset, CryptoNode, CryptoEdge, BlastRadiusResult, RiskAssessment
from app.core.logging import logger

class BlastRadiusEngine:
    """
    Engine for Stage 8: Graph Construction, Edge Inference, & Blast Radius Calculation.
    """

    @staticmethod
    def _map_risk_weight(quantum_risk: str) -> float:
        risk_upper = str(quantum_risk).upper()
        if any(term in risk_upper for term in ["CRITICAL", "QUANTUM_VULNERABLE", "SHOR", "VULNERABLE", "RSA", "ECC", "ECDSA"]):
            return 1.0
        elif "HIGH" in risk_upper:
            return 0.8
        elif any(term in risk_upper for term in ["MODERATE", "MEDIUM", "TRANSITIONAL"]):
            return 0.5
        else:
            return 0.25

    @staticmethod
    def _infer_data_classes(node_name: str, location: str, extra_metadata: Dict[str, Any]) -> List[str]:
        data_classes = set()
        combined = f"{node_name} {location} {str(extra_metadata)}".lower()

        if any(k in combined for k in ["auth", "jwt", "login", "password", "token", "session"]):
            data_classes.add("AUTHENTICATION_CREDENTIALS")
        if any(k in combined for k in ["bank", "payment", "card", "billing", "transaction", "amount"]):
            data_classes.add("FINANCIAL_RECORDS")
        if any(k in combined for k in ["health", "patient", "medical", "record", "hipaa"]):
            data_classes.add("PHI_HEALTH_DATA")
        if any(k in combined for k in ["user", "email", "ssn", "identity", "profile"]):
            data_classes.add("PII_PERSONAL_DATA")
        if any(k in combined for k in ["cert", "ca", "pem", "signature", "key"]):
            data_classes.add("SYSTEM_PKI_KEYS")

        if not data_classes:
            data_classes.add("INTERNAL_APPLICATION_DATA")

        return sorted(list(data_classes))

    def build_graph_for_scan(self, scan_id: str, db: Session) -> Dict[str, Any]:
        """
        Converts all discovered findings for scan_id into CryptoNodes and CryptoEdges.
        Persists nodes and edges to DB.
        """
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Scan '{scan_id}' not found for graph construction.")
            return {"nodes": [], "edges": []}

        assets = db.query(CryptoAsset).filter(CryptoAsset.scan_id == scan_id).all()
        risk_map = {}
        risk_assessments = db.query(RiskAssessment).join(CryptoAsset).filter(CryptoAsset.scan_id == scan_id).all()
        for ra in risk_assessments:
            risk_map[ra.asset_id] = ra

        # Wipe existing nodes/edges for clean rebuild
        db.query(CryptoEdge).filter(CryptoEdge.scan_id == scan_id).delete()
        db.query(CryptoNode).filter(CryptoNode.scan_id == scan_id).delete()
        db.commit()

        created_nodes: Dict[str, CryptoNode] = {}  # node_key -> CryptoNode
        created_edges_set: Set[tuple] = set()       # (src_id, tgt_id, relation_type)

        def get_or_create_node(
            node_key: str,
            name: str,
            artefact_type: str,
            location: Optional[str] = None,
            asset_id: Optional[str] = None,
            quantum_risk: str = "LOW",
            mosca_x: float = 10.0,
            business_criticality: float = 50.0,
            extra_metadata: Optional[Dict[str, Any]] = None
        ) -> CryptoNode:
            if node_key in created_nodes:
                return created_nodes[node_key]

            node = CryptoNode(
                scan_id=scan_id,
                asset_id=asset_id,
                artefact_type=artefact_type,
                name=name,
                location=location,
                quantum_risk=quantum_risk,
                mosca_x=mosca_x,
                business_criticality=business_criticality,
                extra_metadata=extra_metadata or {}
            )
            db.add(node)
            db.flush()  # assign ID
            created_nodes[node_key] = node
            return node

        def add_edge(src_node_id: str, tgt_node_id: str, relation_type: str, strength: float = 1.0, metadata: Optional[Dict[str, Any]] = None):
            if src_node_id == tgt_node_id:
                return
            edge_tuple = (src_node_id, tgt_node_id, relation_type)
            if edge_tuple in created_edges_set:
                return
            created_edges_set.add(edge_tuple)
            edge = CryptoEdge(
                scan_id=scan_id,
                source_node_id=src_node_id,
                target_node_id=tgt_node_id,
                relation_type=relation_type,
                strength=strength,
                extra_metadata=metadata or {}
            )
            db.add(edge)

        # 1. Create nodes for all CryptoAssets
        shared_fingerprint_map: Dict[str, List[CryptoNode]] = collections.defaultdict(list)
        shared_filename_map: Dict[str, List[CryptoNode]] = collections.defaultdict(list)

        for asset in assets:
            loc = asset.location or "unknown"
            q_safety = str(getattr(asset.quantum_safety, "value", asset.quantum_safety))
            ra = risk_map.get(asset.id)
            q_risk = ra.risk_level.value if (ra and hasattr(ra, "risk_level") and hasattr(ra.risk_level, "value")) else ("QUANTUM_VULNERABLE" if "VULNERABLE" in q_safety.upper() else "LOW")
            mosca_x = asset.data_lifetime_years
            crit_score = asset.business_criticality_score

            a_type = asset.asset_type.value if hasattr(asset.asset_type, "value") else str(asset.asset_type)

            asset_node = get_or_create_node(
                node_key=f"asset:{asset.id}",
                name=asset.name or f"{asset.algorithm_name} ({loc})",
                artefact_type=a_type,
                location=loc,
                asset_id=asset.id,
                quantum_risk=q_risk,
                mosca_x=mosca_x,
                business_criticality=crit_score,
                extra_metadata=asset.extra_metadata or {}
            )

            # File node
            file_node = get_or_create_node(
                node_key=f"file:{loc}",
                name=loc,
                artefact_type="FILE",
                location=loc,
                quantum_risk="LOW",
                mosca_x=10.0,
                business_criticality=crit_score
            )

            # Component node
            parts = [p for p in loc.replace("\\", "/").split("/") if p and p not in [".", ".."]]
            comp_name = parts[-2] if len(parts) > 1 else "CoreService"
            comp_node = get_or_create_node(
                node_key=f"comp:{comp_name}",
                name=comp_name,
                artefact_type="COMPONENT",
                location=loc,
                quantum_risk="LOW",
                mosca_x=10.0,
                business_criticality=crit_score
            )

            # Component contains File, File uses Asset
            add_edge(comp_node.id, file_node.id, "depends_on", strength=1.0)
            add_edge(file_node.id, asset_node.id, "uses", strength=1.0)

            # Track shared cert/key fingerprints
            extra_meta = asset.extra_metadata or {}
            fingerprint = extra_meta.get("fingerprint") or extra_meta.get("cert_serial") or extra_meta.get("key_id")
            if fingerprint:
                shared_fingerprint_map[str(fingerprint)].append(asset_node)

            # Track shared certificate/key files (e.g. shared-cert.pem)
            basename = loc.split("/")[-1].split("\\")[-1]
            if any(ext in basename.lower() for ext in [".pem", ".crt", ".key", "shared", "cert"]):
                shared_filename_map[basename].append(asset_node)

            # Handle cross-component references in extra_metadata
            refs = []
            if isinstance(extra_meta, dict):
                refs.extend(extra_meta.get("references", []) or [])
                refs.extend(extra_meta.get("cryptoRefArray", []) or [])

            for ref_file in set(refs):
                ref_file_node = get_or_create_node(
                    node_key=f"file:{ref_file}",
                    name=ref_file,
                    artefact_type="FILE",
                    location=ref_file,
                    quantum_risk="LOW",
                    mosca_x=10.0,
                    business_criticality=crit_score
                )
                add_edge(ref_file_node.id, asset_node.id, "uses", strength=0.9)
                add_edge(file_node.id, ref_file_node.id, "depends_on", strength=0.9)

        # 2. Infer 'shares_key' edges for matching fingerprints / shared key files
        for f_print, nodes_list in shared_fingerprint_map.items():
            if len(nodes_list) > 1:
                for i in range(len(nodes_list)):
                    for j in range(i + 1, len(nodes_list)):
                        add_edge(nodes_list[i].id, nodes_list[j].id, "shares_key", strength=1.0, metadata={"fingerprint": f_print})
                        add_edge(nodes_list[j].id, nodes_list[i].id, "shares_key", strength=1.0, metadata={"fingerprint": f_print})

        for fname, nodes_list in shared_filename_map.items():
            if len(nodes_list) > 1:
                for i in range(len(nodes_list)):
                    for j in range(i + 1, len(nodes_list)):
                        add_edge(nodes_list[i].id, nodes_list[j].id, "shares_key", strength=0.8, metadata={"shared_file": fname})
                        add_edge(nodes_list[j].id, nodes_list[i].id, "shares_key", strength=0.8, metadata={"shared_file": fname})

        db.commit()
        all_nodes = db.query(CryptoNode).filter(CryptoNode.scan_id == scan_id).all()
        all_edges = db.query(CryptoEdge).filter(CryptoEdge.scan_id == scan_id).all()

        logger.info(f"BlastRadiusEngine: Built graph for scan {scan_id} ({len(all_nodes)} nodes, {len(all_edges)} edges).")
        return {"scan_id": scan_id, "nodes": all_nodes, "edges": all_edges}

    def calculate_blast_radius(
        self,
        root_node_id: str,
        scan_id: str,
        db: Session,
        max_hops: int = 3,
        preloaded_nodes: Optional[Dict[str, CryptoNode]] = None,
        preloaded_adj: Optional[Dict[str, List[tuple]]] = None,
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Performs BFS up to max_hops from root_node_id to compute reachable affected nodes,
        weighted impact score, affected systems, data classes, and estimated effort.
        """
        node_map = preloaded_nodes
        if node_map is None:
            all_nodes_list = db.query(CryptoNode).filter(CryptoNode.scan_id == scan_id).all()
            if not all_nodes_list and scan_id:
                # If scan_id was a project_id or scan_id matched 0 nodes, try querying via Scan -> project_id
                all_nodes_list = (
                    db.query(CryptoNode)
                    .join(Scan, CryptoNode.scan_id == Scan.id)
                    .filter(Scan.project_id == scan_id)
                    .all()
                )
            node_map = {n.id: n for n in all_nodes_list}

        root_node = node_map.get(root_node_id)
        if not root_node:
            root_node = next((n for n in node_map.values() if n.asset_id == root_node_id), None)

        if not root_node:
            # Fallback: Direct DB query for root_node by id or asset_id across all scans
            root_node = db.query(CryptoNode).filter(
                (CryptoNode.id == root_node_id) | (CryptoNode.asset_id == root_node_id)
            ).first()
            if root_node:
                scan_id = root_node.scan_id
                all_nodes_list = db.query(CryptoNode).filter(CryptoNode.scan_id == scan_id).all()
                node_map = {n.id: n for n in all_nodes_list}

        if not root_node:
            return {
                "scan_id": scan_id,
                "root_node_id": root_node_id,
                "root_node_name": "Unknown",
                "root_node_type": "Unknown",
                "radius_score": 0.0,
                "affected_nodes_count": 0,
                "systems_count": 0,
                "data_classes": [],
                "estimated_migration_effort": 0.0,
                "affected_nodes": [],
                "affected_systems": []
            }

        adj = preloaded_adj
        if adj is None:
            all_edges = db.query(CryptoEdge).filter(CryptoEdge.scan_id == scan_id).all()
            adj = collections.defaultdict(list)
            for e in all_edges:
                adj[e.source_node_id].append((e.target_node_id, e.relation_type))
                adj[e.target_node_id].append((e.source_node_id, f"reverse_{e.relation_type}"))

        # BFS Traversal
        visited: Dict[str, int] = {root_node.id: 0}  # node_id -> min_distance
        paths: Dict[str, List[str]] = {root_node.id: [root_node.name]}
        queue = collections.deque([(root_node.id, 0, [root_node.name])])

        while queue:
            curr_id, dist, path = queue.popleft()
            if dist >= max_hops:
                continue

            for neighbor_id, rel in adj.get(curr_id, []):
                if neighbor_id not in visited:
                    visited[neighbor_id] = dist + 1
                    neighbor_node = node_map.get(neighbor_id)
                    n_name = neighbor_node.name if neighbor_node else 'Node'
                    new_path = path + [f"--({rel})--> {n_name}"]
                    paths[neighbor_id] = new_path
                    queue.append((neighbor_id, dist + 1, new_path))

        # Compute Blast Radius metrics across affected nodes (excluding root itself)
        affected_nodes_list = []
        total_weighted_impact = 0.0
        affected_systems = set()
        affected_data_classes = set()
        estimated_effort = 0.0

        # Include root node characteristics in data classes and effort
        root_data_classes = self._infer_data_classes(root_node.name, root_node.location or "", root_node.extra_metadata or {})
        affected_data_classes.update(root_data_classes)
        estimated_effort += 1.5 if any(k in str(root_node.quantum_risk).upper() for k in ["VULNERABLE", "SHOR", "CRITICAL", "HIGH"]) else 0.5

        for node_id, dist in visited.items():
            if node_id == root_node.id:
                continue

            n = node_map.get(node_id)
            if not n:
                continue

            risk_weight = self._map_risk_weight(n.quantum_risk)
            crit_weight = (n.business_criticality or 50.0) / 100.0
            mosca_weight = max(0.5, min(2.0, (n.mosca_x or 10.0) / 5.0))
            inv_dist = 1.0 / (1.0 + 0.5 * (dist - 1))

            node_impact = round(risk_weight * crit_weight * mosca_weight * inv_dist * 100.0, 1)
            total_weighted_impact += node_impact

            rel_path = paths.get(node_id, [])

            affected_nodes_list.append({
                "node_id": n.id,
                "name": n.name,
                "artefact_type": n.artefact_type,
                "location": n.location,
                "quantum_risk": n.quantum_risk,
                "distance": dist,
                "relation_path": rel_path,
                "impact_score": node_impact
            })

            # Derive system/component
            if n.location:
                parts = [p for p in n.location.replace("\\", "/").split("/") if p and p not in [".", ".."]]
                if len(parts) > 1:
                    affected_systems.add(parts[-2])
                else:
                    affected_systems.add("CoreService")

            # Data classes
            n_data_classes = self._infer_data_classes(n.name, n.location or "", n.extra_metadata or {})
            affected_data_classes.update(n_data_classes)

            # Effort estimation
            if n.artefact_type in ["ALGORITHM", "KEY", "CERTIFICATE"]:
                estimated_effort += 2.0 if any(k in str(n.quantum_risk).upper() for k in ["VULNERABLE", "SHOR", "CRITICAL", "HIGH"]) else 0.5
            elif n.artefact_type in ["FILE", "COMPONENT"]:
                estimated_effort += 1.0

        # Overall blast radius score (0 - 100 scale)
        if len(affected_nodes_list) == 0:
            risk_w = self._map_risk_weight(root_node.quantum_risk)
            crit_w = (root_node.business_criticality or 50.0) / 100.0
            mosca_w = max(0.5, min(2.0, (root_node.mosca_x or 10.0) / 5.0))
            radius_score = round(min(100.0, max(5.0, risk_w * crit_w * mosca_w * 80.0)), 1)
        else:
            avg_impact = total_weighted_impact / len(affected_nodes_list)
            volume_multiplier = min(2.5, 1.0 + (len(affected_nodes_list) * 0.15))
            radius_score = round(min(100.0, max(5.0, avg_impact * volume_multiplier)), 1)

        result_payload = {
            "scan_id": scan_id,
            "root_node_id": root_node.id,
            "root_node_name": root_node.name,
            "root_node_type": root_node.artefact_type,
            "radius_score": radius_score,
            "affected_nodes_count": len(affected_nodes_list),
            "systems_count": max(1, len(affected_systems)),
            "data_classes": sorted(list(affected_data_classes)),
            "estimated_migration_effort": round(estimated_effort, 1),
            "affected_nodes": affected_nodes_list,
            "affected_systems": sorted(list(affected_systems))
        }

        if save_to_db:
            db.query(BlastRadiusResult).filter(
                BlastRadiusResult.scan_id == scan_id,
                BlastRadiusResult.root_node_id == root_node.id
            ).delete()

            db_res = BlastRadiusResult(
                scan_id=scan_id,
                root_node_id=root_node.id,
                radius_score=radius_score,
                affected_nodes_count=len(affected_nodes_list),
                systems_count=max(1, len(affected_systems)),
                data_classes=sorted(list(affected_data_classes)),
                estimated_migration_effort=round(estimated_effort, 1),
                affected_nodes_json=affected_nodes_list
            )
            db.add(db_res)
            db.commit()
            result_payload["id"] = db_res.id

        return result_payload

    def get_top_blast_radii_for_project(self, project_id: str, db: Session) -> Dict[str, Any]:
        """
        Computes top 10 largest blast radii, shared key alerts, and single points of failure for a project.
        """
        latest_scan = db.query(Scan).filter(Scan.project_id == project_id, Scan.status == "COMPLETED").order_by(Scan.created_at.desc()).first()
        if not latest_scan:
            return {
                "project_id": project_id,
                "top_blast_radii": [],
                "shared_credentials_high_impact": [],
                "single_points_of_failure": []
            }

        all_nodes_list = db.query(CryptoNode).filter(CryptoNode.scan_id == latest_scan.id).all()
        if not all_nodes_list:
            # Auto-build graph if missing
            self.build_graph_for_scan(latest_scan.id, db)
            all_nodes_list = db.query(CryptoNode).filter(CryptoNode.scan_id == latest_scan.id).all()

        node_map = {n.id: n for n in all_nodes_list}
        all_edges = db.query(CryptoEdge).filter(CryptoEdge.scan_id == latest_scan.id).all()
        adj: Dict[str, List[tuple]] = collections.defaultdict(list)
        for e in all_edges:
            adj[e.source_node_id].append((e.target_node_id, e.relation_type))
            adj[e.target_node_id].append((e.source_node_id, f"reverse_{e.relation_type}"))

        calculated_results = []
        for n in all_nodes_list:
            res = self.calculate_blast_radius(
                n.id, latest_scan.id, db, max_hops=3,
                preloaded_nodes=node_map, preloaded_adj=adj, save_to_db=False
            )
            calculated_results.append(res)

        # Sort top blast radii by score descending
        top_blast_radii = sorted(calculated_results, key=lambda r: r["radius_score"], reverse=True)[:10]

        # Identify shared credentials with high impact
        shared_edges = [e for e in all_edges if e.relation_type == "shares_key"]

        shared_credentials = []
        processed_pairs = set()
        for e in shared_edges:
            src = db.query(CryptoNode).filter(CryptoNode.id == e.source_node_id).first()
            tgt = db.query(CryptoNode).filter(CryptoNode.id == e.target_node_id).first()
            if src and tgt:
                pair_key = tuple(sorted([src.id, tgt.id]))
                if pair_key not in processed_pairs:
                    processed_pairs.add(pair_key)
                    shared_credentials.append({
                        "credential_name": src.name,
                        "source_location": src.location,
                        "target_location": tgt.location,
                        "shared_metadata": e.extra_metadata,
                        "risk_level": src.quantum_risk,
                        "impact_description": f"Shared key/cert credential between '{src.location}' and '{tgt.location}'"
                    })

        # Single Points of Failure: Nodes with degree >= 2 or high blast radius
        single_points = []
        for r in top_blast_radii:
            if r["affected_nodes_count"] >= 2 or r["radius_score"] >= 60.0:
                single_points.append({
                    "node_id": r["root_node_id"],
                    "node_name": r["root_node_name"],
                    "node_type": r["root_node_type"],
                    "radius_score": r["radius_score"],
                    "affected_systems_count": r["systems_count"],
                    "risk_level": "CRITICAL" if r["radius_score"] >= 75.0 else "HIGH"
                })

        return {
            "project_id": project_id,
            "top_blast_radii": top_blast_radii,
            "shared_credentials_high_impact": shared_credentials,
            "single_points_of_failure": single_points
        }
