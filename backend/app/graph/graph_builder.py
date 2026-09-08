from typing import List, Dict, Any, Optional
from app.graph.dependency_graph import DependencyGraph

class GraphBuilder:
    """
    Deterministic Graph Builder for SENTRIQ.
    Constructs a DependencyGraph containing Project, Component, SourceFile, Package,
    CryptoAsset, Evidence, RiskAssessment, Recommendation, and MigrationTask nodes.
    """
    def __init__(self):
        self.dep_graph = DependencyGraph()

    def build_graph(
        self,
        assets: List[Any],
        project: Optional[Any] = None,
        risks: Optional[List[Any]] = None,
        recommendations: Optional[List[Any]] = None,
        tasks: Optional[List[Any]] = None
    ) -> DependencyGraph:

        # 1. Add Project Node if available
        project_node_id = None
        if project:
            project_id = getattr(project, "id", "default_project")
            project_name = getattr(project, "name", "Project")
            project_node_id = f"project:{project_id}"
            self.dep_graph.add_node(
                node_id=project_node_id,
                node_type="Project",
                label=project_name,
                metadata={"repository_url": getattr(project, "repository_url", None)}
            )

        # Map locations to components/files
        components_map: Dict[str, str] = {}  # location -> component_name

        for asset in assets:
            asset_id = getattr(asset, "id", None)
            if not asset_id:
                continue

            asset_node_id = f"asset:{asset_id}"
            alg_name = getattr(asset, "algorithm_name", "UNKNOWN")
            location = getattr(asset, "location", "unknown_file.py")
            asset_type_val = asset.asset_type.value if hasattr(asset, "asset_type") and hasattr(asset.asset_type, "value") else str(getattr(asset, "asset_type", "ALGORITHM"))
            purpose_val = asset.purpose.value if hasattr(asset, "purpose") and hasattr(asset.purpose, "value") else str(getattr(asset, "purpose", "UNKNOWN"))

            # Derive Component Name from location path (e.g. backend/app/auth -> auth)
            parts = [p for p in location.replace("\\", "/").split("/") if p and p not in [".", ".."]]
            if len(parts) > 1:
                comp_name = parts[-2]
            else:
                comp_name = "Core"

            comp_node_id = f"component:{comp_name}"
            file_node_id = f"file:{location}"

            # 2. Add Component Node
            self.dep_graph.add_node(
                node_id=comp_node_id,
                node_type="Component",
                label=comp_name,
                metadata={"component_name": comp_name}
            )

            if project_node_id:
                self.dep_graph.add_edge(
                    source_id=project_node_id,
                    target_id=comp_node_id,
                    relationship="contains",
                    provenance="project_structure"
                )

            # 3. Add SourceFile / Binary / Container Node
            file_type = "SourceFile"
            if asset_type_val == "CONTAINER":
                file_type = "Container"
            elif asset_type_val == "BINARY":
                file_type = "Binary"
            elif asset_type_val == "CERTIFICATE":
                file_type = "Certificate"
            elif asset_type_val == "DEPENDENCY":
                file_type = "Package"

            self.dep_graph.add_node(
                node_id=file_node_id,
                node_type=file_type,
                label=location,
                metadata={"location": location}
            )

            self.dep_graph.add_edge(
                source_id=comp_node_id,
                target_id=file_node_id,
                relationship="contains",
                provenance="file_system"
            )

            # 4. Add CryptoAsset Node
            self.dep_graph.add_node(
                node_id=asset_node_id,
                node_type="CryptoAsset",
                label=getattr(asset, "name", f"{alg_name} ({location})"),
                metadata={
                    "algorithm_name": alg_name,
                    "purpose": purpose_val,
                    "location": location,
                    "asset_type": asset_type_val,
                    "quantum_safety": asset.quantum_safety.value if hasattr(asset, "quantum_safety") and hasattr(asset.quantum_safety, "value") else str(getattr(asset, "quantum_safety", "UNKNOWN"))
                }
            )

            # SourceFile uses CryptoAsset
            self.dep_graph.add_edge(
                source_id=file_node_id,
                target_id=asset_node_id,
                relationship="uses",
                provenance="source_scanner"
            )

            # CryptoAsset impacts Component
            self.dep_graph.add_edge(
                source_id=asset_node_id,
                target_id=comp_node_id,
                relationship="impacts",
                provenance="impact_analysis"
            )

            # 4b. Add Cross-Component References (cryptoRefArray / references)
            extra_metadata = getattr(asset, "extra_metadata", {}) or {}
            extra_refs = []
            if isinstance(extra_metadata, dict):
                extra_refs.extend(extra_metadata.get("references", []) or [])
                extra_refs.extend(extra_metadata.get("cryptoRefArray", []) or [])

            for ev in getattr(asset, "evidence_items", []) or []:
                sf = getattr(ev, "source_file", None)
                if sf and sf != location:
                    extra_refs.append(sf)

            for ref_path in set(extra_refs):
                ref_parts = [p for p in ref_path.replace("\\", "/").split("/") if p and p not in [".", ".."]]
                ref_comp_name = ref_parts[-2] if len(ref_parts) > 1 else "Core"
                ref_comp_id = f"component:{ref_comp_name}"
                ref_file_id = f"file:{ref_path}"

                # Ensure Component & SourceFile nodes exist for cross-component reference
                self.dep_graph.add_node(
                    node_id=ref_comp_id,
                    node_type="Component",
                    label=ref_comp_name,
                    metadata={"component_name": ref_comp_name}
                )
                self.dep_graph.add_node(
                    node_id=ref_file_id,
                    node_type="SourceFile",
                    label=ref_path,
                    metadata={"location": ref_path}
                )
                self.dep_graph.add_edge(
                    source_id=ref_comp_id,
                    target_id=ref_file_id,
                    relationship="contains",
                    provenance="file_system"
                )
                self.dep_graph.add_edge(
                    source_id=ref_file_id,
                    target_id=asset_node_id,
                    relationship="uses",
                    provenance="cross_component_reference"
                )
                self.dep_graph.add_edge(
                    source_id=asset_node_id,
                    target_id=ref_comp_id,
                    relationship="impacts",
                    provenance="impact_analysis"
                )

            # 5. Add Evidence Items

            evidence_items = getattr(asset, "evidence_items", []) or []
            for ev in evidence_items:
                ev_id = getattr(ev, "id", None)
                if not ev_id:
                    continue
                ev_node_id = f"evidence:{ev_id}"
                detector = getattr(ev, "detector_name", "Scanner")
                self.dep_graph.add_node(
                    node_id=ev_node_id,
                    node_type="Evidence",
                    label=f"Evidence: {detector}",
                    metadata={
                        "detector_name": detector,
                        "source_file": getattr(ev, "source_file", location),
                        "confidence_score": getattr(ev, "confidence_score", 1.0)
                    }
                )
                self.dep_graph.add_edge(
                    source_id=asset_node_id,
                    target_id=ev_node_id,
                    relationship="supported_by",
                    provenance="scanner_evidence"
                )

        # 6. Add Risk Assessments
        if risks:
            for ra in risks:
                ra_id = getattr(ra, "id", None)
                asset_id = getattr(ra, "asset_id", None)
                if not ra_id or not asset_id:
                    continue
                ra_node_id = f"risk:{ra_id}"
                asset_node_id = f"asset:{asset_id}"
                if asset_node_id in self.dep_graph.graph:
                    r_level = ra.risk_level.value if hasattr(ra, "risk_level") and hasattr(ra.risk_level, "value") else str(getattr(ra, "risk_level", "LOW"))
                    self.dep_graph.add_node(
                        node_id=ra_node_id,
                        node_type="RiskAssessment",
                        label=f"Risk: {r_level} ({getattr(ra, 'risk_score', 0.0):.1f})",
                        metadata={
                            "risk_score": getattr(ra, "risk_score", 0.0),
                            "risk_level": r_level
                        }
                    )
                    self.dep_graph.add_edge(
                        source_id=asset_node_id,
                        target_id=ra_node_id,
                        relationship="has_risk",
                        provenance="risk_engine"
                    )

        # 7. Add Recommendations
        if recommendations:
            for rec in recommendations:
                rec_id = getattr(rec, "id", None)
                asset_id = getattr(rec, "asset_id", None)
                if not rec_id or not asset_id:
                    continue
                rec_node_id = f"recommendation:{rec_id}"
                asset_node_id = f"asset:{asset_id}"
                if asset_node_id in self.dep_graph.graph:
                    cand = getattr(rec, "target_pqc_candidate", "ML-KEM")
                    self.dep_graph.add_node(
                        node_id=rec_node_id,
                        node_type="Recommendation",
                        label=f"Rec: {cand}",
                        metadata={
                            "target_pqc_candidate": cand,
                            "recommended_algorithm": getattr(rec, "recommended_algorithm", cand),
                            "priority": getattr(rec, "priority", "LOW")
                        }
                    )
                    self.dep_graph.add_edge(
                        source_id=asset_node_id,
                        target_id=rec_node_id,
                        relationship="has_recommendation",
                        provenance="recommendation_engine"
                    )

        # 8. Add Migration Tasks
        if tasks:
            task_node_map = {}
            for t in tasks:
                t_id = getattr(t, "id", None)
                asset_id = getattr(t, "asset_id", None)
                if not t_id:
                    continue
                task_node_id = f"task:{t_id}"
                task_node_map[t_id] = task_node_id
                title = getattr(t, "title", "Migration Task")
                task_type = getattr(t, "task_type", "ALGORITHM_REPLACEMENT")
                self.dep_graph.add_node(
                    node_id=task_node_id,
                    node_type="MigrationTask",
                    label=title,
                    metadata={
                        "task_type": task_type,
                        "status": getattr(t, "status", "NOT_STARTED"),
                        "priority": getattr(t, "priority", "P2")
                    }
                )
                if asset_id:
                    asset_node_id = f"asset:{asset_id}"
                    if asset_node_id in self.dep_graph.graph:
                        self.dep_graph.add_edge(
                            source_id=asset_node_id,
                            target_id=task_node_id,
                            relationship="requires",
                            provenance="migration_planner"
                        )

            # Add Task -> Task dependencies
            for t in tasks:
                t_id = getattr(t, "id", None)
                deps = getattr(t, "dependencies", []) or []
                if t_id and deps:
                    curr_node_id = f"task:{t_id}"
                    for dep in deps:
                        dep_node_id = task_node_map.get(dep, f"task:{dep}")
                        if dep_node_id in self.dep_graph.graph:
                            self.dep_graph.add_edge(
                                source_id=curr_node_id,
                                target_id=dep_node_id,
                                relationship="depends_on",
                                provenance="task_ordering"
                            )

        return self.dep_graph


def build_project_graph(
    assets: List[Any],
    project: Optional[Any] = None,
    risks: Optional[List[Any]] = None,
    recommendations: Optional[List[Any]] = None,
    tasks: Optional[List[Any]] = None
) -> DependencyGraph:
    builder = GraphBuilder()
    return builder.build_graph(assets, project=project, risks=risks, recommendations=recommendations, tasks=tasks)
